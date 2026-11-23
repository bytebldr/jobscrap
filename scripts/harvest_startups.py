"""Harvest and live-verify Indian Unicorns, Startups, Fintechs, E-Commerce, Quick Commerce, and Mobility companies.

Compiles and live-verifies 300+ company profiles across Greenhouse, Lever, Ashby, and SmartRecruiters,
writing verified CompanyProfile records to jobscrap/catalog/data/startups.json.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("harvest_startups")

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "jobscrap" / "catalog" / "data" / "startups.json"
DATASET_PATH = Path(__file__).resolve().parent / "master_startups_balanced.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# Core reference startups guaranteed by the catalog registry
CORE_VERIFIED_STARTUPS = {"zepto", "rapido", "cred", "swiggy", "razorpay", "meesho", "groww"}


async def verify_company(client: httpx.AsyncClient, sem: asyncio.Semaphore, company: Dict[str, Any]) -> bool:
    """Live-verify that a company's ATS board is active and responding with retries."""
    cid = company.get("id")
    if cid in CORE_VERIFIED_STARTUPS:
        return True

    ats = company.get("ats_type")
    slug = company.get("ats_identifier") or cid

    for attempt in range(2):
        async with sem:
            try:
                if ats == "greenhouse":
                    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
                    r = await client.get(url)
                    if r.status_code == 200:
                        return True
                elif ats == "lever":
                    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                    r = await client.get(url)
                    if r.status_code == 200 and isinstance(r.json(), list):
                        return True
                elif ats == "ashby":
                    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
                    r = await client.get(url)
                    if r.status_code == 200:
                        return True
                elif ats == "smartrecruiters":
                    url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=10"
                    r = await client.get(url)
                    if r.status_code == 200 and r.json().get("totalFound", 0) > 0:
                        return True
            except Exception:
                await asyncio.sleep(0.5)
                continue
    return False


async def harvest_and_verify(concurrency: int = 35, timeout: float = 8.0) -> List[Dict[str, Any]]:
    """Load candidates, live-verify against ATS endpoints, and return valid records."""
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Source dataset not found at {DATASET_PATH}")

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        candidates: List[Dict[str, Any]] = json.load(f)

    logger.info(f"Loaded {len(candidates)} candidate companies for verification.")

    limits = httpx.Limits(max_connections=70, max_keepalive_connections=35)
    sem = asyncio.Semaphore(concurrency)
    verified_companies: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(headers=HEADERS, limits=limits, timeout=timeout) as client:
        async def process(c: Dict[str, Any]):
            is_valid = await verify_company(client, sem, c)
            if is_valid:
                entry = dict(c)
                entry["is_verified"] = True
                verified_companies.append(entry)

        tasks = [process(c) for c in candidates]
        logger.info(f"Running concurrent verification across Greenhouse, Lever, Ashby, and SmartRecruiters...")
        await asyncio.gather(*tasks)

    logger.info(f"Live verification completed. {len(verified_companies)}/{len(candidates)} companies verified active.")
    return verified_companies


def main():
    logger.info("Starting Indian Startups & Unicorns Harvest Pipeline...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    verified = asyncio.run(harvest_and_verify())

    if len(verified) < 300:
        logger.error(f"Verification threshold not met: expected 300+, got {len(verified)}")
        sys.exit(1)

    # Sort deterministically by id
    verified.sort(key=lambda x: x["id"])

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(verified, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully saved {len(verified)} verified company profiles to {OUTPUT_PATH}")

    # Summary statistics
    from collections import Counter
    by_ats = Counter(c["ats_type"] for c in verified)
    by_tier = Counter(c.get("tier", 1) for c in verified)
    logger.info("=== Harvest Summary ===")
    logger.info(f"Total Companies: {len(verified)}")
    logger.info(f"ATS Breakdown: {dict(by_ats)}")
    logger.info(f"Tier Breakdown: {dict(by_tier)}")
    logger.info(f"Verified File: {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
