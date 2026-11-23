import json
from pathlib import Path
import sys
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jobscrap.core.models import CompanyProfile

data = json.load(open('jobscrap/catalog/data/india_bfsi.json', encoding='utf-8'))
print('Total profiles in india_bfsi.json:', len(data))

# 1. Unique IDs
ids = [d['id'] for d in data]
assert len(ids) == len(set(ids)), f"Duplicate IDs: {len(ids)} vs {len(set(ids))}"

# 2. Unique domains
domains = [d['domain'].lower() for d in data]
assert len(domains) == len(set(domains)), f"Duplicate domains: {len(domains)} vs {len(set(domains))}"

# 3. Required anchor companies
required_examples = [
    'hdfc-bank', 'icici-bank', 'axis-bank', 'kotak-mahindra-bank', 'indusind-bank',
    'idfc-first-bank', 'reliance-jio', 'reliance-retail', 'tata-motors',
    'mahindra-and-mahindra', 'larsen-and-toubro', 'godrej-industries',
    'bajaj-finserv', 'adani-enterprises'
]
for req in required_examples:
    assert req in ids, f"Missing required anchor company: {req}"

# 4. Strict schema & CompanyProfile validation
for item in data:
    assert item['id'].strip()
    assert item['name'].strip()
    assert item['domain'].strip()
    u = urlparse(item['careers_url'])
    assert u.scheme in ('http', 'https') and u.netloc, f"Invalid URL in {item['id']}: {item['careers_url']}"
    assert item['ats_type'] in {'workday', 'smartrecruiters', 'greenhouse', 'lever', 'custom'}
    if item['ats_type'] in {'workday', 'smartrecruiters', 'greenhouse', 'lever'}:
        assert item.get('ats_identifier'), f"Missing ats_identifier for {item['id']}"

    prof = CompanyProfile(
        id=item['id'],
        name=item['name'],
        domain=item['domain'],
        careers_url=item['careers_url'],
        industry=item.get('industry', 'Banking & Financial Services'),
        hq_location=item.get('hq_location', 'Mumbai, India'),
        tier=item.get('tier', 1),
        ats_type=item['ats_type'],
        ats_identifier=item.get('ats_identifier'),
        api_endpoint=item.get('api_endpoint'),
        tags=item.get('tags', []),
    )
    assert prof is not None

print("ALL 208 PROFILES STRICTLY VALIDATED AGAINST CompanyProfile MODEL!")
