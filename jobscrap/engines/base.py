"""Abstract Base Career Engine Protocol."""

from abc import ABC, abstractmethod
from typing import List, Optional
from jobscrap.core.config import JobScrapConfig
from jobscrap.core.models import CompanyProfile, JobListing
from jobscrap.core.session import HttpSession

class BaseCareerEngine(ABC):
    """Base class for all direct company career portal engines."""

    name: str = "base"

    def __init__(self, config: Optional[JobScrapConfig] = None, session: Optional[HttpSession] = None):
        self.config = config or JobScrapConfig()
        self.session = session or HttpSession(self.config)

    @abstractmethod
    def fetch_jobs(self, company: CompanyProfile) -> List[JobListing]:
        """Fetch all live jobs directly from the company's official career endpoint."""
        pass

    @abstractmethod
    async def fetch_jobs_async(self, company: CompanyProfile) -> List[JobListing]:
        """Asynchronously fetch all live jobs directly from the company's official career endpoint."""
        pass
