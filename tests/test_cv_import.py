from app.cv_import import build_profile_draft_from_cv


def test_build_profile_draft_from_text_cv() -> None:
    content = b"""
Ana Silva
ana@example.com
(11) 99999-9999
Estudante com projetos em Python, SQL, FastAPI e Excel.
Busco estagio em dados ou backend.
"""

    draft = build_profile_draft_from_cv("cv.txt", content)

    assert draft.profile.full_name == "Ana Silva"
    assert draft.profile.email == "ana@example.com"
    assert draft.profile.phone == "(11) 99999-9999"
    assert draft.extracted_skills == ["Python", "FastAPI", "SQL", "Excel"]
    assert "Estagio" in draft.profile.target_roles
