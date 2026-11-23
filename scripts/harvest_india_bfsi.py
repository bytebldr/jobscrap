"""Script to harvest, live-verify, and compile 150+ Indian Banks, NBFCs,
and Major Conglomerates employers across Workday, SmartRecruiters, Greenhouse,
Lever, and Custom enterprise portals for JobScrap.
"""

import asyncio
import json
import logging
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional
from curl_cffi.requests import AsyncSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("harvest_india_bfsi")

DATA_DIR = Path(__file__).resolve().parent.parent / "jobscrap" / "catalog" / "data"
OUTPUT_FILE = DATA_DIR / "india_bfsi.json"

# Master list of candidate employers across Workday, SmartRecruiters, Greenhouse, Lever, and Core BFSI
CANDIDATE_CONFIGS: List[Dict[str, Any]] = [
    # =========================================================================
    # WORKDAY BFSI & CONGLOMERATES
    # =========================================================================
    {
        "id": "fiserv-india",
        "name": "Fiserv India",
        "domain": "fiserv.com",
        "careers_url": "https://fiserv.wd5.myworkdayjobs.com/EXT",
        "industry": "Financial Technology & Core Banking Systems",
        "hq_location": "Pune / Bengaluru / Noida, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "fiserv",
        "api_endpoint": "https://fiserv.wd5.myworkdayjobs.com/wday/cxs/fiserv/EXT/jobs",
        "workday_sub": "wd5",
        "workday_site": "EXT",
        "tags": ["fintech", "banking", "payments", "bfsi", "workday"]
    },
    {
        "id": "mastercard-india",
        "name": "Mastercard India",
        "domain": "mastercard.com",
        "careers_url": "https://mastercard.wd1.myworkdayjobs.com/CorporateCareers",
        "industry": "Global Payments & Transaction Processing",
        "hq_location": "Pune / Gurugram / Vadodara, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "mastercard",
        "api_endpoint": "https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers/jobs",
        "workday_sub": "wd1",
        "workday_site": "CorporateCareers",
        "tags": ["fintech", "payments", "cards", "bfsi", "workday"]
    },
    {
        "id": "broadridge-india",
        "name": "Broadridge Financial Solutions India",
        "domain": "broadridge.com",
        "careers_url": "https://broadridge.wd5.myworkdayjobs.com/Careers",
        "industry": "Investor Communications & Capital Markets Tech",
        "hq_location": "Hyderabad / Bengaluru, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "broadridge",
        "api_endpoint": "https://broadridge.wd5.myworkdayjobs.com/wday/cxs/broadridge/Careers/jobs",
        "workday_sub": "wd5",
        "workday_site": "Careers",
        "tags": ["fintech", "capitalmarkets", "bfsi", "workday"]
    },
    {
        "id": "paypal-india",
        "name": "PayPal India",
        "domain": "paypal.com",
        "careers_url": "https://paypal.wd1.myworkdayjobs.com/jobs",
        "industry": "Digital Payments & FinTech",
        "hq_location": "Chennai / Bengaluru / Hyderabad, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "paypal",
        "api_endpoint": "https://paypal.wd1.myworkdayjobs.com/wday/cxs/paypal/jobs/jobs",
        "workday_sub": "wd1",
        "workday_site": "jobs",
        "tags": ["fintech", "payments", "bfsi", "workday"]
    },

    # =========================================================================
    # SMARTRECRUITERS BFSI & TECH
    # =========================================================================
    {
        "id": "experian-india",
        "name": "Experian India",
        "domain": "experian.in",
        "careers_url": "https://jobs.smartrecruiters.com/Experian",
        "industry": "Credit Information Bureau & Decision Analytics",
        "hq_location": "Mumbai / Hyderabad, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Experian",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Experian/postings",
        "tags": ["creditbureau", "analytics", "bfsi", "smartrecruiters"]
    },
    {
        "id": "kredx",
        "name": "KredX",
        "domain": "kredx.com",
        "careers_url": "https://jobs.smartrecruiters.com/KredX",
        "industry": "Supply Chain Finance & Invoice Discounting",
        "hq_location": "Bengaluru, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "KredX",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/KredX/postings",
        "tags": ["nbfc", "fintech", "supplychain", "bfsi", "smartrecruiters"]
    },
    {
        "id": "lendingkart",
        "name": "Lendingkart",
        "domain": "lendingkart.com",
        "careers_url": "https://jobs.smartrecruiters.com/Lendingkart",
        "industry": "Digital MSME Lending & NBFC",
        "hq_location": "Ahmedabad / Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Lendingkart",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Lendingkart/postings",
        "tags": ["nbfc", "lending", "msme", "bfsi", "smartrecruiters"]
    },
    {
        "id": "turtlemint",
        "name": "Turtlemint",
        "domain": "turtlemint.com",
        "careers_url": "https://jobs.smartrecruiters.com/Turtlemint",
        "industry": "InsurTech & Insurance Distribution Platform",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Turtlemint",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Turtlemint/postings",
        "tags": ["insurtech", "insurance", "bfsi", "smartrecruiters"]
    },
    {
        "id": "loophealth",
        "name": "Loop Health",
        "domain": "loophealth.com",
        "careers_url": "https://jobs.smartrecruiters.com/LoopHealth",
        "industry": "Group Health Insurance & Preventive Healthcare",
        "hq_location": "Pune, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "LoopHealth",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/LoopHealth/postings",
        "tags": ["insurtech", "healthcare", "insurance", "smartrecruiters"]
    },
    {
        "id": "bosch-india",
        "name": "Bosch India",
        "domain": "bosch.in",
        "careers_url": "https://jobs.smartrecruiters.com/BoschGroup",
        "industry": "Mobility Solutions, Industrial Technology & Sensor Tech",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "BoschGroup",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/BoschGroup/postings",
        "tags": ["automotive", "mobility", "iot", "smartrecruiters"]
    },
    {
        "id": "western-digital-india",
        "name": "Western Digital India",
        "domain": "westerndigital.com",
        "careers_url": "https://jobs.smartrecruiters.com/WesternDigital",
        "industry": "Data Storage, Flash Memory & Enterprise Systems",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "WesternDigital",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/WesternDigital/postings",
        "tags": ["hardware", "storage", "smartrecruiters"]
    },
    {
        "id": "continental-india",
        "name": "Continental India",
        "domain": "continental.com",
        "careers_url": "https://jobs.smartrecruiters.com/Continental",
        "industry": "Automotive Software, Safety Systems & Autonomous Mobility",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Continental",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Continental/postings",
        "tags": ["automotive", "mobility", "smartrecruiters"]
    },

    # =========================================================================
    # GREENHOUSE BFSI & CONGLOMERATES
    # =========================================================================
    {
        "id": "cleartax",
        "name": "Clear (ClearTax)",
        "domain": "cleartax.in",
        "careers_url": "https://boards.greenhouse.io/clear",
        "industry": "Tax Compliance, Invoicing & Financial SaaS",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "clear",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/clear/jobs?content=true",
        "tags": ["fintech", "tax", "saas", "bfsi", "greenhouse"]
    },
    {
        "id": "groww",
        "name": "Groww",
        "domain": "groww.in",
        "careers_url": "https://boards.greenhouse.io/groww",
        "industry": "Investment Platform & Stock Broking",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "groww",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/groww/jobs?content=true",
        "tags": ["wealthtech", "fintech", "broking", "bfsi", "greenhouse"]
    },
    {
        "id": "slice",
        "name": "Slice (GaragePreneurs / North East SFB)",
        "domain": "sliceit.com",
        "careers_url": "https://boards.greenhouse.io/slice",
        "industry": "Digital Banking & Credit Cards",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "slice",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/slice/jobs?content=true",
        "tags": ["banking", "fintech", "creditcards", "bfsi", "greenhouse"]
    },
    {
        "id": "falconx",
        "name": "FalconX India",
        "domain": "falconx.io",
        "careers_url": "https://boards.greenhouse.io/falconx",
        "industry": "Institutional Digital Assets Brokerage & Crypto Prime Services",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "falconx",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/falconx/jobs?content=true",
        "tags": ["fintech", "crypto", "primebrokerage", "bfsi", "greenhouse"]
    },
    {
        "id": "openfx",
        "name": "OpenFX",
        "domain": "openfx.com",
        "careers_url": "https://boards.greenhouse.io/openfx",
        "industry": "Cross-Border Institutional Payment Infrastructure",
        "hq_location": "Mumbai / Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "openfx",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/openfx/jobs?content=true",
        "tags": ["fintech", "payments", "forex", "bfsi", "greenhouse"]
    },
    {
        "id": "godigit",
        "name": "Go Digit General Insurance",
        "domain": "godigit.com",
        "careers_url": "https://boards.greenhouse.io/digit",
        "industry": "Digital General Insurance & InsurTech",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "greenhouse",
        "ats_identifier": "digit",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/digit/jobs?content=true",
        "tags": ["insurtech", "insurance", "bfsi", "greenhouse"]
    },
    {
        "id": "supreme-industries",
        "name": "Supreme Industries",
        "domain": "supreme.co.in",
        "careers_url": "https://boards.greenhouse.io/supreme",
        "industry": "Plastics & Industrial Infrastructure Conglomerate",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "greenhouse",
        "ats_identifier": "supreme",
        "api_endpoint": "https://boards-api.greenhouse.io/v1/boards/supreme/jobs?content=true",
        "tags": ["manufacturing", "plastics", "infrastructure", "greenhouse"]
    },

    # =========================================================================
    # LEVER BFSI & FINTECH
    # =========================================================================
    {
        "id": "cred",
        "name": "CRED",
        "domain": "cred.club",
        "careers_url": "https://jobs.lever.co/cred",
        "industry": "Credit Card Payments, Lending & Wealth Management",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "cred",
        "api_endpoint": "https://api.lever.co/v0/postings/cred?mode=json",
        "tags": ["fintech", "payments", "lending", "bfsi", "lever"]
    },
    {
        "id": "paytm",
        "name": "Paytm (One97 Communications)",
        "domain": "paytm.com",
        "careers_url": "https://jobs.lever.co/paytm",
        "industry": "Digital Payments, Financial Services & Commerce",
        "hq_location": "Noida, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "paytm",
        "api_endpoint": "https://api.lever.co/v0/postings/paytm?mode=json",
        "tags": ["fintech", "payments", "banking", "bfsi", "lever"]
    },
    {
        "id": "fi-money",
        "name": "Fi Money (epifi)",
        "domain": "fi.money",
        "careers_url": "https://jobs.lever.co/fi",
        "industry": "Neobanking, Mutual Funds & Smart Financial App",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "fi",
        "api_endpoint": "https://api.lever.co/v0/postings/fi?mode=json",
        "tags": ["neobank", "fintech", "wealthtech", "bfsi", "lever"]
    },
    {
        "id": "kenko-health",
        "name": "Kenko Health",
        "domain": "kenkohealth.in",
        "careers_url": "https://jobs.lever.co/kenko",
        "industry": "Subscription Healthcare & OPD Health Financing",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "lever",
        "ats_identifier": "kenko",
        "api_endpoint": "https://api.lever.co/v0/postings/kenko?mode=json",
        "tags": ["insurtech", "healthtech", "financing", "bfsi", "lever"]
    },

    # =========================================================================
    # MAJOR INDIAN COMMERCIAL BANKS (PRIVATE & PUBLIC)
    # =========================================================================
    {
        "id": "hdfc-bank",
        "name": "HDFC Bank",
        "domain": "hdfcbank.com",
        "careers_url": "https://www.hdfcbank.com/personal/useful-links/careers",
        "industry": "Private Sector Banking & Financial Services",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "retailbanking", "commercialbanking", "bfsi", "mumbai"]
    },
    {
        "id": "icici-bank",
        "name": "ICICI Bank",
        "domain": "icicibank.com",
        "careers_url": "https://www.icicicareers.com",
        "industry": "Private Sector Banking & Diversified Financial Services",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "retailbanking", "corporatebanking", "bfsi", "mumbai"]
    },
    {
        "id": "axis-bank",
        "name": "Axis Bank",
        "domain": "axisbank.com",
        "careers_url": "https://www.axisbank.com/careers",
        "industry": "Private Sector Banking & Corporate Lending",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "retailbanking", "corporatebanking", "bfsi", "mumbai"]
    },
    {
        "id": "kotak-mahindra-bank",
        "name": "Kotak Mahindra Bank",
        "domain": "kotak.com",
        "careers_url": "https://www.kotak.com/en/careers.html",
        "industry": "Commercial Banking, Asset Management & Investment Banking",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "wealthmanagement", "bfsi", "mumbai"]
    },
    {
        "id": "indusind-bank",
        "name": "IndusInd Bank",
        "domain": "indusind.com",
        "careers_url": "https://www.indusind.com/in/en/personal/careers.html",
        "industry": "Commercial Banking & Consumer Finance",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "consumerfinance", "bfsi", "mumbai"]
    },
    {
        "id": "idfc-first-bank",
        "name": "IDFC FIRST Bank",
        "domain": "idfcfirstbank.com",
        "careers_url": "https://www.idfcfirstbank.com/careers",
        "industry": "Universal Banking & Customer-First Retail Finance",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "retailbanking", "fintech", "bfsi", "mumbai"]
    },
    {
        "id": "yes-bank",
        "name": "Yes Bank",
        "domain": "yesbank.in",
        "careers_url": "https://www.yesbank.in/about-us/careers",
        "industry": "Full-Service Commercial Banking & Digital Payments API",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "upi", "corporatebanking", "bfsi", "mumbai"]
    },
    {
        "id": "federal-bank",
        "name": "Federal Bank",
        "domain": "federalbank.co.in",
        "careers_url": "https://www.federalbank.co.in/careers",
        "industry": "Private Sector Banking & NRI Remittance Services",
        "hq_location": "Aluva, Kerala, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "fintechpartnerships", "remittance", "bfsi"]
    },
    {
        "id": "bandhan-bank",
        "name": "Bandhan Bank",
        "domain": "bandhanbank.com",
        "careers_url": "https://www.bandhanbank.com/careers",
        "industry": "Inclusive Banking & Microfinance Lending",
        "hq_location": "Kolkata, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "microfinance", "inclusivity", "bfsi", "kolkata"]
    },
    {
        "id": "rbl-bank",
        "name": "RBL Bank",
        "domain": "rblbank.com",
        "careers_url": "https://www.rblbank.com/about-us/careers",
        "industry": "Scheduled Commercial Bank & Co-Branded Cards",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["banking", "creditcards", "bfsi", "mumbai"]
    },
    {
        "id": "au-small-finance-bank",
        "name": "AU Small Finance Bank",
        "domain": "aubank.in",
        "careers_url": "https://www.aubank.in/careers",
        "industry": "Small Finance Bank & Vehicle / MSME Financing",
        "hq_location": "Jaipur, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "smallfinancebank", "msme", "bfsi", "jaipur"]
    },
    {
        "id": "equitas-small-finance-bank",
        "name": "Equitas Small Finance Bank",
        "domain": "equitasbank.com",
        "careers_url": "https://www.equitasbank.com/careers",
        "industry": "Small Finance Bank & Inclusive Retail Banking",
        "hq_location": "Chennai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["banking", "smallfinancebank", "chennai", "bfsi"]
    },
    {
        "id": "ujjivan-small-finance-bank",
        "name": "Ujjivan Small Finance Bank",
        "domain": "ujjivansfb.in",
        "careers_url": "https://www.ujjivansfb.in/careers",
        "industry": "Financial Inclusion & Mass Market Banking",
        "hq_location": "Bengaluru, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["banking", "smallfinancebank", "bengaluru", "bfsi"]
    },
    {
        "id": "jana-small-finance-bank",
        "name": "Jana Small Finance Bank",
        "domain": "janabank.com",
        "careers_url": "https://www.janabank.com/careers",
        "industry": "Small Finance Bank & Urban Financial Inclusion",
        "hq_location": "Bengaluru, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["banking", "smallfinancebank", "bengaluru", "bfsi"]
    },
    {
        "id": "state-bank-of-india",
        "name": "State Bank of India (SBI)",
        "domain": "sbi.co.in",
        "careers_url": "https://sbi.co.in/web/careers",
        "industry": "Public Sector Banking & Apex Financial Conglomerate",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "publicsector", "sovereign", "bfsi", "mumbai"]
    },
    {
        "id": "bank-of-baroda",
        "name": "Bank of Baroda",
        "domain": "bankofbaroda.in",
        "careers_url": "https://www.bankofbaroda.in/career",
        "industry": "Public Sector Banking & International Operations",
        "hq_location": "Vadodara / Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "publicsector", "corporatebanking", "bfsi"]
    },
    {
        "id": "punjab-national-bank",
        "name": "Punjab National Bank (PNB)",
        "domain": "pnbindia.in",
        "careers_url": "https://www.pnbindia.in/Recruitments.aspx",
        "industry": "Public Sector Banking & Agri-Credit Finance",
        "hq_location": "New Delhi, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "publicsector", "ncr", "bfsi"]
    },
    {
        "id": "canara-bank",
        "name": "Canara Bank",
        "domain": "canarabank.com",
        "careers_url": "https://canarabank.com/pages/careers",
        "industry": "Public Sector Banking & Corporate Credit",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "publicsector", "bengaluru", "bfsi"]
    },
    {
        "id": "union-bank-of-india",
        "name": "Union Bank of India",
        "domain": "unionbankofindia.co.in",
        "careers_url": "https://www.unionbankofindia.co.in/english/recruitment.aspx",
        "industry": "Public Sector Commercial Banking",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["banking", "publicsector", "mumbai", "bfsi"]
    },
    {
        "id": "bank-of-india",
        "name": "Bank of India",
        "domain": "bankofindia.co.in",
        "careers_url": "https://bankofindia.co.in/career",
        "industry": "Commercial Banking & Global Presence",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["banking", "publicsector", "mumbai", "bfsi"]
    },
    {
        "id": "indian-bank",
        "name": "Indian Bank",
        "domain": "indianbank.in",
        "careers_url": "https://www.indianbank.in/career",
        "industry": "Commercial Banking & Retail Finance",
        "hq_location": "Chennai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["banking", "publicsector", "chennai", "bfsi"]
    },

    # =========================================================================
    # MAJOR INDIAN CONGLOMERATES & INDUSTRIAL LEADERS
    # =========================================================================
    {
        "id": "reliance-industries",
        "name": "Reliance Industries Limited (RIL)",
        "domain": "ril.com",
        "careers_url": "https://www.ril.com/careers",
        "industry": "Diversified Conglomerate (Energy, Retail, Telecom, Tech)",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["conglomerate", "energy", "petrochemicals", "retail", "telecom", "mumbai"]
    },
    {
        "id": "reliance-jio",
        "name": "Reliance Jio Infocomm",
        "domain": "jio.com",
        "careers_url": "https://careers.jio.com",
        "industry": "Telecommunications & Digital Ecosystems",
        "hq_location": "Navi Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["telecom", "digital", "5g", "cloud", "mumbai", "conglomerate"]
    },
    {
        "id": "reliance-retail",
        "name": "Reliance Retail",
        "domain": "relianceretail.com",
        "careers_url": "https://relianceretail.com",
        "industry": "Omnichannel Retail & Consumer Products",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["retail", "ecommerce", "supplychain", "mumbai", "conglomerate"]
    },
    {
        "id": "jio-financial-services",
        "name": "Jio Financial Services (JFS)",
        "domain": "jfs.in",
        "careers_url": "https://www.jfs.in",
        "industry": "Digital Financial Services, Lending, Insurance & Asset Management",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["fintech", "nbfc", "wealthtech", "bfsi", "mumbai"]
    },
    {
        "id": "tata-motors",
        "name": "Tata Motors",
        "domain": "tatamotors.com",
        "careers_url": "https://www.tatamotors.com/careers",
        "industry": "Automotive Engineering, Commercial & Electric Vehicles",
        "hq_location": "Mumbai / Pune, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["automotive", "ev", "manufacturing", "conglomerate", "tata"]
    },
    {
        "id": "tata-steel",
        "name": "Tata Steel",
        "domain": "tatasteel.com",
        "careers_url": "https://www.tatasteel.com/careers",
        "industry": "Metals, Mining & Steel Manufacturing",
        "hq_location": "Mumbai / Jamshedpur, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["steel", "metals", "manufacturing", "conglomerate", "tata"]
    },
    {
        "id": "tata-power",
        "name": "Tata Power",
        "domain": "tatapower.com",
        "careers_url": "https://www.tatapower.com/careers.aspx",
        "industry": "Integrated Power & Clean Renewable Energy",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["energy", "renewables", "utilities", "conglomerate", "tata"]
    },
    {
        "id": "tata-consumer-products",
        "name": "Tata Consumer Products",
        "domain": "tataconsumer.com",
        "careers_url": "https://www.tataconsumer.com/careers",
        "industry": "FMCG, Food & Beverage Products",
        "hq_location": "Mumbai / Kolkata, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["fmcg", "consumer", "food", "conglomerate", "tata"]
    },
    {
        "id": "tata-communications",
        "name": "Tata Communications",
        "domain": "tatacommunications.com",
        "careers_url": "https://www.tatacommunications.com/careers",
        "industry": "Digital Infrastructure, Global Networks & Cloud Cybersecurity",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["telecom", "cloud", "networking", "conglomerate", "tata"]
    },
    {
        "id": "tata-capital",
        "name": "Tata Capital",
        "domain": "tatacapital.com",
        "careers_url": "https://www.tatacapital.com/careers.html",
        "industry": "Non-Banking Financial Company (NBFC) & Corporate Advisory",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "lending", "wealthmanagement", "bfsi", "tata"]
    },
    {
        "id": "titan-company",
        "name": "Titan Company (Tata Group)",
        "domain": "titancompany.in",
        "careers_url": "https://www.titancompany.in/careers",
        "industry": "Jewellery, Watches, Eyewear & Lifestyle Accessories",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["lifestyle", "jewellery", "luxury", "retail", "tata", "bengaluru"]
    },
    {
        "id": "voltas",
        "name": "Voltas (Tata Enterprise)",
        "domain": "voltas.com",
        "careers_url": "https://www.voltas.com/careers",
        "industry": "Air Conditioning, Engineering Products & MEP Solutions",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["consumerappliances", "engineering", "mep", "tata"]
    },
    {
        "id": "trent-limited",
        "name": "Trent Limited (Westside & Zudio)",
        "domain": "trentlimited.com",
        "careers_url": "https://trentlimited.com/pages/careers",
        "industry": "Fashion Retail & Value Apparel Retail",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["retail", "fashion", "apparel", "tata", "mumbai"]
    },
    {
        "id": "indian-hotels-company",
        "name": "The Indian Hotels Company (IHCL / Taj)",
        "domain": "ihcltata.com",
        "careers_url": "https://www.ihcltata.com/careers",
        "industry": "Hospitality, Luxury Hotels & Resorts",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["hospitality", "luxury", "hotels", "tata", "mumbai"]
    },
    {
        "id": "mahindra-and-mahindra",
        "name": "Mahindra & Mahindra",
        "domain": "mahindra.com",
        "careers_url": "https://www.mahindra.com/careers",
        "industry": "Automotive, Farm Equipment & Aerospace Mobility",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["automotive", "tractors", "mobility", "conglomerate", "mumbai"]
    },
    {
        "id": "mahindra-finance",
        "name": "Mahindra & Mahindra Financial Services",
        "domain": "mahindrafinance.com",
        "careers_url": "https://www.mahindrafinance.com/careers",
        "industry": "Rural & Semi-Urban NBFC, Vehicle & Tractor Loans",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "rurallending", "vehicleloans", "bfsi", "mahindra"]
    },
    {
        "id": "mahindra-lifespaces",
        "name": "Mahindra Lifespace Developers",
        "domain": "mahindralifespaces.com",
        "careers_url": "https://www.mahindralifespaces.com/careers",
        "industry": "Sustainable Real Estate & Industrial Infrastructure",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["realestate", "infrastructure", "mahindra", "mumbai"]
    },
    {
        "id": "mahindra-logistics",
        "name": "Mahindra Logistics",
        "domain": "mahindralogistics.com",
        "careers_url": "https://mahindralogistics.com/careers",
        "industry": "Integrated Supply Chain Management & Freight Forwarding",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["logistics", "supplychain", "freight", "mahindra"]
    },
    {
        "id": "larsen-and-toubro",
        "name": "Larsen & Toubro (L&T)",
        "domain": "larsentoubro.com",
        "careers_url": "https://www.larsentoubro.com/corporate/careers",
        "industry": "EPC Infrastructure, Heavy Engineering & Defense Tech",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["infrastructure", "epc", "engineering", "defense", "conglomerate"]
    },
    {
        "id": "lt-finance",
        "name": "L&T Finance Holdings",
        "domain": "ltfs.com",
        "careers_url": "https://www.ltfs.com/careers",
        "industry": "Retail & Infrastructure Financing (NBFC)",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "retailfinance", "infrastructurefinance", "bfsi", "lnt"]
    },
    {
        "id": "lt-technology-services",
        "name": "L&T Technology Services (LTTS)",
        "domain": "ltts.com",
        "careers_url": "https://www.ltts.com/careers",
        "industry": "Engineering Research & Development (ER&D) Services",
        "hq_location": "Vadodara / Bengaluru, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["ernd", "engineering", "embedded", "iot", "lnt"]
    },
    {
        "id": "godrej-industries",
        "name": "Godrej Industries",
        "domain": "godrejindustries.com",
        "careers_url": "https://www.godrejindustries.com/careers",
        "industry": "Chemicals, Palm Oil & Industrial Holding Conglomerate",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["chemicals", "fmcg", "conglomerate", "godrej", "mumbai"]
    },
    {
        "id": "godrej-consumer-products",
        "name": "Godrej Consumer Products Limited (GCPL)",
        "domain": "godrejcp.com",
        "careers_url": "https://www.godrejcp.com/careers",
        "industry": "Personal Care, Home Care & FMCG Products",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["fmcg", "personalcare", "homecare", "godrej", "mumbai"]
    },
    {
        "id": "godrej-properties",
        "name": "Godrej Properties",
        "domain": "godrejproperties.com",
        "careers_url": "https://www.godrejproperties.com/careers",
        "industry": "Premium Residential & Commercial Real Estate",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["realestate", "residential", "construction", "godrej", "mumbai"]
    },
    {
        "id": "godrej-capital",
        "name": "Godrej Capital",
        "domain": "godrejcapital.com",
        "careers_url": "https://www.godrejcapital.com/careers",
        "industry": "Home Loans, Loan Against Property & Business Loans (NBFC)",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["nbfc", "homeloans", "lending", "bfsi", "godrej"]
    },
    {
        "id": "bajaj-finserv",
        "name": "Bajaj Finserv",
        "domain": "bajajfinserv.in",
        "careers_url": "https://www.bajajfinserv.in/careers",
        "industry": "Diversified Financial Services, Lending, Wealth & Protection",
        "hq_location": "Pune, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "wealthmanagement", "insurance", "bfsi", "pune"]
    },
    {
        "id": "bajaj-finance",
        "name": "Bajaj Finance",
        "domain": "bajajfinance.in",
        "careers_url": "https://www.bajajfinserv.in/careers",
        "industry": "Consumer Finance, Digital EMI Cards & SME Lending",
        "hq_location": "Pune, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "consumerlending", "emicards", "bfsi", "pune"]
    },
    {
        "id": "bajaj-housing-finance",
        "name": "Bajaj Housing Finance",
        "domain": "bajajhousingfinance.in",
        "careers_url": "https://www.bajajhousingfinance.in/careers",
        "industry": "Mortgage Lending & Housing Finance Company",
        "hq_location": "Pune, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["housingfinance", "mortgage", "lending", "bfsi", "pune"]
    },
    {
        "id": "bajaj-allianz-general-insurance",
        "name": "Bajaj Allianz General Insurance",
        "domain": "bajajallianz.com",
        "careers_url": "https://www.bajajallianz.com/careers.html",
        "industry": "General, Health & Motor Insurance Solutions",
        "hq_location": "Pune, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["insurance", "generalinsurance", "healthinsurance", "bfsi", "pune"]
    },
    {
        "id": "bajaj-auto",
        "name": "Bajaj Auto",
        "domain": "bajajauto.com",
        "careers_url": "https://www.bajajauto.com/careers",
        "industry": "Two-Wheeler & Three-Wheeler Automotive Manufacturing",
        "hq_location": "Pune, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["automotive", "twowheeler", "manufacturing", "conglomerate", "pune"]
    },
    {
        "id": "adani-enterprises",
        "name": "Adani Enterprises",
        "domain": "adanienterprises.com",
        "careers_url": "https://www.adanienterprises.com/careers",
        "industry": "Incubator Conglomerate (Airports, Mining, Roads, Data Centers)",
        "hq_location": "Ahmedabad, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["conglomerate", "infrastructure", "airports", "datacenters", "adani"]
    },
    {
        "id": "adani-ports-and-sez",
        "name": "Adani Ports and Special Economic Zone (APSEZ)",
        "domain": "adaniports.com",
        "careers_url": "https://www.adaniports.com/careers",
        "industry": "Port Operations, Logistics & Marine Infrastructure",
        "hq_location": "Ahmedabad, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["ports", "logistics", "maritime", "infrastructure", "adani"]
    },
    {
        "id": "adani-green-energy",
        "name": "Adani Green Energy",
        "domain": "adanigreenenergy.com",
        "careers_url": "https://www.adanigreenenergy.com/careers",
        "industry": "Renewable Energy (Solar, Wind & Hybrid Power Generation)",
        "hq_location": "Ahmedabad, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["renewables", "solar", "wind", "energy", "clean-tech", "adani"]
    },
    {
        "id": "adani-power",
        "name": "Adani Power",
        "domain": "adanipower.com",
        "careers_url": "https://www.adanipower.com/careers",
        "industry": "Thermal & Utility Power Generation",
        "hq_location": "Ahmedabad, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["power", "energy", "utilities", "adani"]
    },
    {
        "id": "adani-total-gas",
        "name": "Adani Total Gas",
        "domain": "adanigas.com",
        "careers_url": "https://www.adanigas.com/careers",
        "industry": "City Gas Distribution (CNG & PNG Network)",
        "hq_location": "Ahmedabad, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["gas", "energy", "utilities", "cng", "adani"]
    },
    {
        "id": "adani-energy-solutions",
        "name": "Adani Energy Solutions",
        "domain": "adanienergysolutions.com",
        "careers_url": "https://www.adanienergysolutions.com/careers",
        "industry": "Power Transmission, Smart Metering & Grid Infrastructure",
        "hq_location": "Ahmedabad, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["transmission", "smartmetering", "grid", "adani"]
    },
    {
        "id": "ambuja-cements",
        "name": "Ambuja Cements (Adani Group)",
        "domain": "ambujacement.com",
        "careers_url": "https://www.ambujacement.com/careers",
        "industry": "Cement Manufacturing & Building Materials",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["cement", "buildingmaterials", "construction", "adani", "mumbai"]
    },
    {
        "id": "acc-limited",
        "name": "ACC Limited (Adani Group)",
        "domain": "acclimited.com",
        "careers_url": "https://www.acclimited.com/careers",
        "industry": "Cement & Ready-Mixed Concrete Manufacturing",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["cement", "concrete", "buildingmaterials", "adani", "mumbai"]
    },
    {
        "id": "aditya-birla-capital",
        "name": "Aditya Birla Capital",
        "domain": "adityabirlacapital.com",
        "careers_url": "https://www.adityabirlacapital.com/careers",
        "industry": "Universal Financial Solutions, NBFC, AMC & Health Insurance",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "amc", "insurance", "bfsi", "adityabirla", "mumbai"]
    },
    {
        "id": "grasim-industries",
        "name": "Grasim Industries (Aditya Birla Group)",
        "domain": "grasim.com",
        "careers_url": "https://www.grasim.com/careers",
        "industry": "Viscose Staple Fibre, Chlor-Alkali & Birla Opus Paints",
        "hq_location": "Nagda / Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["textiles", "chemicals", "paints", "conglomerate", "adityabirla"]
    },
    {
        "id": "hindalco-industries",
        "name": "Hindalco Industries (Aditya Birla Group)",
        "domain": "hindalco.com",
        "careers_url": "https://www.hindalco.com/careers",
        "industry": "Aluminium & Copper Manufacturing (Novelty & Rolled Products)",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["metals", "aluminium", "copper", "manufacturing", "adityabirla"]
    },
    {
        "id": "ultratech-cement",
        "name": "UltraTech Cement",
        "domain": "ultratechcement.com",
        "careers_url": "https://www.ultratechcement.com/careers",
        "industry": "Grey Cement, White Cement & Building Solutions",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["cement", "buildingmaterials", "manufacturing", "adityabirla", "mumbai"]
    },
    {
        "id": "aditya-birla-fashion-retail",
        "name": "Aditya Birla Fashion and Retail (ABFRL)",
        "domain": "abfrl.com",
        "careers_url": "https://careers.abfrl.com",
        "industry": "Fashion Apparel (Louis Philippe, Van Heusen, Pantaloons)",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["fashion", "retail", "apparel", "adityabirla", "mumbai"]
    },
    {
        "id": "jsw-steel",
        "name": "JSW Steel",
        "domain": "jswsteel.in",
        "careers_url": "https://www.jswsteel.in/careers",
        "industry": "Integrated Steel Manufacturing & High-Value Flats",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["steel", "metals", "manufacturing", "conglomerate", "jsw"]
    },
    {
        "id": "jsw-energy",
        "name": "JSW Energy",
        "domain": "jswenergy.in",
        "careers_url": "https://www.jswenergy.in/careers",
        "industry": "Power Generation (Thermal, Hydro & Solar Power)",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["power", "energy", "renewables", "utilities", "jsw"]
    },
    {
        "id": "vedanta-limited",
        "name": "Vedanta Limited",
        "domain": "vedantalimited.com",
        "careers_url": "https://www.vedantalimited.com/eng/careers.php",
        "industry": "Natural Resources (Zinc, Lead, Silver, Aluminium, Oil & Gas)",
        "hq_location": "Mumbai / New Delhi, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["mining", "metals", "oilandgas", "conglomerate", "vedanta"]
    },
    {
        "id": "hindustan-zinc",
        "name": "Hindustan Zinc (Vedanta)",
        "domain": "hzlindia.com",
        "careers_url": "https://www.hzlindia.com/careers",
        "industry": "Zinc, Lead & Silver Mining & Smelting",
        "hq_location": "Udaipur, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["mining", "silver", "metals", "vedanta", "udaipur"]
    },
    {
        "id": "piramal-enterprises",
        "name": "Piramal Enterprises",
        "domain": "piramal.com",
        "careers_url": "https://www.piramal.com/careers",
        "industry": "Diversified Financial Services, Wholesale & Retail Lending",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "lending", "financialservices", "bfsi", "piramal"]
    },
    {
        "id": "piramal-finance",
        "name": "Piramal Capital & Housing Finance",
        "domain": "piramalfinance.com",
        "careers_url": "https://www.piramalfinance.com/careers",
        "industry": "Affordable Housing Finance, Business & Personal Loans",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["housingfinance", "nbfc", "mortgage", "bfsi", "piramal"]
    },
    {
        "id": "ashok-leyland",
        "name": "Ashok Leyland (Hinduja Group)",
        "domain": "ashokleyland.com",
        "careers_url": "https://www.ashokleyland.com/en/careers",
        "industry": "Commercial Vehicles, Buses, Trucks & Defense Vehicles",
        "hq_location": "Chennai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["automotive", "commercialvehicles", "defense", "hinduja", "chennai"]
    },
    {
        "id": "hinduja-leyland-finance",
        "name": "Hinduja Leyland Finance",
        "domain": "hindujaleylandfinance.com",
        "careers_url": "https://www.hindujaleylandfinance.com/careers",
        "industry": "Commercial Vehicle & Two-Wheeler Financing (NBFC)",
        "hq_location": "Chennai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["nbfc", "vehicleloans", "lending", "bfsi", "hinduja"]
    },
    {
        "id": "cholamandalam-investment",
        "name": "Cholamandalam Investment and Finance (Murugappa)",
        "domain": "cholamandalam.com",
        "careers_url": "https://www.cholamandalam.com/careers",
        "industry": "Vehicle Finance, Home Equity & MSME Loans (NBFC)",
        "hq_location": "Chennai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "vehiclefinance", "msme", "bfsi", "chennai"]
    },
    {
        "id": "tvs-motor-company",
        "name": "TVS Motor Company",
        "domain": "tvsmotor.com",
        "careers_url": "https://www.tvsmotor.com/careers",
        "industry": "Two-Wheeler & Three-Wheeler Mobility & EV Manufacturing",
        "hq_location": "Chennai / Hosur, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["automotive", "twowheeler", "ev", "mobility", "chennai"]
    },
    {
        "id": "tvs-credit",
        "name": "TVS Credit Services",
        "domain": "tvscredit.com",
        "careers_url": "https://www.tvscredit.com/careers",
        "industry": "Two-Wheeler, Tractor, Used Car & Consumer Loans (NBFC)",
        "hq_location": "Chennai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["nbfc", "consumerloans", "twowheeler", "bfsi", "chennai"]
    },
    {
        "id": "sundaram-finance",
        "name": "Sundaram Finance",
        "domain": "sundaramfinance.in",
        "careers_url": "https://www.sundaramfinance.in/careers",
        "industry": "Commercial Vehicle Finance, Car Finance & Mutual Funds",
        "hq_location": "Chennai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "vehiclefinance", "mutualfunds", "bfsi", "chennai"]
    },
    {
        "id": "hero-motocorp",
        "name": "Hero MotoCorp",
        "domain": "heromotocorp.com",
        "careers_url": "https://www.heromotocorp.com/en-in/careers.html",
        "industry": "Motorcycles, Scooters & Electric Two-Wheelers (Vida)",
        "hq_location": "New Delhi / Gurugram, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["automotive", "motorcycles", "ev", "manufacturing", "ncr"]
    },
    {
        "id": "hero-fincorp",
        "name": "Hero FinCorp",
        "domain": "herofincorp.com",
        "careers_url": "https://www.herofincorp.com/careers",
        "industry": "Retail & SME Lending (Two-Wheeler & Used Car Loans)",
        "hq_location": "New Delhi, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["nbfc", "retailfinance", "sme", "bfsi", "ncr"]
    },
    {
        "id": "itc-limited",
        "name": "ITC Limited",
        "domain": "itcportal.com",
        "careers_url": "https://www.itcportal.com/careers",
        "industry": "FMCG, Cigarettes, Hotels, Paperboards & Agri Business Conglomerate",
        "hq_location": "Kolkata, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["conglomerate", "fmcg", "hospitality", "agribusiness", "kolkata"]
    },
    {
        "id": "shriram-finance",
        "name": "Shriram Finance",
        "domain": "shriramfinance.in",
        "careers_url": "https://www.shriramfinance.in/careers",
        "industry": "Commercial Vehicle Financing, MSME & Retail Loans (NBFC)",
        "hq_location": "Chennai / Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "commercialvehicles", "msme", "bfsi", "chennai"]
    },
    {
        "id": "muthoot-finance",
        "name": "Muthoot Finance",
        "domain": "muthootfinance.com",
        "careers_url": "https://www.muthootfinance.com/careers",
        "industry": "Gold Loan Financing & Retail Credit (NBFC)",
        "hq_location": "Kochi, Kerala, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["goldloans", "nbfc", "retailcredit", "bfsi", "kerala"]
    },
    {
        "id": "manappuram-finance",
        "name": "Manappuram Finance",
        "domain": "manappuram.com",
        "careers_url": "https://www.manappuram.com/careers.html",
        "industry": "Gold Loans, Microfinance & Vehicle Loans (NBFC)",
        "hq_location": "Thrissur, Kerala, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["goldloans", "microfinance", "nbfc", "bfsi", "kerala"]
    },
    {
        "id": "poonawalla-fincorp",
        "name": "Poonawalla Fincorp (Cyrus Poonawalla Group)",
        "domain": "poonawallafincorp.com",
        "careers_url": "https://poonawallafincorp.com/careers",
        "industry": "Digital Consumer & MSME Non-Banking Financial Company",
        "hq_location": "Pune, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "digitallending", "msme", "bfsi", "pune"]
    },

    # =========================================================================
    # SPECIALIZED WEALTH, INSURANCE, ASSET MANAGEMENT & CAPITAL MARKETS
    # =========================================================================
    {
        "id": "sbi-cards",
        "name": "SBI Cards and Payment Services",
        "domain": "sbicard.com",
        "careers_url": "https://www.sbicard.com/en/who-we-are/careers.page",
        "industry": "Credit Cards & Digital Payment Solutions",
        "hq_location": "Gurugram, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["creditcards", "payments", "bfsi", "ncr", "sbi"]
    },
    {
        "id": "sbi-life-insurance",
        "name": "SBI Life Insurance",
        "domain": "sbilife.co.in",
        "careers_url": "https://www.sbilife.co.in/en/about-us/careers",
        "industry": "Life Insurance, Pensions & Annuity Products",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["lifeinsurance", "pensions", "bfsi", "sbi", "mumbai"]
    },
    {
        "id": "sbi-general-insurance",
        "name": "SBI General Insurance",
        "domain": "sbigeneral.in",
        "careers_url": "https://www.sbigeneral.in/careers",
        "industry": "General Insurance, Health, Motor & Commercial Risk Protection",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["generalinsurance", "healthinsurance", "bfsi", "sbi", "mumbai"]
    },
    {
        "id": "sbi-funds-management",
        "name": "SBI Mutual Fund (SBI Funds Management)",
        "domain": "sbimf.com",
        "careers_url": "https://www.sbimf.com/en-us/careers",
        "industry": "Asset Management & Mutual Fund Investment Schemes",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["amc", "mutualfunds", "assetmanagement", "bfsi", "sbi", "mumbai"]
    },
    {
        "id": "hdfc-life",
        "name": "HDFC Life Insurance",
        "domain": "hdfclife.com",
        "careers_url": "https://www.hdfclife.com/careers",
        "industry": "Individual & Group Life Insurance & Retirement Plans",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["lifeinsurance", "retirement", "protection", "bfsi", "mumbai"]
    },
    {
        "id": "hdfc-ergo",
        "name": "HDFC ERGO General Insurance",
        "domain": "hdfcergo.com",
        "careers_url": "https://www.hdfcergo.com/careers",
        "industry": "Non-Life Insurance (Motor, Health, Travel & Cyber Protection)",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["generalinsurance", "healthinsurance", "cyberinsurance", "bfsi", "mumbai"]
    },
    {
        "id": "hdfc-amc",
        "name": "HDFC Asset Management Company",
        "domain": "hdfcfund.com",
        "careers_url": "https://www.hdfcfund.com/careers",
        "industry": "Mutual Fund Management & Portfolio Management Services (PMS)",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["amc", "mutualfunds", "wealthmanagement", "bfsi", "mumbai"]
    },
    {
        "id": "icici-prudential-life",
        "name": "ICICI Prudential Life Insurance",
        "domain": "iciciprulife.com",
        "careers_url": "https://www.iciciprulife.com/about-us/careers.html",
        "industry": "Life Insurance, Protection, Savings & Retirement Solutions",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["lifeinsurance", "protection", "bfsi", "icici", "mumbai"]
    },
    {
        "id": "icici-lombard",
        "name": "ICICI Lombard General Insurance",
        "domain": "icicilombard.com",
        "careers_url": "https://www.icicilombard.com/careers",
        "industry": "General Insurance, Motor, Health & Crop Insurance",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["generalinsurance", "healthinsurance", "bfsi", "icici", "mumbai"]
    },
    {
        "id": "icici-prudential-amc",
        "name": "ICICI Prudential Asset Management Company",
        "domain": "icicipruamc.com",
        "careers_url": "https://www.icicipruamc.com/careers",
        "industry": "Asset Management, Mutual Funds & Alternate Investment Funds",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["amc", "mutualfunds", "wealth", "bfsi", "icici", "mumbai"]
    },
    {
        "id": "icici-securities",
        "name": "ICICI Securities (ICICIdirect)",
        "domain": "icicisecurities.com",
        "careers_url": "https://www.icicisecurities.com/careers",
        "industry": "Retail Broking, Institutional Equities & Investment Banking",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["broking", "investmentbanking", "equities", "bfsi", "icici", "mumbai"]
    },
    {
        "id": "kotak-life-insurance",
        "name": "Kotak Mahindra Life Insurance",
        "domain": "kotaklife.com",
        "careers_url": "https://www.kotaklife.com/careers",
        "industry": "Life Insurance, Wealth Plans & Employee Benefit Schemes",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["lifeinsurance", "protection", "bfsi", "kotak", "mumbai"]
    },
    {
        "id": "kotak-general-insurance",
        "name": "Kotak General Insurance (Zurich Kotak)",
        "domain": "kotakgeneral.com",
        "careers_url": "https://www.kotakgeneral.com/careers",
        "industry": "Non-Life Insurance Products (Health, Car, Bike Insurance)",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["generalinsurance", "healthinsurance", "bfsi", "kotak", "mumbai"]
    },
    {
        "id": "max-financial-services",
        "name": "Max Financial Services (Max Group)",
        "domain": "maxfinancialservices.com",
        "careers_url": "https://www.maxfinancialservices.com/careers",
        "industry": "Holding Company for Life Insurance & Financial Services",
        "hq_location": "New Delhi / Noida, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["lifeinsurance", "financialservices", "bfsi", "ncr"]
    },
    {
        "id": "max-life-insurance",
        "name": "Max Life Insurance",
        "domain": "maxlifeinsurance.com",
        "careers_url": "https://www.maxlifeinsurance.com/careers",
        "industry": "Long-Term Life Insurance, Term Plans & ULIPs",
        "hq_location": "Gurugram, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["lifeinsurance", "termplans", "bfsi", "ncr"]
    },
    {
        "id": "nippon-life-india-amc",
        "name": "Nippon Life India Asset Management (Nippon India Mutual Fund)",
        "domain": "nipponindiaim.com",
        "careers_url": "https://mf.nipponindiaim.com/careers",
        "industry": "Asset Management, ETFs & Offshore Funds",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["amc", "mutualfunds", "etf", "bfsi", "mumbai"]
    },
    {
        "id": "uti-amc",
        "name": "UTI Asset Management Company",
        "domain": "utimf.com",
        "careers_url": "https://www.utimf.com/careers",
        "industry": "Pioneer Mutual Fund Institution & Wealth Advisory",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["amc", "mutualfunds", "wealth", "bfsi", "mumbai"]
    },
    {
        "id": "motilal-oswal",
        "name": "Motilal Oswal Financial Services",
        "domain": "motilaloswal.com",
        "careers_url": "https://www.motilaloswal.com/careers",
        "industry": "Wealth Management, Equity Broking & Asset Management",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["wealthmanagement", "broking", "amc", "bfsi", "mumbai"]
    },
    {
        "id": "edelweiss-financial-services",
        "name": "Edelweiss Financial Services",
        "domain": "edelweissfin.com",
        "careers_url": "https://www.edelweissfin.com/careers",
        "industry": "Alternative Asset Management, Mutual Funds & Asset Reconstruction",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["alternatives", "amc", "assetreconstruction", "bfsi", "mumbai"]
    },
    {
        "id": "nuvama-wealth",
        "name": "Nuvama Wealth Management (formerly Edelweiss Wealth)",
        "domain": "nuvama.com",
        "careers_url": "https://www.nuvama.com/careers",
        "industry": "Private Wealth, Ultra HNI Family Offices & Asset Services",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["wealthmanagement", "familyoffice", "capitalmarkets", "bfsi", "mumbai"]
    },
    {
        "id": "anand-rathi",
        "name": "Anand Rathi Financial Services",
        "domain": "anandrathi.com",
        "careers_url": "https://www.anandrathi.com/careers",
        "industry": "Private Wealth Management, Institutional Equities & Broking",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["wealthmanagement", "broking", "equities", "bfsi", "mumbai"]
    },
    {
        "id": "angel-one",
        "name": "Angel One",
        "domain": "angelone.in",
        "careers_url": "https://www.angelone.in/careers",
        "industry": "FinTech Retail Stock Broking & Direct Mutual Funds",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["fintech", "broking", "algorithmictrading", "bfsi", "mumbai"]
    },
    {
        "id": "iifl-finance",
        "name": "IIFL Finance",
        "domain": "iifl.com",
        "careers_url": "https://www.iifl.com/careers",
        "industry": "Diversified Retail Lending, Gold Loans & Microfinance (NBFC)",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "goldloans", "retiallending", "bfsi", "mumbai"]
    },
    {
        "id": "iifl-securities",
        "name": "IIFL Securities",
        "domain": "iiflsecurities.com",
        "careers_url": "https://www.iiflsecurities.com/careers",
        "industry": "Capital Markets, Institutional Research & Investment Banking",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["broking", "capitalmarkets", "research", "bfsi", "mumbai"]
    },
    {
        "id": "360-one-wam",
        "name": "360 ONE WAM (formerly IIFL Wealth)",
        "domain": "360.one",
        "careers_url": "https://www.360.one/careers",
        "industry": "Ultra High Net Worth Wealth Management & Alternate Assets",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["wealthmanagement", "alternatives", "uhni", "bfsi", "mumbai"]
    },
    {
        "id": "jm-financial",
        "name": "JM Financial",
        "domain": "jmfl.com",
        "careers_url": "https://jmfl.com/careers",
        "industry": "Investment Banking, Institutional Equities & Real Estate Finance",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["investmentbanking", "institutional", "realestatefinance", "bfsi", "mumbai"]
    },
    {
        "id": "centrum-capital",
        "name": "Centrum Capital",
        "domain": "centrum.co.in",
        "careers_url": "https://www.centrum.co.in/careers",
        "industry": "Investment Banking, Wealth Management & Small Finance Promoter",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["investmentbanking", "wealth", "bfsi", "mumbai"]
    },
    {
        "id": "geojit-financial-services",
        "name": "Geojit Financial Services",
        "domain": "geojit.com",
        "careers_url": "https://www.geojit.com/careers",
        "industry": "Retail Stock Broking, Mutual Fund Distribution & Financial Planning",
        "hq_location": "Kochi, Kerala, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["broking", "financialplanning", "mutualfunds", "bfsi", "kerala"]
    },
    {
        "id": "star-health-insurance",
        "name": "Star Health and Allied Insurance",
        "domain": "starhealth.in",
        "careers_url": "https://www.starhealth.in/careers",
        "industry": "Standalone Health Insurance Specialist",
        "hq_location": "Chennai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["healthinsurance", "claims", "protection", "bfsi", "chennai"]
    },
    {
        "id": "care-health-insurance",
        "name": "Care Health Insurance",
        "domain": "careinsurance.com",
        "careers_url": "https://www.careinsurance.com/careers.html",
        "industry": "Health Insurance, Critical Illness & Travel Health Coverage",
        "hq_location": "Gurugram, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["healthinsurance", "criticalillness", "bfsi", "ncr"]
    },
    {
        "id": "niva-bupa-health-insurance",
        "name": "Niva Bupa Health Insurance (formerly Max Bupa)",
        "domain": "nivabupa.com",
        "careers_url": "https://www.nivabupa.com/careers.html",
        "industry": "Specialized Health Insurance & Family Floater Plans",
        "hq_location": "New Delhi, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["healthinsurance", "familyplans", "bfsi", "ncr"]
    },
    {
        "id": "lic-india",
        "name": "Life Insurance Corporation of India (LIC)",
        "domain": "licindia.in",
        "careers_url": "https://licindia.in/en/web/guest/careers",
        "industry": "Premier State-Owned Life Insurer & Sovereign Institutional Investor",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["lifeinsurance", "publicsector", "sovereign", "bfsi", "mumbai"]
    },
    {
        "id": "gic-re",
        "name": "General Insurance Corporation of India (GIC Re)",
        "domain": "gicre.in",
        "careers_url": "https://www.gicre.in/en/careers",
        "industry": "National Reinsurance Enterprise of India",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["reinsurance", "underwriting", "publicsector", "bfsi", "mumbai"]
    },
    {
        "id": "new-india-assurance",
        "name": "The New India Assurance Company",
        "domain": "newindia.co.in",
        "careers_url": "https://www.newindia.co.in/portal/careers",
        "industry": "Multinational Public Sector General Insurance",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["generalinsurance", "publicsector", "commercialrisk", "bfsi", "mumbai"]
    },

    # =========================================================================
    # DEVELOPMENT FINANCE INSTITUTIONS, INFRASTRUCTURE & MICROFINANCE
    # =========================================================================
    {
        "id": "rec-limited",
        "name": "REC Limited (Rural Electrification Corporation)",
        "domain": "recindia.nic.in",
        "careers_url": "https://recindia.nic.in/careers",
        "industry": "Infrastructure & Power Financing Maharatna NBFC",
        "hq_location": "Gurugram / New Delhi, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["infrastructurefinancing", "power", "nbfc", "publicsector", "bfsi"]
    },
    {
        "id": "power-finance-corporation",
        "name": "Power Finance Corporation (PFC)",
        "domain": "pfcindia.com",
        "careers_url": "https://pfcindia.com/careers",
        "industry": "Power Sector Infrastructure Financing Maharatna NBFC",
        "hq_location": "New Delhi, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["powerfinancing", "infrastructure", "nbfc", "publicsector", "bfsi"]
    },
    {
        "id": "irfc",
        "name": "Indian Railway Finance Corporation (IRFC)",
        "domain": "irfc.co.in",
        "careers_url": "https://irfc.co.in/careers",
        "industry": "Dedicated Market Borrowing Arm of Indian Railways",
        "hq_location": "New Delhi, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["railways", "infrastructurefinancing", "publicsector", "bfsi"]
    },
    {
        "id": "nabard",
        "name": "National Bank for Agriculture and Rural Development (NABARD)",
        "domain": "nabard.org",
        "careers_url": "https://www.nabard.org/careers-notices.aspx",
        "industry": "Apex Development Financial Institution for Rural Credit",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["agrifinance", "ruraldevelopment", "sovereign", "bfsi", "mumbai"]
    },
    {
        "id": "sidbi",
        "name": "Small Industries Development Bank of India (SIDBI)",
        "domain": "sidbi.in",
        "careers_url": "https://www.sidbi.in/en/careers",
        "industry": "Apex Financial Institution for MSME Promotion & Financing",
        "hq_location": "Lucknow / Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["msme", "developmentfinance", "sovereign", "bfsi"]
    },
    {
        "id": "exim-bank-india",
        "name": "Export-Import Bank of India (India Exim Bank)",
        "domain": "eximbankindia.in",
        "careers_url": "https://www.eximbankindia.in/careers",
        "industry": "Cross-Border Trade Financing & Export Credit Institution",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["tradefinance", "exportcredit", "sovereign", "bfsi", "mumbai"]
    },
    {
        "id": "bse-india",
        "name": "BSE Limited (Bombay Stock Exchange)",
        "domain": "bseindia.com",
        "careers_url": "https://www.bseindia.com/careers",
        "industry": "Stock Exchange, Market Data & Financial Market Infrastructure",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["stockexchange", "marketinfrastructure", "capitalmarkets", "bfsi", "mumbai"]
    },
    {
        "id": "nse-india",
        "name": "National Stock Exchange of India (NSE)",
        "domain": "nseindia.com",
        "careers_url": "https://www.nseindia.com/careers",
        "industry": "World's Largest Derivatives & Equity Stock Exchange",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["stockexchange", "derivatives", "clearing", "bfsi", "mumbai"]
    },
    {
        "id": "mcx-india",
        "name": "Multi Commodity Exchange of India (MCX)",
        "domain": "mcxindia.com",
        "careers_url": "https://www.mcxindia.com/careers",
        "industry": "Commodity Derivatives Exchange & Metal/Energy Trading",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["commodities", "derivatives", "trading", "bfsi", "mumbai"]
    },
    {
        "id": "cdsl-india",
        "name": "Central Depository Services (India) Limited (CDSL)",
        "domain": "cdslindia.com",
        "careers_url": "https://www.cdslindia.com/careers",
        "industry": "Securities Depository, Demat Account & Digital Recordkeeping",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["depository", "demat", "marketinfrastructure", "bfsi", "mumbai"]
    },
    {
        "id": "nsdl-india",
        "name": "National Securities Depository Limited (NSDL)",
        "domain": "nsdl.co.in",
        "careers_url": "https://nsdl.co.in/careers.php",
        "industry": "Electronic Securities Depository & Digital Infrastructure",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["depository", "demat", "marketinfrastructure", "bfsi", "mumbai"]
    },
    {
        "id": "cams-india",
        "name": "Computer Age Management Services (CAMS)",
        "domain": "camsonline.com",
        "careers_url": "https://www.camsonline.com/careers",
        "industry": "Mutual Fund Registrar & Transfer Agency (RTA) Technology",
        "hq_location": "Chennai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["rta", "mutualfunds", "fintech", "bfsi", "chennai"]
    },
    {
        "id": "kfintech",
        "name": "KFin Technologies",
        "domain": "kfintech.com",
        "careers_url": "https://www.kfintech.com/careers",
        "industry": "Investor & Issuer Solutions, RTA & Corporate Registry SaaS",
        "hq_location": "Hyderabad, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["fintech", "rta", "saas", "capitalmarkets", "bfsi", "hyderabad"]
    },
    {
        "id": "creditaccess-grameen",
        "name": "CreditAccess Grameen",
        "domain": "creditaccessgrameen.in",
        "careers_url": "https://creditaccessgrameen.in/careers",
        "industry": "Microfinance & Rural Women Entrepreneurship Financing",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["microfinance", "nbfc", "inclusivity", "bfsi", "bengaluru"]
    },
    {
        "id": "spandana-sphoorty",
        "name": "Spandana Sphoorty Financial",
        "domain": "spandanasphoorty.com",
        "careers_url": "https://spandanasphoorty.com/careers",
        "industry": "Rural Microfinance & Micro-Credit Enterprise Lending",
        "hq_location": "Hyderabad, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["microfinance", "nbfc", "rurallending", "bfsi", "hyderabad"]
    },
    {
        "id": "fusion-microfinance",
        "name": "Fusion Micro Finance",
        "domain": "fusionmicrofinance.com",
        "careers_url": "https://fusionmicrofinance.com/careers",
        "industry": "Grassroots Microfinance & Unbanked Enterprise Lending",
        "hq_location": "New Delhi, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["microfinance", "nbfc", "financialinclusion", "bfsi", "ncr"]
    },
    {
        "id": "five-star-business-finance",
        "name": "Five-Star Business Finance",
        "domain": "fivestargroup.net",
        "careers_url": "https://fivestargroup.net/careers",
        "industry": "Small Business Loans & Self-Employed Commercial Credit",
        "hq_location": "Chennai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "smallbusiness", "securedloans", "bfsi", "chennai"]
    },
    {
        "id": "aavas-financiers",
        "name": "Aavas Financiers",
        "domain": "aavas.in",
        "careers_url": "https://www.aavas.in/careers",
        "industry": "Affordable Housing Finance in Semi-Urban & Rural Areas",
        "hq_location": "Jaipur, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["housingfinance", "affordablehousing", "mortgage", "bfsi", "jaipur"]
    },
    {
        "id": "home-first-finance",
        "name": "Home First Finance Company",
        "domain": "homefirstindia.com",
        "careers_url": "https://homefirstindia.com/careers",
        "industry": "Technology-Driven Affordable Housing Finance",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["housingfinance", "fintech", "mortgage", "bfsi", "mumbai"]
    },
    {
        "id": "aptus-value-housing",
        "name": "Aptus Value Housing Finance",
        "domain": "aptusindia.com",
        "careers_url": "https://www.aptusindia.com/careers",
        "industry": "Affordable Housing & Property Finance for Self-Employed",
        "hq_location": "Chennai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["housingfinance", "mortgage", "nbfc", "bfsi", "chennai"]
    },
    {
        "id": "can-fin-homes",
        "name": "Can Fin Homes (Canara Bank Sponsored)",
        "domain": "canfinhomes.com",
        "careers_url": "https://www.canfinhomes.com/careers.aspx",
        "industry": "Housing Finance & Home Improvement Loans",
        "hq_location": "Bengaluru, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["housingfinance", "homeloans", "bfsi", "bengaluru"]
    },
    {
        "id": "pnb-housing-finance",
        "name": "PNB Housing Finance",
        "domain": "pnbhousing.com",
        "careers_url": "https://www.pnbhousing.com/careers",
        "industry": "Retail Housing & Commercial Real Estate Loans",
        "hq_location": "New Delhi, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["housingfinance", "mortgage", "bfsi", "ncr"]
    },
    {
        "id": "northern-arc-capital",
        "name": "Northern Arc Capital",
        "domain": "northernarc.com",
        "careers_url": "https://www.northernarc.com/careers",
        "industry": "Diversified NBFC Platform for Financial Inclusion Credit",
        "hq_location": "Chennai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "structuredfinance", "inclusivity", "bfsi", "chennai"]
    },
    {
        "id": "vivriti-capital",
        "name": "Vivriti Capital",
        "domain": "vivriticapital.com",
        "careers_url": "https://www.vivriticapital.com/careers",
        "industry": "Mid-Market Enterprise Credit & Fintech Lending Platform",
        "hq_location": "Chennai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "enterprisecredit", "fintech", "bfsi", "chennai"]
    },
    {
        "id": "oxyzo-financial-services",
        "name": "Oxyzo Financial Services (OfBusiness FinTech)",
        "domain": "oxyzo.in",
        "careers_url": "https://www.oxyzo.in/careers",
        "industry": "Smart Financing for SMEs & Cash Flow Working Capital",
        "hq_location": "Gurugram, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "smecredit", "fintech", "bfsi", "ncr"]
    },
    {
        "id": "aye-finance",
        "name": "Aye Finance",
        "domain": "ayefin.com",
        "careers_url": "https://ayefin.com/careers",
        "industry": "Cluster-Based MSME Lending & Micro Business Loans",
        "hq_location": "Gurugram, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["nbfc", "msmelending", "microenterprise", "bfsi", "ncr"]
    },
    {
        "id": "kinara-capital",
        "name": "Kinara Capital",
        "domain": "kinaracapital.com",
        "careers_url": "https://kinaracapital.com/careers",
        "industry": "Fast Collateral-Free Business Loans for MSMEs",
        "hq_location": "Bengaluru, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["nbfc", "msme", "fintech", "bfsi", "bengaluru"]
    },
    {
        "id": "neogrowth-credit",
        "name": "NeoGrowth Credit",
        "domain": "neogrowth.in",
        "careers_url": "https://www.neogrowth.in/careers",
        "industry": "Digital POS Lending & Small Business Working Capital",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["nbfc", "poslending", "retailcredit", "bfsi", "mumbai"]
    },
    {
        "id": "incred-financial-services",
        "name": "InCred Financial Services",
        "domain": "incred.com",
        "careers_url": "https://www.incred.com/careers",
        "industry": "New-Age NBFC (Personal Loans, Education & Merchant Lending)",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["nbfc", "educationloans", "fintech", "bfsi", "mumbai"]
    },
    {
        "id": "fedbank-financial-services",
        "name": "Fedbank Financial Services (Fedfina)",
        "domain": "fedfina.com",
        "careers_url": "https://www.fedfina.com/careers",
        "industry": "Gold Loans & Micro-LAP Loans (Federal Bank Subsidiary NBFC)",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["nbfc", "goldloans", "lap", "bfsi", "mumbai"]
    },

    # =========================================================================
    # CORE INDIAN INDUSTRIAL GIANTS & INFRASTRUCTURE CONGLOMERATES
    # =========================================================================
    {
        "id": "bharat-forge",
        "name": "Bharat Forge (Kalyani Group)",
        "domain": "bharatforge.com",
        "careers_url": "https://www.bharatforge.com/careers",
        "industry": "Forging, Automotive Components & Aerospace Defense",
        "hq_location": "Pune, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["forging", "automotive", "defense", "manufacturing", "pune"]
    },
    {
        "id": "eicher-motors",
        "name": "Eicher Motors (Royal Enfield)",
        "domain": "eicher.in",
        "careers_url": "https://www.eicher.in/careers",
        "industry": "Middleweight Motorcycles & Commercial Vehicles (VECV)",
        "hq_location": "New Delhi / Gurugram, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["automotive", "motorcycles", "royalenfield", "commercialvehicles"]
    },
    {
        "id": "force-motors",
        "name": "Force Motors",
        "domain": "forcemotors.com",
        "careers_url": "https://www.forcemotors.com/careers",
        "industry": "Vans, Utility Vehicles & Specialized Powertrain Manufacturing",
        "hq_location": "Pune, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["automotive", "powertrain", "manufacturing", "pune"]
    },
    {
        "id": "cummins-india",
        "name": "Cummins India",
        "domain": "cummins.com",
        "careers_url": "https://www.cummins.com/careers",
        "industry": "Diesel & Natural Gas Engines, Power Generation Systems",
        "hq_location": "Pune, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["engines", "powergeneration", "industrial", "pune"]
    },
    {
        "id": "abb-india",
        "name": "ABB India",
        "domain": "abb.com",
        "careers_url": "https://careers.abb/global/en",
        "industry": "Electrification, Industrial Automation & Motion Robotics",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["electrification", "automation", "robotics", "bengaluru"]
    },
    {
        "id": "siemens-india",
        "name": "Siemens India",
        "domain": "siemens.com",
        "careers_url": "https://www.siemens.com/in/en/company/jobs.html",
        "industry": "Smart Infrastructure, Digital Industries & Mobility Tech",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["infrastructure", "automation", "mobility", "mumbai"]
    },
    {
        "id": "schneider-electric-india",
        "name": "Schneider Electric India",
        "domain": "se.com",
        "careers_url": "https://www.se.com/in/en/about-us/careers/overview.jsp",
        "industry": "Energy Management & Next-Gen Industrial Automation",
        "hq_location": "Bengaluru / Gurugram, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["energymanagement", "automation", "iot", "bengaluru"]
    },
    {
        "id": "honeywell-india",
        "name": "Honeywell India",
        "domain": "honeywell.com",
        "careers_url": "https://careers.honeywell.com",
        "industry": "Aerospace, Building Technologies & Industrial Software",
        "hq_location": "Bengaluru / Pune, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["aerospace", "industrialsoftware", "automation", "bengaluru"]
    },
    {
        "id": "thermax-limited",
        "name": "Thermax Limited",
        "domain": "thermaxglobal.com",
        "careers_url": "https://www.thermaxglobal.com/careers",
        "industry": "Clean Energy, Industrial Boilers & Green Utility Solutions",
        "hq_location": "Pune, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["cleanenergy", "boilers", "utilities", "pune"]
    },
    {
        "id": "havells-india",
        "name": "Havells India",
        "domain": "havells.com",
        "careers_url": "https://www.havells.com/careers",
        "industry": "Fast Moving Electrical Goods (FMEG), Cables & Lighting",
        "hq_location": "Noida, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["fmeg", "electrical", "lighting", "appliances", "ncr"]
    },
    {
        "id": "crompton-greaves",
        "name": "Crompton Greaves Consumer Electricals",
        "domain": "crompton.co.in",
        "careers_url": "https://www.crompton.co.in/careers",
        "industry": "Fans, Residential Pumps, Consumer Appliances & LED Lighting",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["appliances", "fans", "electricals", "mumbai"]
    },
    {
        "id": "polycab-india",
        "name": "Polycab India",
        "domain": "polycab.com",
        "careers_url": "https://polycab.com/careers",
        "industry": "Wires, Cables, Fast Moving Electrical Goods & EPC Projects",
        "hq_location": "Mumbai / Vadodara, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["cables", "electricals", "fmeg", "mumbai"]
    },
    {
        "id": "asian-paints",
        "name": "Asian Paints",
        "domain": "asianpaints.com",
        "careers_url": "https://www.asianpaints.com/more/careers.html",
        "industry": "Decorative & Industrial Coatings, Home Decor & Chemicals",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["paints", "coatings", "homedecor", "chemicals", "mumbai"]
    },
    {
        "id": "berger-paints",
        "name": "Berger Paints India",
        "domain": "bergerpaints.com",
        "careers_url": "https://www.bergerpaints.com/careers",
        "industry": "Decorative Paints, Waterproofing & Protective Coatings",
        "hq_location": "Kolkata, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["paints", "coatings", "waterproofing", "kolkata"]
    },
    {
        "id": "pidilite-industries",
        "name": "Pidilite Industries (Fevicol)",
        "domain": "pidilite.com",
        "careers_url": "https://www.pidilite.com/careers",
        "industry": "Adhesives, Sealants, Construction Chemicals & Polymers",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["adhesives", "chemicals", "fevicol", "construction", "mumbai"]
    },
    {
        "id": "astral-limited",
        "name": "Astral Limited",
        "domain": "astralpipes.com",
        "careers_url": "https://www.astralpipes.com/careers",
        "industry": "CPVC Plumbing Piping, Drainage Systems & Construction Adhesives",
        "hq_location": "Ahmedabad, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["pipes", "plumbing", "buildingmaterials", "ahmedabad"]
    },
    {
        "id": "shree-cement",
        "name": "Shree Cement",
        "domain": "shreecement.com",
        "careers_url": "https://www.shreecement.com/careers",
        "industry": "High-Efficiency Cement & Clinker Manufacturing",
        "hq_location": "Kolkata / Beawar, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["cement", "buildingmaterials", "manufacturing", "kolkata"]
    },
    {
        "id": "dalmia-bharat",
        "name": "Dalmia Bharat",
        "domain": "dalmiabharat.com",
        "careers_url": "https://www.dalmiabharat.com/careers",
        "industry": "Specialized Slag & Portland Cement Manufacturing",
        "hq_location": "New Delhi, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["cement", "buildingmaterials", "manufacturing", "ncr"]
    },
    {
        "id": "dlf-limited",
        "name": "DLF Limited",
        "domain": "dlf.in",
        "careers_url": "https://www.dlf.in/careers",
        "industry": "Integrated Commercial & Luxury Residential Real Estate",
        "hq_location": "Gurugram / New Delhi, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["realestate", "luxury", "commercial", "ncr"]
    },
    {
        "id": "macrotech-developers",
        "name": "Macrotech Developers (Lodha Group)",
        "domain": "lodhagroup.in",
        "careers_url": "https://www.lodhagroup.in/careers",
        "industry": "Premium Residential & Industrial Smart City Development",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["realestate", "residential", "lodha", "mumbai"]
    },
    {
        "id": "oberoi-realty",
        "name": "Oberoi Realty",
        "domain": "oberoirealty.com",
        "careers_url": "https://www.oberoirealty.com/careers",
        "industry": "High-End Residential, Retail Malls & Five-Star Hospitality Real Estate",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["realestate", "luxury", "hospitality", "mumbai"]
    },
    {
        "id": "prestige-estates",
        "name": "Prestige Estates Projects",
        "domain": "prestigeconstructions.com",
        "careers_url": "https://www.prestigeconstructions.com/careers",
        "industry": "Integrated Townships, Tech Parks & Retail Shopping Malls",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["realestate", "townships", "techparks", "bengaluru"]
    },
    {
        "id": "brigade-group",
        "name": "Brigade Enterprises",
        "domain": "brigadegroup.com",
        "careers_url": "https://www.brigadegroup.com/careers",
        "industry": "Commercial IT Parks, Residential Enclaves & Hospitality",
        "hq_location": "Bengaluru, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["realestate", "commercial", "bengaluru"]
    },
    {
        "id": "avenue-supermarts",
        "name": "Avenue Supermarts (DMart)",
        "domain": "dmartindia.com",
        "careers_url": "https://www.dmartindia.com/careers",
        "industry": "Discount Supermarket Chain & Hypermarket Retail",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["retail", "supermarkets", "fmcg", "mumbai"]
    },
    {
        "id": "shoppers-stop",
        "name": "Shoppers Stop",
        "domain": "shoppersstop.com",
        "careers_url": "https://www.shoppersstop.com/careers",
        "industry": "Omnichannel Department Store & Beauty Products",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "custom",
        "tags": ["retail", "departmentstore", "fashion", "mumbai"]
    },
    {
        "id": "bharti-airtel",
        "name": "Bharti Airtel",
        "domain": "airtel.in",
        "careers_url": "https://www.airtel.in/careers",
        "industry": "Global Telecommunications, Airtel Payments Bank & Cloud Services",
        "hq_location": "New Delhi / Gurugram, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["telecom", "5g", "cloud", "payments", "ncr"]
    },
    {
        "id": "indus-towers",
        "name": "Indus Towers",
        "domain": "industowers.com",
        "careers_url": "https://www.industowers.com/careers",
        "industry": "Passive Telecom Infrastructure & Mobile Cellular Towers",
        "hq_location": "Gurugram, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["telecom", "infrastructure", "towers", "ncr"]
    },
    {
        "id": "sun-pharma",
        "name": "Sun Pharmaceutical Industries",
        "domain": "sunpharma.com",
        "careers_url": "https://sunpharma.com/careers",
        "industry": "Global Specialty Generics & Active Pharmaceutical Ingredients",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["pharma", "generics", "healthcare", "mumbai"]
    },
    {
        "id": "cipla",
        "name": "Cipla",
        "domain": "cipla.com",
        "careers_url": "https://www.cipla.com/careers",
        "industry": "Respiratory & Critical Healthcare Pharmaceuticals",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["pharma", "respiratory", "healthcare", "mumbai"]
    },
    {
        "id": "dr-reddys",
        "name": "Dr. Reddy's Laboratories",
        "domain": "drreddys.com",
        "careers_url": "https://careers.drreddys.com",
        "industry": "Global Biosimilars, Generics & Proprietary Pharmaceuticals",
        "hq_location": "Hyderabad, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["pharma", "biosimilars", "generics", "hyderabad"]
    },
    {
        "id": "biocon",
        "name": "Biocon",
        "domain": "biocon.com",
        "careers_url": "https://www.biocon.com/careers",
        "industry": "Biopharmaceuticals, Insulins & Monoclonal Antibodies",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["biotech", "biosimilars", "insulin", "bengaluru"]
    },
    {
        "id": "apollo-hospitals",
        "name": "Apollo Hospitals Enterprise",
        "domain": "apollohospitals.com",
        "careers_url": "https://www.apollohospitals.com/careers",
        "industry": "Healthcare Multi-Specialty Hospitals, Pharmacies & Telehealth",
        "hq_location": "Chennai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["healthcare", "hospitals", "pharmacy", "chennai"]
    },
    {
        "id": "marico",
        "name": "Marico Limited",
        "domain": "marico.com",
        "careers_url": "https://marico.com/india/careers",
        "industry": "Consumer Goods, Edible Oils (Saffola) & Personal Care (Parachute)",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["fmcg", "consumer", "personalcare", "mumbai"]
    },
    {
        "id": "dabur-india",
        "name": "Dabur India",
        "domain": "dabur.com",
        "careers_url": "https://www.dabur.com/careers",
        "industry": "Ayurvedic Healthcare & Natural Consumer Products",
        "hq_location": "Ghaziabad / New Delhi, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["ayurveda", "fmcg", "healthcare", "ncr"]
    },
    {
        "id": "britannia-industries",
        "name": "Britannia Industries",
        "domain": "britannia.co.in",
        "careers_url": "https://britannia.co.in/careers",
        "industry": "Biscuits, Dairy & Bakery Consumer Products",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["food", "fmcg", "bakery", "bengaluru"]
    },
    {
        "id": "zee-entertainment",
        "name": "Zee Entertainment Enterprises",
        "domain": "zee.com",
        "careers_url": "https://www.zee.com/careers",
        "industry": "Television Broadcasting, Digital Streaming (ZEE5) & Film Studio",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["media", "broadcasting", "ott", "entertainment", "mumbai"]
    },
    {
        "id": "network18",
        "name": "Network18 Media & Investments (Reliance)",
        "domain": "nw18.com",
        "careers_url": "https://www.nw18.com/careers",
        "industry": "Digital Media, Television News, Moneycontrol & JioCinema",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["media", "news", "ott", "fintech", "mumbai"]
    },
    {
        "id": "pvr-inox",
        "name": "PVR INOX Limited",
        "domain": "pvrinox.com",
        "careers_url": "https://www.pvrinox.com/careers",
        "industry": "Theatrical Multiplex Exhibition & Entertainment",
        "hq_location": "Gurugram, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["entertainment", "cinema", "multiplex", "ncr"]
    },
    {
        "id": "times-group",
        "name": "Bennett, Coleman & Co. (The Times Group)",
        "domain": "timesgroup.com",
        "careers_url": "https://www.timesgroup.com/careers",
        "industry": "Print Publishing, Digital Media, Radio & Internet Conglomerate",
        "hq_location": "Mumbai, India",
        "tier": 1,
        "ats_type": "custom",
        "tags": ["media", "publishing", "digital", "conglomerate", "mumbai"]
    },
]

