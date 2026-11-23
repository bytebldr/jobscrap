# JobScrap — Autonomous Direct Company Career & Job Aggregator

<p align="center">
  <strong>The high-performance, open-source Python Job Scraper & Direct Career Aggregator for India & Global tech hiring.</strong><br>
  <em>Direct-to-Company Ingestion, 3,100+ Verified Company Career Portals, TLS Fingerprint Bypass, and Smart Deduplication.</em>
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

**JobScrap** is a modern, standalone **Python job scraper and primary-source aggregator** built to extract job postings directly from corporate career portals and major hiring platforms with zero fragile dependencies or commercial API keys.

Unlike generic aggregators that scrape third-party boards and deliver stale, expired, or redirect-trapped links, **JobScrap** features a **Pure Direct-to-Company Pipeline**:
1. **Direct Company Career Ingestion**: Directly taps into the underlying recruitment engines (**Greenhouse, Lever, Ashby, SmartRecruiters, Workday CX**) powering official company career pages.
2. **Master Directory of 3,197+ Employers**: Pre-indexed catalog of Indian Unicorns, Startups, IT Services, Conglomerates, GCCs, and Global Tech firms with SQLite FTS5 BM25 search.
3. **100% Direct Application Links**: Every posting provides the official application URL straight on the employer's portal—zero middlemen, zero affiliate walls.
4. **Autonomous Career Discovery**: Given any domain (e.g., `cred.club`), automatically crawls, fingerprints the hiring engine, and pulls live jobs.
5. **Deduplication & Normalization**: Clusters cross-department and identical postings using token similarity (`0.75`).
6. **Zero Fragile Scraping**: Eliminates fragile HTML web scraping and CAPTCHA bypasses by calling official public ATS JSON/GraphQL APIs.

---

## 🚀 Release v0.5 Highlights

- 🏢 **Direct-to-Company Career Pipeline**: Pulls 100% active, primary-source job postings directly from corporate portals (Greenhouse, Lever, Ashby, SmartRecruiters, Workday CX) in <500ms.
- ⚡ **3,197+ Master Company Directory**: Pre-indexed catalog of Indian Unicorns, Startups, IT Services, Conglomerates, GCCs, and Global Tech firms with SQLite FTS5 BM25 search.
- 🇮🇳 **Deep India Coverage**: 1,200+ Indian corporate profiles including Razorpay, Swiggy, Zepto, CRED, TCS, Infosys, HDFC Bank, ICICI Bank, Tata Motors, Dr. Reddy's, and Reliance Jio.
- 🔗 **Direct Apply Guarantee**: 100% authentic URLs leading straight to company hiring forms with zero aggregator delays or redirect traps.
- 🔍 **Autonomous Career Resolver**: Automatically fingerprints uncataloged company domains to detect their underlying career engine.
- 📦 **Python Library & Modern CLI**: Installable via `pip install -e .` with direct imports (`from jobscrap import JobScraper, CompanyCatalog`) and CLI (`jobscrap company <name>`, `jobscrap search <role>`).

---

## 🌐 Supported Career Engines

JobScrap directly interfaces with standard recruitment systems powering corporate career portals:

| Engine | Protocol | Supported Platforms & Examples | Latency / Reliability |
|---|:---:|---|---|
| **Greenhouse** | Board JSON API | Razorpay, Stripe, Coinbase, Groww, Cloudflare, Databricks, Figma | Zero blocks (<300ms) |
| **Ashby HQ** | GraphQL API | Supabase, Linear, Ramp, CRED, Zepto, Deel, Vercel | Zero blocks (<350ms) |
| **Lever** | Postings v0 API | Spotify, Atlassian, Netflix, Swiggy, Nykaa, Paytm | Zero blocks (<250ms) |
| **SmartRecruiters** | Postings v1 API | Freshworks, Zomato, Delivery Hero, Visa, Miro | Zero blocks (<400ms) |
| **Workday CX** | REST CX Client | TCS, Infosys, Cognizant, PayPal India, Target India | REST JSON (<600ms) |

