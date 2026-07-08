from pathlib import Path
from textwrap import wrap
from uuid import uuid4

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from app.models import JobPosting, UserProfile


PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 48
TOP_MARGIN = PAGE_HEIGHT - 48
LINE_HEIGHT = 14


def draw_wrapped(canvas: Canvas, text: str, x: int, y: int, width: int = 92) -> int:
    for line in wrap(text, width=width):
        canvas.drawString(x, y, line)
        y -= LINE_HEIGHT
    return y


def generate_cv_pdf(profile: UserProfile, job: JobPosting, storage_dir: Path) -> Path:
    storage_dir.mkdir(parents=True, exist_ok=True)
    safe_name = profile.full_name.lower().replace(" ", "-")
    filename = f"cv-{safe_name}-{uuid4().hex[:8]}.pdf"
    output_path = storage_dir / filename

    canvas = Canvas(str(output_path), pagesize=A4)
    y = TOP_MARGIN

    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(LEFT_MARGIN, y, profile.full_name)
    y -= 24

    canvas.setFont("Helvetica", 10)
    contact = " | ".join(item for item in [profile.email, profile.phone, profile.location] if item)
    canvas.drawString(LEFT_MARGIN, y, contact)
    y -= 26

    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(LEFT_MARGIN, y, f"Objetivo: {job.title} - {job.company}")
    y -= 20

    if profile.summary:
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(LEFT_MARGIN, y, "Resumo")
        y -= LINE_HEIGHT
        canvas.setFont("Helvetica", 10)
        y = draw_wrapped(canvas, profile.summary, LEFT_MARGIN, y)
        y -= 8

    if profile.skills:
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(LEFT_MARGIN, y, "Competencias")
        y -= LINE_HEIGHT
        canvas.setFont("Helvetica", 10)
        prioritized = sorted(
            profile.skills,
            key=lambda skill: skill.casefold() not in {s.casefold() for s in job.required_skills},
        )
        y = draw_wrapped(canvas, ", ".join(prioritized), LEFT_MARGIN, y)
        y -= 8

    if profile.experiences:
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(LEFT_MARGIN, y, "Experiencias")
        y -= LINE_HEIGHT
        for experience in profile.experiences:
            canvas.setFont("Helvetica-Bold", 10)
            period = f"{experience.start} - {experience.end or 'atual'}"
            canvas.drawString(
                LEFT_MARGIN,
                y,
                f"{experience.title} | {experience.organization} | {period}",
            )
            y -= LINE_HEIGHT
            canvas.setFont("Helvetica", 10)
            y = draw_wrapped(canvas, experience.description, LEFT_MARGIN, y)
            if experience.skills:
                y = draw_wrapped(canvas, "Skills: " + ", ".join(experience.skills), LEFT_MARGIN, y)
            y -= 8

    if profile.education:
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(LEFT_MARGIN, y, "Formacao")
        y -= LINE_HEIGHT
        canvas.setFont("Helvetica", 10)
        for education in profile.education:
            period = " - ".join(item for item in [education.start, education.end] if item)
            suffix = f" ({period})" if period else ""
            canvas.drawString(LEFT_MARGIN, y, f"{education.course} - {education.institution}{suffix}")
            y -= LINE_HEIGHT

    canvas.save()
    return output_path

