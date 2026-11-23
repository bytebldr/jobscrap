"""Career Engine Signature Classifier and ATS Fingerprinter."""

import re
from typing import Optional, Tuple

def fingerprint_html(html_content: str, current_url: str = "") -> Tuple[Optional[str], Optional[str]]:
    """
    Inspects HTML markup and network redirect URL to detect underlying career engine and token.
    Returns: (engine_name, identifier) or (None, None)
    """
    text = html_content or ""
    combined = f"{current_url}\n{text}"

    # 1. Greenhouse Detection
    # e.g. boards.greenhouse.io/{token} or grnh.se or gh_src
    gh_match = re.search(r"boards\.greenhouse\.io/(?:embed/job_board\?for=|v1/boards/)?([a-zA-Z0-9_-]+)", combined, re.I)
    if gh_match:
        token = gh_match.group(1).split("/")[0].split("?")[0]
        if token not in ("embed", "v1", "job_board"):
            return "greenhouse", token

    if "greenhouse.io" in combined or "gh_src" in combined:
        token_match = re.search(r"for=([a-zA-Z0-9_-]+)", combined)
        if token_match:
            return "greenhouse", token_match.group(1)

    # 2. Lever Detection
    # e.g. jobs.lever.co/{token}
    lever_match = re.search(r"jobs\.lever\.co/([a-zA-Z0-9_-]+)", combined, re.I)
    if lever_match:
        token = lever_match.group(1).split("/")[0].split("?")[0]
        return "lever", token

    # 3. Ashby Detection
    # e.g. jobs.ashbyhq.com/{token}
    ashby_match = re.search(r"jobs\.ashbyhq\.com/([a-zA-Z0-9_-]+)", combined, re.I)
    if ashby_match:
        token = ashby_match.group(1).split("/")[0].split("?")[0]
        if token not in ("api", "graphql"):
            return "ashby", token

    # 4. SmartRecruiters Detection
    # e.g. jobs.smartrecruiters.com/{token}
    sr_match = re.search(r"jobs\.smartrecruiters\.com/([a-zA-Z0-9_-]+)", combined, re.I)
    if sr_match:
        token = sr_match.group(1).split("/")[0].split("?")[0]
        return "smartrecruiters", token

    # 5. Workday Detection
    # e.g. https://{tenant}.wd3.myworkdayjobs.com/
    wd_match = re.search(r"https?://([a-zA-Z0-9_-]+)\.wd\d*\.myworkdayjobs\.com", combined, re.I)
    if wd_match:
        tenant = wd_match.group(1)
        return "workday", tenant

    return None, None
