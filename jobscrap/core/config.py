"""Configuration and settings for JobScrap."""

from dataclasses import dataclass, field
import os
from typing import List, Optional

@dataclass
class JobScrapConfig:
    timeout_seconds: int = 15
    max_retries: int = 3
    concurrency: int = 10
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    impersonate_browser: str = "chrome124"
    proxy: Optional[str] = field(default_factory=lambda: os.getenv("JOBSCRAP_PROXY"))
    enabled_engines: List[str] = field(default_factory=lambda: [
        "greenhouse", "lever", "ashby", "smartrecruiters", "workday", "bamboohr"
    ])
    rate_limit_per_second: float = 5.0
