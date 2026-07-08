from app.models import JobPosting, MatchResult, UserProfile


def normalize_skill(skill: str) -> str:
    return skill.strip().casefold()


def analyze_match(profile: UserProfile, job: JobPosting) -> MatchResult:
    profile_skills = {normalize_skill(skill) for skill in profile.skills}
    required = {normalize_skill(skill) for skill in job.required_skills}
    desired = {normalize_skill(skill) for skill in job.desired_skills}

    matched_required = sorted(required & profile_skills)
    missing_required = sorted(required - profile_skills)
    matched_desired = sorted(desired & profile_skills)

    required_score = 70 if not required else round(70 * len(matched_required) / len(required))
    desired_score = 20 if not desired else round(20 * len(matched_desired) / len(desired))
    mode_score = 10 if not job.work_mode or job.work_mode in profile.preferred_work_modes else 0
    score = min(100, required_score + desired_score + mode_score)

    strong_points = []
    if matched_required:
        strong_points.append("Requisitos obrigatorios atendidos: " + ", ".join(matched_required))
    if matched_desired:
        strong_points.append("Diferenciais presentes: " + ", ".join(matched_desired))
    if job.work_mode and job.work_mode in profile.preferred_work_modes:
        strong_points.append(f"Modalidade compativel: {job.work_mode.value}")

    weak_points = []
    if missing_required:
        weak_points.append("Requisitos obrigatorios ausentes: " + ", ".join(missing_required))
    if job.work_mode and job.work_mode not in profile.preferred_work_modes:
        weak_points.append(f"Modalidade fora da preferencia: {job.work_mode.value}")

    if score >= 80:
        recommendation = "Alta prioridade: gerar CV personalizado e revisar candidatura."
    elif score >= 60:
        recommendation = "Boa oportunidade: candidatar se a vaga fizer sentido para o momento."
    else:
        recommendation = "Baixa prioridade: revisar lacunas antes de candidatar."

    return MatchResult(
        score=score,
        strong_points=strong_points or ["Perfil possui informacoes suficientes para analise inicial."],
        weak_points=weak_points,
        recommendation=recommendation,
    )

