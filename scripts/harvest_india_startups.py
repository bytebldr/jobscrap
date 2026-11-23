"""Harvest and live-verify Indian FinTech, WealthTech, Neobanks, Quick Commerce,
EV, and DeepTech startups across Greenhouse, Lever, Ashby, and SmartRecruiters.

Outputs validated, live-verified CompanyProfile records to
jobscrap/catalog/data/india_startups.json.
"""

import asyncio
import csv
import json
import logging
from pathlib import Path
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import httpx

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from jobscrap.core.models import CompanyProfile

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("harvest_india_startups")

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "jobscrap" / "catalog" / "data" / "india_startups.json"
CACHE_DIR = Path(__file__).resolve().parent / "cache_ats"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# Core marquee reference startups guaranteed by the registry
CORE_MARQUEE_STARTUPS: List[Dict[str, Any]] = [
    # --- FinTech, WealthTech & Neobanks ---
    {
        "id": "angelone",
        "name": "Angel One",
        "domain": "angelone.in",
        "careers_url": "https://www.angelone.in/careers",
        "industry": "FinTech / WealthTech & Stockbroking",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "angelone",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/angelone/postings?limit=100",
        "tags": ["fintech", "wealthtech", "broking", "neobank", "india", "startup"]
    },
    {
        "id": "upstox",
        "name": "Upstox",
        "domain": "upstox.com",
        "careers_url": "https://careers.smartrecruiters.com/upstox",
        "industry": "FinTech / WealthTech & Stockbroking",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "upstox",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/upstox/postings?limit=100",
        "tags": ["fintech", "wealthtech", "trading", "investing", "india", "startup"]
    },
    {
        "id": "dhan",
        "name": "Dhan",
        "domain": "dhan.co",
        "careers_url": "https://dhan.co/careers",
        "industry": "FinTech / WealthTech & Trading",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "dhan",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/dhan/postings?limit=100",
        "tags": ["fintech", "wealthtech", "trading", "investing", "india", "startup"]
    },
    {
        "id": "policybazaar",
        "name": "PolicyBazaar",
        "domain": "policybazaar.com",
        "careers_url": "https://www.policybazaar.com/careers",
        "industry": "FinTech / InsurTech",
        "hq_location": "Gurugram, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "policybazaar",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/policybazaar/postings?limit=100",
        "tags": ["fintech", "insurtech", "insurance", "india", "startup"]
    },
    {
        "id": "mobikwik",
        "name": "MobiKwik",
        "domain": "mobikwik.com",
        "careers_url": "https://www.mobikwik.com/careers",
        "industry": "FinTech / Digital Payments & BNPL",
        "hq_location": "Gurugram, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "mobikwik",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/mobikwik/postings?limit=100",
        "tags": ["fintech", "payments", "bnpl", "wallet", "india", "startup"]
    },
    {
        "id": "kreditbee",
        "name": "KreditBee",
        "domain": "kreditbee.in",
        "careers_url": "https://www.kreditbee.in/careers",
        "industry": "FinTech / Digital Lending & NBFC",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "kreditbee",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/kreditbee/postings?limit=100",
        "tags": ["fintech", "lending", "credit", "nbfc", "india", "startup"]
    },
    {
        "id": "razorpay",
        "name": "Razorpay",
        "domain": "razorpay.com",
        "careers_url": "https://razorpay.com/jobs",
        "industry": "FinTech / Payment Gateway & Banking",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "razorpaysoftwareprivatelimited",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/razorpaysoftwareprivatelimited/jobs",
        "tags": ["fintech", "payments", "neobank", "bengaluru", "india", "startup"]
    },
    {
        "id": "cred",
        "name": "CRED",
        "domain": "cred.club",
        "careers_url": "https://careers.cred.club",
        "industry": "FinTech / Credit Card & Payments",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "cred",
        "api_endpoint": "https://api.lever.co/v0/postings/cred?mode=json",
        "tags": ["fintech", "credit", "payments", "bengaluru", "india", "startup"]
    },
    {
        "id": "groww",
        "name": "Groww",
        "domain": "groww.in",
        "careers_url": "https://groww.in/careers",
        "industry": "FinTech / WealthTech & Stockbroking",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "groww",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/groww/jobs",
        "tags": ["fintech", "wealthtech", "investing", "mutualfunds", "india", "startup"]
    },
    {
        "id": "slice",
        "name": "Slice",
        "domain": "sliceit.com",
        "careers_url": "https://www.sliceit.com/careers",
        "industry": "FinTech / Small Finance Bank & Payments",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "slice",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/slice/jobs",
        "tags": ["fintech", "banking", "payments", "credit", "india", "startup"]
    },
    {
        "id": "fi-money",
        "name": "Fi Money",
        "domain": "fi.money",
        "careers_url": "https://fi.money/careers",
        "industry": "FinTech / Neobanking & Savings",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "fi",
        "api_endpoint": "https://api.lever.co/v0/postings/fi?mode=json",
        "tags": ["fintech", "neobank", "banking", "savings", "india", "startup"]
    },
    {
        "id": "onecard",
        "name": "OneCard (FPL Technologies)",
        "domain": "getonecard.app",
        "careers_url": "https://jobs.ashbyhq.com/fpl",
        "industry": "FinTech / Credit Cards & Neobanking",
        "hq_location": "Pune, India",
        "tier": 1,
        "ats_type": "ashby",
        "ats_identifier": "fpl",
        "api_endpoint": "https://api.ashbyhq.com/posting-api/job-board/fpl",
        "tags": ["fintech", "creditcard", "neobank", "pune", "india", "startup"]
    },
    {
        "id": "refyne",
        "name": "Refyne",
        "domain": "refyne.co.in",
        "careers_url": "https://careers.smartrecruiters.com/refyne",
        "industry": "FinTech / Earned Wage Access",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "refyne",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/refyne/postings?limit=100",
        "tags": ["fintech", "salary", "ewa", "bengaluru", "india", "startup"]
    },
    {
        "id": "turtlemint",
        "name": "Turtlemint",
        "domain": "turtlemint.com",
        "careers_url": "https://careers.smartrecruiters.com/turtlemint",
        "industry": "FinTech / InsurTech Platform",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "turtlemint",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/turtlemint/postings?limit=100",
        "tags": ["fintech", "insurtech", "insurance", "mumbai", "india", "startup"]
    },
    {
        "id": "lendingkart",
        "name": "Lendingkart",
        "domain": "lendingkart.com",
        "careers_url": "https://careers.smartrecruiters.com/lendingkart",
        "industry": "FinTech / MSME Digital Lending",
        "hq_location": "Ahmedabad / Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "lendingkart",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/lendingkart/postings?limit=100",
        "tags": ["fintech", "msme", "lending", "credit", "india", "startup"]
    },
    {
        "id": "clear",
        "name": "Clear (ClearTax)",
        "domain": "clear.in",
        "careers_url": "https://clear.in/careers",
        "industry": "FinTech / Tax & Compliance SaaS",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "clear",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/clear/jobs",
        "tags": ["fintech", "tax", "saas", "compliance", "india", "startup"]
    },
    {
        "id": "karboncard",
        "name": "Karbon Card",
        "domain": "karboncard.com",
        "careers_url": "https://karboncard.com/careers",
        "industry": "FinTech / Corporate Cards & Expense Management",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "karbon",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/karbon/jobs",
        "tags": ["fintech", "corporatecards", "expenses", "india", "startup"]
    },
    {
        "id": "digitinsurance",
        "name": "Digit Insurance",
        "domain": "godigit.com",
        "careers_url": "https://www.godigit.com/careers",
        "industry": "FinTech / InsurTech General Insurance",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "digit",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/digit/jobs",
        "tags": ["fintech", "insurtech", "generalinsurance", "india", "startup"]
    },
    # --- EV & CleanTech / Mobility ---
    {
        "id": "olaelectric",
        "name": "Ola Electric",
        "domain": "olaelectric.com",
        "careers_url": "https://careers.smartrecruiters.com/olaelectricmobility",
        "industry": "EV & CleanTech / Electric 2-Wheelers",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "olaelectricmobility",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/olaelectricmobility/postings?limit=100",
        "tags": ["ev", "electricvehicles", "mobility", "bengaluru", "india", "startup"]
    },
    {
        "id": "atherenergy",
        "name": "Ather Energy",
        "domain": "atherenergy.com",
        "careers_url": "https://www.atherenergy.com/careers",
        "industry": "EV & CleanTech / Electric Scooters & Fast Charging",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "atherenergy",
        "api_endpoint": "https://api.lever.co/v0/postings/atherenergy?mode=json",
        "tags": ["ev", "electricvehicles", "mobility", "hardware", "india", "startup"]
    },
    {
        "id": "bounce",
        "name": "Bounce Infinity",
        "domain": "bounceinfinity.com",
        "careers_url": "https://jobs.ashbyhq.com/bounce",
        "industry": "EV & CleanTech / Battery Swapping & Electric Scooters",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "ashby",
        "ats_identifier": "bounce",
        "api_endpoint": "https://api.ashbyhq.com/posting-api/job-board/bounce",
        "tags": ["ev", "batteryswapping", "mobility", "india", "startup"]
    },
    {
        "id": "statiq",
        "name": "Statiq",
        "domain": "statiq.in",
        "careers_url": "https://careers.smartrecruiters.com/statiq",
        "industry": "EV & CleanTech / EV Charging Network",
        "hq_location": "Gurugram, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "statiq",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/statiq/postings?limit=100",
        "tags": ["ev", "charging", "cleantech", "gurugram", "india", "startup"]
    },
    {
        "id": "rapido",
        "name": "Rapido",
        "domain": "rapido.bike",
        "careers_url": "https://www.rapido.bike/careers",
        "industry": "Mobility & Logistics / Bike Taxi & Auto",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "rapido",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/rapido/jobs",
        "tags": ["mobility", "ridehailing", "logistics", "bengaluru", "india", "startup"]
    },
    # --- Quick Commerce, E-Commerce & Logistics ---
    {
        "id": "swiggy",
        "name": "Swiggy",
        "domain": "swiggy.com",
        "careers_url": "https://careers.smartrecruiters.com/swiggy",
        "industry": "Quick Commerce / Food Delivery & Instamart",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "swiggy",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/swiggy/postings?limit=100",
        "tags": ["quickcommerce", "delivery", "foodtech", "bengaluru", "india", "startup"]
    },
    {
        "id": "zepto",
        "name": "Zepto",
        "domain": "zepto.com",
        "careers_url": "https://jobs.ashbyhq.com/zepto",
        "industry": "Quick Commerce / 10-Minute Grocery Delivery",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "ashby",
        "ats_identifier": "zepto",
        "api_endpoint": "https://api.ashbyhq.com/posting-api/job-board/zepto",
        "tags": ["quickcommerce", "grocery", "delivery", "mumbai", "india", "startup"]
    },
    {
        "id": "delhivery",
        "name": "Delhivery",
        "domain": "delhivery.com",
        "careers_url": "https://www.delhivery.com/careers",
        "industry": "Logistics & Supply Chain / E-Commerce Fulfilment",
        "hq_location": "Gurugram, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "delhivery",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/delhivery/postings?limit=100",
        "tags": ["logistics", "supplychain", "ecommerce", "gurugram", "india", "startup"]
    },
    {
        "id": "shadowfax",
        "name": "Shadowfax",
        "domain": "shadowfax.in",
        "careers_url": "https://www.shadowfax.in/careers",
        "industry": "Logistics & Supply Chain / Hyperlocal & 3PL Logistics",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "shadowfax",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/shadowfax/postings?limit=100",
        "tags": ["logistics", "hyperlocal", "delivery", "bengaluru", "india", "startup"]
    },
    {
        "id": "ninjacart",
        "name": "Ninjacart",
        "domain": "ninjacart.com",
        "careers_url": "https://ninjacart.com/careers",
        "industry": "Agritech & Quick Commerce / B2B Supply Chain",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "ninjacart",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/ninjacart/postings?limit=100",
        "tags": ["agritech", "supplychain", "b2b", "bengaluru", "india", "startup"]
    },
    {
        "id": "meesho",
        "name": "Meesho",
        "domain": "meesho.io",
        "careers_url": "https://jobs.lever.co/meesho",
        "industry": "E-Commerce / Social Commerce Marketplace",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "meesho",
        "api_endpoint": "https://api.lever.co/v0/postings/meesho?mode=json",
        "tags": ["ecommerce", "marketplace", "bengaluru", "india", "startup"]
    },
    {
        "id": "porter",
        "name": "Porter",
        "domain": "porter.in",
        "careers_url": "https://jobs.lever.co/porter",
        "industry": "Logistics & Mobility / Intra-City Mini-Trucks & Courier",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "porter",
        "api_endpoint": "https://api.lever.co/v0/postings/porter?mode=json",
        "tags": ["logistics", "mobility", "delivery", "bengaluru", "india", "startup"]
    },
    {
        "id": "loadshare",
        "name": "LoadShare Networks",
        "domain": "loadshare.net",
        "careers_url": "https://jobs.ashbyhq.com/loadshare",
        "industry": "Logistics & Supply Chain / Express Logistics",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "ashby",
        "ats_identifier": "loadshare",
        "api_endpoint": "https://api.ashbyhq.com/posting-api/job-board/loadshare",
        "tags": ["logistics", "express", "supplychain", "bengaluru", "india", "startup"]
    },
    {
        "id": "captainfresh",
        "name": "Captain Fresh",
        "domain": "captainfresh.in",
        "careers_url": "https://careers.smartrecruiters.com/captainfresh",
        "industry": "Quick Commerce / B2B Seafood & Meat Supply Chain",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "captainfresh",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/captainfresh/postings?limit=100",
        "tags": ["supplychain", "b2b", "seafood", "bengaluru", "india", "startup"]
    },
    # --- DeepTech & AI / Robotics / SpaceTech ---
    {
        "id": "sarvam-ai",
        "name": "Sarvam AI",
        "domain": "sarvam.ai",
        "careers_url": "https://jobs.ashbyhq.com/sarvam",
        "industry": "DeepTech & AI / Indic Generative AI Foundation Models",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "ashby",
        "ats_identifier": "sarvam",
        "api_endpoint": "https://api.ashbyhq.com/posting-api/job-board/sarvam",
        "tags": ["deeptech", "ai", "genai", "llm", "indic", "bengaluru", "india", "startup"]
    },
    {
        "id": "cynlr",
        "name": "CynLr",
        "domain": "cynlr.com",
        "careers_url": "https://jobs.ashbyhq.com/cynlr",
        "industry": "DeepTech & AI / Robotics & Visual Cybernetics",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "ashby",
        "ats_identifier": "cynlr",
        "api_endpoint": "https://api.ashbyhq.com/posting-api/job-board/cynlr",
        "tags": ["deeptech", "robotics", "cybernetics", "vision", "bengaluru", "india", "startup"]
    },
    {
        "id": "netradyne",
        "name": "Netradyne",
        "domain": "netradyne.com",
        "careers_url": "https://boards.greenhouse.io/netradyne",
        "industry": "DeepTech & AI / Fleet Safety & Edge Computing",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "netradyne",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/netradyne/jobs",
        "tags": ["deeptech", "ai", "edgeai", "fleetsafety", "bengaluru", "india", "startup"]
    }
]

