# JobScrap — Autonomous Direct Company Career & Job Aggregator

<p align="center">
  <strong>The high-performance, open-source Python Job Scraper & Direct Career Aggregator for India & Global tech hiring.</strong><br>
  <em>Pure Direct-to-Company Ingestion, 3,197+ Verified Company Career Portals, Zero Middlemen, and Direct Apply Guarantee.</em>
</p>

<p align="center">
  <a href="https://github.com/bytebldr/jobscrap/releases/tag/v0.5"><img src="https://img.shields.io/badge/Release-v0.5-blue.svg" alt="Release v0.5" /></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg" alt="Python Version" />
  <img src="https://img.shields.io/badge/Companies-3%2C197%2B%20Verified-orange.svg" alt="Companies" />
  <img src="https://img.shields.io/badge/Engines-Greenhouse%20%7C%20Lever%20%7C%20Ashby%20%7C%20SmartRecruiters%20%7C%20Workday-purple.svg" alt="Direct Engines" />
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License" />
</p>

---

## 📖 About JobScrap

**JobScrap** is a standalone, high-performance **Python library and CLI for direct-to-company job extraction**. 

Instead of scraping third-party aggregators that deliver stale, expired, or redirect-trapped listings, **JobScrap taps directly into the recruitment engines (ATS) powering official corporate career pages**.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        JobScrap v0.5 Architecture                      │
└────────────────────────────────────────────────────────────────────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
┌──────────────┐             ┌──────────────┐             ┌──────────────┐
│  Greenhouse  │             │   Ashby HQ   │             │    Lever     │
│  (1,311 cos) │             │  (821 cos)   │             │  (309 cos)   │
└──────────────┘             └──────────────┘             └──────────────┘
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
┌──────────────┐             ┌──────────────┐             ┌──────────────┐
│SmartRecruiters             │  Workday CX  │             │Auto-Resolver │
│  (553 cos)   │             │   (19 cos)   │             │(New Domains) │
└──────────────┘             └──────────────┘             └──────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │     3,197+ Pre-Indexed Employers (SQLite FTS5 BM25)     │
       │    100% Direct Application Links | Zero Ghost Jobs      │
       └─────────────────────────────────────────────────────────┘
```

### Core Invariants

1. **Pure Direct-to-Company Ingestion**: Extracts live jobs directly from official corporate recruitment systems (**Greenhouse, Lever, Ashby, SmartRecruiters, Workday CX**) with sub-second response times.
2. **Master Directory of 3,197+ Employers**: Pre-indexed catalog of Indian Unicorns, Startups, IT Services, Conglomerates, GCCs, and Global Tech firms with full-text search.
3. **100% Direct Application Links**: Every posting leads straight to the official corporate application form—zero affiliate redirects, zero registration walls.
4. **Zero Ghost Jobs**: Direct ATS queries return only positions actively open *today* on company job boards.
5. **Autonomous Career Resolver**: Given any domain (e.g. `cred.club`), automatically crawls, fingerprints the company's hiring engine, and pulls live jobs.
6. **Smart Deduplication**: Automatically clusters cross-department and identical postings using token Jaccard similarity (`0.75`), prioritizing verified primary ATS endpoints.

---

## 🚀 Release v0.5 Highlights

- 🏢 **Pure Direct ATS Pipeline**: Interrogates native ATS JSON/GraphQL APIs directly with zero fragile HTML scraping or browser overhead.
- ⚡ **3,197+ Pre-Indexed Companies**: Pre-compiled directory with SQLite FTS5 BM25 search index at `jobscrap/catalog/companies.db`.
- 🇮🇳 **Deep India Coverage**: 1,200+ Indian corporate profiles across Startups (Razorpay, Swiggy, Zepto, CRED, Groww), IT Services (TCS, Infosys, Cognizant), BFSI & Conglomerates (HDFC Bank, ICICI Bank, Tata Motors, Reliance Jio), and Healthcare/Pharma (Dr. Reddy's).
- 🔗 **Direct Apply Guarantee**: 100% verified application URLs straight on official employer portals.
- 🔍 **Autonomous Career Resolver**: Automatically fingerprints uncataloged company domains to detect their underlying career engine.
- 📦 **Modern Python Library & CLI**: Installable via `pip install -e .` with clean programmatic APIs and rich terminal commands.

---

## 🌐 Supported Career Engines

| Engine | Protocol | Supported Platforms & Examples | Latency / Reliability |
|---|:---:|---|---|
| **Greenhouse** | Board JSON API | Razorpay, Stripe, Coinbase, Groww, Cloudflare, Databricks, Figma | Zero blocks (<300ms) |
| **Ashby HQ** | GraphQL API | Supabase, Linear, Ramp, CRED, Zepto, Deel, Vercel, Sarvam AI | Zero blocks (<350ms) |
| **Lever** | Postings v0 API | Spotify, Atlassian, Netflix, Swiggy, Nykaa, Paytm | Zero blocks (<250ms) |
| **SmartRecruiters** | Postings v1 API | Freshworks, Zomato, Delivery Hero, Visa, Miro, Upstox | Zero blocks (<400ms) |
| **Workday CX** | REST CX Client | TCS, Infosys, Cognizant, PayPal India, Target India | REST JSON (<600ms) |

---

## ⚡ Feature Matrix: JobScrap vs. Generic Aggregators

| Feature / Capability | Generic Aggregators & Scrapers | JobScrap (Direct Engine) |
|---|:---:|:---:|
| **Data Source** | ❌ Stale third-party job boards scraped with 3–7 day lag | ✅ **3,197+ direct corporate career endpoints** (Greenhouse, Lever, Ashby, SmartRecruiters, Workday) |
| **Apply Link Integrity** | ❌ Stale links, affiliate trackers, and expired redirects | ✅ **100% direct official application forms** on company sites |
| **Ghost / Expired Jobs** | ⚠️ 30–50% dead listings kept to inflate numbers | ✅ **Real-Time Primary Truth**: 100% active jobs open today |
| **Blocking & CAPTCHAs** | ⚠️ Frequent Cloudflare Turnstile blocks & login walls | ✅ **Zero-Block Official APIs**: Public JSON/GraphQL endpoints with `curl_cffi` TLS impersonation |
| **Master Company Directory** | ❌ None; requires manual search keywords | ✅ **3,197+ pre-indexed companies** with SQLite FTS5 BM25 search |
| **Autonomous Career Resolver** | ❌ None | ✅ **Automatic domain crawler** that fingerprints any unlisted company's career engine |
| **Deduplication** | ❌ None; returns unlinked duplicate entries | ✅ **Built-in Jaccard similarity (`0.75`)** prioritizing direct primary ATS sources |

---

## 🚀 Quickstart

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/bytebldr/jobscrap.git
cd jobscrap

# Install as an editable Python library
pip install -e .
```

