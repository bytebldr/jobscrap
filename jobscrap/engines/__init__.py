"""Career Engine Registry and Factories."""

from typing import Dict, Type
from jobscrap.engines.base import BaseCareerEngine
from jobscrap.engines.greenhouse import GreenhouseEngine
from jobscrap.engines.lever import LeverEngine
from jobscrap.engines.ashby import AshbyEngine
from jobscrap.engines.smartrecruiters import SmartRecruitersEngine
from jobscrap.engines.workday import WorkdayEngine

ENGINES: Dict[str, Type[BaseCareerEngine]] = {
    "greenhouse": GreenhouseEngine,
    "lever": LeverEngine,
    "ashby": AshbyEngine,
    "smartrecruiters": SmartRecruitersEngine,
    "workday": WorkdayEngine,
}

def get_engine(engine_name: str, **kwargs) -> BaseCareerEngine:
    """Retrieve an initialized career engine by its ATS identifier."""
    key = engine_name.lower().strip()
    if key not in ENGINES:
        raise ValueError(f"Unsupported career engine: '{engine_name}'. Available: {list(ENGINES.keys())}")
    return ENGINES[key](**kwargs)

__all__ = [
    "BaseCareerEngine",
    "GreenhouseEngine",
    "LeverEngine",
    "AshbyEngine",
    "SmartRecruitersEngine",
    "WorkdayEngine",
    "ENGINES",
    "get_engine",
]
