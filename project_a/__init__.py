"""
Project A: Indian Income Tax Calculator.
Compares Hand-Coded Rules, Gemini LLM Query-Time, and Gemini Synthesized Rules.
"""

from project_a.models import TaxPayerProfile, RegimeCalculation, TaxComparisonResult
from project_a.rules_engine import calculate_old_regime_tax, calculate_new_regime_tax, compare_regimes
from project_a.llm_calculator import GeminiTaxCalculator
from project_a.rule_synthesizer import TaxRuleSynthesizer
from project_a.nlp_parser import HinglishTaxParser
from project_a.clarification import TaxClarificationEngine

__all__ = [
    "TaxPayerProfile",
    "RegimeCalculation",
    "TaxComparisonResult",
    "calculate_old_regime_tax",
    "calculate_new_regime_tax",
    "compare_regimes",
    "GeminiTaxCalculator",
    "TaxRuleSynthesizer",
    "HinglishTaxParser",
    "TaxClarificationEngine"
]
