"""Master Indian & Global Tech Company Registry and In-Memory Indexer."""

import json
import logging
from pathlib import Path
import re
import sqlite3
from typing import Dict, List, Optional
from jobscrap.core.models import CompanyProfile

logger = logging.getLogger("company_catalog")

CATALOG_FILE = Path(__file__).parent / "companies.json"
CATALOG_DB = Path(__file__).parent / "companies.db"

class CompanyCatalog:
    """Fast indexed in-memory catalog and SQLite FTS5 search engine for companies operating across India."""

    def __init__(self, catalog_path: Optional[Path] = None, db_path: Optional[Path] = None):
        self.path = catalog_path or CATALOG_FILE
        self.db_path = db_path or (self.path.parent / "companies.db" if self.path else CATALOG_DB)
        self._companies_by_id: Dict[str, CompanyProfile] = {}
        self._companies_by_name: Dict[str, CompanyProfile] = {}
        self._companies_by_domain: Dict[str, CompanyProfile] = {}
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            profile = CompanyProfile(
                id=item["id"],
                name=item["name"],
                domain=item["domain"],
                careers_url=item["careers_url"],
                industry=item.get("industry", "Technology"),
                hq_location=item.get("hq_location", "India"),
                tier=item.get("tier", 1),
                ats_type=item.get("ats_type", "custom"),
                ats_identifier=item.get("ats_identifier"),
                api_endpoint=item.get("api_endpoint"),
                tags=item.get("tags", []),
            )
            self._companies_by_id[profile.id.lower()] = profile
            self._companies_by_name[profile.name.lower()] = profile
            self._companies_by_domain[profile.domain.lower()] = profile

    def get(self, query: str) -> Optional[CompanyProfile]:
        """Look up a company by exact or fuzzy name, ID, or domain."""
        q = query.strip().lower()
        if q in self._companies_by_id:
            return self._companies_by_id[q]
        if q in self._companies_by_name:
            return self._companies_by_name[q]
        if q in self._companies_by_domain:
            return self._companies_by_domain[q]
        
        # Substring search
        for name, profile in self._companies_by_name.items():
            if q in name or name in q:
                return profile
        for domain, profile in self._companies_by_domain.items():
            if q in domain:
                return profile
        return None

    def search(
        self,
        query: Optional[str] = None,
        industry: Optional[str] = None,
        ats_type: Optional[str] = None,
        tier: Optional[int] = None,
    ) -> List[CompanyProfile]:
        """Filter companies by query term, industry, ats_type, or tier."""
        results = list(self._companies_by_id.values())
        if query:
            q = query.lower()
            results = [
                c for c in results
                if q in c.name.lower() or q in c.domain.lower() or any(q in t.lower() for t in c.tags)
            ]
        if industry:
            ind = industry.lower()
            results = [c for c in results if ind in c.industry.lower()]
        if ats_type:
            at = ats_type.lower()
            results = [c for c in results if c.ats_type.lower() == at]
        if tier is not None:
            results = [c for c in results if c.tier == tier]
        return results

    def search_fts(
        self,
        query: str,
        limit: int = 50,
        industry: Optional[str] = None,
        ats_type: Optional[str] = None,
        tier: Optional[int] = None,
    ) -> List[CompanyProfile]:
        """Fast full-text search across companies using SQLite FTS5 index with ranked BM25 scoring."""
        if not query or not query.strip():
            return self.search(industry=industry, ats_type=ats_type, tier=tier)[:limit]

        if not self.db_path.exists():
            return self.search(query=query, industry=industry, ats_type=ats_type, tier=tier)[:limit]

        cleaned = re.sub(r"[^\w\s*]", " ", query).strip()
        if not cleaned:
            return []

        # Build prefix match tokens for FTS5 (e.g. "fintech*" "pay*")
        terms = [f'"{term}"*' for term in cleaned.split() if term]
        fts_query = " ".join(terms)

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.id FROM companies c
                JOIN companies_fts f ON c.id = f.id
                WHERE companies_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, limit * 2),
            )
            rows = cursor.fetchall()
            conn.close()

            results: List[CompanyProfile] = []
            for r in rows:
                cid = str(r["id"]).lower()
                profile = self._companies_by_id.get(cid)
                if profile:
                    # Apply secondary filters if requested
                    if industry and industry.lower() not in profile.industry.lower():
                        continue
                    if ats_type and profile.ats_type.lower() != ats_type.lower():
                        continue
                    if tier is not None and profile.tier != tier:
                        continue
                    results.append(profile)
                    if len(results) >= limit:
                        break
            return results
        except Exception as e:
            logger.debug(f"FTS5 query failed, falling back to in-memory search: {e}")
            return self.search(query=query, industry=industry, ats_type=ats_type, tier=tier)[:limit]

    def all(self) -> List[CompanyProfile]:
        return list(self._companies_by_id.values())

    def add(self, profile: CompanyProfile, persist: bool = False):
        self._companies_by_id[profile.id.lower()] = profile
        self._companies_by_name[profile.name.lower()] = profile
        self._companies_by_domain[profile.domain.lower()] = profile
        if persist:
            data = [c.to_dict() for c in self._companies_by_id.values()]
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def __len__(self) -> int:
        return len(self._companies_by_id)
