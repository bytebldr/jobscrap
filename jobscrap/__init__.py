"""JobScrap — Standalone Open-Source Direct Company Career & ATS Job Scraper."""

__version__ = "0.5.0-alpha"

from jobscrap.catalog.registry import CompanyCatalog
from jobscrap.core.config import JobScrapConfig
from jobscrap.core.models import CompanyProfile, JobListing, SalaryRange
from jobscrap.discovery.resolver import CompanyResolver
from jobscrap.scraper import JobScraper

__all__ = [
    "JobScraper",
    "CompanyCatalog",
    "CompanyResolver",
    "CompanyProfile",
    "JobListing",
    "SalaryRange",
    "JobScrapConfig",
]
