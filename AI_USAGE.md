# AI_USAGE.md – AI Assistance Log & Engineering Post-Mortem

## 1. AI Tools and Collaboration Profile

Throughout the design, implementation, and benchmarking of this assignment, AI tools were leveraged across several engineering workflows:

- **AI Model**: Gemini 1.5 Flash / 2.5 Flash via Generative Language API.
- **Roles & Tasks**:
  1. **Statutory Legal Synthesis (Project A – Approach 3)**: Employing Gemini as an offline compiler to synthesize pure Python code closures from Finance Act legislative text.
  2. **Colloquial Multilingual Normalization (Project A NLP)**: Modeling Indian colloquialisms, Hinglish numerical tokens ("LPA", "hazar", "lakh", "crore", "pm", "mahine ka"), and regional abbreviations.
  3. **High-dimensional Contextual Reasoning (Project B – Tier 3 Hybrid)**: Identifying subtle semantic mismatches between operational complaints and resolution descriptions that escape simple keyword regexes.
  4. **Architecture Modeling (Project B Scalability)**: Mathematical modeling of token throughput, stream buffering, and cloud infrastructure costs for 50 million rows/day.

---

## 2. Critical Mistake Caught & Post-Mortem Analysis

### The Mistake: Outdated Pre-Budget Benchmark Ground Truth vs. Finance Act (No. 2) 2024 Amendments

#### Context:
During initial validation of the 30 Income Tax Department benchmark cases, a significant discrepancy emerged between standard online calculators (many of which still reflect the pre-July 2024 Budget slabs) and our deterministic engine.
Specifically, for an individual earning **₹10,00,000 gross salary** in FY 2024-25:
- **Legacy Ground-Truth Note**: Claimed expected tax was **₹54,600**.
- **Engine Output**: Calculated tax was **₹44,200** (a difference of ₹10,400).

#### Root Cause Analysis:
1. **Pre-July 2024 Interim Budget**:
   - Standard deduction was ₹50,000 $\rightarrow$ Taxable income = ₹9,50,000.
   - Slabs: 0–3L Nil, 3–6L 5% (15k), 6–9L 10% (30k), 9–12L 15% (7.5k).
   - Total base tax = ₹52,500 + 4% cess = **₹54,600**.
2. **Actual Enacted Law (Finance Act No. 2, 2024 enacted July 2024)**:
   - Standard deduction was officially raised to **₹75,000** for salaried employees $\rightarrow$ Taxable income = ₹9,25,000.
   - Slabs were amended to:
     - ₹0 to ₹3,00,000: Nil
     - ₹3,00,001 to ₹7,00,000: 5% (₹20,000)
     - ₹7,00,001 to ₹10,00,000: 10% (on ₹2,25,000 = ₹22,500)
   - Total base tax = ₹20,000 + ₹22,500 = ₹42,500.
   - Add 4% cess = ₹42,500 $\times$ 1.04 = **₹44,200**!

#### Remediation:
Blindly forcing code to pass obsolete ground-truth benchmark tables would have introduced illegal statutory calculations into production. By cross-verifying directly with the gazetted Finance Act (No. 2) 2024 text, the benchmark table was updated to reflect the enacted statutory law. The rules engine was proven 100% correct.

---

### Secondary Engineering Bug Caught: F-String Format Specifier on Infinite Float Bounds

#### Context:
During the first execution of `project_a/rules_engine.py`, the slab breakdown formatter threw an unexpected runtime exception:
```python
ValueError: Cannot specify ',' with 's'.
```

#### Root Cause:
In the slab range label formatter:
```python
# Flawed line:
"slab_range": f"{int(lower):,} - {int(upper) if upper != float('inf') else 'Above':,}"
```
When `upper` was `float('inf')`, the ternary operator returned the string `'Above'`. Applying the comma format specifier `:,` to a string literal raised a Python `ValueError`.

#### Resolution:
Refactored into explicit branch formatting:
```python
# Fixed line:
"slab_range": f"{int(lower):,} - {int(upper):,}" if upper != float("inf") else f"Above {int(lower):,}"
```
This was resolved across all three slab computing functions, restoring 100% test pass rates across the test suite.

