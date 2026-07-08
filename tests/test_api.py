from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.database import Database
from app.main import app, get_database


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    test_database = Database(tmp_path / "test.db")
    test_database.init()

    def override_database() -> Database:
        return test_database

    app.dependency_overrides[get_database] = override_database
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def sample_payload() -> dict:
    return {
        "profile": {
            "full_name": "Ana Silva",
            "email": "ana@example.com",
            "phone": "(11) 99999-9999",
            "location": "Sao Paulo, SP",
            "summary": "Estudante com projetos em analise de dados, Python e Excel.",
            "skills": ["Python", "Excel", "SQL"],
            "preferred_work_modes": ["remote"],
            "experiences": [
                {
                    "title": "Projeto de Analise de Dados",
                    "organization": "Faculdade",
                    "start": "2025",
                    "description": "Limpeza e analise de dados academicos usando Python.",
                    "skills": ["Python", "Excel"],
                }
            ],
            "education": [
                {
                    "course": "Analise e Desenvolvimento de Sistemas",
                    "institution": "Instituicao Exemplo",
                    "start": "2024",
                }
            ],
        },
        "job": {
            "title": "Estagio em Dados",
            "company": "Acme",
            "description": "Vaga para apoiar analises de dados.",
            "work_mode": "remote",
            "contract_type": "internship",
            "required_skills": ["Python", "SQL"],
            "desired_skills": ["Excel", "Power BI"],
        },
    }


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_match_endpoint(client: TestClient) -> None:
    response = client.post("/match", json=sample_payload())

    assert response.status_code == 200
    assert response.json()["score"] == 90


def test_cv_endpoint_generates_pdf(client: TestClient) -> None:
    response = client.post("/cv", json=sample_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["filename"].endswith(".pdf")
    assert Path(body["path"]).exists()
    assert body["match"]["score"] == 90


def test_job_search_links_endpoint(client: TestClient) -> None:
    response = client.post(
        "/job-search/links",
        json={
            "role": "Desenvolvedor Python",
            "location": "Sao Paulo",
            "remote": True,
            "internship": True,
            "skills": ["FastAPI", "SQL"],
        },
    )

    assert response.status_code == 200
    searches = response.json()["searches"]
    assert len(searches) == 3
    assert any(search["provider"] == "linkedin" for search in searches)


def test_profile_job_and_application_flow(client: TestClient) -> None:
    payload = sample_payload()
    profile_response = client.post("/profiles", json=payload["profile"])
    job_response = client.post("/jobs", json=payload["job"])

    assert profile_response.status_code == 201
    assert job_response.status_code == 201

    application_response = client.post(
        "/applications",
        json={
            "profile_id": profile_response.json()["id"],
            "job_id": job_response.json()["id"],
            "generate_cv": True,
        },
    )

    assert application_response.status_code == 201
    application = application_response.json()
    assert application["status"] == "pending_review"
    assert application["match"]["score"] == 90
    assert Path(application["cv_path"]).exists()

    list_response = client.get("/applications")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    status_response = client.patch(
        f"/applications/{application['id']}/status",
        json={"status": "approved"},
    )

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "approved"


def test_recommendations_rank_saved_jobs(client: TestClient) -> None:
    payload = sample_payload()
    profile_response = client.post("/profiles", json=payload["profile"])
    high_match_response = client.post("/jobs", json=payload["job"])
    low_match_payload = {
        **payload["job"],
        "title": "Estagio em Design",
        "required_skills": ["Figma", "Photoshop"],
        "desired_skills": ["Illustrator"],
    }
    low_match_response = client.post("/jobs", json=low_match_payload)

    assert profile_response.status_code == 201
    assert high_match_response.status_code == 201
    assert low_match_response.status_code == 201

    response = client.get(
        f"/profiles/{profile_response.json()['id']}/recommendations",
        params={"minimum_score": 0},
    )

    assert response.status_code == 200
    recommendations = response.json()
    assert [item["job_id"] for item in recommendations] == [
        high_match_response.json()["id"],
        low_match_response.json()["id"],
    ]
    assert recommendations[0]["match"]["score"] > recommendations[1]["match"]["score"]
