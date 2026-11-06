"""
Clarification Question and Contradiction Detection Engine.
Identifies incomplete, ambiguous, or contradictory tax claims and
formulates targeted, polite clarification prompts for taxpayers.
"""

from typing import List, Dict, Any, Tuple
from project_a.models import TaxPayerProfile, ClarificationRequest


class TaxClarificationEngine:
    """
    Evaluates taxpayer inputs for omissions, boundary ambiguities,
    and mathematical/legal contradictions.
    """

    @staticmethod
    def evaluate(profile: TaxPayerProfile, raw_text: str = "") -> ClarificationRequest:
        questions: List[str] = []
        contradictions: List[str] = []

        # 1. Salary presence check
        if profile.gross_salary <= 0:
            questions.append(
                "Gross annual salary / CTC is missing or 0. Please specify your annual earnings to calculate tax."
            )

        # 2. Basic salary > Gross salary contradiction
        if profile.basic_salary > profile.gross_salary and profile.gross_salary > 0:
            contradictions.append(
                f"Contradiction: Basic salary (Rs {profile.basic_salary:,.0f}) cannot be greater than Gross Salary (Rs {profile.gross_salary:,.0f})."
            )

        # 3. Rent paid without city clarification
        raw_lower = raw_text.lower()
        if profile.rent_paid > 0 and not profile.is_metro:
            metro_keywords = ["metro", "non-metro", "non metro", "mumbai", "delhi", "kolkata", "chennai"]
            if not any(k in raw_lower for k in metro_keywords):
                questions.append(
                    f"You reported paying rent of Rs {profile.rent_paid:,.0f}/year. "
                    "Do you reside in a metro city (Delhi, Mumbai, Kolkata, Chennai) or non-metro? "
                    "Metro allows up to 50% basic salary exemption vs 40% for non-metro."
                )

        # 4. Rent paid but 0 HRA allowance
        if profile.rent_paid > 0 and profile.hra_received <= 0 and profile.gross_salary > 0:
            questions.append(
                f"You reported paying rent of Rs {profile.rent_paid:,.0f}/year, but HRA received is Rs 0. "
                "Does your employer salary slip include an HRA component? Under Sec 10(13A), HRA exemption requires an actual HRA component."
            )

        # 5. Rent > Gross Salary contradiction
        if profile.rent_paid > profile.gross_salary and profile.gross_salary > 0:
            contradictions.append(
                f"Contradiction: Annual rent paid (Rs {profile.rent_paid:,.0f}) exceeds your entire gross annual salary (Rs {profile.gross_salary:,.0f}). Please verify if the rent amount was entered as monthly instead of annual."
            )

        # 6. Parents health insurance without senior citizen flag
        if profile.health_insurance_parents > 25000 and not profile.parents_senior_citizen:
            questions.append(
                f"You claimed Rs {profile.health_insurance_parents:,.0f} for parents' health insurance. "
                "Are either of your parents aged 60 or older? "
                "The deduction is capped at Rs 25,000 for non-senior parents, but expands to Rs 50,000 for senior citizen parents."
            )

        # 7. Deductions exceed Gross salary
        combined_deductions = (
            profile.deductions_80c
            + profile.deductions_80ccd_1b
            + profile.health_insurance_self
            + profile.health_insurance_parents
            + profile.home_loan_interest_24b
        )
        if combined_deductions > profile.gross_salary and profile.gross_salary > 0:
            contradictions.append(
                f"Contradiction: Total claimed deductions (Rs {combined_deductions:,.0f}) exceed your Gross Salary (Rs {profile.gross_salary:,.0f}). Chapter VI-A deductions cannot exceed Gross Total Income."
            )

        # 8. Statutory limit advisory / alerts
        if profile.deductions_80c > 150000:
            questions.append(
                f"Notice: You entered Rs {profile.deductions_80c:,.0f} under Section 80C. The statutory maximum allowable under Section 80C is Rs 1,50,000. It will automatically be capped."
            )

        if profile.home_loan_interest_24b > 200000:
            questions.append(
                f"Notice: You entered Rs {profile.home_loan_interest_24b:,.0f} for self-occupied home loan interest. Section 24(b) caps self-occupied loss from house property at Rs 2,00,000."
            )

        is_complete = (len(questions) == 0 and len(contradictions) == 0)

        return ClarificationRequest(
            is_complete=is_complete,
            questions=questions,
            contradictions=contradictions,
            extracted_profile=profile
        )

