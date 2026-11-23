"""Greenhouse Board API Direct Career Engine."""

import html
import re
from typing import Any, Dict, List
from jobscrap.core.models import CompanyProfile, JobListing
from jobscrap.engines.base import BaseCareerEngine

class GreenhouseEngine(BaseCareerEngine):
    name = "greenhouse"

    def _parse_job(self, item: Dict[str, Any], company: CompanyProfile) -> JobListing:
        job_id = str(item.get("id"))
        title = item.get("title", "Untitled Opening").strip()
        url = item.get("absolute_url") or f"https://boards.greenhouse.io/{company.ats_identifier}/jobs/{job_id}"
        
        loc_data = item.get("location") or {}
        location = loc_data.get("name") if isinstance(loc_data, dict) else str(loc_data)
        location = location.strip() if location else "India"
        is_remote = "remote" in location.lower() or "remote" in title.lower()

        # Clean description HTML
        raw_content = item.get("content") or ""
        clean_desc = re.sub(r"<[^>]+>", " ", html.unescape(raw_content))
        clean_desc = re.sub(r"\s+", " ", clean_desc).strip()

        departments = item.get("departments") or []
        dept_name = departments[0].get("name") if departments and isinstance(departments[0], dict) else None

        return JobListing(
            id=f"gh_{company.id}_{job_id}",
            source="greenhouse",
            source_type="ats",
            company=company.name,
            title=title,
            location=location,
            url=url,
            description=clean_desc[:3000],
            is_remote=is_remote,
            department=dept_name,
            posted_date=item.get("updated_at", "")[:10] or None,
            raw_metadata={"greenhouse_id": job_id, "internal_code": item.get("internal_job_id")}
        )

    def fetch_jobs(self, company: CompanyProfile) -> List[JobListing]:
        token = company.ats_identifier or company.id
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        resp = self.session.get_sync(url)
        data = resp.json()
        jobs_raw = data.get("jobs", [])
        return [self._parse_job(j, company) for j in jobs_raw]

    async def fetch_jobs_async(self, company: CompanyProfile) -> List[JobListing]:
        token = company.ats_identifier or company.id
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        resp = await self.session.get_async(url)
        data = resp.json()
        jobs_raw = data.get("jobs", [])
        return [self._parse_job(j, company) for j in jobs_raw]
