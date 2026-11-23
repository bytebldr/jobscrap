"""JobScrap Direct-to-Company REST API."""

import csv
import io
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from jobscrap.catalog.registry import CompanyCatalog
from jobscrap.core.config import JobScrapConfig
from jobscrap.core.models import CompanyProfile, JobListing
from jobscrap.scraper import JobScraper

app = FastAPI(
    title="JobScrap Direct Career API",
    description="Autonomous Direct-to-Company Career & Job Aggregator API",
    version="0.5.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

catalog = CompanyCatalog()
scraper = JobScraper(catalog=catalog)

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.5.0", "catalog_size": len(catalog)}

@app.get("/stats")
def get_stats():
    companies = catalog.all()
    by_ats = {}
    by_industry = {}
    for c in companies:
        by_ats[c.ats_type] = by_ats.get(c.ats_type, 0) + 1
        by_industry[c.industry] = by_industry.get(c.industry, 0) + 1
    return {
        "total_companies": len(companies),
        "ats_engines": by_ats,
        "industries": by_industry,
    }

@app.get("/companies")
def search_companies(
    query: Optional[str] = None,
    industry: Optional[str] = None,
    ats_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    """Search cataloged company profiles with SQLite FTS5 BM25 search."""
    if query:
        results = catalog.search(query=query, limit=limit)
    else:
        results = catalog.all()

    if industry:
        results = [c for c in results if c.industry.lower() == industry.lower()]
    if ats_type:
        results = [c for c in results if c.ats_type.lower() == ats_type.lower()]

    return {"count": len(results), "companies": [c.to_dict() for c in results[:limit]]}

@app.get("/companies/{target}/jobs")
async def get_company_jobs(target: str):
    """Fetch live primary job postings directly from a company's official career portal."""
    try:
        jobs = await scraper.get_company_jobs_async(target)
        return {
            "company": target,
            "count": len(jobs),
            "jobs": [j.to_dict() for j in jobs],
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Failed to fetch jobs for '{target}': {str(e)}")

@app.get("/search")
async def search_jobs(
    query: str = Query(..., description="Job title, skill, or role query"),
    location: Optional[str] = None,
    company: Optional[str] = None,
    limit: int = Query(25, ge=1, le=100),
):
    """Search for matching jobs directly across company career portals."""
    locations = [location] if location else None
    companies = [company] if company else None
    jobs = await scraper.search_companies_async(
        query=query,
        locations=locations,
        companies=companies,
        limit=limit,
    )
    return {
        "query": query,
        "count": len(jobs),
        "jobs": [j.to_dict() for j in jobs],
    }

@app.get("/export")
def export_companies(format: str = Query("json", pattern="^(json|csv)$")):
    """Export cataloged companies as JSON or CSV."""
    companies = [c.to_dict() for c in catalog.all()]
    if format == "csv":
        output = io.StringIO()
        if companies:
            writer = csv.DictWriter(output, fieldnames=list(companies[0].keys()))
            writer.writeheader()
            writer.writerows(companies)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=companies.csv"},
        )
    return JSONResponse(content=companies)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
