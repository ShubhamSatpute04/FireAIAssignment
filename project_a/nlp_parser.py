"""
Natural Language (English / Hinglish) Parser for Taxpayer Profiles.
Translates colloquial English and Hinglish salary, deduction, and rent expressions
into structured TaxPayerProfile objects.
"""

import re
import os
from typing import Dict, Any, Tuple, Optional
from project_a.models import TaxPayerProfile


METRO_CITIES = {
    "mumbai", "bombay", "delhi", "new delhi", "ncr", "kolkata", "calcutta", "chennai", "madras"
}


def parse_indian_currency_number(text: str) -> Optional[float]:
    """
    Parses numbers in Indian notation, e.g.:
    - '12 lakh', '12L', '12.5 Lacs', '12 lac' -> 1,200,000
    - '1.5 Cr', '2 crore' -> 15,000,000 / 20,000,000
    - '50 hazar', '50k', '50,000' -> 50,000
    - '18 LPA' -> 1,800,000
    """
    clean = text.lower().strip().replace(",", "")

    # Crore
    cr_match = re.search(r"([\d\.]+)\s*(?:cr|crore|crores)", clean)
    if cr_match:
        return float(cr_match.group(1)) * 10000000.0

    # Lakh / LPA
    lakh_match = re.search(r"([\d\.]+)\s*(?:lakh|lakhs|lac|lacs|lpa|l\b)", clean)
    if lakh_match:
        return float(lakh_match.group(1)) * 100000.0

    # Hazar / k
    k_match = re.search(r"([\d\.]+)\s*(?:k|hazar|thousand)", clean)
    if k_match:
        return float(k_match.group(1)) * 1000.0

    # Raw digits
    raw_match = re.search(r"([\d]+)", clean)
    if raw_match:
        return float(raw_match.group(1))

    return None


