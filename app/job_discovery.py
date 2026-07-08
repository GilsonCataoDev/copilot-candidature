import json
from datetime import UTC, datetime, timedelta
from html import unescape
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.job_import import extract_skills
from app.matching import analyze_match
from app.models import DiscoveredJob, JobPosting, UserProfile


REMOTIVE_ENDPOINT = "https://remotive.com/api/remote-jobs"
GOOGLE_SEARCH_ENDPOINT = "https://www.googleapis.com/customsearch/v1"
TERM_EXPANSIONS = {
    "estagio": ["internship", "intern", "junior"],
    "estágio": ["internship", "intern", "junior"],
    "service desk": ["service desk", "help desk", "IT support", "technical support"],
    "help desk": ["help desk", "service desk", "IT support", "technical support"],
    "suporte": ["IT support", "technical support", "support analyst", "help desk"],
    "atendimento": ["customer support", "technical support", "support specialist"],
    "dados": ["data analyst", "data science", "business intelligence"],
    "analista": ["analyst"],
    "desenvolvedor": ["developer", "software engineer"],
    "backend": ["backend developer", "python developer"],
    "frontend": ["frontend developer", "react developer"],
}


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
    terms = [*profile.target_roles, *profile.skills[:6]]
    expanded_terms = []
    for term in terms:
        clean_term = term.strip()
        if not clean_term:
            continue
        expanded_terms.append(clean_term)
        normalized = clean_term.casefold()
        for trigger, expansions in TERM_EXPANSIONS.items():
            if trigger in normalized:
                expanded_terms.extend(expansions)
    if not expanded_terms:
        expanded_terms = ["python", "data analyst", "developer", "internship"]

    deduped_terms = []
    seen = set()
    for term in expanded_terms:
        normalized = term.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped_terms.append(term)
    return deduped_terms[:10]


def google_queries_for_profile(profile: UserProfile) -> list[str]:
    base_terms = search_terms_for_profile(profile)
    skill_terms = " ".join(profile.skills[:4])
    location = profile.location or "Brasil remoto"
    queries = []
    for term in base_terms:
        queries.append(
            " ".join(
                part
                for part in [
                    term,
                    skill_terms,
                    "vaga OR estagio",
                    location,
                    "site:gupy.io OR site:jobs.lever.co OR site:greenhouse.io OR site:linkedin.com/jobs",
                ]
                if part
            )
        )
    return queries


def fetch_remotive_jobs(search: str, limit: int) -> list[dict]:
    params = urlencode({"search": search, "limit": limit})
    request = Request(
        f"{REMOTIVE_ENDPOINT}?{params}",
        headers={"User-Agent": "CopilotCandidature/0.1 (+https://github.com/GilsonCataoDev)"},
    )
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("jobs", [])


def fetch_google_jobs(query: str, limit: int, api_key: str, search_engine_id: str) -> list[dict]:
    params = urlencode(
        {
            "key": api_key,
            "cx": search_engine_id,
            "q": query,
            "num": min(max(limit, 1), 10),
            "dateRestrict": "m1",
        }
    )
    request = Request(
        f"{GOOGLE_SEARCH_ENDPOINT}?{params}",
        headers={"User-Agent": "CopilotCandidature/0.1"},
    )
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("items", [])


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


def map_google_result(raw_result: dict) -> JobPosting:
    title = raw_result.get("title") or "Vaga encontrada no Google"
    snippet = raw_result.get("snippet") or ""
    display_link = raw_result.get("displayLink") or "Fonte Google"
    extracted_skills = extract_skills(f"{title} {snippet}")
    return JobPosting(
        title=title,
        company=display_link,
        description=snippet or "Descricao resumida encontrada pelo Google. Abrir link para revisar.",
        url=raw_result.get("link"),
        location=None,
        contract_type=infer_google_contract_type(f"{title} {snippet}"),
        required_skills=extracted_skills,
    )


def infer_google_contract_type(text: str) -> str:
    normalized = text.casefold()
    if "estagio" in normalized or "estágio" in normalized or "internship" in normalized:
        return "internship"
    if "pj" in normalized:
        return "pj"
    if "clt" in normalized:
        return "clt"
    return "other"


def is_recent(raw_job: dict, max_age_days: int) -> bool:
    if max_age_days <= 0:
        return True
    publication_date = raw_job.get("publication_date")
    if not publication_date:
        return True
    parsed = datetime.fromisoformat(publication_date.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed >= datetime.now(UTC) - timedelta(days=max_age_days)


def discover_remotive_jobs(
    profile: UserProfile,
    limit_per_term: int = 10,
    max_age_days: int = 14,
    minimum_score: int = 50,
) -> list[DiscoveredJob]:
    discovered: dict[str, DiscoveredJob] = {}
    candidates: dict[str, DiscoveredJob] = {}

    for term in search_terms_for_profile(profile):
        for raw_job in fetch_remotive_jobs(term, limit_per_term):
            source_id = str(raw_job.get("id"))
            if source_id in candidates or not is_recent(raw_job, max_age_days):
                continue
            job = map_remotive_job(raw_job)
            match = analyze_match(profile, job)
            candidate = DiscoveredJob(
                source="remotive",
                source_id=source_id,
                job=job,
                match=match,
                published_at=raw_job.get("publication_date"),
            )
            candidates[source_id] = candidate
            if match.score < minimum_score:
                continue
            discovered[source_id] = candidate

    if not discovered:
        discovered = dict(
            sorted(
                candidates.items(),
                key=lambda item: (item[1].match.score, item[1].published_at or ""),
                reverse=True,
            )[:10]
        )

    return sorted(
        discovered.values(),
        key=lambda item: (item.match.score, item.published_at or ""),
        reverse=True,
    )


def discover_google_jobs(
    profile: UserProfile,
    api_key: str | None,
    search_engine_id: str | None,
    limit_per_term: int = 10,
    minimum_score: int = 35,
) -> list[DiscoveredJob]:
    if not api_key or not search_engine_id:
        return []

    discovered: dict[str, DiscoveredJob] = {}
    for query in google_queries_for_profile(profile):
        for raw_result in fetch_google_jobs(query, limit_per_term, api_key, search_engine_id):
            url = raw_result.get("link")
            if not url or url in discovered:
                continue
            job = map_google_result(raw_result)
            match = analyze_match(profile, job)
            if match.score < minimum_score:
                continue
            discovered[url] = DiscoveredJob(
                source="google",
                source_id=url,
                job=job,
                match=match,
                published_at=None,
            )

    return sorted(discovered.values(), key=lambda item: item.match.score, reverse=True)


def discover_jobs(
    profile: UserProfile,
    google_api_key: str | None = None,
    google_search_engine_id: str | None = None,
    limit_per_term: int = 10,
    max_age_days: int = 14,
    minimum_score: int = 40,
) -> list[DiscoveredJob]:
    discovered = [
        *discover_remotive_jobs(
            profile,
            limit_per_term=limit_per_term,
            max_age_days=max_age_days,
            minimum_score=minimum_score,
        ),
        *discover_google_jobs(
            profile,
            api_key=google_api_key,
            search_engine_id=google_search_engine_id,
            limit_per_term=limit_per_term,
            minimum_score=max(20, minimum_score - 10),
        ),
    ]
    unique: dict[str, DiscoveredJob] = {}
    for item in discovered:
        key = str(item.job.url or item.source_id)
        if key not in unique or item.match.score > unique[key].match.score:
            unique[key] = item
    return sorted(unique.values(), key=lambda item: item.match.score, reverse=True)
