from collections.abc import Iterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.cv_import import build_profile_draft_from_cv
from app.cv_pdf import generate_cv_pdf
from app.database import Database
from app.job_discovery import discover_jobs
from app.job_import import import_job_draft
from app.job_search import build_search_plan
from app.matching import analyze_match
from app.models import (
    ApplicationRecord,
    CreateApplicationRequest,
    CvProfileDraft,
    CvGenerationRequest,
    CvGenerationResponse,
    JobDiscoveryResponse,
    JobPosting,
    JobImportDraft,
    JobImportRequest,
    JobRecommendation,
    JobSearchPlan,
    JobSearchRequest,
    MatchRequest,
    MatchResult,
    StoredJob,
    StoredProfile,
    UpdateApplicationStatusRequest,
    UserProfile,
)

settings = get_settings()
database = Database(settings.database_path)
static_dir = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI) -> Iterator[None]:
    database.init()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def get_database() -> Iterator[Database]:
    yield database


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/match", response_model=MatchResult)
def match_profile_to_job(request: MatchRequest) -> MatchResult:
    return analyze_match(request.profile, request.job)


@app.post("/cv", response_model=CvGenerationResponse)
def create_cv(request: CvGenerationRequest) -> CvGenerationResponse:
    match = analyze_match(request.profile, request.job)
    pdf_path = generate_cv_pdf(request.profile, request.job, settings.storage_dir)
    return CvGenerationResponse(filename=pdf_path.name, path=str(pdf_path), match=match)


@app.post("/job-search/links", response_model=JobSearchPlan)
def create_job_search_links(request: JobSearchRequest) -> JobSearchPlan:
    return build_search_plan(request)


@app.post("/job-import/draft", response_model=JobImportDraft)
def create_job_import_draft(request: JobImportRequest) -> JobImportDraft:
    try:
        return import_job_draft(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/cv-import/profile-draft", response_model=CvProfileDraft)
async def create_profile_draft_from_cv(file: UploadFile = File(...)) -> CvProfileDraft:
    content = await file.read()
    return build_profile_draft_from_cv(file.filename or "cv.txt", content)


@app.post("/profiles", response_model=StoredProfile, status_code=201)
def create_profile(profile: UserProfile, db: Database = Depends(get_database)) -> StoredProfile:
    return db.create_profile(profile)


@app.get("/profiles", response_model=list[StoredProfile])
def list_profiles(db: Database = Depends(get_database)) -> list[StoredProfile]:
    return db.list_profiles()


@app.get("/profiles/{profile_id}", response_model=StoredProfile)
def get_profile(profile_id: int, db: Database = Depends(get_database)) -> StoredProfile:
    profile = db.get_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.post("/jobs", response_model=StoredJob, status_code=201)
def create_job(job: JobPosting, db: Database = Depends(get_database)) -> StoredJob:
    return db.create_job(job)


@app.get("/jobs", response_model=list[StoredJob])
def list_jobs(db: Database = Depends(get_database)) -> list[StoredJob]:
    return db.list_jobs()


@app.get("/jobs/{job_id}", response_model=StoredJob)
def get_job(job_id: int, db: Database = Depends(get_database)) -> StoredJob:
    job = db.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/profiles/{profile_id}/recommendations", response_model=list[JobRecommendation])
def recommend_jobs(
    profile_id: int,
    minimum_score: int = 60,
    limit: int = 20,
    db: Database = Depends(get_database),
) -> list[JobRecommendation]:
    stored_profile = db.get_profile(profile_id)
    if stored_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    recommendations = [
        JobRecommendation(
            job_id=stored_job.id,
            job=stored_job.job,
            match=analyze_match(stored_profile.profile, stored_job.job),
        )
        for stored_job in db.list_jobs()
    ]
    qualified = [
        recommendation
        for recommendation in recommendations
        if recommendation.match.score >= minimum_score
    ]
    return sorted(qualified, key=lambda recommendation: recommendation.match.score, reverse=True)[:limit]


@app.post("/profiles/{profile_id}/discover-jobs", response_model=JobDiscoveryResponse)
def discover_jobs_for_profile(
    profile_id: int,
    limit_per_term: int = 10,
    max_age_days: int = 14,
    minimum_score: int = 50,
    save_top: int = 0,
    db: Database = Depends(get_database),
) -> JobDiscoveryResponse:
    stored_profile = db.get_profile(profile_id)
    if stored_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    discovered_jobs = discover_jobs(
        stored_profile.profile,
        google_api_key=settings.google_api_key,
        google_search_engine_id=settings.google_search_engine_id,
        limit_per_term=limit_per_term,
        max_age_days=max_age_days,
        minimum_score=minimum_score,
    )

    imported_count = 0
    for discovered in discovered_jobs[: max(0, save_top)]:
        db.create_job(discovered.job)
        imported_count += 1

    return JobDiscoveryResponse(
        profile_id=profile_id,
        source=(
            "remotive+google"
            if settings.google_api_key and settings.google_search_engine_id
            else "remotive"
        ),
        imported_count=imported_count,
        jobs=discovered_jobs,
    )


@app.post("/applications", response_model=ApplicationRecord, status_code=201)
def create_application(
    request: CreateApplicationRequest,
    db: Database = Depends(get_database),
) -> ApplicationRecord:
    stored_profile = db.get_profile(request.profile_id)
    if stored_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    stored_job = db.get_job(request.job_id)
    if stored_job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    match = analyze_match(stored_profile.profile, stored_job.job)
    cv_filename = None
    cv_path = None
    if request.generate_cv:
        pdf_path = generate_cv_pdf(stored_profile.profile, stored_job.job, settings.storage_dir)
        cv_filename = pdf_path.name
        cv_path = str(pdf_path)

    return db.create_application(
        profile_id=request.profile_id,
        job_id=request.job_id,
        match=match,
        cv_filename=cv_filename,
        cv_path=cv_path,
    )


@app.get("/applications", response_model=list[ApplicationRecord])
def list_applications(db: Database = Depends(get_database)) -> list[ApplicationRecord]:
    return db.list_applications()


@app.patch("/applications/{application_id}/status", response_model=ApplicationRecord)
def update_application_status(
    application_id: int,
    request: UpdateApplicationStatusRequest,
    db: Database = Depends(get_database),
) -> ApplicationRecord:
    application = db.update_application_status(application_id, request)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application
