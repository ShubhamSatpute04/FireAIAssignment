"""
Hand-Coded Indian Income Tax Rules Engine.
Implements the official provisions of the Indian Income Tax Act 1961,
Finance Act 2024 (No. 2) for FY 2024-25 (AY 2025-26),
and Finance Act 2025 (Budget 2025) for FY 2025-26 (AY 2026-27).
"""

from typing import Dict, Any, List, Tuple
import math
from project_a.models import TaxPayerProfile, RegimeCalculation, TaxComparisonResult


def round_section_288b(amount: float) -> float:
    """
    Rounds an amount to the nearest multiple of 10 as prescribed under Section 288B
    of the Income Tax Act, 1961.
    """
    return float(round(amount / 10.0) * 10)


def calculate_hra_exemption(
    basic_salary: float,
    hra_received: float,
    rent_paid: float,
    is_metro: bool
) -> float:
    """
    Calculate HRA exemption under Section 10(13A) and Rule 2A.
    Exemption is the MINIMUM of:
      1. Actual HRA received
      2. Rent paid - 10% of (Basic + DA)
      3. 50% of Basic (Metro: Delhi, Mumbai, Kolkata, Chennai) or 40% (Non-metro)
    """
    if hra_received <= 0 or rent_paid <= 0 or basic_salary <= 0:
        return 0.0

    excess_rent_over_10pct = rent_paid - (0.10 * basic_salary)
    if excess_rent_over_10pct <= 0:
        return 0.0

    metro_multiplier = 0.50 if is_metro else 0.40
    salary_percentage_limit = metro_multiplier * basic_salary

    exemption = min(hra_received, excess_rent_over_10pct, salary_percentage_limit)
    return max(0.0, float(exemption))


def calculate_80d_deduction(
    health_insurance_self: float,
    health_insurance_parents: float,
    self_senior_citizen: bool = False,
    parents_senior_citizen: bool = False
) -> float:
    """
    Calculate Section 80D deduction for medical insurance.
    - Self, spouse, dependent children: max 25k (50k if self is senior)
    - Parents: max 25k (50k if parents are senior)
    """
    self_limit = 50000.0 if self_senior_citizen else 25000.0
    parents_limit = 50000.0 if parents_senior_citizen else 25000.0

    ded_self = min(max(0.0, health_insurance_self), self_limit)
    ded_parents = min(max(0.0, health_insurance_parents), parents_limit)

    return float(ded_self + ded_parents)


