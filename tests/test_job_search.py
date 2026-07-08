from app.job_search import build_search_plan
from app.models import JobSearchRequest, SearchProvider


def test_build_search_plan_generates_provider_links() -> None:
    plan = build_search_plan(
        JobSearchRequest(
            role="Desenvolvedor Python",
            location="Sao Paulo",
            remote=True,
            internship=True,
            skills=["FastAPI", "SQL"],
        )
    )

    providers = {search.provider for search in plan.searches}

    assert providers == {SearchProvider.linkedin, SearchProvider.indeed, SearchProvider.google}
    assert all("Desenvolvedor" in search.query for search in plan.searches)
    assert any("linkedin.com/jobs/search" in search.url for search in plan.searches)


def test_build_search_plan_respects_selected_providers() -> None:
    plan = build_search_plan(
        JobSearchRequest(
            role="Analista de Dados",
            providers=[SearchProvider.google],
        )
    )

    assert len(plan.searches) == 1
    assert plan.searches[0].provider == SearchProvider.google
