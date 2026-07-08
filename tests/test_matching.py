from app.matching import analyze_match
from app.models import JobPosting, UserProfile, WorkMode


def test_match_prioritizes_required_skills_and_work_mode() -> None:
    profile = UserProfile(
        full_name="Ana Silva",
        email="ana@example.com",
        skills=["Python", "Excel", "SQL"],
        preferred_work_modes=[WorkMode.remote],
    )
    job = JobPosting(
        title="Estagio em Dados",
        company="Acme",
        description="Vaga para apoiar analises de dados.",
        work_mode=WorkMode.remote,
        contract_type="internship",
        required_skills=["Python", "SQL"],
        desired_skills=["Power BI", "Excel"],
    )

    result = analyze_match(profile, job)

    assert result.score == 90
    assert "Alta prioridade" in result.recommendation


def test_match_reports_missing_required_skills() -> None:
    profile = UserProfile(
        full_name="Ana Silva",
        email="ana@example.com",
        skills=["Excel"],
    )
    job = JobPosting(
        title="Estagio em Backend",
        company="Acme",
        description="Vaga para apoiar desenvolvimento.",
        required_skills=["Python", "FastAPI"],
    )

    result = analyze_match(profile, job)

    assert result.score < 60
    assert result.weak_points

