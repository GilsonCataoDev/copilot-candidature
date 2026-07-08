import re
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.models import JobImportDraft, JobImportRequest, JobPosting


KNOWN_SKILLS = [
    "Service Desk",
    "Help Desk",
    "Suporte de TI",
    "IT Support",
    "Technical Support",
    "Atendimento ao usuário",
    "Documentação de processos",
    "Base de conhecimento",
    "Análise de causa raiz",
    "Governança",
    "Conformidade",
    "LGPD",
    "CRUD",
    "API",
    "APIs",
    "Vercel",
    "Monitoramento",
    "Incidentes",
    "Python",
    "JavaScript",
    "TypeScript",
    "React",
    "Node.js",
    "FastAPI",
    "Django",
    "SQL",
    "PostgreSQL",
    "MySQL",
    "Excel",
    "Power BI",
    "Git",
    "GitHub",
    "Docker",
    "AWS",
    "Azure",
    "Scrum",
]


class JobHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.meta: dict[str, str] = {}
        self.text_parts: list[str] = []
        self._capture_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key.casefold(): value or "" for key, value in attrs}
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if tag == "title":
            self._capture_title = True
        if tag == "meta":
            key = attributes.get("property") or attributes.get("name")
            content = attributes.get("content")
            if key and content:
                self.meta[key.casefold()] = content.strip()

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag == "title":
            self._capture_title = False

    def handle_data(self, data: str) -> None:
        clean = " ".join(data.split())
        if not clean:
            return
        if self._capture_title:
            self.title = f"{self.title} {clean}".strip()
        elif self._skip_depth == 0:
            self.text_parts.append(clean)

    @property
    def visible_text(self) -> str:
        return " ".join(self.text_parts)


def fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 CopilotCandidature/0.1 (+guided job import)",
        },
    )
    try:
        with urlopen(request, timeout=10) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except URLError as error:
        raise ValueError(f"Could not fetch job URL: {error}") from error


def split_title_company(raw_title: str) -> tuple[str, str | None]:
    separators = [" | ", " - ", " at ", " em "]
    for separator in separators:
        if separator in raw_title:
            title, company = raw_title.split(separator, 1)
            return title.strip(), company.strip()
    return raw_title.strip(), None


def extract_skills(text: str) -> list[str]:
    return [
        skill
        for skill in KNOWN_SKILLS
        if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", text, flags=re.IGNORECASE)
    ]


def infer_contract_type(text: str) -> str:
    normalized = text.casefold()
    if "estagio" in normalized or "estágio" in normalized or "internship" in normalized:
        return "internship"
    if "pj" in normalized:
        return "pj"
    if "temporario" in normalized or "temporário" in normalized:
        return "temporary"
    if "clt" in normalized:
        return "clt"
    return "other"


def import_job_draft(request: JobImportRequest) -> JobImportDraft:
    html = request.html or fetch_html(str(request.url))
    parser = JobHtmlParser()
    parser.feed(html)

    raw_title = (
        parser.meta.get("og:title")
        or parser.meta.get("twitter:title")
        or parser.title
        or "Vaga importada"
    )
    title, title_company = split_title_company(raw_title)
    description = (
        parser.meta.get("og:description")
        or parser.meta.get("description")
        or parser.visible_text[:1800]
        or "Descricao nao encontrada automaticamente."
    )
    full_text = f"{raw_title} {description} {parser.visible_text}"
    extracted_skills = extract_skills(full_text)

    company = request.fallback_company or title_company or "Empresa a revisar"
    review_notes = []
    if company == "Empresa a revisar":
        review_notes.append("Empresa nao identificada automaticamente.")
    if title == "Vaga importada":
        review_notes.append("Titulo nao identificado automaticamente.")
    if description == "Descricao nao encontrada automaticamente.":
        review_notes.append("Descricao nao identificada automaticamente.")
    if not extracted_skills:
        review_notes.append("Nenhuma skill conhecida foi detectada; revisar requisitos manualmente.")

    job = JobPosting(
        title=title,
        company=company,
        description=description,
        url=request.url,
        location=request.fallback_location,
        contract_type=infer_contract_type(full_text),
        required_skills=extracted_skills,
    )
    return JobImportDraft(job=job, extracted_skills=extracted_skills, review_notes=review_notes)
