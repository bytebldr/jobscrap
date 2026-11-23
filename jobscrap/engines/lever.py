"""Lever Postings v0 Direct Career Engine."""

from datetime import datetime, timezone
from typing import Any, Dict, List
from jobscrap.core.models import CompanyProfile, JobListing
from jobscrap.engines.base import BaseCareerEngine

class LeverEngine(BaseCareerEngine):
    name = "lever"

    def _parse_job(self, item: Dict[str, Any], company: CompanyProfile) -> JobListing:
        job_id = str(item.get("id"))
        title = item.get("text", "Untitled Opening").strip()
        url = item.get("applyUrl") or item.get("hostedUrl") or f"https://jobs.lever.co/{company.ats_identifier}/{job_id}"
        
        cats = item.get("categories") or {}
        location = cats.get("location") or "India"
        commitment = cats.get("commitment", "Full-time")
        department = cats.get("department") or cats.get("team")
        is_remote = "remote" in location.lower() or "remote" in title.lower() or cats.get("workplaceType") == "remote"

        desc = item.get("descriptionPlain") or ""
        
        posted_date = None
        if item.get("createdAt"):
            try:
                ms = item["createdAt"]
                dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
                posted_date = dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        return JobListing(
            id=f"lever_{company.id}_{job_id}",
            source="lever",
            source_type="ats",
            company=company.name,
            title=title,
            location=location,
            url=url,
            description=desc[:3000],
            is_remote=is_remote,
            job_type="internship" if "intern" in commitment.lower() else "fulltime",
            department=department,
            posted_date=posted_date,
            raw_metadata={"lever_id": job_id, "categories": cats}
        )

    def fetch_jobs(self, company: CompanyProfile) -> List[JobListing]:
        token = company.ats_identifier or company.id
        url = f"https://api.lever.co/v0/postings/{token}?mode=json"
        resp = self.session.get_sync(url)
        data = resp.json()
        if not isinstance(data, list):
            data = []
        return [self._parse_job(j, company) for j in data]

    async def fetch_jobs_async(self, company: CompanyProfile) -> List[JobListing]:
        token = company.ats_identifier or company.id
        url = f"https://api.lever.co/v0/postings/{token}?mode=json"
        resp = await self.session.get_async(url)
        data = resp.json()
        if not isinstance(data, list):
            data = []
        return [self._parse_job(j, company) for j in data]
