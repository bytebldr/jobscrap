"""Unified Exception Hierarchy for JobScrap."""

class JobScrapError(Exception):
    """Base exception for all JobScrap operations."""
    pass

class CompanyNotFoundError(JobScrapError):
    """Raised when a company is not in catalog and discovery fails."""
    pass

class CareerEngineNotFoundError(JobScrapError):
    """Raised when an ATS or career engine cannot be fingerprinted."""
    pass

class NetworkError(JobScrapError):
    """Raised on connection timeout, TLS error, or HTTP failure."""
    pass

class ParsingError(JobScrapError):
    """Raised when the career payload fails schema normalization."""
    pass

class RateLimitError(NetworkError):
    """Raised when encountering HTTP 429 Too Many Requests."""
    pass