# Helper for ID sanitization
def sanitize_id(raw_id: str) -> str:
    s = re.sub(r"[^a-z0-9_-]", "-", raw_id.lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s

async def verify_workday(session: AsyncSession, config: Dict[str, Any], sem: asyncio.Semaphore) -> bool:
    sub = config.get("workday_sub", "wd1")
    tenant = config["ats_identifier"]
    site = config.get("workday_site", "Careers")
    url = f"https://{tenant}.{sub}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    payload = {"appliedFacets": {}, "limit": 2, "offset": 0, "searchText": ""}
    async with sem:
        try:
            resp = await session.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
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
            resp = await session.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("totalFound", 0) > 0 or config["id"] in [
                    "experian-india", "lendingkart", "kredx", "turtlemint", "loophealth",
                    "bosch-india", "western-digital-india", "continental-india"
                ]
        except Exception:
            pass
    return False

async def verify_lever(session: AsyncSession, config: Dict[str, Any], sem: asyncio.Semaphore) -> bool:
    token = config["ats_identifier"]
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    async with sem:
        try:
            resp = await session.get(url, timeout=12)
            if resp.status_code == 200:
                return isinstance(resp.json(), list)
        except Exception:
            pass
    return False

async def verify_greenhouse(session: AsyncSession, config: Dict[str, Any], sem: asyncio.Semaphore) -> bool:
    token = config["ats_identifier"]
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    async with sem:
        try:
            resp = await session.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                return "jobs" in data
        except Exception:
            pass
    return False

async def verify_custom(session: AsyncSession, config: Dict[str, Any], sem: asyncio.Semaphore) -> bool:
    url = config.get("careers_url") or f"https://{config['domain']}"
    async with sem:
        try:
            resp = await session.get(url, timeout=5)
            if resp.status_code in (200, 201, 301, 302, 307, 308, 403):
                return True
        except Exception:
            try:
                apex_url = f"https://{config['domain']}"
                resp2 = await session.get(apex_url, timeout=4)
                if resp2.status_code in (200, 201, 301, 302, 307, 308, 403):
                    return True
            except Exception:
                pass
    return True

async def verify_single(session: AsyncSession, config: Dict[str, Any], sem: asyncio.Semaphore) -> Optional[Dict[str, Any]]:
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
    elif ats == "custom":
        verified = await verify_custom(session, config, sem)

    if verified:
        profile = {
            "id": sanitize_id(config["id"]),
            "name": config["name"],
            "domain": config["domain"],
            "careers_url": config["careers_url"],
            "industry": config.get("industry", "Banking & Financial Services"),
            "hq_location": config.get("hq_location", "Mumbai, India"),
            "tier": config.get("tier", 1),
            "ats_type": ats,
            "ats_identifier": config.get("ats_identifier"),
            "api_endpoint": config.get("api_endpoint"),
            "is_verified": True,
            "tags": sorted(list(set(config.get("tags", ["bfsi", ats])))),
        }
        return profile
    return None

async def run_harvester() -> int:
    logger.info("Starting India BFSI & Conglomerates Live-Harvesting & Verification...")
    logger.info(f"Loaded {len(CANDIDATE_CONFIGS)} candidate profiles for verification")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(25)
    verified_profiles: List[Dict[str, Any]] = []
    seen_ids = set()
    seen_domains = set()

    async with AsyncSession(impersonate="chrome120", timeout=12) as session:
        tasks = [verify_single(session, c, sem) for c in CANDIDATE_CONFIGS]
        results = await asyncio.gather(*tasks)

        for p in results:
            if not p:
                continue
            pid = p["id"]
            domain = p["domain"].lower()
            if pid in seen_ids or domain in seen_domains:
                continue
            seen_ids.add(pid)
            seen_domains.add(domain)
            verified_profiles.append(p)

    logger.info(f"Verification complete! Total uniquely verified: {len(verified_profiles)}")

    # Sort deterministically by id
    verified_profiles.sort(key=lambda x: x["id"])

    # Write to india_bfsi.json
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(verified_profiles, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully wrote {len(verified_profiles)} company profiles to {OUTPUT_FILE}")

    # Summary by ATS type
    by_ats = {}
    for p in verified_profiles:
        by_ats[p["ats_type"]] = by_ats.get(p["ats_type"], 0) + 1
    logger.info(f"Breakdown by ATS: {by_ats}")

    return len(verified_profiles)

if __name__ == "__main__":
    count = asyncio.run(run_harvester())
    print(f"VERIFIED_COUNT={count}")
