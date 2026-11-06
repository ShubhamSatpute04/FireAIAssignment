"""
Data models for the Indian Income Tax Calculator.
Supports Pydantic BaseModel if installed, with a robust dataclass-based fallback
to ensure zero-dependency execution out-of-the-box.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
import json

try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False


if HAS_PYDANTIC:
    class TaxPayerProfile(BaseModel):
        gross_salary: float = Field(default=0.0, ge=0.0, description="Gross annual salary in INR")
        basic_salary: float = Field(default=0.0, ge=0.0, description="Basic annual salary in INR")
        hra_received: float = Field(default=0.0, ge=0.0, description="HRA component in salary")
        rent_paid: float = Field(default=0.0, ge=0.0, description="Total annual rent paid by employee")
        is_metro: bool = Field(default=False, description="Whether rented residence is in Delhi, Mumbai, Kolkata, or Chennai")
        deductions_80c: float = Field(default=0.0, ge=0.0, description="Section 80C investments (EPF, PPF, ELSS, etc.)")
        deductions_80ccd_1b: float = Field(default=0.0, ge=0.0, description="Section 80CCD(1B) additional NPS contribution")
        health_insurance_self: float = Field(default=0.0, ge=0.0, description="Section 80D health insurance for self & family")
        health_insurance_parents: float = Field(default=0.0, ge=0.0, description="Section 80D health insurance for parents")
        parents_senior_citizen: bool = Field(default=False, description="Whether parents are senior citizens (>= 60 years)")
        self_senior_citizen: bool = Field(default=False, description="Whether taxpayer is senior citizen (60-79 years)")
        self_super_senior: bool = Field(default=False, description="Whether taxpayer is super senior citizen (80+ years)")
        home_loan_interest_24b: float = Field(default=0.0, ge=0.0, description="Section 24(b) interest paid on housing loan for self-occupied home")
        employer_nps_80ccd_2: float = Field(default=0.0, ge=0.0, description="Section 80CCD(2) employer contribution to NPS")
        other_income: float = Field(default=0.0, ge=0.0, description="Other taxable income (savings interest, dividends, etc.)")
        financial_year: str = Field(default="FY 2024-25", description="Financial Year: 'FY 2024-25' or 'FY 2025-26'")

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()

    class RegimeCalculation(BaseModel):
        regime_name: str
        financial_year: str
        gross_total_income: float
        standard_deduction: float
        hra_exemption: float
        section_24b_loss: float
        deductions_80c: float
        deductions_80ccd_1b: float
        deductions_80d: float
        deductions_80ccd_2: float
        total_deductions: float
        taxable_income: float
        slab_tax_before_rebate: float
        rebate_87a: float
        marginal_relief_87a: float
        tax_after_rebate: float
        surcharge: float
        marginal_relief_surcharge: float
        tax_after_surcharge: float
        cess_4pct: float
        total_tax_payable: float
        effective_tax_rate: float
        breakdown_slabs: List[Dict[str, Any]] = Field(default_factory=list)

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()

    class TaxComparisonResult(BaseModel):
        financial_year: str
        old_regime: RegimeCalculation
        new_regime: RegimeCalculation
        recommended_regime: str
        tax_savings: float
        narrative_summary: str

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()

    class ClarificationRequest(BaseModel):
        is_complete: bool = True
        questions: List[str] = Field(default_factory=list)
        contradictions: List[str] = Field(default_factory=list)
        extracted_profile: Optional[TaxPayerProfile] = None

        def to_dict(self) -> Dict[str, Any]:
            return self.model_dump()

else:
    # Pure Python dataclass implementation with identical API
    @dataclass
    class TaxPayerProfile:
        gross_salary: float = 0.0
        basic_salary: float = 0.0
        hra_received: float = 0.0
        rent_paid: float = 0.0
        is_metro: bool = False
        deductions_80c: float = 0.0
        deductions_80ccd_1b: float = 0.0
        health_insurance_self: float = 0.0
        health_insurance_parents: float = 0.0
        parents_senior_citizen: bool = False
        self_senior_citizen: bool = False
        self_super_senior: bool = False
        home_loan_interest_24b: float = 0.0
        employer_nps_80ccd_2: float = 0.0
        other_income: float = 0.0
        financial_year: str = "FY 2024-25"

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class RegimeCalculation:
        regime_name: str
        financial_year: str
        gross_total_income: float
        standard_deduction: float
        hra_exemption: float
        section_24b_loss: float
        deductions_80c: float
        deductions_80ccd_1b: float
        deductions_80d: float
        deductions_80ccd_2: float
        total_deductions: float
        taxable_income: float
        slab_tax_before_rebate: float
        rebate_87a: float
        marginal_relief_87a: float
        tax_after_rebate: float
        surcharge: float
        marginal_relief_surcharge: float
        tax_after_surcharge: float
        cess_4pct: float
        total_tax_payable: float
        effective_tax_rate: float
        breakdown_slabs: List[Dict[str, Any]] = field(default_factory=list)

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class TaxComparisonResult:
        financial_year: str
        old_regime: RegimeCalculation
        new_regime: RegimeCalculation
        recommended_regime: str
        tax_savings: float
        narrative_summary: str

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)

    @dataclass
    class ClarificationRequest:
        is_complete: bool = True
        questions: List[str] = field(default_factory=list)
        contradictions: List[str] = field(default_factory=list)
        extracted_profile: Optional[TaxPayerProfile] = None

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)

