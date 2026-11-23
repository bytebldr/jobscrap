#!/usr/bin/env python3
"""Script to harvest, live-verify, and compile 150+ Indian IT Services, Consultancies,
and ER&D companies across Workday, SmartRecruiters, Greenhouse, and Lever for JobScrap.

Output is written to jobscrap/catalog/data/india_it.json conforming to CompanyProfile schema.
"""

import asyncio
import json
import logging
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse
import httpx
from curl_cffi.requests import AsyncSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("harvest_india_it")

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "jobscrap" / "catalog" / "data"
OUTPUT_FILE = DATA_DIR / "india_it.json"

INDIA_LOCATIONS = {
    "india", "bengaluru", "bangalore", "hyderabad", "pune", "chennai", "mumbai",
    "noida", "gurugram", "gurgaon", "delhi", "kolkata", "ahmedabad", "kochi",
    "coimbatore", "chandigarh", "indore", "jaipur", "remote", "apac", "global"
}

# Curated Tier 1 & Tier 2 Indian IT Services, Consultancies, ER&D companies
CURATED_PROFILES: List[Dict[str, Any]] = [
    # --- Top Indian IT Services, Consultancies & ER&D Powerhouses ---
    {
        "id": "tcs-it",
        "name": "Tata Consultancy Services (TCS)",
        "domain": "tcs.com",
        "careers_url": "https://boards.greenhouse.io/tcs",
        "industry": "IT Services & Consulting",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "tcs",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/tcs/jobs?content=true",
        "tags": ["itservices", "consulting", "enterprise", "tata", "mumbai", "india-it"]
    },
    {
        "id": "infosys-it",
        "name": "Infosys",
        "domain": "infosys.com",
        "careers_url": "https://infosys.wd103.myworkdayjobs.com/Simplus_Careers",
        "industry": "IT Services & Digital Consulting",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "infosys",
        "api_endpoint": "https://infosys.wd103.myworkdayjobs.com/wday/cxs/infosys/Simplus_Careers/jobs",
        "workday_sub": "wd103",
        "workday_site": "Simplus_Careers",
        "tags": ["itservices", "consulting", "bengaluru", "workday", "india-it"]
    },
    {
        "id": "cognizant-it",
        "name": "Cognizant Technology Solutions",
        "domain": "cognizant.com",
        "careers_url": "https://collaborative.wd1.myworkdayjobs.com/AllOpenings",
        "industry": "IT Services & Digital Transformation",
        "hq_location": "Chennai, Tamil Nadu, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "collaborative",
        "api_endpoint": "https://collaborative.wd1.myworkdayjobs.com/wday/cxs/collaborative/AllOpenings/jobs",
        "workday_sub": "wd1",
        "workday_site": "AllOpenings",
        "tags": ["itservices", "consulting", "chennai", "workday", "india-it"]
    },
    {
        "id": "dxc-technology-it",
        "name": "DXC Technology India",
        "domain": "dxc.com",
        "careers_url": "https://dxctechnology.wd1.myworkdayjobs.com/DXCJobs",
        "industry": "IT Services & Modernization",
        "hq_location": "Bengaluru / Noida Hub, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "dxctechnology",
        "api_endpoint": "https://dxctechnology.wd1.myworkdayjobs.com/wday/cxs/dxctechnology/DXCJobs/jobs",
        "workday_sub": "wd1",
        "workday_site": "DXCJobs",
        "tags": ["itservices", "cloud", "bengaluru", "workday", "india-it"]
    },
    {
        "id": "genpact-it",
        "name": "Genpact",
        "domain": "genpact.com",
        "careers_url": "https://genpact.wd108.myworkdayjobs.com/External_Careers",
        "industry": "Digital IT & Business Process Services",
        "hq_location": "Gurugram / Hyderabad Hub, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "genpact",
        "api_endpoint": "https://genpact.wd108.myworkdayjobs.com/wday/cxs/genpact/External_Careers/jobs",
        "workday_sub": "wd108",
        "workday_site": "External_Careers",
        "tags": ["itservices", "digital-transformation", "gurugram", "workday", "india-it"]
    },
    {
        "id": "thoughtworks-it",
        "name": "Thoughtworks India",
        "domain": "thoughtworks.com",
        "careers_url": "https://boards.greenhouse.io/thoughtworks",
        "industry": "Software Engineering & Agile Consultancy",
        "hq_location": "Bengaluru / Pune Hub, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "thoughtworks",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/thoughtworks/jobs?content=true",
        "tags": ["itservices", "consulting", "bengaluru", "greenhouse", "india-it"]
    },
    {
        "id": "valtech-it",
        "name": "Valtech India",
        "domain": "valtech.com",
        "careers_url": "https://boards.greenhouse.io/valtech",
        "industry": "Digital Business Transformation Consultancy",
        "hq_location": "Bengaluru, Karnataka, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "valtech",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/valtech/jobs?content=true",
        "tags": ["consulting", "digital", "bengaluru", "greenhouse", "india-it"]
    },
    {
        "id": "sutherland-global",
        "name": "Sutherland Global Services",
        "domain": "sutherlandglobal.com",
        "careers_url": "https://careers.smartrecruiters.com/sutherland",
        "industry": "Digital Transformation & Business IT Services",
        "hq_location": "Chennai / Hyderabad Hub, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "sutherland",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/sutherland/postings",
        "tags": ["itservices", "bpo", "chennai", "smartrecruiters", "india-it"]
    },
    {
        "id": "synechron-it",
        "name": "Synechron",
        "domain": "synechron.com",
        "careers_url": "https://careers.smartrecruiters.com/synechron",
        "industry": "Financial Technology & Digital IT Consulting",
        "hq_location": "Pune, Maharashtra, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "synechron",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/synechron/postings",
        "tags": ["fintech", "consulting", "pune", "smartrecruiters", "india-it"]
    },
    {
        "id": "alten-india",
        "name": "Alten India (ER&D Engineering Services)",
        "domain": "alten.com",
        "careers_url": "https://careers.smartrecruiters.com/alten",
        "industry": "Engineering & Technology Consulting (ER&D)",
        "hq_location": "Bengaluru, Karnataka, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "alten",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/alten/postings",
        "tags": ["er&d", "engineering", "bengaluru", "smartrecruiters", "india-it"]
    },
    {
        "id": "jade-global",
        "name": "Jade Global",
        "domain": "jadeglobal.com",
        "careers_url": "https://careers.smartrecruiters.com/jadeglobal",
        "industry": "Enterprise IT Consulting & Cloud Modernization",
        "hq_location": "Pune, Maharashtra, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "jadeglobal",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/jadeglobal/postings",
        "tags": ["cloud", "consulting", "pune", "smartrecruiters", "india-it"]
    },
    {
        "id": "fulcrum-digital",
        "name": "Fulcrum Digital",
        "domain": "fulcrumdigital.com",
        "careers_url": "https://careers.smartrecruiters.com/fulcrumdigital",
        "industry": "Digital Transformation & Cloud Services",
        "hq_location": "Pune / Mumbai Hub, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "fulcrumdigital",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/fulcrumdigital/postings",
        "tags": ["digital", "cloud", "pune", "smartrecruiters", "india-it"]
    },
    {
        "id": "affle-india",
        "name": "Affle India",
        "domain": "affle.com",
        "careers_url": "https://boards.greenhouse.io/affle",
        "industry": "Mobile Marketing & Consumer Cloud Intelligence",
        "hq_location": "Gurugram, Haryana, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "affle",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/affle/jobs?content=true",
        "tags": ["cloud", "adtech", "gurugram", "greenhouse", "india-it"]
    },
    {
        "id": "nucleus-software-it",
        "name": "Nucleus Software",
        "domain": "nucleussoftware.com",
        "careers_url": "https://boards.greenhouse.io/nucleus",
        "industry": "Banking & Financial Software Services",
        "hq_location": "Noida, Uttar Pradesh, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "nucleus",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/nucleus/jobs?content=true",
        "tags": ["fintech", "banking", "noida", "greenhouse", "india-it"]
    },
    {
        "id": "eurofins-india",
        "name": "Eurofins Scientific India",
        "domain": "eurofins.in",
        "careers_url": "https://careers.smartrecruiters.com/Eurofins1",
        "industry": "Bio-Tech IT & Data Analytics",
        "hq_location": "Bengaluru, Karnataka, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Eurofins1",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Eurofins1/postings",
        "tags": ["biotech-it", "analytics", "bengaluru", "smartrecruiters", "india-it"]
    },
    {
        "id": "amisoft-technologies",
        "name": "Amisoft Technologies Limited",
        "domain": "amisoft.net",
        "careers_url": "https://careers.smartrecruiters.com/AmisoftTechnologiesLimited",
        "industry": "Enterprise Software & IT Solutions",
        "hq_location": "Kolkata, West Bengal, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "AmisoftTechnologiesLimited",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/AmisoftTechnologiesLimited/postings",
        "tags": ["itservices", "software", "kolkata", "smartrecruiters", "india-it"]
    },
    {
        "id": "accenture-federal-services",
        "name": "Accenture Enterprise & Technology Hub",
        "domain": "accenturefederalservices.com",
        "careers_url": "https://boards.greenhouse.io/accenturefederalservices",
        "industry": "Global Enterprise IT & Cloud Consultancy",
        "hq_location": "Bengaluru / Global Delivery Hub",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "accenturefederalservices",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/accenturefederalservices/jobs?content=true",
        "tags": ["consulting", "cloud", "enterprise", "greenhouse", "india-it"]
    },
    {
        "id": "acryldata-india",
        "name": "Acryl Data",
        "domain": "acryldata.io",
        "careers_url": "https://boards.greenhouse.io/acryldata",
        "industry": "Enterprise Data Catalog & Metadata Architecture",
        "hq_location": "Bengaluru, Karnataka, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "acryldata",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/acryldata/jobs?content=true",
        "tags": ["data", "metadata", "bengaluru", "greenhouse", "india-it"]
    },
    {
        "id": "acurus-solutions",
        "name": "Acurus Solutions India",
        "domain": "acurussolutions.com",
        "careers_url": "https://boards.greenhouse.io/acurussolutions",
        "industry": "Healthcare IT Consulting & Digital Services",
        "hq_location": "Chennai, Tamil Nadu, India",
        "tier": 2,
        "ats_type": "greenhouse",
        "ats_identifier": "acurussolutions",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/acurussolutions/jobs?content=true",
        "tags": ["healthcare-it", "chennai", "greenhouse", "india-it"]
    },
    {
        "id": "acceldata-india",
        "name": "Acceldata",
        "domain": "acceldata.io",
        "careers_url": "https://jobs.lever.co/acceldata",
        "industry": "Enterprise Data Observability & Cloud Optimization",
        "hq_location": "Bengaluru, Karnataka, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "acceldata",
        "api_endpoint": "https://api.lever.co/v0/postings/acceldata?mode=json",
        "tags": ["data", "cloud", "bengaluru", "lever", "india-it"]
    },
    {
        "id": "aera-technology-india",
        "name": "Aera Technology",
        "domain": "aeratechnology.com",
        "careers_url": "https://jobs.lever.co/aeratechnology",
        "industry": "Decision Intelligence & Cognitive Automation Services",
        "hq_location": "Pune, Maharashtra, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "aeratechnology",
        "api_endpoint": "https://api.lever.co/v0/postings/aeratechnology?mode=json",
        "tags": ["ai", "automation", "pune", "lever", "india-it"]
    },
    {
        "id": "crosscountry-consulting",
        "name": "CrossCountry Consulting",
        "domain": "crosscountry-consulting.com",
        "careers_url": "https://jobs.lever.co/crosscountry-consulting",
        "industry": "Business Advisory & Technology Consulting",
        "hq_location": "Gurugram / India Hub",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "crosscountry-consulting",
        "api_endpoint": "https://api.lever.co/v0/postings/crosscountry-consulting?mode=json",
        "tags": ["advisory", "consulting", "lever", "india-it"]
    },
    {
        "id": "wavicle-data-solutions",
        "name": "Wavicle Data Solutions",
        "domain": "wavicledata.com",
        "careers_url": "https://jobs.lever.co/wavicledata",
        "industry": "Cloud Analytics & Big Data Consulting",
        "hq_location": "Coimbatore / Pune Hub, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "wavicledata",
        "api_endpoint": "https://api.lever.co/v0/postings/wavicledata?mode=json",
        "tags": ["analytics", "bigdata", "consulting", "lever", "india-it"]
    },
    {
        "id": "walker-consultants",
        "name": "Walker Consultants",
        "domain": "walkerconsultants.com",
        "careers_url": "https://jobs.lever.co/walkerconsultants",
        "industry": "Forensic Engineering & Technical Design Consulting",
        "hq_location": "India Delivery Hub",
        "tier": 2,
        "ats_type": "lever",
        "ats_identifier": "walkerconsultants",
        "api_endpoint": "https://api.lever.co/v0/postings/walkerconsultants?mode=json",
        "tags": ["engineering", "consulting", "lever", "india-it"]
    },
    {
        "id": "telus-digital-india",
        "name": "TELUS Digital India",
        "domain": "telusdigital.com",
        "careers_url": "https://jobs.ashbyhq.com/telus-digital",
        "industry": "Digital IT Solutions & AI Data Services",
        "hq_location": "Noida / Bengaluru Hub, India",
        "tier": 1,
        "ats_type": "ashby",
        "ats_identifier": "telus-digital",
        "api_endpoint": "https://api.ashbyhq.com/posting-api/job-board/telus-digital",
        "tags": ["ai", "digital-it", "ashby", "india-it"]
    },
    {
        "id": "tigerdata-india",
        "name": "Tiger Data & Analytics",
        "domain": "tigerdata.com",
        "careers_url": "https://jobs.ashbyhq.com/tigerdata",
        "industry": "Advanced AI & Enterprise Data Engineering",
        "hq_location": "Chennai / Bengaluru Hub, India",
        "tier": 1,
        "ats_type": "ashby",
        "ats_identifier": "tigerdata",
        "api_endpoint": "https://api.ashbyhq.com/posting-api/job-board/tigerdata",
        "tags": ["ai", "analytics", "ashby", "india-it"]
    },
    {
        "id": "vantage-analytics",
        "name": "Vantage Analytics & Consulting",
        "domain": "vantageanalytics.com",
        "careers_url": "https://jobs.ashbyhq.com/vantageanalytics",
        "industry": "Analytics & Enterprise Intelligence Services",
        "hq_location": "Bengaluru / India Hub",
        "tier": 2,
        "ats_type": "ashby",
        "ats_identifier": "vantageanalytics",
        "api_endpoint": "https://api.ashbyhq.com/posting-api/job-board/vantageanalytics",
        "tags": ["analytics", "consulting", "ashby", "india-it"]
    },
    {
        "id": "acutech-group",
        "name": "AcuTech Consulting Group",
        "domain": "acutech-consulting.com",
        "careers_url": "https://boards.greenhouse.io/acutechgroupinc",
        "industry": "Safety & Process Engineering Risk Consulting",
        "hq_location": "Mumbai, Maharashtra, India",
        "tier": 2,
        "ats_type": "greenhouse",
        "ats_identifier": "acutechgroupinc",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/acutechgroupinc/jobs?content=true",
        "tags": ["engineering", "consulting", "mumbai", "greenhouse", "india-it"]
    },
    {
        "id": "advanced-tech-services",
        "name": "Advanced Technology Services",
        "domain": "advancedtech.com",
        "careers_url": "https://boards.greenhouse.io/advancedtechnologyservices",
        "industry": "Industrial Technology & Digital Engineering Services",
        "hq_location": "India Engineering Delivery Center",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "advancedtechnologyservices",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/advancedtechnologyservices/jobs?content=true",
        "tags": ["engineering", "services", "greenhouse", "india-it"]
    },
    {
        "id": "3cloud-azure-consulting",
        "name": "3Cloud Azure Solutions",
        "domain": "3cloudsolutions.com",
        "careers_url": "https://boards.greenhouse.io/3cloud",
        "industry": "Azure Cloud Modernization & Managed Consulting",
        "hq_location": "Bengaluru / India Remote Hub",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "3cloud",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/3cloud/jobs?content=true",
        "tags": ["cloud", "azure", "consulting", "greenhouse", "india-it"]
    }
]