def compute_old_regime_slab_tax(
    taxable_income: float,
    self_senior: bool = False,
    self_super_senior: bool = False
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Compute slab tax under Old Tax Regime.
    Slabs:
    - Normal (<60 yrs): 0-2.5L: Nil, 2.5-5L: 5%, 5-10L: 20%, >10L: 30%
    - Senior (60-79 yrs): 0-3L: Nil, 3-5L: 5%, 5-10L: 20%, >10L: 30%
    - Super Senior (>=80 yrs): 0-5L: Nil, 5-10L: 20%, >10L: 30%
    """
    if taxable_income <= 0:
        return 0.0, []

    if self_super_senior:
        slabs = [
            (0, 500000, 0.0),
            (500000, 1000000, 0.20),
            (1000000, float("inf"), 0.30)
        ]
    elif self_senior:
        slabs = [
            (0, 300000, 0.0),
            (300000, 500000, 0.05),
            (500000, 1000000, 0.20),
            (1000000, float("inf"), 0.30)
        ]
    else:
        slabs = [
            (0, 250000, 0.0),
            (250000, 500000, 0.05),
            (500000, 1000000, 0.20),
            (1000000, float("inf"), 0.30)
        ]

    total_tax = 0.0
    breakdown = []
    rem_income = taxable_income

    for lower, upper, rate in slabs:
        if taxable_income > lower:
            taxable_in_slab = min(taxable_income, upper) - lower
            slab_tax = taxable_in_slab * rate
            total_tax += slab_tax
            breakdown.append({
                "slab_range": f"{int(lower):,} - {int(upper):,}" if upper != float("inf") else f"Above {int(lower):,}",
                "rate_pct": rate * 100,
                "taxable_amount_in_slab": taxable_in_slab,
                "slab_tax": slab_tax
            })
        else:
            break

    return total_tax, breakdown


def compute_new_regime_slab_tax_fy24_25(taxable_income: float) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Compute slab tax under New Tax Regime for FY 2024-25 (Finance Act 2024).
    Slabs:
    - Up to 3,00,000: Nil
    - 3,00,001 to 7,00,000: 5%
    - 7,00,001 to 10,00,000: 10%
    - 10,00,001 to 12,00,000: 15%
    - 12,00,001 to 15,00,000: 20%
    - Above 15,00,000: 30%
    """
    if taxable_income <= 0:
        return 0.0, []

    slabs = [
        (0, 300000, 0.0),
        (300000, 700000, 0.05),
        (700000, 1000000, 0.10),
        (1000000, 1200000, 0.15),
        (1200000, 1500000, 0.20),
        (1500000, float("inf"), 0.30)
    ]

    total_tax = 0.0
    breakdown = []
    for lower, upper, rate in slabs:
        if taxable_income > lower:
            taxable_in_slab = min(taxable_income, upper) - lower
            slab_tax = taxable_in_slab * rate
            total_tax += slab_tax
            breakdown.append({
                "slab_range": f"{int(lower):,} - {int(upper):,}" if upper != float("inf") else f"Above {int(lower):,}",
                "rate_pct": rate * 100,
                "taxable_amount_in_slab": taxable_in_slab,
                "slab_tax": slab_tax
            })
        else:
            break

    return total_tax, breakdown


def compute_new_regime_slab_tax_fy25_26(taxable_income: float) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Compute slab tax under New Tax Regime for FY 2025-26 (Budget 2025 / Finance Bill 2025).
    Slabs:
    - Up to 4,00,000: Nil
    - 4,00,001 to 8,00,000: 5%
    - 8,00,001 to 12,00,000: 10%
    - 12,00,001 to 16,00,000: 15%
    - 16,00,001 to 20,00,000: 20%
    - 20,00,001 to 24,00,000: 25%
    - Above 24,00,000: 30%
    """
    if taxable_income <= 0:
        return 0.0, []

    slabs = [
        (0, 400000, 0.0),
        (400000, 800000, 0.05),
        (800000, 1200000, 0.10),
        (1200000, 1600000, 0.15),
        (1600000, 2000000, 0.20),
        (2000000, 2400000, 0.25),
        (2400000, float("inf"), 0.30)
    ]

    total_tax = 0.0
    breakdown = []
    for lower, upper, rate in slabs:
        if taxable_income > lower:
            taxable_in_slab = min(taxable_income, upper) - lower
            slab_tax = taxable_in_slab * rate
            total_tax += slab_tax
            breakdown.append({
                "slab_range": f"{int(lower):,} - {int(upper):,}" if upper != float("inf") else f"Above {int(lower):,}",
                "rate_pct": rate * 100,
                "taxable_amount_in_slab": taxable_in_slab,
                "slab_tax": slab_tax
            })
        else:
            break

    return total_tax, breakdown


def calculate_surcharge_and_marginal_relief(
    taxable_income: float,
    tax_before_surcharge: float,
    is_new_regime: bool,
    fy: str = "FY 2024-25"
) -> Tuple[float, float, float]:
    """
    Calculate Surcharge and Marginal Relief on Surcharge.
    Surcharge thresholds:
    - 50L to 1Cr: 10%
    - 1Cr to 2Cr: 15%
    - 2Cr to 5Cr: 25% (in New Regime, highest surcharge is capped at 25%)
    - > 5Cr: 37% (Old Regime only; New Regime capped at 25%)

    Marginal Relief Condition:
    Total tax + surcharge cannot exceed:
    (Tax on threshold with applicable surcharge at threshold) + (Taxable Income - threshold).
    """
    if taxable_income <= 5000000:
        return 0.0, 0.0, 0.0

    # Determine applicable surcharge rate and threshold
    if 5000000 < taxable_income <= 10000000:
        rate = 0.10
        threshold = 5000000.0
        # Tax at threshold:
        if is_new_regime:
            tax_at_threshold, _ = (
                compute_new_regime_slab_tax_fy24_25(threshold)
                if fy == "FY 2024-25"
                else compute_new_regime_slab_tax_fy25_26(threshold)
            )
        else:
            tax_at_threshold, _ = compute_old_regime_slab_tax(threshold)
        surcharge_at_threshold = 0.0
    elif 10000000 < taxable_income <= 20000000:
        rate = 0.15
        threshold = 10000000.0
        if is_new_regime:
            tax_at_threshold, _ = (
                compute_new_regime_slab_tax_fy24_25(threshold)
                if fy == "FY 2024-25"
                else compute_new_regime_slab_tax_fy25_26(threshold)
            )
        else:
            tax_at_threshold, _ = compute_old_regime_slab_tax(threshold)
        surcharge_at_threshold = 0.10 * tax_at_threshold
    elif 20000000 < taxable_income <= 50000000:
        rate = 0.25
        threshold = 20000000.0
        if is_new_regime:
            tax_at_threshold, _ = (
                compute_new_regime_slab_tax_fy24_25(threshold)
                if fy == "FY 2024-25"
                else compute_new_regime_slab_tax_fy25_26(threshold)
            )
        else:
            tax_at_threshold, _ = compute_old_regime_slab_tax(threshold)
        surcharge_at_threshold = 0.15 * tax_at_threshold
    else: # > 50000000 (5 Crore)
        if is_new_regime:
            rate = 0.25 # Capped at 25% under Section 115BAC
            threshold = 20000000.0
            tax_at_threshold, _ = (
                compute_new_regime_slab_tax_fy24_25(threshold)
                if fy == "FY 2024-25"
                else compute_new_regime_slab_tax_fy25_26(threshold)
            )
            surcharge_at_threshold = 0.15 * tax_at_threshold
        else:
            rate = 0.37
            threshold = 50000000.0
            tax_at_threshold, _ = compute_old_regime_slab_tax(threshold)
            surcharge_at_threshold = 0.25 * tax_at_threshold

    calculated_surcharge = tax_before_surcharge * rate
    total_tax_and_surcharge = tax_before_surcharge + calculated_surcharge

    max_payable = (tax_at_threshold + surcharge_at_threshold) + (taxable_income - threshold)

    if total_tax_and_surcharge > max_payable:
        marginal_relief = total_tax_and_surcharge - max_payable
        final_surcharge = max(0.0, calculated_surcharge - marginal_relief)
    else:
        marginal_relief = 0.0
        final_surcharge = calculated_surcharge

    return calculated_surcharge, marginal_relief, final_surcharge


def calculate_old_regime_tax(profile: TaxPayerProfile) -> RegimeCalculation:
    """
    Computes tax under Old Tax Regime for FY 2024-25 / FY 2025-26.
    """
    gross_income = profile.gross_salary + profile.other_income
    standard_deduction = 50000.0 if profile.gross_salary >= 50000.0 else profile.gross_salary

    hra_exemption = calculate_hra_exemption(
        basic_salary=profile.basic_salary,
        hra_received=profile.hra_received,
        rent_paid=profile.rent_paid,
        is_metro=profile.is_metro
    )

    # Section 24(b) Loss from house property (home loan interest on self-occupied house capped at 2L)
    sec_24b_loss = min(max(0.0, profile.home_loan_interest_24b), 200000.0)

    # Chapter VI-A deductions
    ded_80c = min(max(0.0, profile.deductions_80c), 150000.0)
    ded_80ccd_1b = min(max(0.0, profile.deductions_80ccd_1b), 50000.0)
    ded_80d = calculate_80d_deduction(
        health_insurance_self=profile.health_insurance_self,
        health_insurance_parents=profile.health_insurance_parents,
        self_senior_citizen=profile.self_senior_citizen,
        parents_senior_citizen=profile.parents_senior_citizen
    )
    ded_80ccd_2 = max(0.0, profile.employer_nps_80ccd_2)

    total_deductions = (
        standard_deduction
        + hra_exemption
        + sec_24b_loss
        + ded_80c
        + ded_80ccd_1b
        + ded_80d
        + ded_80ccd_2
    )

    taxable_income = max(0.0, gross_income - total_deductions)

    # Slab tax
    base_tax, slabs = compute_old_regime_slab_tax(
        taxable_income=taxable_income,
        self_senior=profile.self_senior_citizen,
        self_super_senior=profile.self_super_senior
    )

    # Section 87A Rebate (Old Regime: taxable income <= 5L, max rebate 12.5k)
    rebate_87a = 0.0
    marginal_relief_87a = 0.0
    if taxable_income <= 500000.0:
        rebate_87a = min(base_tax, 12500.0)
        tax_after_rebate = max(0.0, base_tax - rebate_87a)
    else:
        tax_after_rebate = base_tax

    # Surcharge & marginal relief
    calc_surcharge, marginal_relief_surcharge, final_surcharge = calculate_surcharge_and_marginal_relief(
        taxable_income=taxable_income,
        tax_before_surcharge=tax_after_rebate,
        is_new_regime=False,
        fy=profile.financial_year
    )

    tax_after_surcharge = tax_after_rebate + final_surcharge

    # 4% Health & Education Cess
    cess = 0.04 * tax_after_surcharge
    total_tax = round_section_288b(tax_after_surcharge + cess)

    effective_rate = (total_tax / gross_income * 100.0) if gross_income > 0 else 0.0

    return RegimeCalculation(
        regime_name="Old Tax Regime",
        financial_year=profile.financial_year,
        gross_total_income=gross_income,
        standard_deduction=standard_deduction,
        hra_exemption=hra_exemption,
        section_24b_loss=sec_24b_loss,
        deductions_80c=ded_80c,
        deductions_80ccd_1b=ded_80ccd_1b,
        deductions_80d=ded_80d,
        deductions_80ccd_2=ded_80ccd_2,
        total_deductions=total_deductions,
        taxable_income=taxable_income,
        slab_tax_before_rebate=base_tax,
        rebate_87a=rebate_87a,
        marginal_relief_87a=marginal_relief_87a,
        tax_after_rebate=tax_after_rebate,
        surcharge=final_surcharge,
        marginal_relief_surcharge=marginal_relief_surcharge,
        tax_after_surcharge=tax_after_surcharge,
        cess_4pct=cess,
        total_tax_payable=total_tax,
        effective_tax_rate=round(effective_rate, 2),
        breakdown_slabs=slabs
    )


def calculate_new_regime_tax(profile: TaxPayerProfile) -> RegimeCalculation:
    """
    Computes tax under New Tax Regime (Section 115BAC) for FY 2024-25 or FY 2025-26.
    """
    gross_income = profile.gross_salary + profile.other_income

    # Standard deduction in new regime is 75,000 for salaried employees in FY 24-25 & FY 25-26
    std_limit = 75000.0
    standard_deduction = min(profile.gross_salary, std_limit) if profile.gross_salary > 0 else 0.0

    # Employer NPS 80CCD(2) is allowed in New Regime
    ded_80ccd_2 = max(0.0, profile.employer_nps_80ccd_2)

    total_deductions = standard_deduction + ded_80ccd_2
    taxable_income = max(0.0, gross_income - total_deductions)

    # Compute slab tax depending on FY
    fy = profile.financial_year.strip().upper()
    if "2025-26" in fy or "25-26" in fy:
        base_tax, slabs = compute_new_regime_slab_tax_fy25_26(taxable_income)
        rebate_threshold = 1200000.0
        max_rebate = 60000.0
    else:  # FY 2024-25
        base_tax, slabs = compute_new_regime_slab_tax_fy24_25(taxable_income)
        rebate_threshold = 700000.0
        max_rebate = 25000.0

    # Section 87A Rebate and Marginal Relief (New Regime)
    rebate_87a = 0.0
    marginal_relief_87a = 0.0

    if taxable_income <= rebate_threshold:
        rebate_87a = min(base_tax, max_rebate)
        tax_after_rebate = 0.0
    else:
        # Marginal relief under Section 87A for income slightly above threshold:
        # Tax payable cannot exceed income exceeding the threshold
        excess_income = taxable_income - rebate_threshold
        if base_tax > excess_income:
            marginal_relief_87a = base_tax - excess_income
            tax_after_rebate = excess_income
        else:
            tax_after_rebate = base_tax

    # Surcharge & marginal relief
    calc_surcharge, marginal_relief_surcharge, final_surcharge = calculate_surcharge_and_marginal_relief(
        taxable_income=taxable_income,
        tax_before_surcharge=tax_after_rebate,
        is_new_regime=True,
        fy=profile.financial_year
    )

    tax_after_surcharge = tax_after_rebate + final_surcharge

    # 4% Health & Education Cess
    cess = 0.04 * tax_after_surcharge
    total_tax = round_section_288b(tax_after_surcharge + cess)

    effective_rate = (total_tax / gross_income * 100.0) if gross_income > 0 else 0.0

    return RegimeCalculation(
        regime_name="New Tax Regime (Sec 115BAC)",
        financial_year=profile.financial_year,
        gross_total_income=gross_income,
        standard_deduction=standard_deduction,
        hra_exemption=0.0,
        section_24b_loss=0.0,
        deductions_80c=0.0,
        deductions_80ccd_1b=0.0,
        deductions_80d=0.0,
        deductions_80ccd_2=ded_80ccd_2,
        total_deductions=total_deductions,
        taxable_income=taxable_income,
        slab_tax_before_rebate=base_tax,
        rebate_87a=rebate_87a,
        marginal_relief_87a=marginal_relief_87a,
        tax_after_rebate=tax_after_rebate,
        surcharge=final_surcharge,
        marginal_relief_surcharge=marginal_relief_surcharge,
        tax_after_surcharge=tax_after_surcharge,
        cess_4pct=cess,
        total_tax_payable=total_tax,
        effective_tax_rate=round(effective_rate, 2),
        breakdown_slabs=slabs
    )


def compare_regimes(profile: TaxPayerProfile) -> TaxComparisonResult:
    """
    Compares Old vs New Tax Regime for the given taxpayer profile,
    computes tax savings, and generates recommendation with clear narrative.
    """
    old_res = calculate_old_regime_tax(profile)
    new_res = calculate_new_regime_tax(profile)

    diff = old_res.total_tax_payable - new_res.total_tax_payable

    if diff > 0:
        recommended = "New Tax Regime (Sec 115BAC)"
        savings = diff
        summary = (
            f"The New Tax Regime is beneficial by ₹{savings:,.0f}. "
            f"Tax under New Regime is ₹{new_res.total_tax_payable:,.0f} vs "
            f"₹{old_res.total_tax_payable:,.0f} in the Old Regime."
        )
    elif diff < 0:
        recommended = "Old Tax Regime"
        savings = abs(diff)
        summary = (
            f"The Old Tax Regime is beneficial by ₹{savings:,.0f} due to "
            f"significant exemptions (HRA: ₹{old_res.hra_exemption:,.0f}, "
            f"80C: ₹{old_res.deductions_80c:,.0f}, 80D: ₹{old_res.deductions_80d:,.0f}, "
            f"Home loan 24b: ₹{old_res.section_24b_loss:,.0f}). "
            f"Tax under Old Regime is ₹{old_res.total_tax_payable:,.0f} vs "
            f"₹{new_res.total_tax_payable:,.0f} in New Regime."
        )
    else:
        recommended = "Both Regimes Equal"
        savings = 0.0
        summary = (
            f"Both regimes yield identical tax liability of ₹{new_res.total_tax_payable:,.0f}."
        )

    return TaxComparisonResult(
        financial_year=profile.financial_year,
        old_regime=old_res,
        new_regime=new_res,
        recommended_regime=recommended,
        tax_savings=savings,
        narrative_summary=summary
    )
