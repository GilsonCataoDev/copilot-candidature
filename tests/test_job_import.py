from app.job_import import import_job_draft
from app.models import JobImportRequest


SAMPLE_HTML = """
<!doctype html>
<html>
  <head>
    <title>Estagio Backend - Acme</title>
    <meta property="og:description" content="Vaga para atuar com Python, FastAPI, SQL e Git." />
  </head>
  <body>
    <main>
      Buscamos pessoa estudante para estagio remoto com Docker como diferencial.
    </main>
  </body>
</html>
"""


def test_import_job_draft_extracts_job_data_from_html() -> None:
    draft = import_job_draft(
        JobImportRequest(
            url="https://example.com/jobs/1",
            html=SAMPLE_HTML,
            fallback_location="Remoto",
        )
    )

    assert draft.job.title == "Estagio Backend"
    assert draft.job.company == "Acme"
    assert draft.job.location == "Remoto"
    assert draft.job.contract_type == "internship"
    assert draft.job.required_skills == ["Python", "FastAPI", "SQL", "Git", "Docker"]


def test_import_job_draft_marks_uncertain_fields_for_review() -> None:
    draft = import_job_draft(
        JobImportRequest(
            url="https://example.com/jobs/2",
            html="<html><body>Texto generico sem metadados.</body></html>",
        )
    )

    assert draft.job.company == "Empresa a revisar"
    assert draft.review_notes
