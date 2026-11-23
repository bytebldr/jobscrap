"""Canonical Data Models for JobScrap v0.5."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import uuid

@dataclass
class SalaryRange:
    min_inr: Optional[int] = None
    max_inr: Optional[int] = None
    currency: str = "INR"
    raw_text: Optional[str] = None

    def display(self) -> str:
        if self.min_inr and self.max_inr:
            if self.min_inr == self.max_inr:
                return f"₹{self.min_inr:,}"
            return f"₹{self.min_inr:,} - ₹{self.max_inr:,}"
        elif self.min_inr:
            return f"₹{self.min_inr:,}+"
        return self.raw_text or "Competitive / Not Disclosed"

@dataclass
class CompanyProfile:
    id: str
    name: str
    domain: str
    careers_url: str
    industry: str = "Technology"
    hq_location: str = "India"
    tier: int = 1
    ats_type: str = "custom"
    ats_identifier: Optional[str] = None
    api_endpoint: Optional[str] = None
    is_verified: bool = True
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class JobListing:
    id: str                                # Deterministic ID or unique hash
    source: str                            # e.g. 'greenhouse', 'lever', 'ashby', 'smartrecruiters', 'workday'
    source_type: str                       # 'ats' (direct primary career engine)
    company: str                           # Company display name
    title: str                             # Normalized job title
    location: str                          # Job location (e.g., 'Bengaluru, India', 'Remote')
    url: str                               # Direct application URL (official site)
    description: str = ""                  # Full text or clean excerpt
    is_remote: bool = False                # Remote flag
    job_type: str = "fulltime"             # 'fulltime', 'internship', 'contract'
    experience_level: str = "mid"          # 'fresher', 'mid', 'senior', 'lead'
    salary: Optional[SalaryRange] = None   # Structured salary
    min_salary_inr: Optional[int] = None   # Flat minimum INR for fast queries
    max_salary_inr: Optional[int] = None   # Flat maximum INR for fast queries
    department: Optional[str] = None       # Department / team name
    posted_date: Optional[str] = None      # ISO 8601 string
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "live"                   # 'live' | 'dead' | 'unchecked'
    dedup_group_id: Optional[str] = None   # Cross-portal deduplication ID
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.salary and not self.min_salary_inr:
            self.min_salary_inr = self.salary.min_inr
        if self.salary and not self.max_salary_inr:
            self.max_salary_inr = self.salary.max_inr

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.salary:
            d["salary"] = self.salary.display()
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