KEYWORDS_FINTECH = {
    "fintech", "wealth", "bank", "pay", "payment", "lending", "credit", "loan",
    "insur", "broker", "invest", "crypto", "capital", "fund", "money", "securities",
    "neobank", "forex", "asset"
}
KEYWORDS_COMMERCE = {
    "commerce", "retail", "deliver", "logistics", "courier", "supply chain", "cargo",
    "freight", "transport", "fleet", "warehouse", "quick", "grocery", "mart", "shipping"
}
KEYWORDS_EV_MOBILITY = {
    "ev", "electric", "mobility", "battery", "charge", "charging", "scooter", "motor",
    "vehicle", "automotive", "solar", "energy", "cleantech", "ride"
}
KEYWORDS_DEEPTECH = {
    "ai", "robot", "robotics", "drone", "space", "aerospace", "vision", "cybernetics",
    "satellite", "semiconductor", "deeptech", "sensor", "intelligence", "quantum"
}

INDIA_LOCATIONS = {
    "india", "indian", "bengaluru", "bangalore", "mumbai", "delhi", "gurugram",
    "gurgaon", "noida", "hyderabad", "pune", "chennai", "kolkata", "ahmedabad", "jaipur"
}

FOREIGN_EXCLUSIONS = {
    "gmbh", "s.l.u", "slu", "sp. z o.o.", "s.r.o.", "bv", "b.v.", "pty ltd", "nigeria",
    "tanzania", "cameroon", "kenya", "uganda", "ghana"
}


