"""Harvest and live-verify Global Capability Centers (GCCs), MNC Tech Hubs,
and Global Remote Tech Firms hiring in India across Greenhouse, Lever, Ashby,
and SmartRecruiters.

Writes valid, live-verified CompanyProfile records to jobscrap/catalog/data/gcc.json.
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("harvest_gcc")

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "jobscrap" / "catalog" / "data" / "gcc.json"

INDIA_LOCATIONS = {
    "india", "bengaluru", "bangalore", "hyderabad", "pune", "gurugram",
    "gurgaon", "delhi", "mumbai", "chennai", "noida", "remote", "anywhere",
    "apac", "worldwide", "global"
}

# --- Curated Top GCCs, MNC Tech Hubs & Remote Tech Firms ---
CURATED_PROFILES: List[Dict[str, Any]] = [
    # Greenhouse
    {
        "id": "stripe", "name": "Stripe", "domain": "stripe.com",
        "careers_url": "https://stripe.com/jobs", "industry": "Fintech / Payments",
        "hq_location": "San Francisco, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "stripe",
        "tags": ["fintech", "payments", "gcc", "bengaluru", "global-tech"]
    },
    {
        "id": "coinbase", "name": "Coinbase", "domain": "coinbase.com",
        "careers_url": "https://www.coinbase.com/careers", "industry": "Crypto / Web3",
        "hq_location": "Remote / Hyderabad Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "coinbase",
        "tags": ["crypto", "web3", "remote", "hyderabad", "gcc"]
    },
    {
        "id": "cloudflare", "name": "Cloudflare", "domain": "cloudflare.com",
        "careers_url": "https://www.cloudflare.com/careers", "industry": "Cloud / Cybersecurity",
        "hq_location": "San Francisco, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "cloudflare",
        "tags": ["cloud", "cybersecurity", "cdn", "bengaluru", "gcc"]
    },
    {
        "id": "databricks", "name": "Databricks", "domain": "databricks.com",
        "careers_url": "https://databricks.com/company/careers", "industry": "Data / AI",
        "hq_location": "San Francisco, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "databricks",
        "tags": ["data", "ai", "lakehouse", "bengaluru", "gcc"]
    },
    {
        "id": "figma", "name": "Figma", "domain": "figma.com",
        "careers_url": "https://www.figma.com/careers", "industry": "Design Tools",
        "hq_location": "San Francisco, CA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "figma",
        "tags": ["design", "saas", "collaboration", "remote"]
    },
    {
        "id": "airbnb", "name": "Airbnb", "domain": "airbnb.com",
        "careers_url": "https://careers.airbnb.com", "industry": "Travel / Hospitality",
        "hq_location": "San Francisco, CA / Gurugram Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "airbnb",
        "tags": ["travel", "hospitality", "marketplace", "gurugram", "gcc"]
    },
    {
        "id": "reddit", "name": "Reddit", "domain": "reddit.com",
        "careers_url": "https://www.redditinc.com/careers", "industry": "Social Media",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "reddit",
        "tags": ["social", "community", "content", "remote"]
    },
    {
        "id": "pinterest", "name": "Pinterest", "domain": "pinterest.com",
        "careers_url": "https://www.pinterestcareers.com", "industry": "Social Media / Search",
        "hq_location": "San Francisco, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "pinterest",
        "tags": ["social", "search", "media", "bengaluru", "gcc"]
    },
    {
        "id": "affirm", "name": "Affirm", "domain": "affirm.com",
        "careers_url": "https://www.affirm.com/careers", "industry": "Fintech / BNPL",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "affirm",
        "tags": ["fintech", "bnpl", "payments", "remote"]
    },
    {
        "id": "brex", "name": "Brex", "domain": "brex.com",
        "careers_url": "https://www.brex.com/careers", "industry": "Fintech / Corporate Cards",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "brex",
        "tags": ["fintech", "banking", "cards", "remote"]
    },
    {
        "id": "samsara", "name": "Samsara", "domain": "samsara.com",
        "careers_url": "https://www.samsara.com/company/careers", "industry": "IoT / Connected Operations",
        "hq_location": "San Francisco, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "samsara",
        "tags": ["iot", "fleet", "hardware", "bengaluru", "gcc"]
    },
    {
        "id": "toast", "name": "Toast", "domain": "toasttab.com",
        "careers_url": "https://careers.toasttab.com", "industry": "Fintech / Restaurant Tech",
        "hq_location": "Boston, MA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "toast",
        "tags": ["restaurant", "pos", "fintech", "bengaluru", "gcc"]
    },
    {
        "id": "asana", "name": "Asana", "domain": "asana.com",
        "careers_url": "https://asana.com/jobs", "industry": "Productivity / SaaS",
        "hq_location": "San Francisco, CA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "asana",
        "tags": ["productivity", "collaboration", "saas", "remote"]
    },
    {
        "id": "twilio", "name": "Twilio", "domain": "twilio.com",
        "careers_url": "https://www.twilio.com/company/jobs", "industry": "Communications / CPaaS",
        "hq_location": "San Francisco, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "twilio",
        "tags": ["communications", "api", "cpaas", "bengaluru", "gcc"]
    },
    {
        "id": "okta", "name": "Okta", "domain": "okta.com",
        "careers_url": "https://www.okta.com/company/careers", "industry": "Identity / Cybersecurity",
        "hq_location": "San Francisco, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "okta",
        "tags": ["identity", "security", "saas", "bengaluru", "gcc"]
    },
    {
        "id": "mongodb", "name": "MongoDB", "domain": "mongodb.com",
        "careers_url": "https://www.mongodb.com/careers", "industry": "Database / Cloud",
        "hq_location": "New York, NY / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "mongodb",
        "tags": ["database", "nosql", "cloud", "bengaluru", "gcc"]
    },
    {
        "id": "robinhood", "name": "Robinhood", "domain": "robinhood.com",
        "careers_url": "https://robinhood.com/us/en/careers", "industry": "Fintech / Brokerage",
        "hq_location": "Menlo Park, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "robinhood",
        "tags": ["fintech", "trading", "investing", "remote"]
    },
    {
        "id": "grammarly", "name": "Grammarly", "domain": "grammarly.com",
        "careers_url": "https://www.grammarly.com/jobs", "industry": "AI / Productivity",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "grammarly",
        "tags": ["ai", "nlp", "saas", "remote"]
    },
    {
        "id": "dropbox", "name": "Dropbox", "domain": "dropbox.com",
        "careers_url": "https://jobs.dropbox.com", "industry": "Cloud Storage / SaaS",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "dropbox",
        "tags": ["storage", "cloud", "saas", "remote"]
    },
    {
        "id": "duolingo", "name": "Duolingo", "domain": "duolingo.com",
        "careers_url": "https://careers.duolingo.com", "industry": "EdTech / AI",
        "hq_location": "Pittsburgh, PA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "duolingo",
        "tags": ["edtech", "ai", "mobile", "remote"]
    },
    {
        "id": "scaleai", "name": "Scale AI", "domain": "scale.com",
        "careers_url": "https://scale.com/careers", "industry": "AI / Data Labeling",
        "hq_location": "San Francisco, CA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "scaleai",
        "tags": ["ai", "machine-learning", "data", "remote"]
    },
    {
        "id": "klaviyo", "name": "Klaviyo", "domain": "klaviyo.com",
        "careers_url": "https://www.klaviyo.com/careers", "industry": "Marketing Automation / SaaS",
        "hq_location": "Boston, MA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "klaviyo",
        "tags": ["marketing", "ecommerce", "saas", "remote"]
    },
    {
        "id": "purestorage", "name": "Pure Storage", "domain": "purestorage.com",
        "careers_url": "https://www.purestorage.com/company/careers.html", "industry": "Data Storage / Hardware",
        "hq_location": "Mountain View, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "purestorage",
        "tags": ["storage", "flash", "hardware", "bengaluru", "gcc"]
    },
    {
        "id": "crowdstrike", "name": "CrowdStrike", "domain": "crowdstrike.com",
        "careers_url": "https://www.crowdstrike.com/careers", "industry": "Cybersecurity",
        "hq_location": "Austin, TX / Pune Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "crowdstrike",
        "tags": ["security", "endpoint", "cloud-security", "pune", "gcc"]
    },
    {
        "id": "zscaler", "name": "Zscaler", "domain": "zscaler.com",
        "careers_url": "https://www.zscaler.com/careers", "industry": "Cybersecurity / Zero Trust",
        "hq_location": "San Jose, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "zscaler",
        "tags": ["security", "cloud-security", "zero-trust", "bengaluru", "gcc"]
    },
    {
        "id": "sentinelone", "name": "SentinelOne", "domain": "sentinelone.com",
        "careers_url": "https://www.sentinelone.com/careers", "industry": "Cybersecurity / AI",
        "hq_location": "Mountain View, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "sentinelone",
        "tags": ["security", "ai", "endpoint", "bengaluru", "gcc"]
    },
    {
        "id": "newrelic", "name": "New Relic", "domain": "newrelic.com",
        "careers_url": "https://newrelic.com/about/careers", "industry": "Observability / DevOps",
        "hq_location": "San Francisco, CA / Hyderabad Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "newrelic",
        "tags": ["observability", "apm", "monitoring", "hyderabad", "gcc"]
    },
    {
        "id": "pagerduty", "name": "PagerDuty", "domain": "pagerduty.com",
        "careers_url": "https://www.pagerduty.com/careers", "industry": "DevOps / Incident Management",
        "hq_location": "San Francisco, CA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "pagerduty",
        "tags": ["devops", "monitoring", "saas", "remote"]
    },
    {
        "id": "fastly", "name": "Fastly", "domain": "fastly.com",
        "careers_url": "https://www.fastly.com/careers", "industry": "Edge Cloud / CDN",
        "hq_location": "San Francisco, CA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "fastly",
        "tags": ["cdn", "edge", "cloud", "security", "remote"]
    },
    {
        "id": "confluent", "name": "Confluent", "domain": "confluent.io",
        "careers_url": "https://www.confluent.io/careers", "industry": "Data Streaming / Kafka",
        "hq_location": "Mountain View, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "confluent",
        "tags": ["kafka", "streaming", "data", "bengaluru", "gcc"]
    },
    {
        "id": "singlestore", "name": "SingleStore", "domain": "singlestore.com",
        "careers_url": "https://www.singlestore.com/careers", "industry": "Database / Real-Time",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "singlestore",
        "tags": ["database", "realtime", "sql", "remote"]
    },
    {
        "id": "cockroachlabs", "name": "Cockroach Labs", "domain": "cockroachlabs.com",
        "careers_url": "https://www.cockroachlabs.com/careers", "industry": "Database / Distributed SQL",
        "hq_location": "New York, NY / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "cockroachlabs",
        "tags": ["database", "distributed", "sql", "remote"]
    },
    {
        "id": "temporal", "name": "Temporal", "domain": "temporal.io",
        "careers_url": "https://temporal.io/careers", "industry": "Developer Tools / Workflows",
        "hq_location": "Bellevue, WA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "temporal",
        "tags": ["devtools", "workflows", "orchestration", "remote"]
    },
    {
        "id": "fivetran", "name": "Fivetran", "domain": "fivetran.com",
        "careers_url": "https://www.fivetran.com/careers", "industry": "Data Integration / ELT",
        "hq_location": "Oakland, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "fivetran",
        "tags": ["data", "elt", "pipelines", "bengaluru", "gcc"]
    },
    {
        "id": "airbyte", "name": "Airbyte", "domain": "airbyte.com",
        "careers_url": "https://airbyte.com/careers", "industry": "Data Integration / Open Source",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "airbyte",
        "tags": ["data", "open-source", "integration", "remote"]
    },
    {
        "id": "grafanalabs", "name": "Grafana Labs", "domain": "grafana.com",
        "careers_url": "https://grafana.com/about/careers", "industry": "Observability / Open Source",
        "hq_location": "New York, NY / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "grafanalabs",
        "tags": ["observability", "metrics", "open-source", "remote"]
    },
    {
        "id": "postman", "name": "Postman", "domain": "postman.com",
        "careers_url": "https://www.postman.com/careers", "industry": "API Platform / Developer Tools",
        "hq_location": "San Francisco, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "postman",
        "tags": ["api", "devtools", "testing", "bengaluru", "gcc"]
    },
    {
        "id": "launchdarkly", "name": "LaunchDarkly", "domain": "launchdarkly.com",
        "careers_url": "https://launchdarkly.com/careers", "industry": "Feature Management / DevOps",
        "hq_location": "Oakland, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "launchdarkly",
        "tags": ["devtools", "feature-flags", "devops", "remote"]
    },
    {
        "id": "snyk", "name": "Snyk", "domain": "snyk.io",
        "careers_url": "https://snyk.io/careers", "industry": "Cybersecurity / DevSecOps",
        "hq_location": "Boston, MA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "snyk",
        "tags": ["security", "devsecops", "open-source", "remote"]
    },
    {
        "id": "wiz", "name": "Wiz", "domain": "wiz.io",
        "careers_url": "https://www.wiz.io/careers", "industry": "Cloud Security",
        "hq_location": "New York, NY / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "wiz",
        "tags": ["cloud-security", "compliance", "cybersecurity", "remote"]
    },
    {
        "id": "1password", "name": "1Password", "domain": "1password.com",
        "careers_url": "https://1password.com/careers", "industry": "Cybersecurity / Vaults & Identity",
        "hq_location": "Toronto, Canada / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "1password",
        "tags": ["security", "vaults", "remote"]
    },
    {
        "id": "notion", "name": "Notion", "domain": "notion.so",
        "careers_url": "https://www.notion.so/careers", "industry": "Productivity / Knowledge Management",
        "hq_location": "San Francisco, CA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "notion",
        "tags": ["productivity", "workspace", "collaboration", "remote"]
    },
    {
        "id": "openai", "name": "OpenAI", "domain": "openai.com",
        "careers_url": "https://openai.com/careers", "industry": "AI / Frontier Models",
        "hq_location": "San Francisco, CA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "openai",
        "tags": ["ai", "llm", "chatgpt", "frontier-ai"]
    },
    {
        "id": "box", "name": "Box", "domain": "box.com",
        "careers_url": "https://www.box.com/careers", "industry": "Cloud Content Management",
        "hq_location": "Redwood City, CA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "box",
        "tags": ["cloud", "storage", "enterprise", "remote"]
    },
    {
        "id": "rubrik", "name": "Rubrik", "domain": "rubrik.com",
        "careers_url": "https://www.rubrik.com/company/careers", "industry": "Cloud Data Management",
        "hq_location": "Palo Alto, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "rubrik",
        "tags": ["security", "backup", "cloud", "bengaluru", "gcc"]
    },
    {
        "id": "cohesity", "name": "Cohesity", "domain": "cohesity.com",
        "careers_url": "https://www.cohesity.com/company/careers", "industry": "Data Security & Backup",
        "hq_location": "San Jose, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "cohesity",
        "tags": ["data", "backup", "security", "bengaluru", "gcc"]
    },
    {
        "id": "dremio", "name": "Dremio", "domain": "dremio.com",
        "careers_url": "https://www.dremio.com/careers", "industry": "Data Lakehouse / SQL",
        "hq_location": "Santa Clara, CA / Hyderabad Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "dremio",
        "tags": ["data", "sql", "lakehouse", "hyderabad", "gcc"]
    },
    {
        "id": "starburst", "name": "Starburst", "domain": "starburst.io",
        "careers_url": "https://www.starburst.io/careers", "industry": "Data Analytics / Trino",
        "hq_location": "Boston, MA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "starburst",
        "tags": ["data", "trino", "analytics", "bengaluru", "gcc"]
    },
    {
        "id": "yugabyte", "name": "Yugabyte", "domain": "yugabyte.com",
        "careers_url": "https://www.yugabyte.com/careers", "industry": "Distributed SQL Database",
        "hq_location": "Sunnyvale, CA / Pune Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "yugabyte",
        "tags": ["database", "postgres", "distributed", "pune", "gcc"]
    },
    {
        "id": "timescale", "name": "Timescale", "domain": "timescale.com",
        "careers_url": "https://www.timescale.com/careers", "industry": "Time-Series Database",
        "hq_location": "New York, NY / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "timescale",
        "tags": ["database", "timeseries", "postgres", "remote"]
    },
    {
        "id": "astronomer", "name": "Astronomer", "domain": "astronomer.io",
        "careers_url": "https://www.astronomer.io/careers", "industry": "Data Orchestration / Airflow",
        "hq_location": "New York, NY / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "astronomer",
        "tags": ["airflow", "orchestration", "data", "remote"]
    },
    {
        "id": "prefect", "name": "Prefect", "domain": "prefect.io",
        "careers_url": "https://www.prefect.io/careers", "industry": "Workflow Automation / Data",
        "hq_location": "Washington, DC / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "prefect",
        "tags": ["data", "workflow", "python", "remote"]
    },
    {
        "id": "montecarlo", "name": "Monte Carlo", "domain": "montecarlodata.com",
        "careers_url": "https://www.montecarlodata.com/careers", "industry": "Data Observability",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "montecarlo",
        "tags": ["data", "observability", "quality", "remote"]
    },
    {
        "id": "sourcegraph", "name": "Sourcegraph", "domain": "sourcegraph.com",
        "careers_url": "https://about.sourcegraph.com/jobs", "industry": "Code Intelligence / AI",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "sourcegraph",
        "tags": ["devtools", "code-search", "ai", "remote"]
    },
    {
        "id": "apollographql", "name": "Apollo GraphQL", "domain": "apollographql.com",
        "careers_url": "https://www.apollographql.com/careers", "industry": "GraphQL Platform",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "apollographql",
        "tags": ["graphql", "api", "devtools", "remote"]
    },
    {
        "id": "netlify", "name": "Netlify", "domain": "netlify.com",
        "careers_url": "https://www.netlify.com/careers", "industry": "Web Development Cloud",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "netlify",
        "tags": ["cloud", "jamstack", "frontend", "remote"]
    },
    {
        "id": "pulumi", "name": "Pulumi", "domain": "pulumi.com",
        "careers_url": "https://www.pulumi.com/careers", "industry": "Infrastructure as Code",
        "hq_location": "Seattle, WA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "pulumi",
        "tags": ["iac", "cloud", "devops", "remote"]
    },
    {
        "id": "circleci", "name": "CircleCI", "domain": "circleci.com",
        "careers_url": "https://circleci.com/careers", "industry": "CI/CD / DevOps",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "circleci",
        "tags": ["cicd", "devops", "cloud", "remote"]
    },
    {
        "id": "buildkite", "name": "Buildkite", "domain": "buildkite.com",
        "careers_url": "https://buildkite.com/careers", "industry": "CI/CD / Developer Tools",
        "hq_location": "Melbourne, Australia / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "buildkite",
        "tags": ["cicd", "devops", "developer-tools", "remote"]
    },
    {
        "id": "bitrise", "name": "Bitrise", "domain": "bitrise.io",
        "careers_url": "https://bitrise.io/careers", "industry": "Mobile CI/CD",
        "hq_location": "Budapest, Hungary / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "bitrise",
        "tags": ["mobile", "cicd", "devops", "remote"]
    },
    {
        "id": "codecov", "name": "Codecov", "domain": "codecov.io",
        "careers_url": "https://about.codecov.io/careers", "industry": "Code Coverage / DevSecOps",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "codecov",
        "tags": ["devtools", "testing", "coverage", "remote"]
    },
    {
        "id": "sonarsource", "name": "SonarSource", "domain": "sonarsource.com",
        "careers_url": "https://www.sonarsource.com/company/careers", "industry": "Clean Code / Static Analysis",
        "hq_location": "Geneva, Switzerland / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "sonarsource",
        "tags": ["devtools", "code-quality", "security", "remote"]
    },
    {
        "id": "veracode", "name": "Veracode", "domain": "veracode.com",
        "careers_url": "https://www.veracode.com/about/careers", "industry": "Application Security",
        "hq_location": "Burlington, MA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "veracode",
        "tags": ["appsec", "security", "sast", "dast", "remote"]
    },
    {
        "id": "checkmarx", "name": "Checkmarx", "domain": "checkmarx.com",
        "careers_url": "https://checkmarx.com/careers", "industry": "AppSec / SAST",
        "hq_location": "Ramat Gan, Israel / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "checkmarx",
        "tags": ["security", "appsec", "devsecops", "remote"]
    },
    {
        "id": "orcasecurity", "name": "Orca Security", "domain": "orca.security",
        "careers_url": "https://orca.security/careers", "industry": "Agentless Cloud Security",
        "hq_location": "Portland, OR / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "orcasecurity",
        "tags": ["cloud-security", "cybersecurity", "remote"]
    },
    {
        "id": "sysdig", "name": "Sysdig", "domain": "sysdig.com",
        "careers_url": "https://sysdig.com/company/careers", "industry": "Cloud / Container Security",
        "hq_location": "San Francisco, CA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "sysdig",
        "tags": ["containers", "kubernetes", "security", "remote"]
    },
    {
        "id": "aquasecurity", "name": "Aqua Security", "domain": "aquasec.com",
        "careers_url": "https://www.aquasec.com/about-us/careers", "industry": "Cloud Native Security",
        "hq_location": "Boston, MA / Hyderabad Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "aquasecurity",
        "tags": ["security", "kubernetes", "cloud-native", "hyderabad", "gcc"]
    },
    {
        "id": "cyberark", "name": "CyberArk", "domain": "cyberark.com",
        "careers_url": "https://www.cyberark.com/careers", "industry": "Identity Security / PAM",
        "hq_location": "Newton, MA / Hyderabad Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "cyberark",
        "tags": ["security", "identity", "pam", "hyderabad", "gcc"]
    },
    {
        "id": "sailpoint", "name": "SailPoint", "domain": "sailpoint.com",
        "careers_url": "https://www.sailpoint.com/company/careers", "industry": "Identity Governance",
        "hq_location": "Austin, TX / Pune Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "sailpoint",
        "tags": ["identity", "security", "governance", "pune", "gcc"]
    },
    {
        "id": "pingidentity", "name": "Ping Identity", "domain": "pingidentity.com",
        "careers_url": "https://www.pingidentity.com/en/company/careers.html", "industry": "Enterprise Identity",
        "hq_location": "Denver, CO / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "pingidentity",
        "tags": ["identity", "security", "sso", "bengaluru", "gcc"]
    },
    {
        "id": "jumpcloud", "name": "JumpCloud", "domain": "jumpcloud.com",
        "careers_url": "https://jumpcloud.com/careers", "industry": "Directory / Cloud IAM",
        "hq_location": "Louisville, CO / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "jumpcloud",
        "tags": ["identity", "directory", "cloud", "remote"]
    },
    {
        "id": "telesign", "name": "Telesign", "domain": "telesign.com",
        "careers_url": "https://www.telesign.com/careers", "industry": "Customer Identity / CPaaS",
        "hq_location": "Los Angeles, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "telesign",
        "tags": ["cpaas", "identity", "communications", "bengaluru", "gcc"]
    },
    {
        "id": "messagebird", "name": "MessageBird", "domain": "messagebird.com",
        "careers_url": "https://www.messagebird.com/careers", "industry": "Omnichannel Communications",
        "hq_location": "Amsterdam, Netherlands / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "messagebird",
        "tags": ["communications", "sms", "cpaas", "remote"]
    },
    {
        "id": "sinch", "name": "Sinch", "domain": "sinch.com",
        "careers_url": "https://www.sinch.com/careers", "industry": "Cloud Communications",
        "hq_location": "Stockholm, Sweden / Noida Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "sinch",
        "tags": ["communications", "messaging", "voice", "noida", "gcc"]
    },
    {
        "id": "infobip", "name": "Infobip", "domain": "infobip.com",
        "careers_url": "https://www.infobip.com/careers", "industry": "Omnichannel CPaaS",
        "hq_location": "Vodnjan, Croatia / Mumbai Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "infobip",
        "tags": ["communications", "messaging", "cpaas", "mumbai", "gcc"]
    },
    {
        "id": "vonage", "name": "Vonage", "domain": "vonage.com",
        "careers_url": "https://www.vonage.com/careers", "industry": "Cloud Communications",
        "hq_location": "Holmdel, NJ / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "vonage",
        "tags": ["communications", "cpaas", "voip", "bengaluru", "gcc"]
    },
    {
        "id": "sendbird", "name": "Sendbird", "domain": "sendbird.com",
        "careers_url": "https://sendbird.com/careers", "industry": "Conversational AI / Chat API",
        "hq_location": "San Mateo, CA / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "sendbird",
        "tags": ["chat", "messaging", "api", "bengaluru", "gcc"]
    },
    {
        "id": "stream", "name": "Stream", "domain": "getstream.io",
        "careers_url": "https://getstream.io/team", "industry": "Activity Feeds / Chat API",
        "hq_location": "Boulder, CO / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "stream",
        "tags": ["api", "chat", "feeds", "remote"]
    },
    {
        "id": "livekit", "name": "LiveKit", "domain": "livekit.io",
        "careers_url": "https://livekit.io/careers", "industry": "Real-Time Audio & Video WebRTC",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "livekit",
        "tags": ["webrtc", "video", "audio", "remote"]
    },
    {
        "id": "agora", "name": "Agora", "domain": "agora.io",
        "careers_url": "https://www.agora.io/en/careers", "industry": "Real-Time Engagement / RTC",
        "hq_location": "Santa Clara, CA / Global Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "agora",
        "tags": ["rtc", "voice", "video", "api", "remote"]
    },
    {
        "id": "bitwarden", "name": "Bitwarden", "domain": "bitwarden.com",
        "careers_url": "https://bitwarden.com/careers", "industry": "Credential Security & Vaults",
        "hq_location": "Santa Barbara, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "bitwarden",
        "tags": ["security", "vaults", "open-source", "remote"]
    },
    {
        "id": "dashlane", "name": "Dashlane", "domain": "dashlane.com",
        "careers_url": "https://www.dashlane.com/careers", "industry": "Access Management",
        "hq_location": "New York, NY / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "dashlane",
        "tags": ["security", "vaults", "remote"]
    },
    {
        "id": "nordsecurity", "name": "Nord Security", "domain": "nordsecurity.com",
        "careers_url": "https://nordsecurity.com/careers", "industry": "Cybersecurity / VPN",
        "hq_location": "Vilnius, Lithuania / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "nordsecurity",
        "tags": ["security", "vpn", "privacy", "remote"]
    },
    {
        "id": "proton", "name": "Proton", "domain": "proton.me",
        "careers_url": "https://proton.me/careers", "industry": "Privacy / Encrypted Mail",
        "hq_location": "Geneva, Switzerland / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "proton",
        "tags": ["privacy", "encryption", "email", "remote"]
    },
    {
        "id": "brave", "name": "Brave", "domain": "brave.com",
        "careers_url": "https://brave.com/careers", "industry": "Privacy Browser / Search",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "brave",
        "tags": ["browser", "privacy", "web3", "remote"]
    },
    {
        "id": "mozilla", "name": "Mozilla", "domain": "mozilla.org",
        "careers_url": "https://careers.mozilla.org", "industry": "Open Source Web / Firefox",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "mozilla",
        "tags": ["browser", "open-source", "web", "remote"]
    },
    {
        "id": "duckduckgo", "name": "DuckDuckGo", "domain": "duckduckgo.com",
        "careers_url": "https://duckduckgo.com/hiring", "industry": "Privacy Search Engine",
        "hq_location": "Paoli, PA / Remote Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "duckduckgo",
        "tags": ["privacy", "search", "remote"]
    },
    {
        "id": "suse", "name": "SUSE", "domain": "suse.com",
        "careers_url": "https://jobs.suse.com", "industry": "Enterprise Linux / Kubernetes",
        "hq_location": "Nuremberg, Germany / Bengaluru Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "suse",
        "tags": ["linux", "open-source", "containers", "bengaluru", "gcc"]
    },
    {
        "id": "redhat", "name": "Red Hat", "domain": "redhat.com",
        "careers_url": "https://www.redhat.com/en/jobs", "industry": "Enterprise Open Source",
        "hq_location": "Raleigh, NC / Pune Hub", "tier": 1,
        "ats_type": "greenhouse", "ats_identifier": "redhat",
        "tags": ["linux", "open-source", "cloud", "pune", "gcc"]
    },

    # --- Ashby ---
    {
        "id": "linear", "name": "Linear", "domain": "linear.app",
        "careers_url": "https://linear.app/careers", "industry": "Project Management / DevTools",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "linear",
        "tags": ["devtools", "project-management", "remote", "global-tech"]
    },
    {
        "id": "supabase", "name": "Supabase", "domain": "supabase.com",
        "careers_url": "https://supabase.com/careers", "industry": "Backend / Database",
        "hq_location": "Singapore / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "supabase",
        "tags": ["database", "postgres", "open-source", "remote", "global-tech"]
    },
    {
        "id": "sentry", "name": "Sentry", "domain": "sentry.io",
        "careers_url": "https://sentry.io/careers", "industry": "Developer Tools / Error Monitoring",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "sentry",
        "tags": ["devtools", "monitoring", "errors", "remote", "global-tech"]
    },
    {
        "id": "ramp", "name": "Ramp", "domain": "ramp.com",
        "careers_url": "https://ramp.com/careers", "industry": "Fintech / Spend Management",
        "hq_location": "New York, NY / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "ramp",
        "tags": ["fintech", "corporate-cards", "spend-management", "remote"]
    },
    {
        "id": "deel", "name": "Deel", "domain": "deel.com",
        "careers_url": "https://www.deel.com/careers", "industry": "HRTech / Global Payroll",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "deel",
        "tags": ["hrtech", "payroll", "compliance", "remote", "global-tech"]
    },
    {
        "id": "vercel", "name": "Vercel", "domain": "vercel.com",
        "careers_url": "https://vercel.com/careers", "industry": "Frontend Cloud / Developer Tools",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "vercel",
        "tags": ["frontend", "cloud", "nextjs", "remote", "global-tech"]
    },
    {
        "id": "anthropic", "name": "Anthropic", "domain": "anthropic.com",
        "careers_url": "https://www.anthropic.com/careers", "industry": "AI / Frontier Models",
        "hq_location": "San Francisco, CA / Global Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "anthropic",
        "tags": ["ai", "llm", "frontier-ai", "safety", "remote"]
    },
    {
        "id": "retool", "name": "Retool", "domain": "retool.com",
        "careers_url": "https://retool.com/careers", "industry": "Low-Code / Developer Tools",
        "hq_location": "San Francisco, CA / Global Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "retool",
        "tags": ["low-code", "devtools", "internal-tools", "remote"]
    },
    {
        "id": "remote", "name": "Remote", "domain": "remote.com",
        "careers_url": "https://remote.com/careers", "industry": "HRTech / Global Employment",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "remote",
        "tags": ["hrtech", "payroll", "remote", "global-tech"]
    },
    {
        "id": "webflow", "name": "Webflow", "domain": "webflow.com",
        "careers_url": "https://webflow.com/careers", "industry": "No-Code / Web Design",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "webflow",
        "tags": ["no-code", "cms", "design", "remote"]
    },
    {
        "id": "cohere", "name": "Cohere", "domain": "cohere.com",
        "careers_url": "https://cohere.com/careers", "industry": "Enterprise AI / LLM",
        "hq_location": "Toronto, Canada / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "cohere",
        "tags": ["ai", "llm", "nlp", "remote"]
    },
    {
        "id": "synthesia", "name": "Synthesia", "domain": "synthesia.io",
        "careers_url": "https://www.synthesia.io/careers", "industry": "AI Video Generation",
        "hq_location": "London, UK / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "synthesia",
        "tags": ["ai", "video", "creative", "remote"]
    },
    {
        "id": "runway", "name": "Runway", "domain": "runwayml.com",
        "careers_url": "https://runwayml.com/careers", "industry": "Generative AI / Media",
        "hq_location": "New York, NY / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "runway",
        "tags": ["ai", "genai", "creative", "remote"]
    },
    {
        "id": "deepgram", "name": "Deepgram", "domain": "deepgram.com",
        "careers_url": "https://deepgram.com/careers", "industry": "AI Speech Recognition / Voice",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "deepgram",
        "tags": ["ai", "speech", "voice", "remote"]
    },
    {
        "id": "elevenlabs", "name": "ElevenLabs", "domain": "elevenlabs.io",
        "careers_url": "https://elevenlabs.io/careers", "industry": "AI Voice Generation",
        "hq_location": "New York, NY / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "elevenlabs",
        "tags": ["ai", "audio", "voice", "remote"]
    },
    {
        "id": "pinecone", "name": "Pinecone", "domain": "pinecone.io",
        "careers_url": "https://www.pinecone.io/careers", "industry": "Vector Database / AI Infra",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "pinecone",
        "tags": ["ai", "vector-db", "search", "remote"]
    },
    {
        "id": "weaviate", "name": "Weaviate", "domain": "weaviate.io",
        "careers_url": "https://weaviate.io/company/careers", "industry": "Open Source Vector Database",
        "hq_location": "Amsterdam, Netherlands / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "weaviate",
        "tags": ["ai", "vector-db", "open-source", "remote"]
    },
    {
        "id": "qdrant", "name": "Qdrant", "domain": "qdrant.tech",
        "careers_url": "https://qdrant.tech/careers", "industry": "Vector Search Engine / AI",
        "hq_location": "Berlin, Germany / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "qdrant",
        "tags": ["ai", "vector-db", "search", "remote"]
    },
    {
        "id": "chroma", "name": "Chroma", "domain": "trychroma.com",
        "careers_url": "https://www.trychroma.com/careers", "industry": "AI Embedding Database",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "chroma",
        "tags": ["ai", "embeddings", "vector-db", "remote"]
    },
    {
        "id": "langchain", "name": "LangChain", "domain": "langchain.com",
        "careers_url": "https://www.langchain.com/careers", "industry": "LLM Application Framework",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "langchain",
        "tags": ["ai", "llm", "framework", "remote"]
    },
    {
        "id": "llamaindex", "name": "LlamaIndex", "domain": "llamaindex.ai",
        "careers_url": "https://www.llamaindex.ai/careers", "industry": "Data Framework for LLMs",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "llamaindex",
        "tags": ["ai", "llm", "data", "remote"]
    },
    {
        "id": "posthog", "name": "PostHog", "domain": "posthog.com",
        "careers_url": "https://posthog.com/careers", "industry": "Product Analytics / Open Source",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "posthog",
        "tags": ["analytics", "product", "open-source", "remote"]
    },
    {
        "id": "prisma", "name": "Prisma", "domain": "prisma.io",
        "careers_url": "https://www.prisma.io/careers", "industry": "Next-Gen ORM / Database",
        "hq_location": "Berlin, Germany / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "prisma",
        "tags": ["orm", "database", "typescript", "remote"]
    },
    {
        "id": "resend", "name": "Resend", "domain": "resend.com",
        "careers_url": "https://resend.com/careers", "industry": "Email API for Developers",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "resend",
        "tags": ["email", "api", "developer-tools", "remote"]
    },
    {
        "id": "clerk", "name": "Clerk", "domain": "clerk.com",
        "careers_url": "https://clerk.com/careers", "industry": "Authentication & User Management",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "clerk",
        "tags": ["auth", "security", "react", "remote"]
    },
    {
        "id": "raycast", "name": "Raycast", "domain": "raycast.com",
        "careers_url": "https://www.raycast.com/careers", "industry": "Productivity / Launcher",
        "hq_location": "London, UK / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "raycast",
        "tags": ["productivity", "macos", "devtools", "remote"]
    },
    {
        "id": "loops", "name": "Loops", "domain": "loops.so",
        "careers_url": "https://loops.so/careers", "industry": "Email Platform for SaaS",
        "hq_location": "New York, NY / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "loops",
        "tags": ["email", "marketing", "saas", "remote"]
    },
    {
        "id": "render", "name": "Render", "domain": "render.com",
        "careers_url": "https://render.com/careers", "industry": "Cloud Application Hosting",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "render",
        "tags": ["cloud", "hosting", "devops", "remote"]
    },
    {
        "id": "railway", "name": "Railway", "domain": "railway.app",
        "careers_url": "https://railway.app/careers", "industry": "Infrastructure Deployment",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "railway",
        "tags": ["cloud", "infrastructure", "devops", "remote"]
    },
    {
        "id": "fly", "name": "Fly.io", "domain": "fly.io",
        "careers_url": "https://fly.io/jobs", "industry": "Global Application Platform",
        "hq_location": "Chicago, IL / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "fly",
        "tags": ["cloud", "edge", "infrastructure", "remote"]
    },
    {
        "id": "modal", "name": "Modal", "domain": "modal.com",
        "careers_url": "https://modal.com/careers", "industry": "Serverless Cloud for AI",
        "hq_location": "New York, NY / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "modal",
        "tags": ["ai", "serverless", "cloud", "remote"]
    },
    {
        "id": "together", "name": "Together AI", "domain": "together.ai",
        "careers_url": "https://www.together.ai/careers", "industry": "Cloud for AI Inference",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "together",
        "tags": ["ai", "cloud", "inference", "remote"]
    },
    {
        "id": "fireworks", "name": "Fireworks AI", "domain": "fireworks.ai",
        "careers_url": "https://fireworks.ai/careers", "industry": "Fast AI Inference Platform",
        "hq_location": "San Mateo, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "fireworks",
        "tags": ["ai", "llm", "inference", "remote"]
    },
    {
        "id": "baseten", "name": "Baseten", "domain": "baseten.co",
        "careers_url": "https://www.baseten.co/careers", "industry": "Machine Learning Infrastructure",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "baseten",
        "tags": ["ai", "mlops", "cloud", "remote"]
    },
    {
        "id": "replicate", "name": "Replicate", "domain": "replicate.com",
        "careers_url": "https://replicate.com/careers", "industry": "AI Model Cloud API",
        "hq_location": "San Francisco, CA / Remote Hub", "tier": 1,
        "ats_type": "ashby", "ats_identifier": "replicate",
        "tags": ["ai", "ml", "api", "remote"]
    },

    # --- Lever ---
    {
        "id": "spotify", "name": "Spotify", "domain": "spotify.com",
        "careers_url": "https://www.lifeatspotify.com", "industry": "Music / Audio Streaming",
        "hq_location": "Stockholm, Sweden / Mumbai Hub", "tier": 1,
        "ats_type": "lever", "ats_identifier": "spotify",
        "tags": ["music", "streaming", "media", "mumbai", "gcc"]
    },
    {
        "id": "palantir", "name": "Palantir", "domain": "palantir.com",
        "careers_url": "https://www.palantir.com/careers", "industry": "Big Data / Defense Tech",
        "hq_location": "Denver, CO / Global Hub", "tier": 1,
        "ats_type": "lever", "ats_identifier": "palantir",
        "tags": ["big-data", "analytics", "ai", "defense", "remote"]
    },
    {
        "id": "benchling", "name": "Benchling", "domain": "benchling.com",
        "careers_url": "https://www.benchling.com/careers", "industry": "Life Sciences R&D Cloud",
        "hq_location": "San Francisco, CA / Global Hub", "tier": 1,
        "ats_type": "lever", "ats_identifier": "benchling",
        "tags": ["biotech", "cloud", "saas", "remote"]
    },
    {
        "id": "revolut", "name": "Revolut", "domain": "revolut.com",
        "careers_url": "https://www.revolut.com/careers", "industry": "Fintech / NeoBanking",
        "hq_location": "London, UK / Bengaluru Hub", "tier": 1,
        "ats_type": "lever", "ats_identifier": "revolut",
        "tags": ["fintech", "banking", "payments", "bengaluru", "gcc"]
    },
    {
        "id": "klarna", "name": "Klarna", "domain": "klarna.com",
        "careers_url": "https://www.klarna.com/careers", "industry": "Fintech / BNPL & Payments",
        "hq_location": "Stockholm, Sweden / Global Hub", "tier": 1,
        "ats_type": "lever", "ats_identifier": "klarna",
        "tags": ["fintech", "payments", "bnpl", "remote"]
    },
    {
        "id": "checkout", "name": "Checkout.com", "domain": "checkout.com",
        "careers_url": "https://www.checkout.com/careers", "industry": "Global Payment Processing",
        "hq_location": "London, UK / Global Hub", "tier": 1,
        "ats_type": "lever", "ats_identifier": "checkout",
        "tags": ["fintech", "payments", "gateway", "remote"]
    },
    {
        "id": "bolt", "name": "Bolt", "domain": "bolt.eu",
        "careers_url": "https://bolt.eu/careers", "industry": "Mobility / Ride Hailing",
        "hq_location": "Tallinn, Estonia / Global Hub", "tier": 1,
        "ats_type": "lever", "ats_identifier": "bolt",
        "tags": ["mobility", "delivery", "transport", "remote"]
    },
    {
        "id": "grab", "name": "Grab", "domain": "grab.com",
        "careers_url": "https://grab.careers", "industry": "SuperApp / Mobility / Fintech",
        "hq_location": "Singapore / Bengaluru R&D Hub", "tier": 1,
        "ats_type": "lever", "ats_identifier": "grab",
        "tags": ["superapp", "mobility", "fintech", "bengaluru", "gcc"]
    },
    {
        "id": "gojek", "name": "Gojek", "domain": "gojek.com",
        "careers_url": "https://www.gojek.io/careers", "industry": "On-Demand Services / SuperApp",
        "hq_location": "Jakarta, Indonesia / Bengaluru Tech Hub", "tier": 1,
        "ats_type": "lever", "ats_identifier": "gojek",
        "tags": ["superapp", "on-demand", "transport", "bengaluru", "gcc"]
    },
    {
        "id": "hopper", "name": "Hopper", "domain": "hopper.com",
        "careers_url": "https://www.hopper.com/careers", "industry": "Travel / FinTech",
        "hq_location": "Montreal, Canada / Remote Hub", "tier": 1,
        "ats_type": "lever", "ats_identifier": "hopper",
        "tags": ["travel", "fintech", "mobile", "remote"]
    },

    # --- SmartRecruiters ---
    {
        "id": "bosch", "name": "Bosch Group", "domain": "bosch.com",
        "careers_url": "https://www.bosch.in/careers", "industry": "Automotive & Industrial Tech",
        "hq_location": "Gerlingen, Germany / Bengaluru & Pune Hubs", "tier": 1,
        "ats_type": "smartrecruiters", "ats_identifier": "BoschGroup",
        "tags": ["automotive", "iot", "industrial", "bengaluru", "pune", "gcc"]
    },
    {
        "id": "konecranes", "name": "Konecranes", "domain": "konecranes.com",
        "careers_url": "https://www.konecranes.com/careers", "industry": "Industrial Machinery & Automation",
        "hq_location": "Hyvinkaa, Finland / Pune Tech Center", "tier": 1,
        "ats_type": "smartrecruiters", "ats_identifier": "Konecranes",
        "tags": ["industrial", "automation", "pune", "gcc"]
    },
    {
        "id": "redbull", "name": "Red Bull", "domain": "redbull.com",
        "careers_url": "https://jobs.redbull.com", "industry": "Consumer / Media & Tech",
        "hq_location": "Fuschl, Austria / Mumbai Hub", "tier": 1,
        "ats_type": "smartrecruiters", "ats_identifier": "RedBull",
        "tags": ["consumer", "media", "sports", "mumbai", "gcc"]
    },
    {
        "id": "freshworks", "name": "Freshworks", "domain": "freshworks.com",
        "careers_url": "https://www.freshworks.com/company/careers", "industry": "CRM / Customer Support SaaS",
        "hq_location": "San Mateo, CA / Chennai & Bengaluru Hubs", "tier": 1,
        "ats_type": "smartrecruiters", "ats_identifier": "Freshworks",
        "tags": ["saas", "crm", "support", "chennai", "bengaluru", "gcc"]
    },
    {
        "id": "sodexo", "name": "Sodexo", "domain": "sodexo.com",
        "careers_url": "https://www.sodexo.com/careers", "industry": "Food & Facilities Tech",
        "hq_location": "Issy-les-Moulineaux, France / Mumbai Hub", "tier": 1,
        "ats_type": "smartrecruiters", "ats_identifier": "Sodexo",
        "tags": ["enterprise", "services", "mumbai", "gcc"]
    },
]

def format_company_name(slug: str) -> str:
    parts = re.split(r"[-_]", slug)
    return " ".join(p.capitalize() for p in parts if p)

def determine_industry_from_name(name: str) -> str:
    name_l = name.lower()
    if any(k in name_l for k in ["pay", "bank", "credit", "fin", "capital", "fund"]):
        return "Fintech / Financial Services"
    if any(k in name_l for k in ["sec", "cyber", "guard", "safe", "shield"]):
        return "Cybersecurity"
    if any(k in name_l for k in ["data", "ai", "intel", "ml", "metric", "graph"]):
        return "Data / AI Platform"
    if any(k in name_l for k in ["cloud", "dev", "code", "ops", "tool", "stack"]):
        return "Developer Tools / Cloud"
    if any(k in name_l for k in ["health", "bio", "med", "cure"]):
        return "HealthTech / BioTech"
    if any(k in name_l for k in ["shop", "market", "commerce", "store"]):
        return "E-Commerce / Consumer Tech"
    return "Enterprise Software / SaaS"

def determine_location(loc_names: List[str]) -> str:
    joined = " ".join(loc_names).lower()
    if "bengaluru" in joined or "bangalore" in joined:
        return "Bengaluru Hub / Global GCC"
    if "hyderabad" in joined:
        return "Hyderabad Hub / Global GCC"
    if "pune" in joined:
        return "Pune Hub / Global GCC"
    if "gurugram" in joined or "gurgaon" in joined or "delhi" in joined:
        return "Gurugram / NCR Hub"
    if "mumbai" in joined:
        return "Mumbai Tech Center"
    if "chennai" in joined:
        return "Chennai Tech Center"
    if "noida" in joined:
        return "Noida Tech Center"
    if "india" in joined:
        return "India Tech Hub"
    return "Global Remote / Tech Hub"

async def verify_greenhouse(
    client: httpx.AsyncClient, slug: str, sem: asyncio.Semaphore
) -> Optional[Tuple[str, List[str], int]]:
    async with sem:
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
        try:
            r = await client.get(url, timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                jobs = data.get("jobs", [])
                if jobs:
                    locs = [
                        (j.get("location") or {}).get("name", "")
                        for j in jobs if isinstance(j.get("location"), dict)
                    ]
                    return slug, locs, len(jobs)
        except Exception:
            pass
        return None

async def verify_ashby(
    client: httpx.AsyncClient, slug: str, sem: asyncio.Semaphore
) -> Optional[Tuple[str, List[str], int]]:
    async with sem:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
        try:
            r = await client.get(url, timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                jobs = data.get("jobs", [])
                if jobs:
                    locs = [j.get("location", "") for j in jobs if j.get("location")]
                    return slug, locs, len(jobs)
        except Exception:
            pass
        return None

async def verify_lever(
    client: httpx.AsyncClient, slug: str, sem: asyncio.Semaphore
) -> Optional[Tuple[str, List[str], int]]:
    async with sem:
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        try:
            r = await client.get(url, timeout=4.0)
            if r.status_code == 200 and isinstance(r.json(), list):
                postings = r.json()
                if postings:
                    locs = [
                        (p.get("categories") or {}).get("location", "")
                        for p in postings if isinstance(p.get("categories"), dict)
                    ]
                    return slug, locs, len(postings)
        except Exception:
            pass
        return None

async def verify_smartrecruiters(
    client: httpx.AsyncClient, slug: str, sem: asyncio.Semaphore
) -> Optional[Tuple[str, List[str], int]]:
    async with sem:
        url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=10"
        try:
            r = await client.get(url, timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                content = data.get("content", [])
                if content:
                    locs = [
                        (c.get("location") or {}).get("city", "")
                        for c in content if isinstance(c.get("location"), dict)
                    ]
                    return slug, locs, len(content)
        except Exception:
            pass
        return None

async def harvest_all():
    logger.info("Starting GCC, MNC Tech Hub, and Remote Tech Firm harvesting...")
    limits = httpx.Limits(max_keepalive_connections=80, max_connections=120)
    sem = asyncio.Semaphore(60)

    verified_profiles: Dict[str, Dict[str, Any]] = {}

    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        # Phase 1: Live-verify Curated Seed Profiles concurrently
        logger.info(f"Phase 1: Live verifying {len(CURATED_PROFILES)} curated GCC seed profiles...")
        curated_coros = []
        for p in CURATED_PROFILES:
            ats = p["ats_type"]
            slug = p["ats_identifier"]
            if ats == "greenhouse":
                curated_coros.append((p, verify_greenhouse(client, slug, sem)))
            elif ats == "ashby":
                curated_coros.append((p, verify_ashby(client, slug, sem)))
            elif ats == "lever":
                curated_coros.append((p, verify_lever(client, slug, sem)))
            elif ats == "smartrecruiters":
                curated_coros.append((p, verify_smartrecruiters(client, slug, sem)))

        results = await asyncio.gather(*[c[1] for c in curated_coros])
        for (prof, _), res in zip(curated_coros, results):
            if res is not None:
                title, locs, job_count = res
                prof_copy = dict(prof)
                prof_copy["is_verified"] = True
                if prof_copy["ats_type"] == "greenhouse":
                    prof_copy["api_endpoint"] = f"https://boards-api.greenhouse.io/v1/boards/{prof_copy['ats_identifier']}/jobs?content=true"
                elif prof_copy["ats_type"] == "ashby":
                    prof_copy["api_endpoint"] = f"https://api.ashbyhq.com/posting-api/job-board/{prof_copy['ats_identifier']}"
                elif prof_copy["ats_type"] == "lever":
                    prof_copy["api_endpoint"] = f"https://api.lever.co/v0/postings/{prof_copy['ats_identifier']}?mode=json"
                elif prof_copy["ats_type"] == "smartrecruiters":
                    prof_copy["api_endpoint"] = f"https://api.smartrecruiters.com/v1/companies/{prof_copy['ats_identifier']}/postings?limit=100"

                verified_profiles[prof_copy["id"]] = prof_copy

        logger.info(f"Phase 1 Complete: {len(verified_profiles)} curated profiles verified.")

        # Phase 2: Pull external candidate pools
        logger.info("Phase 2: Pulling extended ATS candidates from public job datasets...")
        base = "https://raw.githubusercontent.com/Riley-Dorrington/job-board-aggregator/main/"
        try:
            gh_req = await client.get(base + "data/greenhouse_companies.json", timeout=10.0)
            ashby_req = await client.get(base + "data/ashby_companies.json", timeout=10.0)
            lever_req = await client.get(base + "data/lever_companies.json", timeout=10.0)
            gh_candidates = gh_req.json() if gh_req.status_code == 200 else []
            ashby_candidates = ashby_req.json() if ashby_req.status_code == 200 else []
            lever_candidates = lever_req.json() if lever_req.status_code == 200 else []
        except Exception as e:
            logger.warning(f"Could not fetch external candidate datasets: {e}")
            gh_candidates, ashby_candidates, lever_candidates = [], [], []

        logger.info(f"External pools loaded: GH={len(gh_candidates)}, Ashby={len(ashby_candidates)}, Lever={len(lever_candidates)}")

        existing_identifiers = {p["ats_identifier"].lower() for p in verified_profiles.values()}

        # Phase 3: Probe and Validate Ashby Candidates in Parallel
        logger.info("Phase 3: Probing and validating Ashby candidates in parallel...")
        ashby_pool = [c for c in ashby_candidates if c.lower() not in existing_identifiers][:600]
        ashby_results = await asyncio.gather(*[verify_ashby(client, s, sem) for s in ashby_pool])

        for slug, res in zip(ashby_pool, ashby_results):
            if res is not None:
                name, locs, job_count = res
                is_india_remote = any(
                    any(k in l.lower() for k in INDIA_LOCATIONS)
                    for l in locs
                )
                if is_india_remote or job_count >= 5:
                    comp_id = re.sub(r"[^a-z0-9]", "", slug.lower())
                    if comp_id and comp_id not in verified_profiles:
                        display_name = format_company_name(slug)
                        location = determine_location(locs)
                        industry = determine_industry_from_name(display_name)
                        tags = ["ashby", "remote", "global-tech"]
                        if "india" in location.lower() or "bengaluru" in location.lower():
                            tags.append("india-hiring")
                        
                        verified_profiles[comp_id] = {
                            "id": comp_id,
                            "name": display_name,
                            "domain": f"{comp_id}.com",
                            "careers_url": f"https://jobs.ashbyhq.com/{slug}",
                            "industry": industry,
                            "hq_location": location,
                            "tier": 1 if job_count >= 10 else 2,
                            "ats_type": "ashby",
                            "ats_identifier": slug,
                            "api_endpoint": f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
                            "is_verified": True,
                            "tags": tags
                        }

        logger.info(f"Total verified after Ashby: {len(verified_profiles)}")

        # Phase 4: Probe and Validate Greenhouse Candidates in Parallel
        logger.info("Phase 4: Probing and validating Greenhouse candidates in parallel...")
        gh_pool = [c for c in gh_candidates if c.lower() not in existing_identifiers][:1200]
        gh_results = await asyncio.gather(*[verify_greenhouse(client, s, sem) for s in gh_pool])

        for slug, res in zip(gh_pool, gh_results):
            if res is not None:
                title, locs, job_count = res
                is_india_remote = any(
                    any(k in l.lower() for k in INDIA_LOCATIONS)
                    for l in locs
                )
                if is_india_remote or job_count >= 8:
                    comp_id = re.sub(r"[^a-z0-9]", "", slug.lower())
                    if comp_id and comp_id not in verified_profiles:
                        display_name = format_company_name(slug)
                        location = determine_location(locs)
                        industry = determine_industry_from_name(display_name)
                        tags = ["greenhouse", "gcc", "global-tech"]
                        if "bengaluru" in location.lower():
                            tags.append("bengaluru")
                        elif "hyderabad" in location.lower():
                            tags.append("hyderabad")
                        elif "pune" in location.lower():
                            tags.append("pune")
                        elif "india" in location.lower():
                            tags.append("india-hiring")

                        verified_profiles[comp_id] = {
                            "id": comp_id,
                            "name": display_name,
                            "domain": f"{comp_id}.com",
                            "careers_url": f"https://boards.greenhouse.io/{slug}",
                            "industry": industry,
                            "hq_location": location,
                            "tier": 1 if job_count >= 15 else 2,
                            "ats_type": "greenhouse",
                            "ats_identifier": slug,
                            "api_endpoint": f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
                            "is_verified": True,
                            "tags": tags
                        }

        logger.info(f"Total verified after Greenhouse: {len(verified_profiles)}")

        # Phase 5: Probe and Validate Lever Candidates in Parallel
        logger.info("Phase 5: Probing and validating Lever candidates in parallel...")
        lever_pool = [c for c in lever_candidates if c.lower() not in existing_identifiers][:500]
        lever_results = await asyncio.gather(*[verify_lever(client, s, sem) for s in lever_pool])

        for slug, res in zip(lever_pool, lever_results):
            if res is not None:
                name, locs, job_count = res
                is_india_remote = any(
                    any(k in l.lower() for k in INDIA_LOCATIONS)
                    for l in locs
                )
                if is_india_remote or job_count >= 5:
                    comp_id = re.sub(r"[^a-z0-9]", "", slug.lower())
                    if comp_id and comp_id not in verified_profiles:
                        display_name = format_company_name(slug)
                        location = determine_location(locs)
                        industry = determine_industry_from_name(display_name)
                        tags = ["lever", "gcc", "global-tech"]
                        if "bengaluru" in location.lower():
                            tags.append("bengaluru")

                        verified_profiles[comp_id] = {
                            "id": comp_id,
                            "name": display_name,
                            "domain": f"{comp_id}.com",
                            "careers_url": f"https://jobs.lever.co/{slug}",
                            "industry": industry,
                            "hq_location": location,
                            "tier": 1 if job_count >= 15 else 2,
                            "ats_type": "lever",
                            "ats_identifier": slug,
                            "api_endpoint": f"https://api.lever.co/v0/postings/{slug}?mode=json",
                            "is_verified": True,
                            "tags": tags
                        }

        logger.info(f"Total verified after Lever: {len(verified_profiles)}")

    # Sort profiles alphabetically by name
    output_records = sorted(verified_profiles.values(), key=lambda x: x["name"].lower())
    
    # Ensure directory exists and write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_records, f, indent=2)

    logger.info(f"Successfully wrote {len(output_records)} live-verified GCC company profiles to {OUTPUT_PATH}")

    # Summary breakdown
    by_ats = {}
    by_tier = {}
    for r in output_records:
        at = r["ats_type"]
        by_ats[at] = by_ats.get(at, 0) + 1
        t = r["tier"]
        by_tier[t] = by_tier.get(t, 0) + 1

    logger.info(f"ATS Breakdown: {by_ats}")
    logger.info(f"Tier Breakdown: {by_tier}")
    return output_records

if __name__ == "__main__":
    records = asyncio.run(harvest_all())
    print(f"\nHARVEST COMPLETE: {len(records)} verified companies written to {OUTPUT_PATH}")
