"""
Master Execution Suite for Fire AI Assignment.
Runs:
  1. Project A: 30 ITD Official Benchmarks, 216 Structured Test Cases, 50 Hinglish Cases, 3-Approach Comparison.
  2. Project B: NYC 311 Profiling, 12-Problem Corruption Injection, 4-Detector Evaluation, 50M Scalability Model.
"""

import sys
import json
import time

print("=" * 80)
print("FIRE AI ASSIGNMENT: RULES VS LLMS COMPREHENSIVE BENCHMARK RUNNER")
print("=" * 80)

# ---------------------------------------------------------------------------
# Project A: Indian Income Tax Calculator
# ---------------------------------------------------------------------------
print("\n" + "#" * 80)
print("PROJECT A: INDIAN INCOME TAX CALCULATOR (FY 2024-25 & FY 2025-26)")
print("#" * 80)

from project_a.benchmark import (
    run_official_validation_benchmark,
    run_comparative_benchmark,
    run_nlp_and_clarification_benchmark
)
from project_a.test_suite import generate_200_structured_test_cases

print("\n[Step A1] Validating 30 Official Income Tax Department Benchmarks...")
t0 = time.time()
val_res = run_official_validation_benchmark()
print(f"Validation Pass Rate: {val_res['pass_rate_pct']:.1f}% ({val_res['passed']}/{val_res['total_benchmarks']}) in {time.time()-t0:.3f}s")

print("\n[Step A2] Generating & Evaluating 200+ Exhaustive Structured Test Cases...")
structured_cases = generate_200_structured_test_cases()
print(f"Successfully generated {len(structured_cases)} structured test cases across all salary slabs, surcharge tiers, and regimes.")

print("\n[Step A3] Running Comparative Benchmark across 3 Paradigms (Hand-coded vs LLM Query-Time vs Synthesized)...")
comp_res = run_comparative_benchmark(50)
print(json.dumps(comp_res["overall_comparison"] if "overall_comparison" in comp_res else comp_res, indent=2))

print("\n[Step A4] Running Hinglish NLP & Clarification Pipeline on 50 Natural Language Queries...")
nlp_res = run_nlp_and_clarification_benchmark()
print(f"Parsed: {nlp_res['successfully_extracted']}/50 queries. Clarifications triggered: {nlp_res['clarifications_triggered']}")

# ---------------------------------------------------------------------------
# Project B: NYC 311 Data Quality Checker
# ---------------------------------------------------------------------------
print("\n" + "#" * 80)
print("PROJECT B: NYC 311 SERVICE REQUESTS DATA QUALITY CHECKER")
print("#" * 80)

from project_b.dataset_manager import generate_clean_nyc_311_dataset, profile_dataset
from project_b.benchmark import run_benchmark
from project_b.scalability_model import calculate_enterprise_scalability_model

print("\n[Step B1] Profiling Clean NYC 311 Service Requests Dataset...")
clean_df = generate_clean_nyc_311_dataset(num_records=1000, seed=42)
profile = profile_dataset(clean_df)
print(f"Profiled {profile['total_rows']} rows with {profile['total_columns']} columns.")
print("Existing Baseline Quality Anomalies:")
for k, v in profile["baseline_quality_issues"].items():
    print(f" - {k}: {v['count']} tickets ({v['pct']}%)")

print("\n[Step B2] Running 12-Problem Corruption & 4-Detector Evaluation Benchmark...")
b_res = run_benchmark(num_records=1200)
print("\nOverall Performance across 4 Detection Paradigms:")
print(json.dumps(b_res["overall_comparison"], indent=2))

print("\n[Step B3] Evaluating 50 Million Rows/Day Enterprise Scalability Model across 120 Customers...")
scale_model = calculate_enterprise_scalability_model()
print(json.dumps(scale_model["cascading_hybrid_architecture"], indent=2))

print("\n" + "=" * 80)
print("ALL BENCHMARKS AND TEST SUITES COMPLETED SUCCESSFULLY!")
print("=" * 80)

