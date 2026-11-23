"""AshbyHQ GraphQL Direct Career Engine."""

from typing import Any, Dict, List
from curl_cffi.requests import AsyncSession, Session
from jobscrap.core.models import CompanyProfile, JobListing
from jobscrap.engines.base import BaseCareerEngine

ASHBY_GRAPHQL_URL = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"

ASHBY_QUERY = (
    "query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {"
    "  jobBoard: jobBoardWithTeams(organizationHostedJobsPageName: $organizationHostedJobsPageName) {"
    "    jobPostings {"
    "      id"
    "      title"
    "      locationName"
    "      teamId"
    "    }"
    "  }"
    "}"
)

class AshbyEngine(BaseCareerEngine):
    name = "ashby"

    def _parse_job(self, item: Dict[str, Any], company: CompanyProfile, org_name: str) -> JobListing:
        job_id = str(item.get("id"))
        title = item.get("title", "Untitled Opening").strip()
        location = item.get("locationName") or "India"
        is_remote = "remote" in location.lower() or "remote" in title.lower()

        url = f"https://jobs.ashbyhq.com/{org_name}/{job_id}"

        return JobListing(
            id=f"ashby_{company.id}_{job_id}",
            source="ashby",
            source_type="ats",
            company=company.name,
            title=title,
            location=location,
            url=url,
            is_remote=is_remote,
            job_type="fulltime",
            department=item.get("teamId"),
            raw_metadata={"ashby_id": job_id, "team_id": item.get("teamId")}
        )

    def fetch_jobs(self, company: CompanyProfile) -> List[JobListing]:
        org_name = company.ats_identifier or company.id
        body = {
            "operationName": "ApiJobBoardWithTeams",
            "variables": {"organizationHostedJobsPageName": org_name},
            "query": ASHBY_QUERY
        }
        with Session(headers={"Content-Type": "application/json", "User-Agent": self.config.user_agent}) as s:
            resp = s.post(ASHBY_GRAPHQL_URL, json=body, timeout=self.config.timeout_seconds)
            resp.raise_for_status()
            data = resp.json()
            job_board = data.get("data", {}).get("jobBoard") or {}
            postings = job_board.get("jobPostings", [])
            return [self._parse_job(p, company, org_name) for p in postings]

    async def fetch_jobs_async(self, company: CompanyProfile) -> List[JobListing]:
        org_name = company.ats_identifier or company.id
        body = {
            "operationName": "ApiJobBoardWithTeams",
            "variables": {"organizationHostedJobsPageName": org_name},
            "query": ASHBY_QUERY
        }
        async with AsyncSession(headers={"Content-Type": "application/json", "User-Agent": self.config.user_agent}) as s:
            resp = await s.post(ASHBY_GRAPHQL_URL, json=body, timeout=self.config.timeout_seconds)
            resp.raise_for_status()
            data = resp.json()
            job_board = data.get("data", {}).get("jobBoard") or {}
            postings = job_board.get("jobPostings", [])
            return [self._parse_job(p, company, org_name) for p in postings]
