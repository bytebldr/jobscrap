"""SmartRecruiters Public Postings Direct Career Engine."""

from typing import Any, Dict, List
from jobscrap.core.models import CompanyProfile, JobListing
from jobscrap.engines.base import BaseCareerEngine

class SmartRecruitersEngine(BaseCareerEngine):
    name = "smartrecruiters"

    def _parse_job(self, item: Dict[str, Any], company: CompanyProfile) -> JobListing:
        job_id = str(item.get("id"))
        title = item.get("name", "Untitled Opening").strip()
        
        loc_data = item.get("location") or {}
        city = loc_data.get("city") or ""
        country = loc_data.get("country") or "India"
        location = f"{city}, {country}".strip(", ") if city else country
        is_remote = bool(loc_data.get("remote")) or "remote" in location.lower() or "remote" in title.lower()

        token = company.ats_identifier or company.id
        url = f"https://jobs.smartrecruiters.com/{token}/{job_id}"

        dept = (item.get("department") or {}).get("label")
        emp_type = (item.get("typeOfEmployment") or {}).get("label", "Full-time")

        return JobListing(
            id=f"sr_{company.id}_{job_id}",
            source="smartrecruiters",
            source_type="ats",
            company=company.name,
            title=title,
            location=location,
            url=url,
            is_remote=is_remote,
            job_type="internship" if "intern" in emp_type.lower() else "fulltime",
            department=dept,
            posted_date=str(item.get("releasedDate") or "")[:10] or None,
            raw_metadata={"smartrecruiters_id": job_id}
        )

    def fetch_jobs(self, company: CompanyProfile) -> List[JobListing]:
        token = company.ats_identifier or company.id
        url = f"https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100"
        resp = self.session.get_sync(url)
        data = resp.json()
        postings = data.get("content", [])
        return [self._parse_job(p, company) for p in postings]

    async def fetch_jobs_async(self, company: CompanyProfile) -> List[JobListing]:
        token = company.ats_identifier or company.id
        url = f"https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100"
        resp = await self.session.get_async(url)
        data = resp.json()
        postings = data.get("content", [])
        return [self._parse_job(p, company) for p in postings]