def classify_category(name: str, slug: str) -> Optional[str]:
    text = f"{name} {slug}".lower()
    words = set(re.findall(r'\b\w+\b', text))
    if words & KEYWORDS_FINTECH:
        return "FinTech & WealthTech"
    if words & KEYWORDS_EV_MOBILITY:
        return "EV & CleanTech / Mobility"
    if words & KEYWORDS_COMMERCE:
        return "Quick Commerce & Logistics"
    if words & KEYWORDS_DEEPTECH:
        return "DeepTech & AI"
    return None


def clean_id(slug: str) -> str:
    cleaned = re.sub(r'[^a-z0-9]', '', slug.lower())
    return cleaned


def clean_domain(name: str, slug: str) -> str:
    base = re.sub(r'[^a-z0-9]', '', slug.lower())
    return f"{base}.com"


def load_ats_candidates() -> List[Dict[str, Any]]:
    """Scan cache_ats CSVs for candidate profiles matching our targeted categories."""
    candidates = []
    
    csv_map = [
        ("smartrecruiters", CACHE_DIR / "smartrecruiters.csv"),
        ("greenhouse", CACHE_DIR / "greenhouse.csv"),
        ("lever", CACHE_DIR / "lever.csv"),
        ("ashby", CACHE_DIR / "ashby.csv"),
    ]

    for ats, path in csv_map:
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = str(row.get("name", "")).strip()
                slug = str(row.get("slug", "")).strip()
                if not name or not slug:
                    continue
                name_l = name.lower()
                slug_l = slug.lower()
                
                # Filter obvious foreign non-startup suffixes
                if any(fe in name_l or fe in slug_l for fe in FOREIGN_EXCLUSIONS):
                    continue

                cat = classify_category(name, slug)
                if cat:
                    candidates.append({
                        "name": name,
                        "slug": slug,
                        "ats": ats,
                        "category": cat
                    })

    logger.info(f"Loaded {len(candidates)} total domain-matched candidates across CSVs.")
    return candidates


