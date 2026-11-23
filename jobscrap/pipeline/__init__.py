"""Post-processing, enrichment, and normalization pipeline."""

from jobscrap.pipeline.dedup import deduplicate_jobs
from jobscrap.pipeline.salary import parse_salary

__all__ = ["deduplicate_jobs", "parse_salary"]
