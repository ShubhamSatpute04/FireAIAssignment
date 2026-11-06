"""
Project B: NYC 311 Data Quality Checker.
Detects 12 data corruptions comparing Rule-Based, Statistical/ML, Gemini LLM, and Cascading Hybrid approaches.
"""

from project_b.dataset_manager import generate_clean_nyc_311_dataset, profile_dataset
from project_b.corruption_injector import NYC311CorruptionInjector
from project_b.detectors.rule_detector import RuleBasedQualityDetector
from project_b.detectors.ml_detector import StatisticalMLQualityDetector
from project_b.detectors.llm_detector import GeminiLLMQualityDetector
from project_b.detectors.hybrid_detector import CascadingHybridQualityDetector
from project_b.scalability_model import calculate_enterprise_scalability_model

__all__ = [
    "generate_clean_nyc_311_dataset",
    "profile_dataset",
    "NYC311CorruptionInjector",
    "RuleBasedQualityDetector",
    "StatisticalMLQualityDetector",
    "GeminiLLMQualityDetector",
    "CascadingHybridQualityDetector",
    "calculate_enterprise_scalability_model"
]

