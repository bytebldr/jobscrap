"""Salary Normalization Pipeline for Indian and International Bands."""

import re
from typing import Optional
from jobscrap.core.models import SalaryRange

def parse_salary(text: Optional[str]) -> Optional[SalaryRange]:
    """Parse LPA, Lakhs, monthly rupees, or international salaries into a structured SalaryRange."""
    if not text:
        return None

    clean = text.lower().replace(",", "")
    
    # 1. Lakhs / LPA range (e.g. 12 - 20 LPA, 8 to 14 Lakhs)
    lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:lakh|lpa)", clean)
    if lakh_match:
        min_v = int(float(lakh_match.group(1)) * 100000)
        max_v = int(float(lakh_match.group(2)) * 100000)
        return SalaryRange(min_inr=min_v, max_inr=max_v, currency="INR", raw_text=text)

    # 2. Single Lakh / LPA (e.g. 15 LPA)
    single_lakh = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lpa)", clean)
    if single_lakh:
        val = int(float(single_lakh.group(1)) * 100000)
        return SalaryRange(min_inr=val, max_inr=val, currency="INR", raw_text=text)

    # 3. Rupee symbols (₹30,000 - ₹50,000 / month or annual)
    rupees = re.findall(r"(?:₹|rs\.?)\s*(\d+)", clean)
    if len(rupees) >= 2:
        v1, v2 = int(rupees[0]), int(rupees[1])
        if v1 < 100000:  # Monthly -> convert to annual
            v1, v2 = v1 * 12, v2 * 12
        return SalaryRange(min_inr=v1, max_inr=v2, currency="INR", raw_text=text)
    elif len(rupees) == 1:
        v = int(rupees[0])
        if v < 100000:
            v *= 12
        return SalaryRange(min_inr=v, max_inr=v, currency="INR", raw_text=text)

    return SalaryRange(raw_text=text)
