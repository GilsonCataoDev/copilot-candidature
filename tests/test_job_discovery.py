from app.job_discovery import discover_remotive_jobs
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
    assert jobs[0].match.score == 100
