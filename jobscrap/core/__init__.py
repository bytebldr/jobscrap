"""Core primitives, models, and configuration for JobScrap."""

from jobscrap.core.config import JobScrapConfig
from jobscrap.core.exceptions import (
    CompanyNotFoundError,
    CareerEngineNotFoundError,
    JobScrapError,
    NetworkError,
    ParsingError,
    RateLimitError,
)
from jobscrap.core.models import CompanyProfile, JobListing, SalaryRange
from jobscrap.core.session import HttpSession

__all__ = [
    "JobScrapConfig",
    "JobScrapError",
    "CompanyNotFoundError",
    "CareerEngineNotFoundError",
    "NetworkError",
    "ParsingError",
    "RateLimitError",
    "CompanyProfile",
    "JobListing",
    "SalaryRange",
    "HttpSession",
]