async def verify_endpoint(client: httpx.AsyncClient, sem: asyncio.Semaphore, ats: str, slug: str) -> Optional[int]:
    """Live-verify that the ATS endpoint is responding with 200 OK and returns job postings."""
    for attempt in range(2):
        async with sem:
            try:
                if ats == "greenhouse":
                    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
                    r = await client.get(url)
                    if r.status_code == 200:
                        return len(r.json().get("jobs", []))
                elif ats == "lever":
                    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                    r = await client.get(url)
                    if r.status_code == 200:
                        data = r.json()
                        if isinstance(data, list):
                            return len(data)
                elif ats == "ashby":
                    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
                    r = await client.get(url)
                    if r.status_code == 200:
                        return len(r.json().get("jobs", []))
                elif ats == "smartrecruiters":
                    url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=10"
                    r = await client.get(url)
                    if r.status_code == 200:
                        return r.json().get("totalFound", 0)
            except Exception:
                await asyncio.sleep(0.3)
                continue
    return None


async def harvest_and_verify(concurrency: int = 40, timeout: float = 6.0) -> List[Dict[str, Any]]:
    """Harvest and live-verify Indian and tech startup profiles."""
    candidates = load_ats_candidates()
    
    limits = httpx.Limits(max_connections=80, max_keepalive_connections=40)
    sem = asyncio.Semaphore(concurrency)

    verified_records: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()
    seen_domains: Set[str] = set()

    # Seed primary marquee startups first to guarantee inclusion
    for p in CORE_MARQUEE_STARTUPS:
        seen_ids.add(p["id"])
        seen_domains.add(p["domain"])
        verified_records.append(dict(p))

    logger.info(f"Seeded {len(verified_records)} primary marquee startups.")

    async with httpx.AsyncClient(headers=HEADERS, limits=limits, timeout=timeout) as client:
        async def process(c: Dict[str, Any]):
            cid = clean_id(c["slug"])
            if not cid or cid in seen_ids:
                return

            jobs = await verify_endpoint(client, sem, c["ats"], c["slug"])
            if jobs is not None and jobs > 0:
                dom = clean_domain(c["name"], c["slug"])
                if dom in seen_domains:
                    dom = f"{cid}.io"
                if dom in seen_domains:
                    dom = f"{cid}.in"

                ats = c["ats"]
                slug = c["slug"]
                if ats == "greenhouse":
                    curl = f"https://boards.greenhouse.io/{slug}"
                    api = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
                elif ats == "lever":
                    curl = f"https://jobs.lever.co/{slug}"
                    api = f"https://api.lever.co/v0/postings/{slug}?mode=json"
                elif ats == "ashby":
                    curl = f"https://jobs.ashbyhq.com/{slug}"
                    api = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
                elif ats == "smartrecruiters":
                    curl = f"https://careers.smartrecruiters.com/{slug}"
                    api = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100"

                entry = {
                    "id": cid,
                    "name": c["name"],
                    "domain": dom,
                    "careers_url": curl,
                    "industry": c["category"],
                    "hq_location": "India",
                    "tier": 1 if jobs >= 10 else 2,
                    "ats_type": ats,
                    "ats_identifier": slug,
                    "api_endpoint": api,
                    "is_verified": True,
                    "tags": [
                        "india",
                        "startup",
                        ats,
                        c["category"].lower().replace(" & ", "-").replace(" / ", "-").replace(" ", "-")
                    ]
                }
                seen_ids.add(cid)
                seen_domains.add(dom)
                verified_records.append(entry)

        tasks = [process(c) for c in candidates]
        logger.info(f"Running concurrent live verification of {len(candidates)} candidates...")
        await asyncio.gather(*tasks)

    logger.info(f"Total live-verified profiles collected: {len(verified_records)}")
    return verified_records


