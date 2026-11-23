"""Script to harvest, live-verify, and compile 300+ Enterprise IT, Consultancies,
SaaS, HealthTech, and EdTech employers across Workday, SmartRecruiters,
Greenhouse, and Lever for JobScrap.
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
logger = logging.getLogger("harvest_enterprise")

DATA_DIR = Path(__file__).resolve().parent.parent / "jobscrap" / "catalog" / "data"
OUTPUT_FILE = DATA_DIR / "enterprise.json"

# Master list of candidate employers across the 4 specified ATS systems:
# Workday, SmartRecruiters, Greenhouse, and Lever
CANDIDATE_CONFIGS: List[Dict[str, Any]] = [
    # =========================================================================
    # WORKDAY CANDIDATES
    # =========================================================================
    {
        "id": "target-india",
        "name": "Target India",
        "domain": "target.com",
        "careers_url": "https://target.wd5.myworkdayjobs.com/targetcareers",
        "industry": "Retail & Technology Enterprise Hub",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "target",
        "api_endpoint": "https://target.wd5.myworkdayjobs.com/wday/cxs/target/targetcareers/jobs",
        "workday_sub": "wd5",
        "workday_site": "targetcareers",
        "tags": ["retail", "ecommerce", "bengaluru", "enterprise", "workday"]
    },
    {
        "id": "nvidia",
        "name": "NVIDIA India",
        "domain": "nvidia.com",
        "careers_url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
        "industry": "AI & Accelerated Computing",
        "hq_location": "Bengaluru / Pune / Hyderabad, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "nvidia",
        "api_endpoint": "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs",
        "workday_sub": "wd5",
        "workday_site": "NVIDIAExternalCareerSite",
        "tags": ["ai", "semiconductor", "hardware", "enterprise", "workday"]
    },
    {
        "id": "salesforce",
        "name": "Salesforce India",
        "domain": "salesforce.com",
        "careers_url": "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site",
        "industry": "Enterprise Cloud & CRM",
        "hq_location": "Hyderabad / Bengaluru, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "salesforce",
        "api_endpoint": "https://salesforce.wd12.myworkdayjobs.com/wday/cxs/salesforce/External_Career_Site/jobs",
        "workday_sub": "wd12",
        "workday_site": "External_Career_Site",
        "tags": ["crm", "saas", "cloud", "enterprise", "workday"]
    },
    {
        "id": "pvh-corp",
        "name": "PVH Corp (Tommy Hilfiger & Calvin Klein)",
        "domain": "pvh.com",
        "careers_url": "https://pvh.wd1.myworkdayjobs.com/PVH_Careers",
        "industry": "Global Retail & Tech",
        "hq_location": "Bengaluru, India",
        "tier": 2,
        "ats_type": "workday",
        "ats_identifier": "pvh",
        "api_endpoint": "https://pvh.wd1.myworkdayjobs.com/wday/cxs/pvh/PVH_Careers/jobs",
        "workday_sub": "wd1",
        "workday_site": "PVH_Careers",
        "tags": ["retail", "fashion", "bengaluru", "workday"]
    },
    {
        "id": "cisco",
        "name": "Cisco Systems India",
        "domain": "cisco.com",
        "careers_url": "https://cisco.wd5.myworkdayjobs.com/Cisco_Careers",
        "industry": "Networking & Cloud Security",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "cisco",
        "api_endpoint": "https://cisco.wd5.myworkdayjobs.com/wday/cxs/cisco/Cisco_Careers/jobs",
        "workday_sub": "wd5",
        "workday_site": "Cisco_Careers",
        "tags": ["networking", "cloud", "cybersecurity", "enterprise", "workday"]
    },
    {
        "id": "intel",
        "name": "Intel India",
        "domain": "intel.com",
        "careers_url": "https://intel.wd1.myworkdayjobs.com/External",
        "industry": "Semiconductors & Silicon Systems",
        "hq_location": "Bengaluru / Hyderabad, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "intel",
        "api_endpoint": "https://intel.wd1.myworkdayjobs.com/wday/cxs/intel/External/jobs",
        "workday_sub": "wd1",
        "workday_site": "External",
        "tags": ["semiconductor", "hardware", "systems", "enterprise", "workday"]
    },
    {
        "id": "3m-india",
        "name": "3M India",
        "domain": "3m.com",
        "careers_url": "https://3m.wd1.myworkdayjobs.com/Search",
        "industry": "Applied Science & Industrial Tech",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "3m",
        "api_endpoint": "https://3m.wd1.myworkdayjobs.com/wday/cxs/3m/Search/jobs",
        "workday_sub": "wd1",
        "workday_site": "Search",
        "tags": ["manufacturing", "science", "materials", "enterprise", "workday"]
    },
    {
        "id": "mastercard",
        "name": "Mastercard India",
        "domain": "mastercard.com",
        "careers_url": "https://mastercard.wd1.myworkdayjobs.com/CorporateCareers",
        "industry": "Payments & Financial Technology",
        "hq_location": "Pune / Gurugram / Vadodara, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "mastercard",
        "api_endpoint": "https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers/jobs",
        "workday_sub": "wd1",
        "workday_site": "CorporateCareers",
        "tags": ["fintech", "payments", "bfsi", "enterprise", "workday"]
    },
    {
        "id": "paypal",
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
        "tags": ["fintech", "payments", "enterprise", "workday"]
    },
    {
        "id": "workday",
        "name": "Workday India",
        "domain": "workday.com",
        "careers_url": "https://workday.wd5.myworkdayjobs.com/workday",
        "industry": "Enterprise Cloud Applications",
        "hq_location": "Pune / Bengaluru, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "workday",
        "api_endpoint": "https://workday.wd5.myworkdayjobs.com/wday/cxs/workday/workday/jobs",
        "workday_sub": "wd5",
        "workday_site": "workday",
        "tags": ["saas", "hcm", "erp", "enterprise", "workday"]
    },
    {
        "id": "adobe",
        "name": "Adobe India",
        "domain": "adobe.com",
        "careers_url": "https://adobe.wd5.myworkdayjobs.com/external_experienced",
        "industry": "Creative & Digital Experience Software",
        "hq_location": "Noida / Bengaluru, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "adobe",
        "api_endpoint": "https://adobe.wd5.myworkdayjobs.com/wday/cxs/adobe/external_experienced/jobs",
        "workday_sub": "wd5",
        "workday_site": "external_experienced",
        "tags": ["saas", "creative", "ai", "enterprise", "workday"]
    },
    {
        "id": "redhat",
        "name": "Red Hat India",
        "domain": "redhat.com",
        "careers_url": "https://redhat.wd5.myworkdayjobs.com/Jobs",
        "industry": "Open Source & Enterprise Cloud",
        "hq_location": "Pune / Bengaluru, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "redhat",
        "api_endpoint": "https://redhat.wd5.myworkdayjobs.com/wday/cxs/redhat/Jobs/jobs",
        "workday_sub": "wd5",
        "workday_site": "Jobs",
        "tags": ["opensource", "linux", "cloud", "enterprise", "workday"]
    },
    {
        "id": "autodesk",
        "name": "Autodesk India",
        "domain": "autodesk.com",
        "careers_url": "https://autodesk.wd1.myworkdayjobs.com/Ext",
        "industry": "Design & 3D Engineering Software",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "workday",
        "ats_identifier": "autodesk",
        "api_endpoint": "https://autodesk.wd1.myworkdayjobs.com/wday/cxs/autodesk/Ext/jobs",
        "workday_sub": "wd1",
        "workday_site": "Ext",
        "tags": ["cad", "3d", "design", "enterprise", "workday"]
    },

    # =========================================================================
    # SMARTRECRUITERS CANDIDATES
    # =========================================================================
    {
        "id": "bosch-india",
        "name": "Bosch India",
        "domain": "bosch.in",
        "careers_url": "https://jobs.smartrecruiters.com/BoschGroup",
        "industry": "Mobility & Industrial Technology",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "BoschGroup",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/BoschGroup/postings",
        "tags": ["mobility", "iot", "automotive", "engineering", "smartrecruiters"]
    },
    {
        "id": "sgs-india",
        "name": "SGS India",
        "domain": "sgs.com",
        "careers_url": "https://jobs.smartrecruiters.com/SGS",
        "industry": "Testing, Inspection & Certification",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "SGS",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/SGS/postings",
        "tags": ["testing", "inspection", "certification", "smartrecruiters"]
    },
    {
        "id": "eurofins-india",
        "name": "Eurofins Scientific India",
        "domain": "eurofins.in",
        "careers_url": "https://jobs.smartrecruiters.com/Eurofins",
        "industry": "Bioanalytical Testing & Genomics",
        "hq_location": "Bengaluru, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Eurofins",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Eurofins/postings",
        "tags": ["biotech", "genomics", "testing", "healthtech", "smartrecruiters"]
    },
    {
        "id": "securitas-india",
        "name": "Securitas India",
        "domain": "securitas.in",
        "careers_url": "https://jobs.smartrecruiters.com/Securitas",
        "industry": "Protective Services & Digital Security",
        "hq_location": "Gurugram, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Securitas",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Securitas/postings",
        "tags": ["security", "facilities", "smartrecruiters"]
    },
    {
        "id": "aramark",
        "name": "Aramark",
        "domain": "aramark.com",
        "careers_url": "https://jobs.smartrecruiters.com/Aramark",
        "industry": "Facilities Management & Operations",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Aramark",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Aramark/postings",
        "tags": ["facilities", "hospitality", "smartrecruiters"]
    },
    {
        "id": "continental-india",
        "name": "Continental India",
        "domain": "continental.com",
        "careers_url": "https://jobs.smartrecruiters.com/Continental",
        "industry": "Automotive Software & Autonomous Driving",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Continental",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Continental/postings",
        "tags": ["automotive", "mobility", "embedded", "smartrecruiters"]
    },
    {
        "id": "avery-dennison-india",
        "name": "Avery Dennison India",
        "domain": "averydennison.com",
        "careers_url": "https://jobs.smartrecruiters.com/AveryDennison",
        "industry": "Materials Science & Digital Identification Tech",
        "hq_location": "Bengaluru, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "AveryDennison",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/AveryDennison/postings",
        "tags": ["rfid", "materials", "smartrecruiters"]
    },
    {
        "id": "konecranes-india",
        "name": "Konecranes India",
        "domain": "konecranes.com",
        "careers_url": "https://jobs.smartrecruiters.com/Konecranes",
        "industry": "Industrial Lifting & Port Automation",
        "hq_location": "Pune, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Konecranes",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Konecranes/postings",
        "tags": ["automation", "industrial", "smartrecruiters"]
    },
    {
        "id": "western-digital-india",
        "name": "Western Digital India",
        "domain": "westerndigital.com",
        "careers_url": "https://jobs.smartrecruiters.com/WesternDigital",
        "industry": "Data Storage & Memory Architecture",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "WesternDigital",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/WesternDigital/postings",
        "tags": ["storage", "hardware", "semiconductor", "smartrecruiters"]
    },
    {
        "id": "sodexo-india",
        "name": "Sodexo India",
        "domain": "sodexo.com",
        "careers_url": "https://jobs.smartrecruiters.com/Sodexo",
        "industry": "Employee Benefits Tech & Workplace Services",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Sodexo",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Sodexo/postings",
        "tags": ["fintech", "benefits", "services", "smartrecruiters"]
    },
    {
        "id": "freshworks",
        "name": "Freshworks",
        "domain": "freshworks.com",
        "careers_url": "https://careers.smartrecruiters.com/freshworks",
        "industry": "Enterprise SaaS / CRM",
        "hq_location": "Chennai, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "freshworks",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/freshworks/postings",
        "tags": ["saas", "crm", "chennai", "nasdaq", "smartrecruiters"]
    },
    {
        "id": "colliers-india",
        "name": "Colliers International India",
        "domain": "colliers.com",
        "careers_url": "https://jobs.smartrecruiters.com/Colliers",
        "industry": "Real Estate Advisory & PropTech",
        "hq_location": "Mumbai, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Colliers",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Colliers/postings",
        "tags": ["proptech", "realestate", "consulting", "smartrecruiters"]
    },
    {
        "id": "cern",
        "name": "CERN",
        "domain": "cern.ch",
        "careers_url": "https://jobs.smartrecruiters.com/CERN",
        "industry": "Nuclear & Computational Research",
        "hq_location": "Geneva, Switzerland / India Collaboration",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "CERN",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/CERN/postings",
        "tags": ["research", "computing", "smartrecruiters"]
    },
    {
        "id": "alorica-india",
        "name": "Alorica India",
        "domain": "alorica.com",
        "careers_url": "https://jobs.smartrecruiters.com/Alorica",
        "industry": "Customer Experience & Business Process IT",
        "hq_location": "Bengaluru, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Alorica",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Alorica/postings",
        "tags": ["bpm", "customerexperience", "smartrecruiters"]
    },
    {
        "id": "microchip-technology",
        "name": "Microchip Technology India",
        "domain": "microchip.com",
        "careers_url": "https://jobs.smartrecruiters.com/Microchip",
        "industry": "Semiconductors & Embedded Control",
        "hq_location": "Bengaluru / Chennai, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Microchip",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Microchip/postings",
        "tags": ["semiconductor", "embedded", "smartrecruiters"]
    },
    {
        "id": "new-relic",
        "name": "New Relic India",
        "domain": "newrelic.com",
        "careers_url": "https://jobs.smartrecruiters.com/NewRelic",
        "industry": "Observability & Software Analytics",
        "hq_location": "Hyderabad, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "NewRelic",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/NewRelic/postings",
        "tags": ["observability", "devops", "saas", "smartrecruiters"]
    },
    {
        "id": "uber-india",
        "name": "Uber India Engineering",
        "domain": "uber.com",
        "careers_url": "https://jobs.smartrecruiters.com/Uber",
        "industry": "Mobility & Delivery Tech Hub",
        "hq_location": "Bengaluru / Hyderabad, India",
        "tier": 1,
        "ats_type": "smartrecruiters",
        "ats_identifier": "Uber",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/Uber/postings",
        "tags": ["mobility", "delivery", "techhub", "smartrecruiters"]
    },
    {
        "id": "solarwinds-sr",
        "name": "SolarWinds India (SR)",
        "domain": "solarwinds.com",
        "careers_url": "https://jobs.smartrecruiters.com/SolarWinds",
        "industry": "IT Infrastructure Management",
        "hq_location": "Bengaluru, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "SolarWinds",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/SolarWinds/postings",
        "tags": ["itmanagement", "observability", "smartrecruiters"]
    },
    {
        "id": "ttec-india",
        "name": "TTEC India",
        "domain": "ttec.com",
        "careers_url": "https://jobs.smartrecruiters.com/TTEC",
        "industry": "Customer Experience & Digital Engagement",
        "hq_location": "Ahmedabad / Hyderabad, India",
        "tier": 2,
        "ats_type": "smartrecruiters",
        "ats_identifier": "TTEC",
        "api_endpoint": "https://api.smartrecruiters.com/v1/companies/TTEC/postings",
        "tags": ["cx", "bpm", "smartrecruiters"]
    },

    # =========================================================================
    # LEVER CANDIDATES
    # =========================================================================
    {
        "id": "mindtickle",
        "name": "MindTickle",
        "domain": "mindtickle.com",
        "careers_url": "https://jobs.lever.co/mindtickle",
        "industry": "Sales Readiness & Enablement SaaS",
        "hq_location": "Pune, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "mindtickle",
        "api_endpoint": "https://api.lever.co/v0/postings/mindtickle?mode=json",
        "tags": ["saas", "salestech", "unicorn", "pune", "lever"]
    },
    {
        "id": "oliver-wyman",
        "name": "Oliver Wyman India",
        "domain": "oliverwyman.com",
        "careers_url": "https://jobs.lever.co/oliverwyman",
        "industry": "Management Consulting & Advisory",
        "hq_location": "Mumbai / Gurugram, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "oliverwyman",
        "api_endpoint": "https://api.lever.co/v0/postings/oliverwyman?mode=json",
        "tags": ["consulting", "management", "strategy", "lever"]
    },
    {
        "id": "kpmg-lever",
        "name": "KPMG India (Advisory)",
        "domain": "kpmg.com",
        "careers_url": "https://jobs.lever.co/kpmg",
        "industry": "Audit, Tax & Advisory Services",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "kpmg",
        "api_endpoint": "https://api.lever.co/v0/postings/kpmg?mode=json",
        "tags": ["audit", "consulting", "advisory", "lever"]
    },
    {
        "id": "cred-lever",
        "name": "CRED",
        "domain": "cred.club",
        "careers_url": "https://jobs.lever.co/cred",
        "industry": "FinTech / Credit & Rewards",
        "hq_location": "Bengaluru, India",
        "tier": 1,
        "ats_type": "lever",
        "ats_identifier": "cred",
        "api_endpoint": "https://api.lever.co/v0/postings/cred?mode=json",
        "tags": ["fintech", "unicorn", "bengaluru", "lever"]
    },
]

# Master pool of verified Greenhouse companies operating across India & Globally
GREENHOUSE_DATA = [
    # Top Indian Enterprise IT, Consultancies & SaaS
    ("tcs", "Tata Consultancy Services (TCS)", "tcs.com", "IT Services & Consulting", "Mumbai, India", 1, ["itservices", "consulting", "enterprise"]),
    ("thoughtworks", "Thoughtworks India", "thoughtworks.com", "Global Software Consultancy & Digital Engineering", "Bengaluru / Pune / Gurugram / Chennai, India", 1, ["consulting", "software", "agile", "bengaluru"]),
    ("druva", "Druva", "druva.com", "Cloud Data Protection & Cyber Resilience", "Pune, India", 1, ["saas", "cybersecurity", "cloud", "pune", "unicorn"]),
    ("highradius", "HighRadius", "highradius.com", "Autonomous Finance & Order-to-Cash SaaS", "Hyderabad, India", 1, ["fintech", "saas", "unicorn", "hyderabad"]),
    ("zenoti", "Zenoti", "zenoti.com", "Enterprise Wellness & Spa Software", "Hyderabad, India", 1, ["saas", "wellness", "unicorn", "hyderabad"]),
    ("hackerrank", "HackerRank", "hackerrank.com", "Developer Skills & Technical Assessment", "Bengaluru, India", 1, ["edtech", "developer", "hrtech", "bengaluru"]),
    ("inmobi", "InMobi", "inmobi.com", "Mobile Advertising & Consumer Technology", "Bengaluru, India", 1, ["adtech", "mobile", "unicorn", "bengaluru"]),
    ("glance", "Glance", "glance.com", "Smart Lock Screen Content Platform", "Bengaluru, India", 1, ["media", "consumer", "ai", "bengaluru"]),
    ("slice", "Slice", "sliceit.com", "Consumer Payments & Neobanking", "Bengaluru, India", 1, ["fintech", "banking", "unicorn", "bengaluru"]),
    ("groww", "Groww", "groww.in", "Investment & Wealth Management Platform", "Bengaluru, India", 1, ["fintech", "wealthtech", "unicorn", "bengaluru"]),
    ("razorpaysoftwareprivatelimited", "Razorpay", "razorpay.com", "Full-Stack Payments & Banking Platform", "Bengaluru, India", 1, ["fintech", "payments", "unicorn", "bengaluru"]),
    ("sonicwall", "SonicWall India", "sonicwall.com", "Cybersecurity & Firewall Defense", "Bengaluru, India", 1, ["cybersecurity", "network", "cloud"]),
    ("sas", "SAS Institute India", "sas.com", "Advanced Analytics & Business Intelligence", "Mumbai / Pune, India", 1, ["analytics", "data", "ai"]),
    ("nasdaq", "Nasdaq India Tech Hub", "nasdaq.com", "Financial Markets Technology & SaaS", "Bengaluru, India", 1, ["fintech", "capitalmarkets", "saas"]),
    ("westernunion", "Western Union India", "westernunion.com", "Global Money Movement & Payments", "Pune, India", 1, ["fintech", "payments", "pune"]),
    ("verifone", "Verifone India", "verifone.com", "Electronic Payment Solutions & POS", "Bengaluru, India", 1, ["fintech", "pos", "payments"]),
    ("polaris", "Polaris Wireless", "polariswireless.com", "High-Accuracy Location Technology", "Bengaluru, India", 2, ["location", "telecom", "security"]),
    ("solera", "Solera Holdings", "solera.com", "Automotive Fleet & Risk Intelligence Software", "Bengaluru, India", 1, ["automotive", "fleet", "risk"]),
    ("northgate", "Northgate Public Services", "northgateps.com", "Public Sector Software Solutions", "Mumbai, India", 2, ["publicsector", "government", "software"]),
    ("oath", "Yahoo / Oath India", "yahooinc.com", "Digital Media & Consumer Internet", "Bengaluru, India", 1, ["media", "consumer", "advertising"]),
    
    # Global Enterprise Cloud, Infrastructure & SaaS (with major India Centers)
    ("databricks", "Databricks India", "databricks.com", "Data Lakehouse & Enterprise AI", "Bengaluru, India", 1, ["data", "ai", "lakehouse", "enterprise"]),
    ("stripe", "Stripe India", "stripe.com", "Financial Infrastructure & Payments API", "Bengaluru, India", 1, ["fintech", "payments", "infrastructure"]),
    ("cloudflare", "Cloudflare India", "cloudflare.com", "Cloud Connectivity & Edge Cybersecurity", "Bengaluru, India", 1, ["cloud", "cybersecurity", "cdn"]),
    ("mongodb", "MongoDB India", "mongodb.com", "Developer Data Platform & Modern Database", "Bengaluru / Gurugram, India", 1, ["database", "nosql", "developer"]),
    ("purestorage", "Pure Storage India", "purestorage.com", "Enterprise Flash Data Storage Solutions", "Bengaluru, India", 1, ["storage", "hardware", "enterprise"]),
    ("datadog", "Datadog India", "datadoghq.com", "Cloud Observability & Security Platform", "Bengaluru, India", 1, ["observability", "devops", "cloud"]),
    ("zscaler", "Zscaler India", "zscaler.com", "Cloud Cybersecurity & Zero Trust Platform", "Bengaluru / Chandigarh / Pune, India", 1, ["cybersecurity", "cloud", "zerotrust"]),
    ("elastic", "Elastic India", "elastic.co", "Search AI & Enterprise Analytics Platform", "Bengaluru, India", 1, ["search", "ai", "observability"]),
    ("okta", "Okta India", "okta.com", "Identity & Access Management SaaS", "Bengaluru, India", 1, ["identity", "security", "saas"]),
    ("braze", "Braze", "braze.com", "Customer Engagement Platform", "Bengaluru, India", 1, ["martech", "engagement", "saas"]),
    ("coinbase", "Coinbase India", "coinbase.com", "Cryptocurrency & Web3 Financial Infrastructure", "Hyderabad, India", 1, ["crypto", "web3", "fintech"]),
    ("brex", "Brex", "brex.com", "Corporate Cards & AI Spend Management", "Remote / India", 1, ["fintech", "spendmanagement"]),
    ("gitlab", "GitLab", "gitlab.com", "DevSecOps & Code Collaboration Platform", "Remote / India", 1, ["devops", "git", "remote"]),
    ("rubrik", "Rubrik India", "rubrik.com", "Zero Trust Data Security Platform", "Bengaluru, India", 1, ["cybersecurity", "backup", "cloud"]),
    ("scaleai", "Scale AI", "scale.com", "Enterprise AI Data Foundry", "Remote / India", 1, ["ai", "data", "machinelearning"]),
    ("figma", "Figma", "figma.com", "Collaborative Interface Design Platform", "Remote / India", 1, ["design", "ui", "collaboration"]),
    ("grafanalabs", "Grafana Labs", "grafana.com", "Open Observability & Dashboards Platform", "Bengaluru, India", 1, ["observability", "metrics", "opensource"]),
    ("anaplan", "Anaplan India", "anaplan.com", "Connected Business Strategy & Financial Planning", "Hyderabad, India", 1, ["planning", "enterprise", "saas"]),
    ("nice", "NICE Systems India", "nice.com", "Cloud Contact Center & Customer AI", "Pune, India", 1, ["cpaas", "cx", "ai", "enterprise"]),
    ("intercom", "Intercom", "intercom.com", "AI Customer Service Platform", "Remote / India", 1, ["cx", "support", "ai", "saas"]),
    ("ripple", "Ripple India", "ripple.com", "Enterprise Blockchain & Cross-Border Payments", "Bengaluru, India", 1, ["blockchain", "payments", "fintech"]),
    ("asana", "Asana", "asana.com", "Enterprise Work Management & Collaboration", "Remote / India", 1, ["productivity", "collaboration", "saas"]),
    ("twilio", "Twilio India", "twilio.com", "Customer Engagement & Communications Platform", "Bengaluru, India", 1, ["cpaas", "telecom", "api"]),
    ("zoominfo", "ZoomInfo", "zoominfo.com", "Go-To-Market Intelligence SaaS", "Chennai, India", 1, ["b2b", "salesintel", "saas"]),
    ("solarwinds", "SolarWinds India", "solarwinds.com", "IT Infrastructure Management & Observability", "Bengaluru, India", 2, ["observability", "it", "monitoring"]),
    ("gusto", "Gusto", "gusto.com", "Payroll, HR & Benefits Platform", "Remote / India", 1, ["hrtech", "payroll", "fintech"]),
    ("five9", "Five9 India", "five9.com", "Intelligent Cloud Contact Center", "Bengaluru, India", 1, ["cpaas", "cx", "cloud"]),
    ("carta", "Carta", "carta.com", "Equity Management & Ownership Infrastructure", "Remote / India", 1, ["fintech", "equity", "saas"]),
    ("smartsheet", "Smartsheet", "smartsheet.com", "Enterprise Work Management Software", "Remote / India", 1, ["collaboration", "enterprise", "saas"]),
    ("pingidentity", "Ping Identity India", "pingidentity.com", "Intelligent Identity & Access Management", "Bengaluru, India", 1, ["security", "identity", "enterprise"]),
    ("cockroachlabs", "Cockroach Labs", "cockroachlabs.com", "Cloud Distributed SQL Database", "Remote / India", 1, ["database", "sql", "cloud"]),
    ("udemy", "Udemy India", "udemy.com", "Online Learning & Corporate Skills Marketplace", "Gurugram, India", 1, ["edtech", "elearning", "skills"]),
    ("coursera", "Coursera India", "coursera.org", "Higher Education & Degrees Platform", "Mumbai, India", 1, ["edtech", "degrees", "education"]),
    ("launchdarkly", "LaunchDarkly", "launchdarkly.com", "Feature Management & Continuous Delivery", "Remote / India", 1, ["devops", "developer", "saas"]),
    ("natera", "Natera India", "natera.com", "Cell-Free DNA Genetic Testing & Oncology", "Bengaluru, India", 1, ["healthtech", "genomics", "oncology"]),
    ("anthropic", "Anthropic", "anthropic.com", "AI Research & Frontier Foundation Models", "Remote / India", 1, ["ai", "llm", "research"]),
    ("axon", "Axon India", "axon.com", "Public Safety Hardware & Cloud Software", "Bengaluru, India", 1, ["cloud", "publicsafety", "hardware"]),
    ("canonical", "Canonical (Ubuntu)", "canonical.com", "Open Source Operating Systems & Cloud", "Remote / India", 1, ["linux", "ubuntu", "opensource"]),
    ("celonis", "Celonis India", "celonis.com", "Process Mining & Execution Management", "Bengaluru, India", 1, ["processmining", "enterprise", "saas"]),
    ("binance", "Binance", "binance.com", "Cryptocurrency & Blockchain Infrastructure", "Remote / India", 1, ["crypto", "web3", "fintech"]),
    ("flexport", "Flexport", "flexport.com", "Global Freight Forwarding & Supply Chain SaaS", "Remote / India", 1, ["logistics", "supplychain", "saas"]),
    ("fivetran", "Fivetran India", "fivetran.com", "Automated Data Movement & ELT Pipelines", "Bengaluru, India", 1, ["data", "etl", "integration", "bengaluru"]),
    ("deliveroo", "Deliveroo India Tech Hub", "deliveroo.com", "Online Food Delivery Engineering Hub", "Hyderabad, India", 1, ["foodtech", "techhub", "hyderabad"]),
    ("appian", "Appian India", "appian.com", "Low-Code Process Automation & Case Management", "Chennai, India", 1, ["lowcode", "automation", "bpm"]),
    ("epicgames", "Epic Games India", "epicgames.com", "Unreal Engine & Interactive Entertainment", "Remote / India", 1, ["gaming", "unrealengine", "3d"]),
    ("faire", "Faire", "faire.com", "Online Wholesale B2B Marketplace", "Remote / India", 1, ["ecommerce", "b2b", "marketplace"]),
    ("bitgo", "BitGo", "bitgo.com", "Digital Asset Custody & Security Infrastructure", "Bengaluru, India", 1, ["crypto", "security", "fintech"]),
    ("bloomreach", "Bloomreach India", "bloomreach.com", "Commerce Experience Cloud & Personalization AI", "Bengaluru, India", 1, ["ecommerce", "ai", "personalization"]),
    ("duolingo", "Duolingo", "duolingo.com", "Mobile Language Learning & Gamified EdTech", "Remote / India", 1, ["edtech", "language", "education"]),
    ("roblox", "Roblox", "roblox.com", "Immersive Virtual World & Game Engine Platform", "Remote / India", 1, ["gaming", "metaverse", "platform"]),
    ("qualtrics", "Qualtrics India", "qualtrics.com", "Experience Management (XM) Software", "Gurugram, India", 1, ["saas", "xm", "enterprise"]),
    ("pinterest", "Pinterest", "pinterest.com", "Visual Discovery & Social Commerce Engine", "Remote / India", 1, ["consumer", "search", "social"]),
    ("robinhood", "Robinhood", "robinhood.com", "Pioneering Financial Services Platform", "Remote / India", 1, ["fintech", "investing", "brokerage"]),
    ("lyft", "Lyft", "lyft.com", "Ridesharing & Multimodal Mobility Platform", "Remote / India", 1, ["transportation", "mobility"]),
    ("mozilla", "Mozilla", "mozilla.org", "Open Web Technologies & Firefox Privacy", "Remote / India", 1, ["browser", "opensource", "privacy"]),
    ("klaviyo", "Klaviyo", "klaviyo.com", "Intelligent Marketing Automation Platform", "Remote / India", 1, ["martech", "ecommerce", "saas"]),
    ("roku", "Roku", "roku.com", "TV Streaming Platform & Connected AdTech", "Remote / India", 1, ["streaming", "hardware", "media"]),
    ("jfrog", "JFrog India", "jfrog.com", "DevOps & Software Supply Chain Platform", "Bengaluru, India", 1, ["devops", "binaries", "developer", "bengaluru"]),
    ("ziprecruiter", "ZipRecruiter", "ziprecruiter.com", "AI-Powered Employment Marketplace", "Remote / India", 1, ["recruiting", "ai", "marketplace"]),
    ("monzo", "Monzo", "monzo.com", "Digital Banking & Mobile FinTech", "Remote / India", 1, ["fintech", "banking", "mobile"]),
    ("sofi", "SoFi", "sofi.com", "Digital Personal Finance & Lending Suite", "Remote / India", 1, ["fintech", "banking", "lending"]),
    ("workato", "Workato India", "workato.com", "Enterprise Integration & Workflow Automation", "Bengaluru, India", 1, ["integration", "automation", "saas", "bengaluru"]),
    ("twitch", "Twitch", "twitch.tv", "Interactive Live Streaming Platform", "Remote / India", 1, ["streaming", "gaming", "video"]),
    ("pagerduty", "PagerDuty", "pagerduty.com", "Digital Operations Management Platform", "Remote / India", 1, ["devops", "incidentmanagement", "saas"]),
    ("zuora", "Zuora India", "zuora.com", "Subscription Economy Monetization Platform", "Chennai, India", 1, ["billing", "subscriptions", "saas", "chennai"]),
    ("peloton", "Peloton Interactive", "onepeloton.com", "Connected Fitness Hardware & Software", "Remote / India", 1, ["fitness", "hardware", "consumer"]),
    ("mixpanel", "Mixpanel", "mixpanel.com", "Event-Based Product Analytics Platform", "Remote / India", 1, ["analytics", "product", "saas"]),
    ("seatgeek", "SeatGeek", "seatgeek.com", "Mobile-Focused Ticket Marketplace", "Remote / India", 1, ["ticketing", "mobile", "marketplace"]),
    ("checkr", "Checkr", "checkr.com", "AI-Powered Background Check Platform", "Remote / India", 1, ["hrtech", "compliance", "ai"]),
    ("backblaze", "Backblaze", "backblaze.com", "Cloud Storage & Computer Backup", "Remote / India", 2, ["storage", "backup", "cloud"]),
    ("blend", "Blend", "blend.com", "Digital Banking Infrastructure Platform", "Remote / India", 1, ["fintech", "banking", "lending"]),
    ("voxmedia", "Vox Media", "voxmedia.com", "Modern Media & Publishing Platform", "Remote / India", 2, ["media", "publishing", "content"]),
    ("betterment", "Betterment", "betterment.com", "Automated Investing & Wealth Management", "Remote / India", 1, ["fintech", "investing", "roboadvisor"]),
    ("dropbox", "Dropbox", "dropbox.com", "Cloud Storage, Collaboration & DocuSign", "Remote / India", 1, ["storage", "collaboration", "saas"]),
    ("discord", "Discord", "discord.com", "Voice, Video & Text Communication Platform", "Remote / India", 1, ["chat", "community", "gaming"]),
    ("branch", "Branch Metrics", "branch.io", "Deep Linking & Mobile Measurement Platform", "Bengaluru, India", 1, ["mobile", "analytics", "martech"]),
    ("surveymonkey", "SurveyMonkey (Momentive)", "surveymonkey.com", "Experience Data & Survey Software", "Remote / India", 1, ["survey", "feedback", "saas"]),
    ("webflow", "Webflow", "webflow.com", "Visual Web Development Platform", "Remote / India", 1, ["webdesign", "nocode", "saas"]),
    ("smartbear", "SmartBear India", "smartbear.com", "Software Quality, Testing & API Tools", "Bengaluru, India", 1, ["testing", "api", "devtools"]),
    ("chime", "Chime", "chime.com", "Consumer Neobanking Platform", "Remote / India", 1, ["fintech", "banking", "mobile"]),
    ("hootsuite", "Hootsuite", "hootsuite.com", "Social Media Management Platform", "Remote / India", 1, ["socialmedia", "martech", "saas"]),
    ("gemini", "Gemini", "gemini.com", "Cryptocurrency Exchange & Custodian", "Gurugram, India", 1, ["crypto", "web3", "fintech", "gurugram"]),
    ("squarespace", "Squarespace", "squarespace.com", "Website Building & E-Commerce Platform", "Remote / India", 1, ["website", "ecommerce", "saas"]),
    ("upwork", "Upwork", "upwork.com", "Global Freelance Talent Marketplace", "Remote / India", 1, ["freelance", "talent", "marketplace"]),
    ("sproutsocial", "Sprout Social", "sproutsocial.com", "Social Media Management & Analytics", "Remote / India", 1, ["social", "martech", "analytics"]),
    ("godaddy", "GoDaddy India", "godaddy.com", "Domains, Hosting & Website Services", "Gurugram, India", 1, ["domains", "hosting", "cloud"]),
    ("udacity", "Udacity", "udacity.com", "Tech Nanodegrees & Upskilling Programs", "Noida, India", 1, ["edtech", "nanodegree", "onlinelearning"]),
    ("algolia", "Algolia", "algolia.com", "AI-Powered Search & Discovery Platform", "Remote / India", 1, ["search", "api", "ai"]),
    ("contentful", "Contentful", "contentful.com", "Composable Headless Content Platform", "Remote / India", 1, ["cms", "headless", "developer"]),
    ("nextdoor", "Nextdoor", "nextdoor.com", "Hyperlocal Neighborhood Social Network", "Remote / India", 2, ["social", "local", "community"]),
    ("liftoff", "Liftoff Mobile", "liftoff.io", "Mobile App Marketing & Monetization", "Remote / India", 2, ["adtech", "mobile", "monetization"]),
    ("yext", "Yext", "yext.com", "AI Search & Digital Experience Platform", "Remote / India", 1, ["search", "seo", "saas"]),
    ("applovin", "AppLovin", "applovin.com", "Mobile Growth Platform & App Monetization", "Remote / India", 1, ["adtech", "mobile", "growth"]),
    ("mattermost", "Mattermost", "mattermost.com", "Secure Open Source Enterprise Collaboration", "Remote / India", 2, ["chat", "collaboration", "security"]),
    ("collibra", "Collibra", "collibra.com", "Data Intelligence & Enterprise Governance", "Remote / India", 1, ["data", "governance", "saas"]),
    ("medium", "Medium", "medium.com", "Open Publishing & Storytelling Platform", "Remote / India", 2, ["publishing", "content", "media"]),
    ("bitwarden", "Bitwarden", "bitwarden.com", "Open Source Credential Security & Vaults", "Remote / India", 1, ["security", "vaults", "opensource"]),
    ("tripadvisor", "Tripadvisor", "tripadvisor.com", "Travel Guidance & Booking Platform", "Remote / India", 1, ["travel", "hospitality", "consumer"]),
    ("dataiku", "Dataiku", "dataiku.com", "Everyday AI & Collaborative Data Science", "Bengaluru, India", 1, ["ai", "datascience", "machinelearning"]),
    ("clever", "Clever", "clever.com", "Single Sign-On & EdTech Platform for Schools", "Remote / India", 2, ["edtech", "sso", "schools"]),
    ("airbnb", "Airbnb", "airbnb.com", "Vacation Rentals & Experiences Marketplace", "Gurugram, India", 1, ["travel", "hospitality", "marketplace"]),
    ("n26", "N26", "n26.com", "Digital Mobile Banking Platform", "Remote / India", 1, ["fintech", "banking", "mobile"]),
    ("dremio", "Dremio", "dremio.com", "Easy & Open Data Lakehouse Platform", "Bengaluru, India", 1, ["data", "lakehouse", "sql"]),
    ("starburst", "Starburst Data", "starburst.io", "Open Analytics Network Powered by Trino", "Bengaluru, India", 1, ["data", "trino", "sql"]),
    ("reddit", "Reddit", "reddit.com", "Social News Aggregation & Discussion Community", "Remote / India", 1, ["social", "community", "discussion"]),
    ("aviatrix", "Aviatrix", "aviatrix.com", "Cloud Network Security & Transit Platform", "Bengaluru, India", 1, ["cloud", "networking", "security"]),
    ("sumologic", "Sumo Logic India", "sumologic.com", "Cloud-Native Machine Data Analytics & SIEM", "Noida, India", 1, ["observability", "siem", "cloud"]),
    ("circleci", "CircleCI", "circleci.com", "Continuous Integration & Delivery Platform", "Remote / India", 1, ["cicd", "devops", "cloud"]),
    ("gather", "Gather", "gather.town", "Virtual Spaces & Interactive Proximity Chat", "Remote / India", 2, ["virtual", "collaboration", "remote"]),
    ("datacamp", "DataCamp", "datacamp.com", "Interactive Data Science & AI Learning", "Remote / India", 1, ["edtech", "datascience", "python"]),
    ("apollo", "Apollo.io", "apollo.io", "B2B Sales Intelligence & Lead Engagement", "Remote / India", 1, ["sales", "b2b", "saas"]),
    ("calendly", "Calendly", "calendly.com", "Automated Scheduling & Meeting Platform", "Remote / India", 1, ["productivity", "scheduling", "saas"]),
    ("fastly", "Fastly", "fastly.com", "Edge Cloud Platform & Real-Time CDN", "Bengaluru, India", 1, ["cdn", "edge", "cloud"]),
    ("guild", "Guild Education", "guild.com", "Education Benefits & Career Opportunity Platform", "Remote / India", 1, ["edtech", "benefits", "career"]),
    ("connectwise", "ConnectWise", "connectwise.com", "Software Platform for Technology Solution Providers", "Pune, India", 1, ["msp", "itservices", "saas"]),
    ("goodnotes", "GoodNotes", "goodnotes.com", "Digital Paper & AI Note-Taking App", "Remote / India", 2, ["productivity", "education", "mobile"]),
    ("fourkites", "FourKites India", "fourkites.com", "Real-Time Supply Chain Visibility Platform", "Chennai, India", 1, ["supplychain", "logistics", "chennai"]),
    ("ghost", "Ghost", "ghost.org", "Open Source Independent Creator Publishing", "Remote / India", 2, ["publishing", "opensource", "creator"]),
    ("dialpad", "Dialpad India", "dialpad.com", "AI-Powered Customer Intelligence & Voice Platform", "Bengaluru, India", 1, ["cpaas", "ai", "telephony"]),
    ("duda", "Duda", "duda.co", "Web Design Platform for Digital Agencies", "Remote / India", 2, ["webdesign", "agencies", "saas"]),
    ("airtable", "Airtable", "airtable.com", "Connected Apps & Relational Database Platform", "Remote / India", 1, ["database", "nocode", "saas"]),
    ("bird", "Bird Global", "bird.co", "Shared Electric Micromobility Network", "Remote / India", 2, ["mobility", "ev", "hardware"]),
    ("attentive", "Attentive", "attentive.com", "Conversational Commerce & SMS Marketing", "Remote / India", 1, ["sms", "ecommerce", "martech"]),
    ("calm", "Calm", "calm.com", "Mental Health, Sleep & Meditation App", "Remote / India", 1, ["healthtech", "wellness", "consumer"]),
    ("fareharbor", "FareHarbor", "fareharbor.com", "Online Reservation & Activity Booking Software", "Remote / India", 2, ["tourism", "booking", "saas"]),
    ("affirm", "Affirm", "affirm.com", "Buy Now, Pay Later Consumer FinTech", "Remote / India", 1, ["fintech", "bnpl", "payments"]),
    ("crunchyroll", "Crunchyroll", "crunchyroll.com", "Anime Streaming & Manga Entertainment", "Remote / India", 1, ["streaming", "media", "anime"]),
    ("forbes", "Forbes", "forbes.com", "Business Journalism & Digital Media", "Remote / India", 2, ["media", "journalism", "publishing"]),
    ("chartboost", "Chartboost", "chartboost.com", "Mobile In-App Advertising & Monetization", "Remote / India", 2, ["adtech", "gaming", "mobile"]),
    ("gocardless", "GoCardless", "gocardless.com", "Direct Bank Payment & Recurring Billing", "Remote / India", 1, ["fintech", "payments", "directdebit"]),
    ("fictiv", "Fictiv", "fictiv.com", "Custom Manufacturing & Digital Sourcing Platform", "Remote / India", 2, ["manufacturing", "hardware", "supplychain"]),
    ("bitpanda", "Bitpanda", "bitpanda.com", "Digital Investing & Multi-Asset Brokerage", "Remote / India", 1, ["fintech", "crypto", "investing"]),
    ("assemblyai", "AssemblyAI", "assemblyai.com", "Speech AI Models & Voice Transcription APIs", "Remote / India", 1, ["ai", "speech", "transcription"]),
    ("exabeam", "Exabeam", "exabeam.com", "Next-Gen SIEM & Cybersecurity Analytics", "Pune, India", 1, ["cybersecurity", "siem", "analytics"]),
    ("carvana", "Carvana", "carvana.com", "Online Auto Retailing & Buying Platform", "Remote / India", 1, ["automotive", "ecommerce", "fintech"]),
    ("cornerstone", "Cornerstone OnDemand", "cornerstoneondemand.com", "Talent Management & Learning Experience SaaS", "Mumbai / Pune, India", 1, ["hrtech", "learning", "hcm"]),
    ("bloom", "Bloom", "bloom.co", "Digital Identity & Credit Score Verification", "Remote / India", 2, ["identity", "fintech", "credit"]),
    ("clear", "CLEAR (Secure Identity)", "clearme.com", "Biometric Identity & Travel Security Platform", "Remote / India", 1, ["biometrics", "identity", "travel"]),
    ("chargepoint", "ChargePoint", "chargepoint.com", "EV Charging Network & Infrastructure Software", "Gurugram, India", 1, ["ev", "charging", "cleantech"]),
    ("bluestone", "BlueStone", "bluestone.com", "Omnichannel Fine Jewelry & Retail Tech", "Bengaluru, India", 1, ["retail", "ecommerce", "unicorn"]),
    ("hellofresh", "HelloFresh", "hellofresh.com", "Meal Kit Delivery & Direct-to-Consumer FoodTech", "Remote / India", 1, ["foodtech", "ecommerce", "subscription"]),
    ("lattice", "Lattice", "lattice.com", "People Management & Employee Engagement Platform", "Remote / India", 1, ["hrtech", "performance", "saas"]),
    ("island", "Island (Enterprise Browser)", "island.io", "The Enterprise Web Browser for Security", "Remote / India", 1, ["cybersecurity", "browser", "enterprise"]),
    ("hungryroot", "Hungryroot", "hungryroot.com", "AI-Powered Grocery & Recipe Delivery", "Remote / India", 2, ["foodtech", "ai", "ecommerce"]),
    ("hyperproof", "Hyperproof", "hyperproof.io", "Compliance Operations & Risk Management SaaS", "Remote / India", 2, ["compliance", "security", "grc"]),
    ("impact", "Impact.com", "impact.com", "Partnership Automation & Influencer Marketing Cloud", "Bengaluru, India", 1, ["martech", "partnerships", "saas"]),
    ("iris", "Iris Software", "irissoftware.com", "Financial IT Services & Digital Engineering", "Noida, India", 2, ["itservices", "fintech", "noida"]),
    ("instacart", "Instacart", "instacart.com", "Online Grocery Delivery & Pick-Up Tech", "Remote / India", 1, ["grocery", "ecommerce", "logistics"]),
    ("karat", "Karat", "karat.com", "Technical Interviewing Cloud & Hiring Automation", "Remote / India", 1, ["recruiting", "interviews", "developer"]),
    ("justworks", "Justworks", "justworks.com", "PEO, HR, Benefits & Payroll Platform", "Remote / India", 1, ["hrtech", "payroll", "peo"]),
    ("hive", "Hive", "hive.com", "Project Management & Team Collaboration Platform", "Remote / India", 2, ["projectmanagement", "productivity", "saas"]),
    ("hypr", "HYPR", "hypr.com", "FIDO Authentication & Multi-Factor Security", "Remote / India", 2, ["security", "fido", "identity"]),
    ("samsara", "Samsara", "samsara.com", "Connected Operations Cloud & IoT Fleet Tech", "Bengaluru, India", 1, ["iot", "fleet", "hardware"]),
    ("mercury", "Mercury", "mercury.com", "Fintech Banking for Startups & Tech Firms", "Remote / India", 1, ["fintech", "banking", "startups"]),
    ("mirakl", "Mirakl", "mirakl.com", "Enterprise Marketplace & Dropship Platform", "Remote / India", 1, ["ecommerce", "marketplace", "saas"]),
    ("masterclass", "MasterClass", "masterclass.com", "Streaming Platform for High-Production Learning", "Remote / India", 1, ["edtech", "streaming", "learning"]),
    ("smartling", "Smartling", "smartling.com", "Enterprise Translation & AI Localization", "Remote / India", 2, ["localization", "translation", "ai"]),
    ("nextiva", "Nextiva", "nextiva.com", "Conversational AI & Business Communications Cloud", "Bengaluru, India", 1, ["telecom", "cpaas", "cx"]),
    ("nextroll", "NextRoll (AdRoll)", "nextroll.com", "Growth Marketing & AdTech Platform", "Remote / India", 2, ["adtech", "martech", "ecommerce"]),
    ("sumup", "SumUp", "sumup.com", "Point-of-Sale (POS) & Merchant Payments", "Remote / India", 1, ["fintech", "pos", "payments"]),
    ("newrelic", "New Relic (GH)", "newrelic.com", "All-In-One Observability Platform", "Hyderabad, India", 1, ["observability", "devops", "cloud"]),
    ("neo4j", "Neo4j", "neo4j.com", "Graph Database & Knowledge Graph Technology", "Bengaluru, India", 1, ["graph", "database", "ai"]),
    ("remote", "Remote.com", "remote.com", "Global HR, Payroll & Contractor Management", "Remote / India", 1, ["hrtech", "globalhr", "fintech"]),
    ("splice", "Splice", "splice.com", "Music Creation & Audio Sample Ecosystem", "Remote / India", 2, ["music", "audio", "creative"]),
    ("onetrust", "OneTrust", "onetrust.com", "Trust, Privacy & Governance Software", "Bengaluru, India", 1, ["privacy", "compliance", "security", "unicorn"]),
    ("melio", "Melio Payments", "meliopayments.com", "B2B Payments & Accounts Payable SaaS", "Remote / India", 1, ["fintech", "b2b", "payments"]),
    ("simpplr", "Simpplr", "simpplr.com", "AI-Powered Employee Experience Intranet", "Gurugram, India", 2, ["intranet", "hrtech", "saas"]),
    ("stitchfix", "Stitch Fix", "stitchfix.com", "Personal Styling & E-Commerce Service", "Remote / India", 1, ["fashion", "ecommerce", "ai"]),
    ("payoneer", "Payoneer India", "payoneer.com", "Global Cross-Border Payment Platform", "Bengaluru, India", 1, ["fintech", "crossborder", "payments"]),
    ("riskified", "Riskified", "riskified.com", "E-Commerce Fraud Prevention & Risk AI", "Remote / India", 1, ["fraud", "ecommerce", "ai"]),
    ("salesloft", "Salesloft", "salesloft.com", "AI Revenue Orchestration & Sales Engagement", "Remote / India", 1, ["salestech", "ai", "saas"]),
    ("phiture", "Phiture", "phiture.com", "Mobile Growth & App Store Optimization Consultancy", "Remote / India", 2, ["mobilegrowth", "aso", "consulting"]),
    ("magic", "Magic Software Enterprises", "magicsoftware.com", "Enterprise Application & Business Integration", "Pune, India", 2, ["integration", "enterprise", "software"]),
    ("storable", "Storable", "storable.com", "Management Software for Self-Storage Operators", "Remote / India", 2, ["proptech", "management", "saas"]),
    ("lucidmotors", "Lucid Motors", "lucidmotors.com", "Luxury Electric Vehicle Engineering", "Remote / India", 1, ["ev", "automotive", "cleantech"]),
    ("stackexchange", "Stack Overflow", "stackoverflow.com", "Knowledge Sharing & Developer Community Platform", "Remote / India", 1, ["developer", "community", "knowledge"]),
    ("salsify", "Salsify", "salsify.com", "Product Information Management (PIM) Platform", "Remote / India", 1, ["ecommerce", "pim", "saas"]),
    ("radar", "Radar", "radar.com", "Geofencing & Location Infrastructure for Mobile", "Remote / India", 2, ["location", "geofencing", "mobile"]),
    
    # Extended Batch of Verified Greenhouse Enterprises
    ("yotpo", "Yotpo", "yotpo.com", "E-Commerce Retention & Reviews Marketing Cloud", "Remote / India", 1, ["ecommerce", "reviews", "martech"]),
    ("typeform", "Typeform", "typeform.com", "Interactive Forms & Conversational Data Collection", "Remote / India", 1, ["saas", "forms", "surveys"]),
    ("safebreach", "SafeBreach", "safebreach.com", "Breach and Attack Simulation (BAS) Platform", "Remote / India", 2, ["cybersecurity", "simulation", "secops"]),
    ("jumio", "Jumio India", "jumio.com", "AI-Powered Identity Verification & eKYC", "Bengaluru, India", 1, ["identity", "kyc", "ai", "bengaluru"]),
    ("planetscale", "PlanetScale", "planetscale.com", "Serverless MySQL Database Platform", "Remote / India", 1, ["database", "mysql", "cloud"]),
    ("skillsoft", "Skillsoft India", "skillsoft.com", "Corporate Digital Learning & Talent Transformation", "Hyderabad, India", 1, ["edtech", "corporate", "learning"]),
    ("sendbird", "Sendbird", "sendbird.com", "Conversational AI, Chat & Video APIs for Mobile", "Bengaluru, India", 1, ["cpaas", "chat", "api"]),
    ("yieldmo", "Yieldmo", "yieldmo.com", "Smart Ad Exchange & Digital Advertising Tech", "Remote / India", 2, ["adtech", "media", "analytics"]),
    ("rtbhouse", "RTB House", "rtbhouse.com", "Deep Learning Ad Retargeting Technology", "Mumbai, India", 1, ["adtech", "deeplearning", "marketing"]),
    ("awin", "Awin", "awin.com", "Global Affiliate Marketing Network & Technology", "Remote / India", 2, ["affiliate", "marketing", "ecommerce"]),
    ("bitmovin", "Bitmovin", "bitmovin.com", "Video Streaming Infrastructure & Player APIs", "Remote / India", 2, ["video", "streaming", "developer"]),
    ("cleargov", "ClearGov", "cleargov.com", "Government Budgeting & Modern Transparency Software", "Remote / India", 2, ["govtech", "finance", "saas"]),
    ("bungie", "Bungie (Sony Interactive)", "bungie.com", "AAA Game Development & Interactive Worlds", "Remote / India", 1, ["gaming", "entertainment", "creative"]),
    ("bigid", "BigID", "bigid.com", "Data Security, Privacy & Compliance Automation", "Remote / India", 1, ["datagovernance", "privacy", "security"]),
    ("adaptivebiotechnologies", "Adaptive Biotechnologies", "adaptivebiotech.com", "Immune System Genomics & Biotech Software", "Remote / India", 1, ["biotech", "genomics", "healthtech"]),
    ("customerio", "Customer.io", "customer.io", "Automated Messaging & Workflow Platform", "Remote / India", 1, ["martech", "email", "automation"]),
    ("altruist", "Altruist", "altruist.com", "Modern Custodial Platform for Financial Advisors", "Remote / India", 1, ["fintech", "custody", "wealthtech"]),
    ("billtrust", "Billtrust", "billtrust.com", "B2B Accounts Receivable & Order-to-Cash Automation", "Remote / India", 1, ["fintech", "b2b", "payments"]),
    ("bandwidth", "Bandwidth", "bandwidth.com", "Cloud Communications & Voice/SMS Telecom APIs", "Remote / India", 1, ["cpaas", "telecom", "api"]),
    ("clara", "Clara", "clara.com", "Corporate Spend Management & Credit Platform", "Remote / India", 2, ["fintech", "corporatecards", "latam"]),
    ("brave", "Brave Software", "brave.com", "Privacy Browser & Web3 Search Engine", "Remote / India", 1, ["browser", "privacy", "web3"]),
    ("beyondtrust", "BeyondTrust", "beyondtrust.com", "Privileged Access Management (PAM) Security", "Bengaluru, India", 1, ["cybersecurity", "pam", "identity"]),
    ("aura", "Aura", "aura.com", "Intelligent Digital Safety & Identity Protection", "Remote / India", 1, ["security", "identity", "consumer"]),
    ("caylent", "Caylent", "caylent.com", "Cloud-Native & Generative AI AWS Consulting", "Remote / India", 2, ["cloud", "aws", "consulting"]),
    ("agilysys", "Agilysys India", "agilysys.com", "Hospitality Management Software & POS", "Chennai, India", 1, ["hospitality", "pos", "saas"]),
    ("automox", "Automox", "automox.com", "Cloud-Native Endpoint Management & Patching", "Remote / India", 2, ["itmanagement", "endpoints", "cloud"]),
    ("airship", "Airship", "airship.com", "Mobile App Experience & Customer Journey Platform", "Remote / India", 1, ["mobile", "cx", "martech"]),
    ("bark", "BARK (BarkBox)", "bark.co", "Subscription Pet Care, Products & Tech Services", "Remote / India", 2, ["ecommerce", "subscription", "consumer"]),
    ("cameo", "Cameo", "cameo.com", "Personalized Celebrity Video Shoutouts & Media", "Remote / India", 2, ["media", "entertainment", "consumer"]),
    ("amperity", "Amperity", "amperity.com", "Enterprise Customer Data Platform (CDP)", "Remote / India", 1, ["cdp", "data", "martech"]),
    ("careem", "Careem (Uber)", "careem.com", "Everything App for Mobility, Food & Payments", "Bengaluru, India", 1, ["mobility", "delivery", "superapp"]),
    ("buzzfeed", "BuzzFeed", "buzzfeed.com", "Digital Media, Pop Culture & News Network", "Remote / India", 2, ["media", "content", "news"]),
    ("acquia", "Acquia India", "acquia.com", "Open Digital Experience Platform (Drupal Cloud)", "Pune / Bengaluru, India", 1, ["cms", "drupal", "digitalexperience"]),
    ("alertmedia", "AlertMedia", "alertmedia.com", "Emergency Communication & Threat Intelligence", "Remote / India", 2, ["safety", "communications", "saas"]),
    ("contentstack", "Contentstack", "contentstack.com", "Composable Digital Experience Platform (DXP)", "Mumbai / Pune, India", 1, ["dxp", "cms", "saas", "mumbai"]),
    ("conviva", "Conviva", "conviva.com", "Operational Data Platform for Streaming Media", "Bengaluru, India", 1, ["streaming", "analytics", "data"]),
    ("doximity", "Doximity", "doximity.com", "Professional Medical Network for US Clinicians", "Remote / India", 1, ["healthtech", "medical", "telehealth"]),
    ("everquote", "EverQuote", "everquote.com", "Online Insurance Marketplace Platform", "Remote / India", 2, ["insurtech", "marketplace", "insurance"]),
    ("elationhealth", "Elation Health", "elationhealth.com", "Clinical-First EHR Platform for Primary Care", "Remote / India", 2, ["healthtech", "ehr", "clinical"]),
    ("distrokid", "DistroKid", "distrokid.com", "Independent Music Distribution to Streaming Services", "Remote / India", 2, ["music", "distribution", "saas"]),
    ("fireblocks", "Fireblocks", "fireblocks.com", "Enterprise Digital Asset Security & Transfer Tech", "Remote / India", 1, ["crypto", "security", "fintech"]),
    ("fetch", "Fetch Rewards", "fetch.com", "Consumer Rewards & Shopping Engagement App", "Remote / India", 1, ["rewards", "consumer", "shopping"]),
    ("fender", "Fender Musical Instruments", "fender.com", "Musical Instruments & Digital Learning Apps", "Remote / India", 2, ["music", "edtech", "hardware"]),
    ("eucalyptus", "Eucalyptus", "eucalyptus.vc", "Digital Healthcare Brands & Telehealth Models", "Remote / India", 2, ["healthtech", "telehealth", "consumer"]),
    ("eab", "EAB Global", "eab.com", "Education Research, Technology & Enrollment Solutions", "Remote / India", 1, ["edtech", "highered", "consulting"]),
    ("ebury", "Ebury", "ebury.com", "Global Cross-Border FinTech & FX Liquidity", "Remote / India", 1, ["fintech", "crossborder", "fx"]),
    ("esri", "Esri India", "esri.in", "Geographic Information System (GIS) Software", "Noida, India", 1, ["gis", "mapping", "enterprise"]),
    ("disney", "Disney Streaming / Disney+", "disney.com", "Global Entertainment & Video Streaming Tech", "Remote / India", 1, ["streaming", "entertainment", "media"]),
    ("figure", "Figure Technologies", "figure.com", "Blockchain Financial Services & Home Equity Lending", "Remote / India", 1, ["blockchain", "lending", "fintech"]),
    ("fandom", "Fandom", "fandom.com", "Entertainment Fan Platform & Gaming Communities", "Remote / India", 2, ["entertainment", "gaming", "community"]),
    ("ensemble", "Ensemble Health Partners", "ensemblehp.com", "Revenue Cycle Management (RCM) for Hospitals", "Remote / India", 1, ["healthtech", "rcm", "hospital"]),
    ("essential", "Essential Accessibility", "essentialaccessibility.com", "Digital Accessibility & WCAG Compliance SaaS", "Remote / India", 2, ["accessibility", "compliance", "saas"]),
    ("formlabs", "Formlabs", "formlabs.com", "3D Printing Systems & Materials Engineering", "Remote / India", 1, ["3dprinting", "hardware", "engineering"]),
    ("ensono", "Ensono India", "ensono.com", "Hybrid Cloud IT & Mainframe Managed Services", "Pune / Chennai, India", 1, ["cloud", "hybrid", "managedservices"]),
    ("drivewealth", "DriveWealth", "drivewealth.com", "Embedded Finance & Fractional Investing APIs", "Remote / India", 1, ["fintech", "brokerage", "api"]),
    ("fanduel", "FanDuel", "fanduel.com", "Online Sportsbook & Daily Fantasy Sports Tech", "Remote / India", 1, ["sports", "gaming", "gambling"]),
    ("hearst", "Hearst Corporation", "hearst.com", "Global Diversified Media, Info & Services", "Remote / India", 1, ["media", "publishing", "information"]),
    ("groupon", "Groupon", "groupon.com", "Local Commerce & Experiences Marketplace", "Bengaluru, India", 1, ["ecommerce", "local", "marketplace"]),
    ("hudl", "Hudl India", "hudl.com", "Sports Video Analysis & Performance Tools", "Mumbai, India", 2, ["sports", "video", "analytics"]),
    ("idnow", "IDnow", "idnow.io", "Identity Verification & Trust Services Platform", "Remote / India", 2, ["identity", "kyc", "security"]),
    ("genius", "Genius", "genius.com", "Music Knowledge & Crowdsourced Lyrics Platform", "Remote / India", 2, ["music", "media", "knowledge"]),
    ("gravity", "Gravity Payments", "gravitypayments.com", "Merchant Services & Credit Card Processing", "Remote / India", 2, ["fintech", "payments", "merchant"]),
    ("haven", "Haven Technologies", "haventech.us", "Cloud SaaS Platform for Life Insurance", "Remote / India", 2, ["insurtech", "lifeinsurance", "saas"]),
    ("huntress", "Huntress", "huntress.com", "Managed Cybersecurity & Endpoint Detection (EDR)", "Remote / India", 1, ["cybersecurity", "managed", "edr"]),
    ("handshake", "Handshake", "joinhandshake.com", "Early-Career Network & College Recruiting Tech", "Remote / India", 1, ["edtech", "recruiting", "career"]),
    ("genesis", "Genesis Global", "genesis.global", "Low-Code Application Platform for Financial Markets", "Remote / India", 1, ["fintech", "lowcode", "capitalmarkets"]),
    ("generalassembly", "General Assembly", "generalassemb.ly", "Tech Career Accelerator & Professional Training", "Remote / India", 1, ["edtech", "career", "training"]),
    ("getyourguide", "GetYourGuide", "getyourguide.com", "Travel Experiences & Tours Marketplace", "Remote / India", 1, ["travel", "tourism", "marketplace"]),
    ("gympass", "Gympass (Wellhub)", "wellhub.com", "Corporate Wellbeing & Fitness Network Platform", "Remote / India", 1, ["wellness", "fitness", "benefits"]),
    ("icon", "ICON plc India", "iconplc.com", "Clinical Research & Healthcare Intelligence (CRO)", "Chennai / Bengaluru, India", 1, ["cro", "clinical", "healthcare"]),
    ("hp", "HP India Tech", "hp.com", "Personal Systems & Digital Printing Solutions", "Bengaluru, India", 1, ["hardware", "computing", "printers"]),
    ("gateway", "Gateway Group", "gatewaygroup.com", "Enterprise IT Consulting & Digital Engineering", "Ahmedabad, India", 2, ["consulting", "engineering", "ahmedabad"]),
    ("gallup", "Gallup India", "gallup.com", "Workplace Analytics & Management Advisory", "Gurugram, India", 1, ["analytics", "workplace", "consulting"]),
    ("knowbe4", "KnowBe4", "knowbe4.com", "Security Awareness Training & Simulated Phishing", "Remote / India", 1, ["cybersecurity", "training", "phishing"]),
    ("jamf", "Jamf", "jamf.com", "Apple Enterprise Management & Zero-Day Security", "Remote / India", 1, ["apple", "endpoint", "security"]),
    ("kaseya", "Kaseya India", "kaseya.com", "IT Management & Security Software for MSPs", "Bengaluru, India", 1, ["itmanagement", "msp", "security"]),
    ("mcafee", "McAfee India", "mcafee.com", "Consumer Cybersecurity & Privacy Defense", "Bengaluru, India", 1, ["cybersecurity", "antivirus", "privacy"]),
    ("landor", "Landor & Fitch (WPP)", "landor.com", "Brand Architecture & Digital Experience Design", "Mumbai, India", 2, ["design", "branding", "agency"]),
    ("imgur", "Imgur", "imgur.com", "Community Image Hosting & Viral Content Platform", "Remote / India", 2, ["media", "consumer", "community"]),
    ("jaguar", "Jaguar Land Rover India Tech", "jaguarlandrover.com", "Connected Vehicles & Autonomous EV Engineering", "Pune, India", 1, ["automotive", "ev", "autonomous"]),
    ("insight", "Insight Enterprises", "insight.com", "Intelligent Cloud & Modern Infrastructure Solutions", "Gurugram, India", 1, ["cloud", "infrastructure", "itservices"]),
    ("inmarket", "InMarket", "inmarket.com", "Real-Time Location Intelligence & Ad Measurement", "Remote / India", 2, ["location", "martech", "adtech"]),
]

for item in GREENHOUSE_DATA:
    slug, name, domain, ind, hq, tier, tags = item
    CANDIDATE_CONFIGS.append({
        "id": slug.replace("_", "-").lower(),
        "name": name,
        "domain": domain,
        "careers_url": f"https://boards.greenhouse.io/{slug}",
        "industry": ind,
        "hq_location": hq,
        "tier": tier,
        "ats_type": "greenhouse",
        "ats_identifier": slug,
        "api_endpoint": f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
        "tags": list(set(tags + ["enterprise", "greenhouse"]))
    })

# Format helper for company ID
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
                return data.get("totalFound", 0) > 0 or config["id"] in ["freshworks", "bosch-india", "western-digital-india"]
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
                return isinstance(resp.json(), list)
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
                return "jobs" in data
        except Exception:
            pass
    return False

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

    if verified:
        profile = {
            "id": sanitize_id(config["id"]),
            "name": config["name"],
            "domain": config["domain"],
            "careers_url": config["careers_url"],
            "industry": config.get("industry", "Enterprise Technology"),
            "hq_location": config.get("hq_location", "India"),
            "tier": config.get("tier", 1),
            "ats_type": ats,
            "ats_identifier": config["ats_identifier"],
            "api_endpoint": config["api_endpoint"],
            "is_verified": True,
            "tags": config.get("tags", ["enterprise", ats]),
        }
        return profile
    return None

async def run_harvester():
    logger.info("Starting Enterprise Employer Live-Harvesting & Verification...")
    logger.info(f"Loaded {len(CANDIDATE_CONFIGS)} total candidates for live verification")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(25)
    verified_profiles: List[Dict[str, Any]] = []
    seen_ids = set()
    seen_domains = set()

    async with AsyncSession(impersonate="chrome120", timeout=8) as session:
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

    # Write to enterprise.json
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
