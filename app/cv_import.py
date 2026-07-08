import re
from io import BytesIO

from pypdf import PdfReader

from app.job_import import KNOWN_SKILLS, extract_skills
from app.models import CvProfileDraft, UserProfile


EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2}\)?[\s.-]?)?\d{4,5}[\s.-]?\d{4}")


def extract_text_from_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_upload(filename: str, content: bytes) -> str:
    lower_name = filename.casefold()
    if lower_name.endswith(".pdf"):
        return extract_text_from_pdf(content)
    return content.decode("utf-8", errors="replace")


def infer_target_roles(text: str) -> list[str]:
    normalized = text.casefold()
    roles = []
    if any(skill.casefold() in normalized for skill in ["python", "sql", "power bi", "excel"]):
        roles.append("Analista de Dados")
    if any(skill.casefold() in normalized for skill in ["python", "fastapi", "django", "node.js"]):
        roles.append("Desenvolvedor Backend")
    if any(skill.casefold() in normalized for skill in ["react", "javascript", "typescript"]):
        roles.append("Desenvolvedor Frontend")
    if "estagio" in normalized or "estágio" in normalized:
        roles.insert(0, "Estagio")
    return list(dict.fromkeys(roles))


def build_profile_draft_from_cv(filename: str, content: bytes) -> CvProfileDraft:
    text = extract_text_from_upload(filename, content)
    email_match = EMAIL_PATTERN.search(text)
    phone_match = PHONE_PATTERN.search(text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    full_name = lines[0] if lines else "Nome a revisar"
    extracted_skills = extract_skills(text)
    target_roles = infer_target_roles(text)

    review_notes = []
    if full_name == "Nome a revisar":
        review_notes.append("Nome nao identificado automaticamente.")
    if not email_match:
        review_notes.append("Email nao identificado automaticamente.")
    if not extracted_skills:
        review_notes.append(
            "Nenhuma skill conhecida foi detectada. Skills monitoradas: "
            + ", ".join(KNOWN_SKILLS)
        )
    if not target_roles:
        review_notes.append("Cargo alvo nao inferido automaticamente.")

    profile = UserProfile(
        full_name=full_name,
        email=email_match.group(0) if email_match else "email@revisar.local",
        phone=phone_match.group(0) if phone_match else None,
        summary=" ".join(lines[1:6])[:600] if len(lines) > 1 else None,
        skills=extracted_skills,
        target_roles=target_roles,
    )
    return CvProfileDraft(
        profile=profile,
        extracted_skills=extracted_skills,
        review_notes=review_notes,
    )
