import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from pydantic import BaseModel

from app.models import (
    ApplicationRecord,
    ApplicationStatus,
    JobPosting,
    MatchResult,
    StoredJob,
    StoredProfile,
    UpdateApplicationStatusRequest,
    UserProfile,
)


def encode_model(model: BaseModel) -> str:
    return model.model_dump_json()


def decode_json(raw: str) -> dict:
    return json.loads(raw)


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def init(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payload TEXT NOT NULL,
                    url TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER NOT NULL,
                    job_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    match_payload TEXT NOT NULL,
                    cv_filename TEXT,
                    cv_path TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (profile_id) REFERENCES profiles (id),
                    FOREIGN KEY (job_id) REFERENCES jobs (id)
                );
                """
            )

    def create_profile(self, profile: UserProfile) -> StoredProfile:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO profiles (payload) VALUES (?)",
                (encode_model(profile),),
            )
            profile_id = int(cursor.lastrowid)
        return StoredProfile(id=profile_id, profile=profile)

    def list_profiles(self) -> list[StoredProfile]:
        with self.connect() as connection:
            rows = connection.execute("SELECT id, payload FROM profiles ORDER BY id DESC").fetchall()
        return [
            StoredProfile(id=row["id"], profile=UserProfile.model_validate(decode_json(row["payload"])))
            for row in rows
        ]

    def get_profile(self, profile_id: int) -> StoredProfile | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id, payload FROM profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()
        if row is None:
            return None
        return StoredProfile(id=row["id"], profile=UserProfile.model_validate(decode_json(row["payload"])))

    def create_job(self, job: JobPosting) -> StoredJob:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO jobs (payload, url) VALUES (?, ?)",
                (encode_model(job), str(job.url) if job.url else None),
            )
            job_id = int(cursor.lastrowid)
        return StoredJob(id=job_id, job=job)

    def list_jobs(self) -> list[StoredJob]:
        with self.connect() as connection:
            rows = connection.execute("SELECT id, payload FROM jobs ORDER BY id DESC").fetchall()
        return [
            StoredJob(id=row["id"], job=JobPosting.model_validate(decode_json(row["payload"])))
            for row in rows
        ]

    def get_job(self, job_id: int) -> StoredJob | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id, payload FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return StoredJob(id=row["id"], job=JobPosting.model_validate(decode_json(row["payload"])))

    def create_application(
        self,
        profile_id: int,
        job_id: int,
        match: MatchResult,
        cv_filename: str | None = None,
        cv_path: str | None = None,
    ) -> ApplicationRecord:
        status = ApplicationStatus.pending_review
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO applications (
                    profile_id, job_id, status, match_payload, cv_filename, cv_path
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (profile_id, job_id, status.value, encode_model(match), cv_filename, cv_path),
            )
            application_id = int(cursor.lastrowid)
        return ApplicationRecord(
            id=application_id,
            profile_id=profile_id,
            job_id=job_id,
            status=status,
            match=match,
            cv_filename=cv_filename,
            cv_path=cv_path,
        )

    def list_applications(self) -> list[ApplicationRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, profile_id, job_id, status, match_payload, cv_filename, cv_path
                FROM applications
                ORDER BY id DESC
                """
            ).fetchall()
        return [
            ApplicationRecord(
                id=row["id"],
                profile_id=row["profile_id"],
                job_id=row["job_id"],
                status=ApplicationStatus(row["status"]),
                match=MatchResult.model_validate(decode_json(row["match_payload"])),
                cv_filename=row["cv_filename"],
                cv_path=row["cv_path"],
            )
            for row in rows
        ]

    def get_application(self, application_id: int) -> ApplicationRecord | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, profile_id, job_id, status, match_payload, cv_filename, cv_path
                FROM applications
                WHERE id = ?
                """,
                (application_id,),
            ).fetchone()
        if row is None:
            return None
        return ApplicationRecord(
            id=row["id"],
            profile_id=row["profile_id"],
            job_id=row["job_id"],
            status=ApplicationStatus(row["status"]),
            match=MatchResult.model_validate(decode_json(row["match_payload"])),
            cv_filename=row["cv_filename"],
            cv_path=row["cv_path"],
        )

    def update_application_status(
        self,
        application_id: int,
        request: UpdateApplicationStatusRequest,
    ) -> ApplicationRecord | None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE applications SET status = ? WHERE id = ?",
                (request.status.value, application_id),
            )
        return self.get_application(application_id)
