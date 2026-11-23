#!/usr/bin/env python3
"""Quality and Schema Verification Suite for jobscrap/catalog/data/india_consumer.json."""

import json
from pathlib import Path
import sys
from urllib.parse import urlparse

# Ensure repo root is on path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jobscrap.core.models import CompanyProfile

DATA_FILE = REPO_ROOT / "jobscrap" / "catalog" / "data" / "india_consumer.json"

def verify():
    assert DATA_FILE.exists(), f"File {DATA_FILE} does not exist!"
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"1. Scale Check: Loaded {len(data)} profiles.")
    assert len(data) >= 150, f"Expected >= 150 profiles, got {len(data)}"
    print("   [PASS] Total count >= 150 requirement met.")

    # 2. Check unique IDs
    ids = [d["id"] for d in data]
    dup_ids = [i for i in ids if ids.count(i) > 1]
    assert len(dup_ids) == 0, f"Found duplicate IDs: {set(dup_ids)}"
    print(f"   [PASS] 100% unique IDs ({len(set(ids))} unique).")

    # 3. Check unique Domains
    domains = [d["domain"] for d in data]
    dup_domains = [d for d in domains if domains.count(d) > 1]
    assert len(dup_domains) == 0, f"Found duplicate domains: {set(dup_domains)}"
    print(f"   [PASS] 100% unique domains ({len(set(domains))} unique).")

    # 4. Check schema validity against CompanyProfile
    ats_counts = {}
    industry_counts = {}
    valid_ats_types = {"greenhouse", "lever", "ashby", "smartrecruiters"}

    for idx, d in enumerate(data):
        assert d["ats_type"] in valid_ats_types, f"Invalid ATS type: {d['ats_type']} in {d['id']}"
        assert d["careers_url"].startswith("http"), f"Invalid careers_url: {d['careers_url']}"
        assert d["api_endpoint"].startswith("http"), f"Invalid api_endpoint: {d['api_endpoint']}"
        assert d["is_verified"] is True, f"Expected is_verified=True in {d['id']}"
        assert len(d["tags"]) > 0, f"Tags empty in {d['id']}"

        # Test CompanyProfile instantiation
        cp = CompanyProfile(**d)
        assert cp.id == d["id"]

        ats_counts[d["ats_type"]] = ats_counts.get(d["ats_type"], 0) + 1
        industry_counts[d["industry"]] = industry_counts.get(d["industry"], 0) + 1

    print(f"   [PASS] 100% schema conformity with CompanyProfile.")
    print(f"   ATS Distribution: {ats_counts}")
    print(f"   Industry Distribution: {industry_counts}")
    print("\nALL CONSUMER AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    verify()
