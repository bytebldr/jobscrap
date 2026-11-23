"""High-Level JobScraper Facade for JobScrap Library."""

import asyncio
import logging
from typing import List, Optional
from jobscrap.catalog.registry import CompanyCatalog
from jobscrap.core.config import JobScrapConfig
from jobscrap.core.models import CompanyProfile, JobListing
from jobscrap.discovery.resolver import CompanyResolver
from jobscrap.engines import get_engine
from jobscrap.pipeline.dedup import deduplicate_jobs

logger = logging.getLogger("jobscrap")

class JobScraper:
    """The unified direct company career scraper interface."""

    def __init__(self, config: Optional[JobScrapConfig] = None, catalog: Optional[CompanyCatalog] = None):
        self.config = config or JobScrapConfig()
        self.catalog = catalog or CompanyCatalog()
        self.resolver = CompanyResolver(catalog=self.catalog, config=self.config)

    def get_company_jobs(self, target: str) -> List[JobListing]:
        """Fetch all live jobs directly from a company's official career portal."""
        profile = self.resolver.resolve(target)
        engine = get_engine(profile.ats_type, config=self.config)
        return engine.fetch_jobs(profile)

    async def get_company_jobs_async(self, target: str) -> List[JobListing]:
        """Asynchronously fetch all live jobs directly from a company's official career portal."""
        profile = await self.resolver.resolve_async(target)
        engine = get_engine(profile.ats_type, config=self.config)
        return await engine.fetch_jobs_async(profile)

    async def search_companies_async(
        self,
        query: str,
        locations: Optional[List[str]] = None,
        companies: Optional[List[str]] = None,
        limit: int = 50,
        concurrency: int = 8,
    ) -> List[JobListing]:
        """
        Search for matching job titles/roles directly across multiple company career portals in parallel.
        """
        targets: List[CompanyProfile] = []
        if companies:
            for c in companies:
                try:
                    targets.append(self.resolver.resolve(c))
                except Exception as e:
                    logger.warning(f"Could not resolve target company '{c}': {e}")
        else:
            targets = self.catalog.all()

        sem = asyncio.Semaphore(concurrency)
        all_matches: List[JobListing] = []

        q_lower = query.strip().lower()
        loc_lowers = [l.strip().lower() for l in locations] if locations else []

        async def fetch_and_filter(comp: CompanyProfile) -> List[JobListing]:
            async with sem:
                try:
                    engine = get_engine(comp.ats_type, config=self.config)
                    jobs = await engine.fetch_jobs_async(comp)
                    matched = []
                    for j in jobs:
                        # Match title or department
                        title_match = q_lower in j.title.lower() or (j.department and q_lower in j.department.lower())
                        if not title_match:
                            continue
                        
                        # Match location if specified
                        if loc_lowers:
                            j_loc = j.location.lower()
                            if not any(l in j_loc for l in loc_lowers):
                                continue

                        matched.append(j)
                    return matched
                except Exception as err:
                    logger.debug(f"Failed fetching {comp.name}: {err}")
                    return []

        tasks = [fetch_and_filter(comp) for comp in targets]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, list):
                all_matches.extend(res)

        deduped = deduplicate_jobs(all_matches)
        return deduped[:limit]

    def search_companies(
        self,
        query: str,
        locations: Optional[List[str]] = None,
        companies: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[JobListing]:
        """Synchronous wrapper for search_companies_async."""
        return asyncio.run(
            self.search_companies_async(
                query=query, locations=locations, companies=companies, limit=limit
            )
        )
