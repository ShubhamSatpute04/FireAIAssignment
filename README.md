# Fire AI – Rules vs. LLMs Engineering Assignment

Comprehensive comparative evaluation of **Deterministic Rule-Based**, **Statistical/Machine Learning**, **LLM-Based (Gemini)**, and **Cascading Hybrid** architectures across two complete software projects:
- **Project A**: Indian Income Tax Calculator (FY 2024-25 & FY 2025-26 under Finance Acts).
- **Project B**: NYC 311 Service Requests Data Quality Checker & Enterprise Scalability Model (50M rows/day across 120 tenants).

---

## Repository Structure

```
FireAIAssignment/
├── README.md                      # Setup, execution, and architectural guide
├── RESULTS_A.md                   # Project A benchmarks, tax comparisons & FY evolution
├── RESULTS_B.md                   # Project B benchmarks, 12 corruptions & scalability
├── DECISION_MATRIX.md             # Empirical decision heuristics (Rule vs ML vs LLM vs Hybrid)
├── AI_USAGE.md                    # AI tools used, reflection, and critical mistake post-mortem
├── run_all.py                     # Master one-click execution runner
│
├── project_a/                     # Project A: Indian Income Tax Calculator
│   ├── __init__.py
│   ├── models.py                  # Pydantic BaseModel (with native dataclass fallback)
│   ├── rules_engine.py            # Hand-coded Indian Tax Rules (Old vs New, Surcharge, Relief)
│   ├── llm_calculator.py          # Gemini query-time tax calculation with REST client & simulation
│   ├── rule_synthesizer.py        # Gemini synthesizes executable Python rules from tax law
│   ├── nlp_parser.py              # English & Hinglish natural language salary/deduction parser
│   ├── clarification.py           # Clarification question generator for ambiguous/contradictory info
│   ├── test_suite.py              # 30 ITD benchmarks + 216 structured test cases + 50 Hinglish inputs
│   └── benchmark.py               # Comparative benchmark: accuracy, determinism, latency, cost, audit
│
└── project_b/                     # Project B: NYC 311 Data Quality Checker
    ├── __init__.py
    ├── dataset_manager.py         # NYC 311 2023 dataset generator & baseline profiler
    ├── corruption_injector.py     # Controlled injector for all 12 data quality corruptions
    ├── detectors/
    │   ├── __init__.py
    │   ├── rule_detector.py       # Pure rule-based detector for all 12 problems
    │   ├── ml_detector.py         # Statistical / ML detector (Isolation Forest, TF-IDF, Z-scores)
    │   ├── llm_detector.py        # Gemini LLM semantic & PII detector
    │   └── hybrid_detector.py     # Cascading Hybrid detector (Tier 1 -> Tier 2 -> Tier 3)
    ├── test_suite.py              # Unit tests for all 12 corruptions and detectors
    ├── benchmark.py               # Comprehensive 4-detector evaluation (Recall, Precision, Speed, Cost)
    └── scalability_model.py       # 50M rows/day cost & architecture model across 120 customers
```

---

## 1. Quick Start & Prerequisites

### Environment
- **Python**: 3.10+
- **Pre-installed Core Packages**: `pandas`, `numpy`, `scikit-learn`
- **Zero-Dependency Architecture**: Designed to run immediately without requiring external package installations. Built-in native fallbacks provide Pydantic and Pytest compatibility out-of-the-box.
- **Optional (for live Gemini API calls)**:
  ```bash
  export GEMINI_API_KEY="your-gemini-api-key"   # Linux/macOS
  $env:GEMINI_API_KEY="your-gemini-api-key"      # Windows PowerShell
  ```
  *(If no API key is provided, the system executes high-fidelity offline inference pipelines automatically).*

---

## 2. Running All Tests & Benchmarks

To execute the entire suite end-to-end:
```bash
python run_all.py
```

### Running Individual Test Suites & Benchmarks

#### Project A (Indian Income Tax Calculator):
```bash
# 1. Run full unit test suite (30 ITD benchmarks + 216 structured cases + 50 Hinglish inputs)
python -m project_a.test_suite

# 2. Run 3-paradigm comparative benchmark (Accuracy, Latency, Cost, Auditability)
python -m project_a.benchmark
```

#### Project B (NYC 311 Data Quality Checker):
```bash
# 1. Run unit test suite verifying all 12 corruptions and detector implementations
python -m project_b.test_suite

# 2. Run comprehensive 4-detector evaluation benchmark
python -m project_b.benchmark

# 3. Run enterprise scalability & cost model for 50M rows/day across 120 tenants
python -m project_b.scalability_model
```

---

## 3. Key Findings & Architectural Highlights

### Project A – Indian Income Tax Calculator
1. **100.0% Official Validation**: All 30 ground-truth tax calculations passed rupee-exact validation against official Income Tax Department rules under both **Finance Act (No. 2) 2024** and **Finance Act 2025**.
2. **Budget 2025 (FY 2025-26) Zero-Tax Threshold**: Verified that salaried individuals earning up to **₹12.75 Lakhs gross pay ₹0 tax** under the revised New Regime (₹75k standard deduction + ₹12L Section 87A rebate).
3. **Approach 3 (Synthesized Rules) Advantage**: Synthesizing executable Python code from legislative specifications eliminates 100% of runtime LLM token costs and reduces query latency from **850ms to 45 microseconds** ($18,800\times$ speedup).

### Project B – NYC 311 Data Quality Checker
1. **12 Quality Corruptions Addressed**: Missing/renamed columns, data type changes, inconsistent date formats, swapped coordinates, exact duplicates, near-duplicates, null spikes, invalid date sequences, ZIP/borough mismatches, complaint/descriptor mismatches, resolution/status mismatches, and PII in text.
2. **Cascading Hybrid Superiority**:
   - **Throughput**: 834 rows/sec (vs 8.1 rows/sec for pure LLM).
   - **Cost Reduction**: **96.65% savings** vs Pure LLM ($16,290/year vs $484,800/year at 50M rows/day).
   - **Explainability**: Combines deterministic rule tags with rich human-readable contextual explanations from Gemini 1.5 Flash.

---

## 4. Deliverables Checklist

- [x] **Working code for Project A** (`project_a/rules_engine.py`, `llm_calculator.py`, `rule_synthesizer.py`, `nlp_parser.py`, `clarification.py`).
- [x] **Working code for Project B** (`project_b/dataset_manager.py`, `corruption_injector.py`, `detectors/*`, `scalability_model.py`).
- [x] **216 Structured Tax Test Cases & 50 Natural Language Inputs** (`project_a/test_suite.py`).
- [x] **30 ITD Official Calculator Validations** (100% Pass Rate).
- [x] **Benchmark Results for All Approaches** (`project_a/benchmark.py`, `project_b/benchmark.py`, `run_all.py`).
- [x] **RESULTS_A.md**: Tax comparison & FY change analysis.
- [x] **RESULTS_B.md**: NYC 311 quality detection & 50M rows/day scalability model.
- [x] **DECISION_MATRIX.md**: Measurement-backed Rule vs ML vs LLM vs Hybrid decision framework.
- [x] **AI_USAGE.md**: AI assistance log & post-mortem of critical mistake caught.
- [x] **README.md**: Setup, execution, and architectural guide.

