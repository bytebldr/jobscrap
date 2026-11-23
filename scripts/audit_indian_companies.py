import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jobscrap.catalog.registry import CompanyCatalog
from jobscrap.core.models import CompanyProfile
from jobscrap.scraper import JobScraper

def main():
    catalog_path = Path("jobscrap/catalog/companies.json")
    with open(catalog_path, "r", encoding="utf-8") as f:
        companies = json.load(f)

    print(f"Total catalog count: {len(companies)}")

    # Check duplicates
    ids = [c["id"] for c in companies]
    domains = [c["domain"] for c in companies]
    dup_ids = len(ids) - len(set(ids))
    dup_domains = len(domains) - len(set(domains))
    print(f"Duplicate IDs: {dup_ids}, Duplicate Domains: {dup_domains}")

    # Check Schema
    valid = 0
    for c in companies:
        try:
            p = CompanyProfile(
                id=c["id"],
                name=c["name"],
                domain=c["domain"],
                careers_url=c["careers_url"],
                industry=c.get("industry", "Technology"),
                hq_location=c.get("hq_location", "India"),
                tier=c.get("tier", 1),
                ats_type=c.get("ats_type", "custom"),
                ats_identifier=c.get("ats_identifier"),
                api_endpoint=c.get("api_endpoint"),
                tags=c.get("tags", []),
            )
            valid += 1
        except Exception as e:
            print(f"Schema error for {c.get('name')}: {e}")
    print(f"Schema validity: {valid}/{len(companies)} ({(valid/len(companies))*100:.1f}%)")

    # Specific Indian company live ATS test
    catalog = CompanyCatalog(catalog_path=catalog_path)
    scraper = JobScraper(catalog=catalog)

    indian_samples = [
        "Razorpay",
        "Swiggy",
        "CRED",
        "Groww",
        "Zepto",
        "AngelOne",
        "Upstox",
        "Dr. Reddy's Laboratories",
        "Netradyne",
        "Sarvam AI",
        "Shadowfax",
        "TCS"
    ]

    print("\n--- Live ATS Indian Company Extraction Samples ---")
    for comp_name in indian_samples:
        prof = catalog.get(comp_name)
        if not prof:
            print(f"[-] {comp_name}: NOT FOUND in catalog")
            continue
        ats = prof.ats_type
        ats_id = prof.ats_identifier
        if ats in ["greenhouse", "lever", "ashby", "smartrecruiters"]:
            try:
                jobs = scraper.get_company_jobs(comp_name)
                print(f"[+] {comp_name} ({ats} / {ats_id}): Success - {len(jobs)} live jobs extracted")
            except Exception as e:
                print(f"[-] {comp_name} ({ats} / {ats_id}): Failed - {e}")
        else:
            print(f"[~] {comp_name} ({ats}): Configured with career portal {prof.careers_url}")

if __name__ == "__main__":
    main()
