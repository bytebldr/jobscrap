# JobScrap Architecture Blueprint (v0.5+)

## 1. Executive Summary & Philosophy

**JobScrap** is a high-performance Python library, CLI, and REST API designed for **pure Direct-to-Company career portal ingestion**.

### The Core Problem with Generic Aggregators
Third-party job aggregators (Naukri, Indeed, LinkedIn, etc.) suffer from inherent architectural decay:
1. **The 3–7 Day Stale Window**: Aggregators crawl intermittently; postings are often filled or closed days before appearing on aggregator feeds.
2. **Ghost Listings**: Aggregators retain expired listings to inflate search inventory.
3. **Redirect Traps & Login Walls**: Candidates are forced through affiliate redirects, tracking walls, or account creation gates.
4. **Anti-Bot Arms Race**: Scraping aggregator HTML requires fragile headless browser automation and CAPTCHA circumvention.

### The Direct-to-Company Invariant
98% of modern enterprises do not build bespoke career portals from scratch. Instead, they embed standard **Applicant Tracking System (ATS)** platforms behind their corporate career pages.

By interfacing directly with the standard public JSON and GraphQL APIs of these ATS platforms, **JobScrap eliminates scraping fragility entirely**:
- **Sub-Second Latency**: Direct API calls execute in <300ms.
- **100% Real-Time Truth**: Every job returned is currently active on the employer's official recruitment portal.
- **Authentic Application URLs**: Applicants apply directly on the company's official job board with zero intermediary redirect chains.

---

## 2. System Architecture

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

---

## 3. Supported ATS Protocol Specifications

### 3.1 Greenhouse Board API
- **Endpoint**: `GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true`
- **Method**: Direct HTTP JSON
- **Parsing**: Standard Greenhouse payload (`jobs[]` array with `id`, `title`, `location.name`, `departments`, `absolute_url`).
- **Engine Implementation**: `jobscrap.engines.greenhouse.GreenhouseEngine`

### 3.2 Ashby HQ GraphQL API
- **Endpoint**: `POST https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams`
- **Method**: GraphQL Query
- **Query Operation**: `ApiJobBoardWithTeams` requesting `jobBoard { jobPostings { id title locationName teamId } }`
- **Engine Implementation**: `jobscrap.engines.ashby.AshbyEngine`

### 3.3 Lever Postings v0 API
- **Endpoint**: `GET https://api.lever.co/v0/postings/{token}?mode=json`
- **Method**: Direct HTTP JSON
- **Parsing**: Lever posting objects with `text` (title), `categories.location`, `categories.team`, `hostedUrl`.
- **Engine Implementation**: `jobscrap.engines.lever.LeverEngine`

### 3.4 SmartRecruiters Postings API
- **Endpoint**: `GET https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100`
- **Method**: Paginated REST JSON
- **Parsing**: Content items with `name` (title), `location.city`, `department.label`, `refNumber`.
- **Engine Implementation**: `jobscrap.engines.smartrecruiters.SmartRecruitersEngine`

### 3.5 Workday CX (Candidate Experience) Client
- **Endpoint**: `POST https://{tenant}.wd3.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs`
- **Method**: REST JSON Search
- **Parsing**: Workday job list with `title`, `locationsText`, `externalPath`.
- **Engine Implementation**: `jobscrap.engines.workday.WorkdayEngine`

---

## 4. Master Directory & SQLite FTS5 Registry

The catalog maintains **3,197+ verified employers** indexed across 7 curated sector registries:
1. `enterprise.json`: Global Enterprise Software, SaaS, and Cloud Infrastructure.
2. `gcc.json`: Global Capability Centers and multinational technology hubs.
3. `startups.json`: Unicorns and venture-backed tech platforms.
4. `india_startups.json`: FinTech, WealthTech, Quick Commerce, EV, and DeepTech startups.
5. `india_it.json`: IT Services, Consultancies, and ER&D companies.
6. `india_bfsi.json`: Banks, NBFCs, and major conglomerates.
7. `india_consumer.json`: Healthcare, Pharma, D2C, Travel, and Digital Media.

### Registry Features
- **SQLite FTS5 BM25 Search**: `jobscrap/catalog/companies.db` provides sub-millisecond ranking over company names, domains, tags, and industries.
- **Canonical Schema**: 100% compliant with `CompanyProfile` dataclass.
- **Zero Duplicate Invariant**: Enforced 0 duplicate IDs and 0 duplicate domains across the entire directory.

---

## 5. Autonomous Career Discovery & Fingerprinting

When an unindexed domain is passed to `CompanyResolver` (e.g. `jobscrap resolve "example.com"`):
1. **SSRF Guard**: Destination domain and IP are checked to block local/private network ranges.
2. **Career Landing Page Discovery**: Probes `/careers`, `/jobs`, `/join-us`, `/about/careers`.
3. **Engine Fingerprinting**:
   - Analyzes script `src` attributes, iframe URLs, and network redirects.
   - Matches known ATS CDN signatures (`boards.greenhouse.io`, `jobs.ashbyhq.com`, `lever.co`, `smartrecruiters.com`, `myworkdayjobs.com`).
4. **Token Extraction**: Extracts the organization's unique slug or identifier.
5. **Live Verification**: Queries the candidate ATS endpoint to ensure live job retrieval works before returning the profile.

---

## 6. Smart Deduplication Pipeline

`jobscrap.pipeline.dedup.deduplicate_jobs` prevents redundant entries when sweeping multiple departments or overlapping postings:
- **Token-based Jaccard Similarity**: Calculates token overlap across normalized `title`, `company`, and `location`.
- **Threshold**: `0.75` Jaccard score clusters postings into unified groups.
- **Source Priority**: Direct ATS primary endpoints are prioritized over custom or unverified portals.

---

## 7. Interfaces

### 7.1 Python Library
```python
from jobscrap import JobScraper, CompanyCatalog

scraper = JobScraper()
jobs = scraper.get_company_jobs("Razorpay")
catalog = CompanyCatalog()
matches = catalog.search("fintech")
```

### 7.2 Modern CLI
```bash
jobscrap company "Razorpay"
jobscrap search "Backend Engineer" --location "Bengaluru"
jobscrap catalog --stats
jobscrap resolve "cred.club"
```

### 7.3 REST API (`api.py`)
```bash
uvicorn api:app --port 8000
```
- `GET /health`
- `GET /stats`
- `GET /companies?query=...`
- `GET /companies/{target}/jobs`
- `GET /search?query=...&location=...`
- `GET /export?format=json|csv`

---

## 8. Quality & Defensive Security

- **OWASP SSRF Protection (A01)**: All outbound discovery requests validate target hostnames against private IP subnets (`10.0.0.0/8`, `192.168.0.0/16`, `127.0.0.0/8`) and cloud metadata services (`169.254.169.254`).
- **SQL Injection Prevention**: All queries to SQLite catalogs use parameterized `?` bind variables with zero string interpolation.
- **Zero-Secret Invariant**: Zero API keys or authentication credentials required.
- **Minimal Dependencies**: Requires only `curl_cffi` and `pydantic`. Zero browser automation overhead.