class HinglishTaxParser:
    """
    Parser for English and Hinglish tax queries.
    Combines rule-based regex entity extractors with optional Gemini LLM parsing.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")

    def parse(self, text: str, default_fy: str = "FY 2024-25") -> TaxPayerProfile:
        """
        Parses text query into structured TaxPayerProfile.
        """
        lower = text.lower()

        # 1. Financial Year
        fy = default_fy
        if "2025-26" in lower or "25-26" in lower:
            fy = "FY 2025-26"
        elif "2024-25" in lower or "24-25" in lower:
            fy = "FY 2024-25"

        # 2. Gross / Annual Salary / CTC
        gross_salary = 0.0
        # Check patterns like "gross salary 12 lakh", "salary 15 lpa", "ctc 20 lakh", "meri salary 10L hai"
        salary_patterns = [
            r"(?:gross(?:\s*salary|\s*pension)?|ctc|package|salary|pension|meri\s*salary|kamata\s*hu|earn|earns|earning|get|gets)\s*(?:is|hai|of|:|=|around)?\s*([0-9\.]+\s*(?:cr|crore|lakh|lakhs|lac|lacs|lpa|l|k|hazar|thousand)?(?:\s*per\s*annum|\s*salana|\s*yearly|\s*per\s*month|\s*pm)?)",
            r"([0-9\.]+\s*(?:lpa|lakh|lacs|cr|crore))\s*(?:ctc|salary|gross|package|pension|per\s*annum)?",
            r"(?:income|kamai)\s*(?:hai|is)?\s*([0-9\.]+\s*(?:lakh|lacs|lac|l|k|cr|crore))"
        ]
        for pat in salary_patterns:
            m = re.search(pat, lower)
            if m:
                matched_str = m.group(1)
                val = parse_indian_currency_number(matched_str)
                if val:
                    # check if per month was specified
                    if "per month" in matched_str or "pm" in matched_str or "per month" in lower[m.start():m.end()+25]:
                        if val < 500000:
                            gross_salary = val * 12.0
                        else:
                            gross_salary = val
                    else:
                        gross_salary = val
                    break

        # Check monthly salary pattern e.g. "monthly salary 80k", "mahine ka 1 lakh"
        if gross_salary == 0.0:
            monthly_m = re.search(r"(?:monthly(?:\s*salary)?|per\s*month|mahine\s*ka|har\s*mahine)\s*(?:salary|is|hai)?\s*([0-9\.]+\s*(?:k|lakh|lac|hazar)?\b)", lower)
            if monthly_m:
                val = parse_indian_currency_number(monthly_m.group(1))
                if val and val < 500000:  # Reasonable monthly limit
                    gross_salary = val * 12.0

        # 3. Basic Salary
        basic_salary = 0.0
        basic_patterns = [
            r"(?:basic(?:\s*salary)?)\s*(?:is|hai|of|:|=|around)?\s*([0-9\.]+\s*(?:lakh|lacs|lac|l|k|hazar)?)",
            r"([0-9\.]+\s*(?:lakh|lacs|lac|l|k))\s*basic"
        ]
        for pat in basic_patterns:
            m = re.search(pat, lower)
            if m:
                val = parse_indian_currency_number(m.group(1))
                if val:
                    # check if monthly
                    if "per month" in lower[m.start():m.end()+15] or "monthly" in lower[max(0, m.start()-15):m.end()]:
                        basic_salary = val * 12.0
                    else:
                        basic_salary = val
                    break
        if basic_salary == 0.0 and gross_salary > 0:
            # Standard corporate default in India: Basic is typically 40% to 50% of CTC
            basic_salary = round(gross_salary * 0.50)

        # 4. HRA Received
        hra_received = 0.0
        hra_patterns = [
            r"(?:hra(?:\s*component|\s*received)?)\s*(?:is|hai|of|:|=|around)?\s*([0-9\.]+\s*(?:lakh|lacs|lac|l|k|hazar)?)",
            r"([0-9\.]+\s*(?:lakh|lacs|lac|l|k))\s*hra"
        ]
        for pat in hra_patterns:
            m = re.search(pat, lower)
            if m:
                val = parse_indian_currency_number(m.group(1))
                if val:
                    if "per month" in lower[m.start():m.end()+15] or "monthly" in lower[max(0, m.start()-15):m.end()]:
                        hra_received = val * 12.0
                    else:
                        hra_received = val
                    break

        # 5. Rent Paid & Metro City
        rent_paid = 0.0
        rent_patterns = [
            r"(?:rent(?:\s*paid|\s*pay|\s*deta)?)\s*(?:is|hai|of|:|=|around)?\s*([0-9\.]+\s*(?:lakh|lacs|lac|l|k|hazar)?)(?:\s*(?:pm|per\s*month|mahine))?",
            r"([0-9\.]+\s*(?:lakh|lacs|lac|l|k|hazar)?)\s*(?:rent|kiraya)"
        ]
        for pat in rent_patterns:
            m = re.search(pat, lower)
            if m:
                val = parse_indian_currency_number(m.group(1))
                if val:
                    # If specified as monthly or value is typical monthly (< 80,000 and gross > 500,000)
                    if any(term in lower for term in ["per month", "pm", "mahina", "mahine", "har mahine", "p.m."]) or val <= 70000:
                        rent_paid = val * 12.0
                    else:
                        rent_paid = val
                    break

        is_metro = any(city in lower for city in METRO_CITIES)

        # If HRA received wasn't explicitly given but rent is paid and gross exists, reasonable assumption or 0
        if hra_received == 0.0 and rent_paid > 0 and gross_salary > 0:
            # Common allowance: 40% of basic
            hra_received = round(basic_salary * 0.40)

        # 6. Section 80C
        deductions_80c = 0.0
        c_patterns = [
            r"(?:80c|80-c|section\s*80c|ppf|elss|pf|epf|life\s*insurance|lic)\s*(?:me|invested|investment|is|hai|of|:|=|around)?\s*([0-9\.]+\s*(?:lakh|lacs|lac|l|k|hazar)?)",
            r"([0-9\.]+\s*(?:lakh|lacs|lac|l|k))\s*(?:in|under)?\s*80c"
        ]
        for pat in c_patterns:
            m = re.search(pat, lower)
            if m:
                val = parse_indian_currency_number(m.group(1))
                if val:
                    deductions_80c = val
                    break
        if "80c full" in lower or "full 80c" in lower or "80c max" in lower or "1.5l in 80c" in lower:
            deductions_80c = 150000.0

        # 7. Section 80CCD(1B) NPS
        deductions_80ccd_1b = 0.0
        nps_patterns = [
            r"(?:80ccd(?:\(1b\))?|nps)\s*(?:me|contribution|invested|is|hai|of|:|=|around)?\s*([0-9\.]+\s*(?:lakh|lacs|lac|l|k|hazar)?)",
            r"([0-9\.]+\s*(?:lakh|lacs|lac|l|k))\s*(?:in|to)?\s*nps"
        ]
        for pat in nps_patterns:
            m = re.search(pat, lower)
            if m:
                val = parse_indian_currency_number(m.group(1))
                if val:
                    deductions_80ccd_1b = val
                    break

        # 8. Section 80D Health Insurance
        health_insurance_self = 0.0
        health_insurance_parents = 0.0
        parents_senior = any(term in lower for term in [
            "parents senior", "senior citizen parents", "parents are senior", "buzurg parents",
            "father is 6", "mother is 6", "father is 7", "mother is 7", "parents > 60"
        ])
        self_senior = any(term in lower for term in ["i am senior citizen", "my age is 6", "my age is 7"])
        self_super_senior = any(term in lower for term in ["super senior", "age is 8", "age > 80"])

        # Health insurance self
        d_self_m = re.search(r"(?:health\s*insurance|medical\s*insurance|mediclaim|80d)\s*(?:for\s*self|self|family)?\s*(?:is|hai|of|:|=|around)?\s*([0-9\.]+\s*(?:k|hazar|thousand|lakh)?)", lower)
        if d_self_m:
            val = parse_indian_currency_number(d_self_m.group(1))
            if val:
                health_insurance_self = val

        # Health insurance parents
        d_parents_m = re.search(r"(?:parents(?:\s*ka|\s*ke)?\s*(?:health|medical|mediclaim|insurance)?|parents\s*insurance)\s*(?:is|hai|of|:|=|around)?\s*([0-9\.]+\s*(?:k|hazar|thousand|lakh)?)", lower)
        if d_parents_m:
            val = parse_indian_currency_number(d_parents_m.group(1))
            if val:
                health_insurance_parents = val

        # 9. Home Loan Interest Section 24(b)
        home_loan_interest_24b = 0.0
        hl_patterns = [
            r"(?:home\s*loan\s*interest|housing\s*loan\s*interest|interest\s*on\s*home\s*loan|24b|section\s*24)\s*(?:is|hai|of|:|=|around)?\s*([0-9\.]+\s*(?:lakh|lacs|lac|l|k|hazar)?)",
            r"([0-9\.]+\s*(?:lakh|lacs|lac|l|k))\s*(?:home\s*loan\s*interest)"
        ]
        for pat in hl_patterns:
            m = re.search(pat, lower)
            if m:
                val = parse_indian_currency_number(m.group(1))
                if val:
                    home_loan_interest_24b = val
                    break

        # 10. Other income
        other_income = 0.0
        other_m = re.search(r"(?:other\s*income|interest\s*income|savings\s*interest|extra\s*income)\s*(?:is|hai|of|:|=|around)?\s*([0-9\.]+\s*(?:lakh|lacs|lac|l|k|hazar)?)", lower)
        if other_m:
            val = parse_indian_currency_number(other_m.group(1))
            if val:
                other_income = val

        return TaxPayerProfile(
            gross_salary=gross_salary,
            basic_salary=basic_salary,
            hra_received=hra_received,
            rent_paid=rent_paid,
            is_metro=is_metro,
            deductions_80c=deductions_80c,
            deductions_80ccd_1b=deductions_80ccd_1b,
            health_insurance_self=health_insurance_self,
            health_insurance_parents=health_insurance_parents,
            parents_senior_citizen=parents_senior,
            self_senior_citizen=self_senior,
            self_super_senior=self_super_senior,
            home_loan_interest_24b=home_loan_interest_24b,
            employer_nps_80ccd_2=0.0,
            other_income=other_income,
            financial_year=fy
        )
