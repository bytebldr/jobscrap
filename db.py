"""SQLite persistence store for JobListing records and search caching."""

import contextlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from jobscrap.core.models import JobListing

DB_PATH = Path(__file__).parent / "jobs.db"

@contextlib.contextmanager
def get_db(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db(db_path: Path = DB_PATH):
    with get_db(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'ats',
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT,
            url TEXT NOT NULL,
            description TEXT,
            is_remote INTEGER DEFAULT 0,
            job_type TEXT DEFAULT 'fulltime',
            experience_level TEXT DEFAULT 'mid',
            department TEXT,
            posted_date TEXT,
            scraped_at TEXT NOT NULL,
            status TEXT DEFAULT 'live',
            dedup_group_id TEXT,
            min_salary_inr INTEGER,
            max_salary_inr INTEGER
        );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);")

def upsert_job(job: JobListing, db_path: Path = DB_PATH):
    with get_db(db_path) as conn:
        conn.execute("""
        INSERT INTO jobs (
            id, source, source_type, company, title, location, url,
            description, is_remote, job_type, experience_level, department,
            posted_date, scraped_at, status, dedup_group_id, min_salary_inr, max_salary_inr
        ) VALUES (
            :id, :source, :source_type, :company, :title, :location, :url,
            :description, :is_remote, :job_type, :experience_level, :department,
            :posted_date, :scraped_at, :status, :dedup_group_id, :min_salary_inr, :max_salary_inr
        ) ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            location=excluded.location,
            url=excluded.url,
            status=excluded.status,
            scraped_at=excluded.scraped_at;
        """, {
            "id": job.id,
            "source": job.source,
            "source_type": job.source_type,
            "company": job.company,
            "title": job.title,
            "location": job.location,
            "url": job.url,
            "description": job.description,
            "is_remote": 1 if job.is_remote else 0,
            "job_type": job.job_type,
            "experience_level": job.experience_level,
            "department": job.department,
            "posted_date": job.posted_date,
            "scraped_at": job.scraped_at,
            "status": job.status,
            "dedup_group_id": job.dedup_group_id,
            "min_salary_inr": job.min_salary_inr,
            "max_salary_inr": job.max_salary_inr,
        })

def get_jobs_by_company(company: str, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    with get_db(db_path) as conn:
        rows = conn.execute("SELECT * FROM jobs WHERE company LIKE ? ORDER BY scraped_at DESC", (f"%{company}%",)).fetchall()
        return [dict(r) for r in rows]
