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


def test_build_profile_draft_detects_service_desk_cv() -> None:
    content = """
GILSON PEREIRA DO NASCIMENTO FILHO
Estagiário de Service Desk / Suporte de TI
Garanhuns - PE (100% remoto) | gilsonfilho96@outlook.com
Atendimento ao usuário, documentação de processos, base de conhecimento,
análise de causa raiz, LGPD, JavaScript, TypeScript, Python, Node.js e Git/GitHub.
""".encode()

    draft = build_profile_draft_from_cv("cv.txt", content)

    assert "Service Desk" in draft.profile.target_roles
    assert "Suporte de TI" in draft.profile.target_roles
    assert "Help Desk" in draft.profile.target_roles
    assert "Service Desk" in draft.extracted_skills
    assert "Atendimento ao usuário" in draft.extracted_skills
    assert "Base de conhecimento" in draft.extracted_skills
    assert "remote" in draft.profile.preferred_work_modes