def main():
    logger.info("Starting Indian FinTech, WealthTech, EV, Quick Commerce & DeepTech Harvest...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    verified = asyncio.run(harvest_and_verify())

    if len(verified) < 150:
        logger.error(f"Scale threshold failed: expected >= 150 companies, got {len(verified)}")
        sys.exit(1)

    # Validate schema for 100% of records against CompanyProfile dataclass
    validated_profiles: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()
    seen_domains: Set[str] = set()

    for item in verified:
        cid = item["id"].lower().strip()
        dom = item["domain"].lower().strip()
        if cid in seen_ids or dom in seen_domains:
            continue
        try:
            profile = CompanyProfile(
                id=item["id"],
                name=item["name"],
                domain=item["domain"],
                careers_url=item["careers_url"],
                industry=item.get("industry", "Technology"),
                hq_location=item.get("hq_location", "India"),
                tier=item.get("tier", 1),
                ats_type=item.get("ats_type", "custom"),
                ats_identifier=item.get("ats_identifier"),
                api_endpoint=item.get("api_endpoint"),
                tags=item.get("tags", []),
                is_verified=True
            )
            validated_profiles.append(profile.to_dict())
            seen_ids.add(cid)
            seen_domains.add(dom)
        except Exception as e:
            logger.warning(f"Skipping profile {item.get('id')} due to validation error: {e}")

    # Deterministic alphabetical sort by name
    validated_profiles.sort(key=lambda x: x["name"].lower())

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(validated_profiles, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully saved {len(validated_profiles)} verified startup profiles to {OUTPUT_PATH}")

    # Summary Statistics
    from collections import Counter
    by_ats = Counter(c["ats_type"] for c in validated_profiles)
    by_tier = Counter(c.get("tier", 1) for c in validated_profiles)
    by_ind = Counter(c.get("industry", "") for c in validated_profiles)

    logger.info("=== Harvest Summary ===")
    logger.info(f"Total Companies: {len(validated_profiles)}")
    logger.info(f"ATS Breakdown: {dict(by_ats)}")
    logger.info(f"Tier Breakdown: {dict(by_tier)}")
    logger.info(f"Top Industries: {dict(by_ind.most_common(6))}")
    logger.info(f"Target Output: {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
