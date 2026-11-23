"""Workday Career Experience (CX) Direct Career Engine."""

import re
from typing import Any, Dict, List
from curl_cffi.requests import AsyncSession, Session
from jobscrap.core.models import CompanyProfile, JobListing
from jobscrap.engines.base import BaseCareerEngine

class WorkdayEngine(BaseCareerEngine):
    name = "workday"

    def _parse_job(self, item: Dict[str, Any], company: CompanyProfile, base_url: str, site_name: str) -> JobListing:
        path = item.get("externalPath") or ""
        job_id = re.sub(r"[^a-zA-Z0-9_-]", "", path.split("/")[-1]) if path else "job"
        title = item.get("title", "Untitled Opening").strip()
        location = item.get("locationsText") or "India"
        is_remote = "remote" in location.lower() or "remote" in title.lower()
        
        url = f"{base_url}/en-US/{site_name}{path}" if path.startswith("/") else f"{base_url}/{path}"

        return JobListing(
            id=f"wd_{company.id}_{job_id}",
            source="workday",
            source_type="ats",
            company=company.name,
            title=title,
            location=location,
            url=url,
            is_remote=is_remote,
            job_type="fulltime",
            raw_metadata={"workday_path": path, "bullet_fields": item.get("bulletFields", [])}
        )

    def _get_endpoint(self, company: CompanyProfile):
        tenant = company.ats_identifier or company.id
        site = "Careers"
        base = f"https://{tenant}.wd3.myworkdayjobs.com"
        endpoint = f"{base}/wday/cxs/{tenant}/{site}/jobs"
        return endpoint, base, site

    def fetch_jobs(self, company: CompanyProfile) -> List[JobListing]:
        endpoint, base, site = self._get_endpoint(company)
        payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}
        try:
            with Session(headers={"Content-Type": "application/json", "User-Agent": self.config.user_agent}) as s:
                resp = s.post(endpoint, json=payload, timeout=self.config.timeout_seconds)
                resp.raise_for_status()
                data = resp.json()
                postings = data.get("jobPostings", [])
                return [self._parse_job(p, company, base, site) for p in postings]
        except Exception:
            return []

    async def fetch_jobs_async(self, company: CompanyProfile) -> List[JobListing]:
        endpoint, base, site = self._get_endpoint(company)
        payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}
        try:
            async with AsyncSession(headers={"Content-Type": "application/json", "User-Agent": self.config.user_agent}) as s:
                resp = await s.post(endpoint, json=payload, timeout=self.config.timeout_seconds)
                resp.raise_for_status()
                data = resp.json()
                postings = data.get("jobPostings", [])
                return [self._parse_job(p, company, base, site) for p in postings]
        except Exception:
            return []
