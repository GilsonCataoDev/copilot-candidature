from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class WorkMode(str, Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"


class Experience(BaseModel):
    title: str
    organization: str
    start: str
    end: str | None = None
    description: str
    skills: list[str] = Field(default_factory=list)


class Education(BaseModel):
    course: str
    institution: str
    start: str | None = None
    end: str | None = None


class UserProfile(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    summary: str | None = None
    links: list[HttpUrl] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    preferred_work_modes: list[WorkMode] = Field(default_factory=list)


class JobPosting(BaseModel):
    title: str
    company: str
    description: str
    url: HttpUrl | None = None
    location: str | None = None
    work_mode: WorkMode | None = None
    contract_type: Literal["internship", "clt", "pj", "temporary", "other"] = "other"
    required_skills: list[str] = Field(default_factory=list)
    desired_skills: list[str] = Field(default_factory=list)


class MatchResult(BaseModel):
    score: int = Field(ge=0, le=100)
    strong_points: list[str]
    weak_points: list[str]
    recommendation: str


class MatchRequest(BaseModel):
    profile: UserProfile
    job: JobPosting


class CvGenerationRequest(BaseModel):
    profile: UserProfile
    job: JobPosting


class CvGenerationResponse(BaseModel):
    filename: str
    path: str
    match: MatchResult


class StoredProfile(BaseModel):
    id: int
    profile: UserProfile


class StoredJob(BaseModel):
    id: int
    job: JobPosting


class ApplicationStatus(str, Enum):
    pending_review = "pending_review"
    approved = "approved"
    submitted = "submitted"
    rejected = "rejected"


class ApplicationRecord(BaseModel):
    id: int
    profile_id: int
    job_id: int
    status: ApplicationStatus
    match: MatchResult
    cv_filename: str | None = None
    cv_path: str | None = None


class CreateApplicationRequest(BaseModel):
    profile_id: int
    job_id: int
    generate_cv: bool = True


class UpdateApplicationStatusRequest(BaseModel):
    status: ApplicationStatus


class JobRecommendation(BaseModel):
    job_id: int
    job: JobPosting
    match: MatchResult


class SearchProvider(str, Enum):
    linkedin = "linkedin"
    indeed = "indeed"
    google = "google"


class JobSearchRequest(BaseModel):
    role: str
    location: str | None = None
    remote: bool = False
    internship: bool = False
    skills: list[str] = Field(default_factory=list)
    providers: list[SearchProvider] = Field(
        default_factory=lambda: [
            SearchProvider.linkedin,
            SearchProvider.indeed,
            SearchProvider.google,
        ]
    )


class JobSearchLink(BaseModel):
    provider: SearchProvider
    label: str
    url: str
    query: str


class JobSearchPlan(BaseModel):
    searches: list[JobSearchLink]
