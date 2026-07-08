from app.job_discovery import (
    discover_google_jobs,
    discover_jobs,
    discover_remotive_jobs,
    is_recent,
    search_terms_for_profile,
)
from app.models import UserProfile, WorkMode


def test_discover_remotive_jobs_ranks_recent_matches(monkeypatch) -> None:
    def fake_fetch(search: str, limit: int) -> list[dict]:
        return [
            {
                "id": 101,
                "url": "https://remotive.com/remote-jobs/software-dev/python-dev-101",
                "title": "Python Developer",
                "company_name": "Acme",
                "description": "<p>Build APIs with Python and FastAPI.</p>",
                "candidate_required_location": "Worldwide",
                "tags": ["Python", "FastAPI", "SQL"],
                "publication_date": "2026-07-08T10:00:00Z",
            },
            {
                "id": 102,
                "url": "https://remotive.com/remote-jobs/design/designer-102",
                "title": "Designer",
                "company_name": "Design Co",
                "description": "<p>Design role.</p>",
                "candidate_required_location": "Worldwide",
                "tags": ["Figma"],
                "publication_date": "2026-07-08T10:00:00Z",
            },
        ]

    monkeypatch.setattr("app.job_discovery.fetch_remotive_jobs", fake_fetch)
    profile = UserProfile(
        full_name="Ana Silva",
        email="ana@example.com",
        skills=["Python", "FastAPI", "SQL"],
        target_roles=["Python Developer"],
        preferred_work_modes=[WorkMode.remote],
    )

    jobs = discover_remotive_jobs(profile, minimum_score=50)

    assert len(jobs) == 1
    assert jobs[0].source == "remotive"
    assert jobs[0].match.score == 90


def test_search_terms_expand_portuguese_profile_terms() -> None:
    profile = UserProfile(
        full_name="Ana Silva",
        email="ana@example.com",
        skills=["Python", "SQL"],
        target_roles=["Estagio em Dados"],
    )

    terms = search_terms_for_profile(profile)

    assert "Estagio em Dados" in terms
    assert "internship" in terms
    assert "data analyst" in terms
    assert "Python" in terms


def test_search_terms_expand_service_desk_terms() -> None:
    profile = UserProfile(
        full_name="Gilson Nascimento",
        email="gilson@example.com",
        skills=["Atendimento ao usuário", "Python"],
        target_roles=["Suporte de TI"],
    )

    terms = search_terms_for_profile(profile)

    assert "Suporte de TI" in terms
    assert "IT support" in terms
    assert "technical support" in terms
    assert "support analyst" in terms


def test_discover_remotive_jobs_returns_candidates_when_minimum_score_filters_all(
    monkeypatch,
) -> None:
    def fake_fetch(search: str, limit: int) -> list[dict]:
        return [
            {
                "id": 201,
                "url": "https://remotive.com/remote-jobs/software-dev/support-201",
                "title": "Support Engineer",
                "company_name": "Acme",
                "description": "<p>Support customers.</p>",
                "candidate_required_location": "Worldwide",
                "tags": ["Customer Support"],
                "publication_date": "2026-07-08T10:00:00Z",
            }
        ]

    monkeypatch.setattr("app.job_discovery.fetch_remotive_jobs", fake_fetch)
    profile = UserProfile(
        full_name="Ana Silva",
        email="ana@example.com",
        skills=["Python"],
        target_roles=["Estagio em Dados"],
    )

    jobs = discover_remotive_jobs(profile, minimum_score=100)

    assert len(jobs) == 1
    assert jobs[0].match.score < 100


def test_discover_google_jobs_uses_official_search_results(monkeypatch) -> None:
    def fake_google_fetch(query: str, limit: int, api_key: str, search_engine_id: str) -> list[dict]:
        return [
            {
                "title": "Estagio Python - Acme",
                "displayLink": "jobs.example.com",
                "link": "https://jobs.example.com/estagio-python",
                "snippet": "Vaga remota com Python, SQL e FastAPI.",
            }
        ]

    monkeypatch.setattr("app.job_discovery.fetch_google_jobs", fake_google_fetch)
    profile = UserProfile(
        full_name="Ana Silva",
        email="ana@example.com",
        skills=["Python", "FastAPI", "SQL"],
        target_roles=["Estagio Python"],
    )

    jobs = discover_google_jobs(profile, api_key="key", search_engine_id="cx", minimum_score=30)

    assert len(jobs) == 1
    assert jobs[0].source == "google"
    assert jobs[0].job.required_skills == ["Python", "FastAPI", "SQL"]


def test_discover_jobs_combines_sources(monkeypatch) -> None:
    monkeypatch.setattr("app.job_discovery.fetch_remotive_jobs", lambda *args, **kwargs: [])

    profile = UserProfile(full_name="Ana Silva", email="ana@example.com", skills=["Python"])
    jobs = discover_jobs(profile, google_api_key=None, google_search_engine_id=None)

    assert jobs == []


def test_is_recent_accepts_naive_publication_dates() -> None:
    assert is_recent({"publication_date": "2026-07-08T10:00:00"}, max_age_days=1)
