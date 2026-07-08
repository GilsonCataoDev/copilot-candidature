import json
from datetime import UTC, datetime, timedelta
from html import unescape
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.matching import analyze_match
from app.models import DiscoveredJob, JobPosting, UserProfile


REMOTIVE_ENDPOINT = "https://remotive.com/api/remote-jobs"


def strip_html(value: str) -> str:
    result = []
    in_tag = False
    for character in value:
        if character == "<":
            in_tag = True
        elif character == ">":
            in_tag = False
            result.append(" ")
        elif not in_tag:
            result.append(character)
    return " ".join(unescape("".join(result)).split())


def search_terms_for_profile(profile: UserProfile) -> list[str]:
    terms = profile.target_roles[:3]
    if not terms and profile.skills:
        terms = profile.skills[:3]
    if not terms:
        terms = ["python", "data", "developer"]
    return terms


def fetch_remotive_jobs(search: str, limit: int) -> list[dict]:
    params = urlencode({"search": search, "limit": limit})
    request = Request(
        f"{REMOTIVE_ENDPOINT}?{params}",
        headers={"User-Agent": "CopilotCandidature/0.1 (+https://github.com/GilsonCataoDev)"},
    )
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("jobs", [])


def map_remotive_job(raw_job: dict) -> JobPosting:
    tags = raw_job.get("tags") or []
    description = strip_html(raw_job.get("description") or "")
    return JobPosting(
        title=raw_job.get("title") or "Vaga sem titulo",
        company=raw_job.get("company_name") or "Empresa nao informada",
        description=description[:2400],
        url=raw_job.get("url"),
        location=raw_job.get("candidate_required_location") or "Remote",
        work_mode="remote",
        contract_type="other",
        required_skills=tags[:12],
    )


def is_recent(raw_job: dict, max_age_days: int) -> bool:
    if max_age_days <= 0:
        return True
    publication_date = raw_job.get("publication_date")
    if not publication_date:
        return True
    parsed = datetime.fromisoformat(publication_date.replace("Z", "+00:00"))
    return parsed >= datetime.now(UTC) - timedelta(days=max_age_days)


def discover_remotive_jobs(
    profile: UserProfile,
    limit_per_term: int = 10,
    max_age_days: int = 14,
    minimum_score: int = 50,
) -> list[DiscoveredJob]:
    discovered: dict[str, DiscoveredJob] = {}

    for term in search_terms_for_profile(profile):
        for raw_job in fetch_remotive_jobs(term, limit_per_term):
            source_id = str(raw_job.get("id"))
            if source_id in discovered or not is_recent(raw_job, max_age_days):
                continue
            job = map_remotive_job(raw_job)
            match = analyze_match(profile, job)
            if match.score < minimum_score:
                continue
            discovered[source_id] = DiscoveredJob(
                source="remotive",
                source_id=source_id,
                job=job,
                match=match,
                published_at=raw_job.get("publication_date"),
            )

    return sorted(
        discovered.values(),
        key=lambda item: (item.match.score, item.published_at or ""),
        reverse=True,
    )