---

## ⚡ Feature Matrix: JobScrap vs. Typical Job Scrapers

| Feature / Capability | Standard / Generic Scrapers | JobScrap (This Engine) |
|---|:---:|:---:|
| **Direct Company Career Ingestion** | ❌ None; generic aggregators scrape stale third-party boards with 3–7 day lag | ✅ **3,197+ direct corporate career endpoints** (Greenhouse, Lever, Ashby, SmartRecruiters, Workday) |
| **Direct Apply Link Integrity** | ❌ Stale links, affiliate trackers, and expired 404/login redirects | ✅ **100% direct official application forms** on company sites |
| **Anti-Bot & TLS Fingerprint Evasion** | ⚠️ Basic HTTP headers easily blocked by Cloudflare Turnstile, Akamai, and JA3/JA4 fingerprinting | ✅ **Full browser impersonation** via `curl_cffi` (`chrome124`, `safari17_0`) + native Edge for complex React SPAs |
| **Cross-Portal Deduplication** | ❌ None; returns unlinked duplicate entries across multiple job boards | ✅ **Built-in Jaccard similarity (`0.75`)** with indexed candidate pre-filtering to cluster cross-board postings |
| **Self-Healing Dead-Link Purge** | ❌ None; expired and closed postings remain in output datasets indefinitely | ✅ **Autonomous async validator** with soft-404 redirect detection, auto-purging dead links after 2 strikes |
| **Master Company Directory** | ❌ None; requires manual search keywords | ✅ **3,197+ pre-indexed companies** with SQLite FTS5 BM25 search |
| **Autonomous Career Resolver** | ❌ None | ✅ **Automatic domain crawler** that fingerprints any unlisted company's career engine |

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

### 2. Python Library Usage

```python
from jobscrap import JobScraper, CompanyCatalog

scraper = JobScraper()

# 1. Fetch live jobs directly from a company's official career portal
jobs = scraper.get_company_jobs("Razorpay")
print(f"Found {len(jobs)} live jobs directly from Razorpay!")
for j in jobs[:5]:
    print(f"• {j.title} ({j.location}) -> {j.url}")

# 2. Search across 3,197+ company career portals in parallel
matches = await scraper.search_companies_async(
    query="Backend Engineer",
    locations=["Bengaluru", "Remote"],
    limit=25
)
for m in matches:
    print(f"[{m.company}] {m.title} | {m.url}")
```

### 3. Command-Line Interface (CLI)

```bash
# Fetch live jobs from any company career portal
jobscrap company "Razorpay"
jobscrap company "Supabase"
jobscrap company "Freshworks"

# Search across all company career portals
jobscrap search "Software Engineer" --location "Bengaluru"

# Search pre-indexed companies in the catalog
jobscrap catalog --query "fintech"

# Automatically resolve an unlisted company's career engine
jobscrap resolve "cred.club"
```

### 4. Run REST API Server
```bash
# Start FastAPI backend on port 8000
uvicorn api:app --port 8000

# Available Endpoints:
# GET /health
# GET /stats
# GET /companies?query=fintech
# GET /companies/razorpay/jobs
# GET /search?query=backend&location=bengaluru
# GET /export?format=json|csv
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

## 🔒 Security & Privacy (OWASP Top 10:2025)

- **SSRF Prevention (A01:2025)**: Validates destination IPs during link validation to prevent probing private subnets (`10.0.0.0/8`, `192.168.0.0/16`, `127.0.0.0/8`) and cloud metadata endpoints (`169.254.169.254`).
- **Input Sanitization (A05:2025)**: Sanitizes search queries and URL slugs to block path manipulation.
- **Credential Protection (A09:2025)**: Automatically redacts proxy credentials from logs and error messages.
- **SQL Injection Safe**: All queries use parameterized bind variables (`?` / `:key`) with zero string interpolation.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
