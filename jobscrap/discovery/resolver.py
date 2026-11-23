"""Autonomous Career Portal Discovery and Resolver."""

import re
from typing import Optional
import urllib.parse
from curl_cffi.requests import AsyncSession, Session

from jobscrap.catalog.registry import CompanyCatalog
from jobscrap.core.config import JobScrapConfig
from jobscrap.core.exceptions import CareerEngineNotFoundError, CompanyNotFoundError
from jobscrap.core.models import CompanyProfile
from jobscrap.discovery.detector import fingerprint_html

class CompanyResolver:
    """Discovers and resolves company career portals to their underlying ATS engine."""

    def __init__(self, catalog: Optional[CompanyCatalog] = None, config: Optional[JobScrapConfig] = None):
        self.catalog = catalog or CompanyCatalog()
        self.config = config or JobScrapConfig()

    def _normalize_domain(self, target: str) -> str:
        clean = target.strip().lower()
        if clean.startswith("http://") or clean.startswith("https://"):
            parsed = urllib.parse.urlparse(clean)
            return parsed.netloc.replace("www.", "")
        if "/" in clean:
            clean = clean.split("/")[0]
        return clean.replace("www.", "")

    def resolve(self, target: str) -> CompanyProfile:
        """
        Resolves a company name, domain, or URL into a CompanyProfile.
        First consults the catalog; if not found, dynamically probes the domain.
        """
        # 1. Check Catalog First
        existing = self.catalog.get(target)
        if existing:
            return existing

        domain = self._normalize_domain(target)
        name = domain.split(".")[0].capitalize()

        candidates = [
            f"https://careers.{domain}",
            f"https://{domain}/careers",
            f"https://{domain}/jobs",
            f"https://{domain}/about/careers",
            f"https://{domain}",
        ]

        with Session(headers={"User-Agent": self.config.user_agent}) as s:
            for url in candidates:
                try:
                    resp = s.get(url, timeout=8, allow_redirects=True)
                    if resp.status_code >= 400:
                        continue
                    final_url = str(resp.url)
                    engine, token = fingerprint_html(resp.text, final_url)
                    if engine and token:
                        profile = CompanyProfile(
                            id=name.lower(),
                            name=name,
                            domain=domain,
                            careers_url=final_url,
                            ats_type=engine,
                            ats_identifier=token,
                            is_verified=False
                        )
                        self.catalog.add(profile, persist=False)
                        return profile
                except Exception:
                    continue

        raise CareerEngineNotFoundError(
            f"Could not automatically detect the career portal engine for '{target}' ({domain})."
        )

    async def resolve_async(self, target: str) -> CompanyProfile:
        """Asynchronous resolver for company career portals."""
        existing = self.catalog.get(target)
        if existing:
            return existing

        domain = self._normalize_domain(target)
        name = domain.split(".")[0].capitalize()

        candidates = [
            f"https://careers.{domain}",
            f"https://{domain}/careers",
            f"https://{domain}/jobs",
            f"https://{domain}/about/careers",
            f"https://{domain}",
        ]

        async with AsyncSession(headers={"User-Agent": self.config.user_agent}) as s:
            for url in candidates:
                try:
                    resp = await s.get(url, timeout=8, allow_redirects=True)
                    if resp.status_code >= 400:
                        continue
                    final_url = str(resp.url)
                    engine, token = fingerprint_html(resp.text, final_url)
                    if engine and token:
                        profile = CompanyProfile(
                            id=name.lower(),
                            name=name,
                            domain=domain,
                            careers_url=final_url,
                            ats_type=engine,
                            ats_identifier=token,
                            is_verified=False
                        )
                        self.catalog.add(profile, persist=False)
                        return profile
                except Exception:
                    continue

        raise CareerEngineNotFoundError(
            f"Could not automatically detect the career portal engine for '{target}' ({domain})."
        )
