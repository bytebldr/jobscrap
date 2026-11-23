"""Token-based Jaccard Similarity and Deduplication."""

import re
from typing import Any, Dict, List, Set
import uuid
from jobscrap.core.models import JobListing

def tokenize(text: str) -> Set[str]:
    return set(re.findall(r"\w+", text.lower()))

def jaccard_score(set1: Set[str], set2: Set[str]) -> float:
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)

def deduplicate_jobs(jobs: List[JobListing], threshold: float = 0.75) -> List[JobListing]:
    """
    Groups and clusters duplicate job postings using Jaccard token similarity
    over title, company, and location.
    """
    pool: List[tuple[JobListing, Set[str]]] = []
    
    for job in jobs:
        tokens = tokenize(f"{job.title} {job.company} {job.location}")
        matched_group = None
        for cand, cand_tokens in pool:
            if jaccard_score(tokens, cand_tokens) >= threshold:
                matched_group = cand.dedup_group_id or cand.id
                cand.dedup_group_id = matched_group
                break
        
        job.dedup_group_id = matched_group or str(uuid.uuid4())
        pool.append((job, tokens))

    # Keep unique by dedup_group_id, preferring primary direct ATS sources over custom/third-party portals
    grouped: Dict[str, JobListing] = {}
    for job in jobs:
        gid = job.dedup_group_id or job.id
        if gid not in grouped:
            grouped[gid] = job
        else:
            # If existing is not primary ATS and incoming is primary ATS, prioritize ATS
            if grouped[gid].source_type != "ats" and job.source_type == "ats":
                grouped[gid] = job

    return list(grouped.values())
