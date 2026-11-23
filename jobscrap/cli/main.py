"""JobScrap Modern Command-Line Interface."""

import argparse
import json
import sys
from jobscrap import CompanyCatalog, CompanyResolver, JobScraper

def main():
    parser = argparse.ArgumentParser(
        prog="jobscrap",
        description="JobScrap v0.5 — Autonomous Direct Company Career & ATS Job Scraper",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: company
    cmd_company = subparsers.add_parser("company", help="Fetch all active jobs directly from a company career portal")
    cmd_company.add_argument("name", help="Company name, domain, or token (e.g. 'Razorpay', 'Swiggy', 'zepto.com')")
    cmd_company.add_argument("--json", action="store_true", help="Output raw JSON array")

    # Command: search
    cmd_search = subparsers.add_parser("search", help="Search job openings across company career portals")
    cmd_search.add_argument("query", help="Job role / keyword (e.g. 'Software Engineer', 'Backend', 'Data')")
    cmd_search.add_argument("--location", "-l", help="Filter by location (e.g. 'Bengaluru', 'Remote')")
    cmd_search.add_argument("--limit", "-n", type=int, default=25, help="Maximum results to return")
    cmd_search.add_argument("--json", action="store_true", help="Output raw JSON array")

    # Command: catalog
    cmd_catalog = subparsers.add_parser("catalog", help="List pre-indexed companies in the catalog")
    cmd_catalog.add_argument("--query", "-q", help="Filter companies by name or tag")

    # Command: resolve
    cmd_resolve = subparsers.add_parser("resolve", help="Auto-fingerprint and resolve an unlisted company career portal")
    cmd_resolve.add_argument("domain", help="Company website or domain (e.g. 'cred.club', 'postman.com')")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    scraper = JobScraper()

    if args.command == "company":
        try:
            jobs = scraper.get_company_jobs(args.name)
            if args.json:
                print(json.dumps([j.to_dict() for j in jobs], indent=2))
            else:
                print(f"\n🎯 Found {len(jobs)} active primary jobs for '{args.name.upper()}':\n" + "=" * 65)
                for i, j in enumerate(jobs[:20], 1):
                    print(f"[{i:02d}] {j.title}")
                    print(f"     📍 Location: {j.location} | 🏢 Dept: {j.department or 'General'}")
                    print(f"     🔗 Direct Apply: {j.url}\n")
                if len(jobs) > 20:
                    print(f"... and {len(jobs) - 20} more jobs.")
        except Exception as e:
            print(f"❌ Error fetching company jobs: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "search":
        try:
            locs = [args.location] if args.location else None
            jobs = scraper.search_companies(query=args.query, locations=locs, limit=args.limit)
            if args.json:
                print(json.dumps([j.to_dict() for j in jobs], indent=2))
            else:
                print(f"\n🔍 Found {len(jobs)} live jobs across company career portals for '{args.query}':\n" + "=" * 70)
                for i, j in enumerate(jobs, 1):
                    print(f"[{i:02d}] {j.title} at {j.company}")
                    print(f"     📍 Location: {j.location}")
                    print(f"     🔗 Direct Apply: {j.url}\n")
        except Exception as e:
            print(f"❌ Error during company search: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "catalog":
        catalog = CompanyCatalog()
        companies = catalog.search(query=args.query) if args.query else catalog.all()
        print(f"\n📚 Pre-Indexed Companies ({len(companies)} total):\n" + "=" * 60)
        for c in companies:
            print(f"• {c.name:20s} | {c.industry:30s} | ATS: {c.ats_type:15s}")

    elif args.command == "resolve":
        resolver = CompanyResolver()
        try:
            profile = resolver.resolve(args.domain)
            print(f"\n✅ Resolved '{args.domain}':")
            print(f"• Name:       {profile.name}")
            print(f"• Domain:     {profile.domain}")
            print(f"• ATS Engine: {profile.ats_type}")
            print(f"• Token:      {profile.ats_identifier}")
            print(f"• Career URL: {profile.careers_url}")
        except Exception as e:
            print(f"❌ Could not resolve: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
