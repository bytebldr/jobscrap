import sys
sys.path.insert(0, ".")
import json
from jobscrap.core.models import CompanyProfile

def main():
    with open("jobscrap/catalog/data/gcc.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Total companies in gcc.json: {len(data)}")

    # Schema Validation
    ats_counts = {}
    tier_counts = {}
    for i, item in enumerate(data):
        cp = CompanyProfile(**item)
        assert cp.id, f"Missing id at {i}"
        assert cp.name, f"Missing name at {i}"
        assert cp.domain, f"Missing domain at {i}"
        assert cp.careers_url, f"Missing careers_url at {i}"
        assert cp.ats_type in ["greenhouse", "ashby", "lever", "smartrecruiters"], f"Unknown ats_type {cp.ats_type} at {i}"
        assert cp.ats_identifier, f"Missing ats_identifier at {i}"
        assert cp.api_endpoint, f"Missing api_endpoint at {i}"
        assert cp.is_verified is True
        ats_counts[cp.ats_type] = ats_counts.get(cp.ats_type, 0) + 1
        tier_counts[cp.tier] = tier_counts.get(cp.tier, 0) + 1

    print("All records strictly match CompanyProfile schema!")
    print(f"ATS Breakdown: {ats_counts}")
    print(f"Tier Breakdown: {tier_counts}")

    print("\nSpot check key companies requested in brief:")
    for target in ["stripe", "coinbase", "cloudflare", "databricks", "linear", "supabase", "spotify", "bosch"]:
        matches = [c for c in data if c["id"] == target or target in c["id"]]
        if matches:
            c = matches[0]
            print(f"  [{c['ats_type']}] {c['name']} (ID: {c['id']}) - {c['hq_location']} | Endpoint: {c['api_endpoint'][:60]}...")

if __name__ == "__main__":
    main()