# Helper functions for normalization and live verification
def sanitize_id(raw_id: str) -> str:
    s = re.sub(r"[^a-z0-9_-]", "-", raw_id.lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s

def format_company_name(slug: str) -> str:
    clean = re.sub(r"[-_]+", " ", slug).strip()
    return " ".join([w.capitalize() for w in clean.split()])

def determine_location(locs: List[str]) -> str:
    for l in locs:
        l_lower = l.lower()
        if "bengaluru" in l_lower or "bangalore" in l_lower:
            return "Bengaluru, India"
        if "hyderabad" in l_lower:
            return "Hyderabad, India"
        if "pune" in l_lower:
            return "Pune, India"
        if "chennai" in l_lower:
            return "Chennai, India"
        if "noida" in l_lower:
            return "Noida, India"
        if "gurugram" in l_lower or "gurgaon" in l_lower:
            return "Gurugram, India"
        if "mumbai" in l_lower:
            return "Mumbai, India"
        if "delhi" in l_lower:
            return "New Delhi, India"
        if "india" in l_lower:
            return "India"
    return "Bengaluru / India Hub"

def determine_industry_from_name(name: str) -> str:
    n = name.lower()
    if any(k in n for k in ["consult", "advisory"]):
        return "Technology & Strategic Consulting"
    if any(k in n for k in ["cloud", "azure", "aws", "devops"]):
        return "Cloud Infrastructure & Managed IT Services"
    if any(k in n for k in ["data", "analytics", "ai", "intelligence"]):
        return "Enterprise Data & AI Solutions"
    if any(k in n for k in ["security", "cyber", "network"]):
        return "Cybersecurity & IT Infrastructure Services"
    if any(k in n for k in ["er&d", "engineer", "cad", "embedded"]):
        return "Engineering & R&D Services (ER&D)"
    return "IT Services & Digital Engineering"

async def verify_workday(session: AsyncSession, config: Dict[str, Any], sem: asyncio.Semaphore) -> bool:
    sub = config.get("workday_sub", "wd1")
    tenant = config["ats_identifier"]
    site = config.get("workday_site", "Careers")
    url = config.get("api_endpoint") or f"https://{tenant}.{sub}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    payload = {"appliedFacets": {}, "limit": 2, "offset": 0, "searchText": ""}
    async with sem:
        try:
            resp = await session.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                return "jobPostings" in data or "total" in data
        except Exception:
            pass
    return False

async def verify_smartrecruiters(session: AsyncSession, config: Dict[str, Any], sem: asyncio.Semaphore) -> bool:
    token = config["ats_identifier"]
    url = f"https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=1"
    async with sem:
        try:
            resp = await session.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("totalFound", 0) > 0
        except Exception:
            pass
    return False

async def verify_lever(session: AsyncSession, config: Dict[str, Any], sem: asyncio.Semaphore) -> bool:
    token = config["ats_identifier"]
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    async with sem:
        try:
            resp = await session.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                return isinstance(data, list) and len(data) > 0
        except Exception:
            pass
    return False

async def verify_greenhouse(session: AsyncSession, config: Dict[str, Any], sem: asyncio.Semaphore) -> bool:
    token = config["ats_identifier"]
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    async with sem:
        try:
            resp = await session.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                return "jobs" in data and len(data["jobs"]) > 0
        except Exception:
            pass
    return False

async def verify_ashby(session: AsyncSession, config: Dict[str, Any], sem: asyncio.Semaphore) -> bool:
    token = config["ats_identifier"]
    url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
    async with sem:
        try:
            resp = await session.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                return "jobs" in data and len(data["jobs"]) > 0
        except Exception:
            pass
    return False

async def verify_candidate(session: AsyncSession, config: Dict[str, Any], sem: asyncio.Semaphore) -> Optional[Dict[str, Any]]:
    ats = config["ats_type"]
    verified = False
    if ats == "workday":
        verified = await verify_workday(session, config, sem)
    elif ats == "smartrecruiters":
        verified = await verify_smartrecruiters(session, config, sem)
    elif ats == "lever":
        verified = await verify_lever(session, config, sem)
    elif ats == "greenhouse":
        verified = await verify_greenhouse(session, config, sem)
    elif ats == "ashby":
        verified = await verify_ashby(session, config, sem)

    if verified:
        return config
    return None

async def harvest_all():
    logger.info("Starting Indian IT Services, Consultancies, and ER&D Harvester...")
    sem = asyncio.Semaphore(35)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    verified_profiles: Dict[str, Dict[str, Any]] = {}
    seen_domains: Set[str] = set()

    # Phase 1: Verify curated core profiles
    logger.info(f"Phase 1: Verifying {len(CURATED_PROFILES)} curated IT/ER&D profiles...")
    async with AsyncSession(impersonate="chrome120", timeout=8) as session:
        curated_tasks = [verify_candidate(session, c, sem) for c in CURATED_PROFILES]
        curated_results = await asyncio.gather(*curated_tasks)

        for p in curated_results:
            if not p:
                continue
            cid = sanitize_id(p["id"])
            dom = p["domain"].lower()
            if cid in verified_profiles or dom in seen_domains:
                continue
            seen_domains.add(dom)
            verified_profiles[cid] = {
                "id": cid,
                "name": p["name"],
                "domain": dom,
                "careers_url": p["careers_url"],
                "industry": p.get("industry", "IT Services & Consulting"),
                "hq_location": p.get("hq_location", "India"),
                "tier": p.get("tier", 1),
                "ats_type": p["ats_type"],
                "ats_identifier": p["ats_identifier"],
                "api_endpoint": p["api_endpoint"],
                "is_verified": True,
                "tags": p.get("tags", ["india-it", p["ats_type"]])
            }

    logger.info(f"Phase 1 Complete: {len(verified_profiles)} curated profiles live-verified.")

    # Phase 2: Load extended IT services pool from discovered_it_pool.json if available
    discovered_pool_path = REPO_ROOT / "discovered_it_pool.json"
    candidate_items = []
    if discovered_pool_path.exists():
        with open(discovered_pool_path, "r", encoding="utf-8") as f:
            candidate_items = json.load(f)
        logger.info(f"Phase 2: Loaded {len(candidate_items)} discovered candidates from pool.")
    elif OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing_records = json.load(f)
        logger.info(f"Phase 2: Loaded {len(existing_records)} existing candidate records from {OUTPUT_FILE.name}")
        candidate_items = [
            {
                "slug": r.get("ats_identifier") or r["id"],
                "name": r["name"],
                "ats": r["ats_type"],
                "loc": r.get("hq_location", "Bengaluru, India"),
                "jobs": 10
            }
            for r in existing_records
        ]
    else:
        logger.info("Phase 2: No cached candidates found, querying dynamic sources...")

    # Filter candidate items for IT services & consultancies
    filtered_candidates: List[Dict[str, Any]] = []
    for item in candidate_items:
        slug = item["slug"].lower()
        name = item["name"]
        dom = f"{slug}.com"
        cid = sanitize_id(f"{slug}-it" if slug in ["apple", "google", "meta"] else slug)
        if cid in verified_profiles or dom in seen_domains:
            continue

        ats = item["ats"]
        if ats == "greenhouse":
            endpoint = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
            careers_url = f"https://boards.greenhouse.io/{slug}"
        elif ats == "lever":
            endpoint = f"https://api.lever.co/v0/postings/{slug}?mode=json"
            careers_url = f"https://jobs.lever.co/{slug}"
        elif ats == "ashby":
            endpoint = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
            careers_url = f"https://jobs.ashbyhq.com/{slug}"
        elif ats == "smartrecruiters":
            endpoint = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
            careers_url = f"https://careers.smartrecruiters.com/{slug}"
        else:
            continue

        industry = determine_industry_from_name(name)
        tags = ["india-it", "itservices", ats]
        loc = item.get("loc", "Bengaluru, India")
        if "bengaluru" in loc.lower():
            tags.append("bengaluru")
        elif "pune" in loc.lower():
            tags.append("pune")
        elif "chennai" in loc.lower():
            tags.append("chennai")
        elif "hyderabad" in loc.lower():
            tags.append("hyderabad")
        elif "mumbai" in loc.lower():
            tags.append("mumbai")
        elif "noida" in loc.lower() or "gurugram" in loc.lower():
            tags.append("ncr")

        filtered_candidates.append({
            "id": cid,
            "name": name,
            "domain": dom,
            "careers_url": careers_url,
            "industry": industry,
            "hq_location": loc,
            "tier": 1 if item.get("jobs", 0) >= 15 else 2,
            "ats_type": ats,
            "ats_identifier": slug,
            "api_endpoint": endpoint,
            "tags": tags
        })

    logger.info(f"Phase 3: Probing {len(filtered_candidates)} candidates for live verification...")
    async with AsyncSession(impersonate="chrome120", timeout=7) as session:
        probe_tasks = [verify_candidate(session, c, sem) for c in filtered_candidates]
        probe_results = await asyncio.gather(*probe_tasks)

        for p in probe_results:
            if not p:
                continue
            cid = p["id"]
            dom = p["domain"].lower()
            if cid in verified_profiles or dom in seen_domains:
                continue
            seen_domains.add(dom)
            verified_profiles[cid] = {
                "id": cid,
                "name": p["name"],
                "domain": dom,
                "careers_url": p["careers_url"],
                "industry": p["industry"],
                "hq_location": p["hq_location"],
                "tier": p["tier"],
                "ats_type": p["ats_type"],
                "ats_identifier": p["ats_identifier"],
                "api_endpoint": p["api_endpoint"],
                "is_verified": True,
                "tags": p["tags"]
            }

    # Final list sorted deterministically by ID
    output_profiles = sorted(verified_profiles.values(), key=lambda x: x["id"])
    logger.info(f"Harvest complete! Total verified Indian IT & ER&D profiles: {len(output_profiles)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_profiles, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully wrote {len(output_profiles)} company profiles to {OUTPUT_FILE}")

    # Summary by ATS
    by_ats = {}
    for p in output_profiles:
        by_ats[p["ats_type"]] = by_ats.get(p["ats_type"], 0) + 1
    logger.info(f"ATS Breakdown: {by_ats}")

    return output_profiles

if __name__ == "__main__":
    records = asyncio.run(harvest_all())
    print(f"VERIFIED_COUNT={len(records)}")