### 2. Programmatic Python Usage

```python
from jobscrap import JobScraper, CompanyCatalog

scraper = JobScraper()

# 1. Fetch live jobs directly from any company
jobs = scraper.get_company_jobs("Razorpay")
print(f"Found {len(jobs)} live jobs from Razorpay:")
for j in jobs[:5]:
    print(f"• {j.title} | {j.location} -> {j.url}")

# 2. Search across 3,197+ company career portals in parallel (async)
import asyncio

async def search_roles():
    matches = await scraper.search_companies_async(
        query="Backend Engineer",
        locations=["Bengaluru", "Remote"],
        limit=25
    )
    for m in matches:
        print(f"[{m.company}] {m.title} | {m.url}")

asyncio.run(search_roles())

# 3. Search pre-indexed company profiles with SQLite FTS5 BM25
catalog = CompanyCatalog()
companies = catalog.search("fintech", limit=10)
for c in companies:
    print(f"{c.name} ({c.domain}) -> ATS: {c.ats_type}")
```

### 3. Command-Line Interface (CLI)

```bash
# Fetch live jobs from any company career portal
jobscrap company "Razorpay"
jobscrap company "Sarvam AI"
jobscrap company "Freshworks"

# Search live roles across company career portals
jobscrap search "Software Engineer" --location "Bengaluru"

# Search pre-indexed companies in the catalog (FTS5 BM25)
jobscrap catalog --query "fintech"
jobscrap catalog --stats

# Automatically resolve an unlisted company's career engine
jobscrap resolve "cred.club"
```

### 4. Direct-to-Company REST API

```bash
# Start FastAPI backend on port 8000
uvicorn api:app --port 8000

# Available Endpoints:
# GET /health                    -> Health check and catalog size
# GET /stats                     -> Total companies and ATS distribution
# GET /companies?query=fintech   -> Search cataloged company profiles (BM25)
# GET /companies/razorpay/jobs   -> Fetch live jobs directly from company ATS
# GET /search?query=backend      -> Search live company jobs across catalog
# GET /export?format=json|csv    -> Export company catalog
```

### 5. Run Verification Test Suite

```bash
# Run unit and scale verification tests
python -m unittest tests/test_catalog_scale.py tests/test_v05_direct_company.py
```

---

## 📊 Canonical Job Schema

Every job record is normalized into this consistent schema:

```json
{
  "id": "gh_razorpay_4741226005",
  "source": "greenhouse",
  "source_type": "ats",
  "company": "Razorpay",
  "title": "Analyst, Banking Alliances",
  "location": "Chennai",
  "url": "https://job-boards.greenhouse.io/razorpaysoftwareprivatelimited/jobs/4741226005",
  "is_remote": false,
  "job_type": "fulltime",
  "experience_level": "mid",
  "department": "Banking Alliances",
  "posted_date": "2026-11-20",
  "scraped_at": "2026-11-23T14:30:00Z",
  "status": "live",
  "min_salary_inr": null,
  "max_salary_inr": null
}
```

---

## 🔒 Security & Quality Standards

- **SSRF Prevention (OWASP A01)**: Restricts outbound career discovery to valid HTTP/HTTPS schemes, blocking access to private network subnets and cloud metadata endpoints.
- **SQL Injection Safe**: Pre-indexed search uses parameterized SQLite FTS5 queries (`?` bind parameters) with zero raw string interpolation.
- **Input Sanitization**: Canonical domain normalization strips path traversal and invalid characters before registry lookup.
- **Minimal Dependencies**: Pure Python library requiring only `curl_cffi` and `pydantic`. Zero browser automation overhead.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
