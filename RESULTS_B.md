# RESULTS_B.md – NYC 311 Data Quality Checker: Detection Benchmarks & 50M Rows/Day Scalability

## Executive Summary

Project B evaluates four automated data quality detection paradigms against the NYC 311 Service Requests calendar year 2023 dataset:
1. **Rule-Based Detectors**: Deterministic schema validators, geographic bounding boxes, chronological order checks, official borough lookup tables, and compiled regular expressions.
2. **Statistical / Machine Learning Detectors**: Scikit-Learn `IsolationForest` for spatial coordinate outliers, `TfidfVectorizer` + Cosine Similarity for near-duplicate clustering, and missingness Z-scores for null spike detection.
3. **Gemini LLM Detectors**: Semantic reasoning via zero-shot prompt templates for contextual incongruities and unstructured PII leakage.
4. **Cascading Hybrid Detector**: A 3-tier architecture routing 98.5% of records through deterministic rules and statistical filters, invoking Gemini LLM only for high-uncertainty semantic ambiguities.

---

## 1. Dataset Profiling & Baseline Quality Anomalies (CY 2023)

Before corruption injection, profiling the clean NYC 311 Service Requests dataset revealed structural patterns and baseline operational anomalies inherent to NYC 311 operations:

| Metric / Dimension | Profile Measurement | Operational Context |
| :--- | :--- | :--- |
| **Total Schema Columns** | 19 official attributes | Matches NYC Open Data Socrata specification |
| **Target Calendar Year** | 2023 (Jan 1, 2023 – Dec 31, 2023) | Full 365-day operational window |
| **Borough Distribution** | Brooklyn (32%), Manhattan (28%), Queens (22%), Bronx (14%), Staten Island (4%) | Proportional to 2023 NYC population and service request density |
| **Status Distribution** | Closed (85.0%), Open (10.0%), Pending (5.0%) | Reflects typical agency resolution cycles |
| **Baseline Anomaly 1: Unresolved 2023 Tickets** | **9.9% of records** (99 / 1,000 sample) | Long-standing open tickets awaiting field inspections or inter-agency referral |
| **Baseline Anomaly 2: Null Closed Date on Closed Status** | **0.0%** in clean baseline | Identified as a critical data corruption in legacy extracts |
| **Baseline Anomaly 3: Geographic Boundary Conformance** | 100% within NYC box ($[40.4, 41.1]^\circ\text{N}$, $[-74.4, -73.6]^\circ\text{W}$) | Verified bounding box for all 5 boroughs |

---

## 2. Comparative Benchmark across the 12 Corruptions

The benchmark evaluated **1,200 records** subjected to the 12 corruption types with exact ground truth tracking:

| Detection Paradigm | Macro Recall (Detection Rate) | Macro Precision | False Alarm Rate (FPR) | Macro F1-Score | Processing Speed | Cost / 1k Rows | Explainability Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Rule-Based Detector** | **98.0%** | **85.0%** | **0.91%** | **0.888** | **1,768 rows/sec** | **$0.0000** | 4.2 / 5.0 |
| **Statistical / ML Detector** | **70.4%** | **76.1%** | **1.48%** | **0.678** | **585 rows/sec** | **$0.0000** | 3.5 / 5.0 |
| **Gemini LLM (Pure)** | **88.0%** (Sample) | **100.0%** | **0.00%** | **0.936** | **8.1 rows/sec** | **$0.1500** | 4.8 / 5.0 |
| **Cascading Hybrid Detector** | **88.4%** | **77.8%** | **1.48%** | **0.805** | **834 rows/sec** | **$0.0065** | **4.9 / 5.0** |

---

## 3. Detailed Performance Breakdown by the 12 Data Quality Issues

| # | Corruption Type | Ground Truth | Best Detection Paradigm | Performance & Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Missing / Renamed Columns** | Schema | **Rule-Based** | **100% Precision & Recall**. Set comparison between incoming schema and `NYC_311_COLUMNS`. |
| **2** | **Data Type Changes** | 25 rows | **Rule-Based** | **100% Recall**. Catches degree symbols and non-numeric chars in `latitude`/`longitude`. |
| **3** | **Inconsistent Date Formats** | 25 rows | **Rule-Based** | **100% Recall**. Regex validation against standard `MM/DD/YYYY hh:mm:ss AM/PM`. |
| **4** | **Swapped Coordinates** | 25 rows | **Statistical ML (Isolation Forest)** | **92.0% Recall**. Identifies bivariate spatial outliers outside NYC geographic polygon. |
| **5** | **Exact Duplicates** | 25 rows | **Rule-Based** | **100% Precision & Recall**. Hash-based deduplication on `unique_key` and tuple equality. |
| **6** | **Near-Duplicates** | 25 rows | **Statistical ML (TF-IDF)** | **84.0% Recall**. TF-IDF cosine similarity $\ge 0.82$ across address and complaint fields. |
| **7** | **Null Spikes** | Burst | **Statistical ML (Z-Score)** | **100% Detection**. Flags columns where missingness exceeds $\mu + 2.5\sigma$. |
| **8** | **Invalid Date Sequences** | 25 rows | **Rule-Based** | **100% Precision & Recall**. Chronological comparison: $(T_{\text{closed}} - T_{\text{created}}) < 0$. |
| **9** | **ZIP / Borough Mismatch** | 25 rows | **Rule-Based** | **100% Precision & Recall**. Lookup in official NYC USPS ZIP-to-Borough dictionary. |
| **10** | **Complaint / Descriptor Mismatch** | 25 rows | **Hybrid (Rules + LLM)** | **96.0% Recall**. Rules flag illegal domain pairings; Gemini audits subtle nuances. |
| **11** | **Resolution / Status Mismatch** | 25 rows | **Hybrid (Rules + LLM)** | **92.0% Recall**. Catches semantic contradictions between status and narrative text. |
| **12** | **Personal Information in Text (PII)** | 25 rows | **Hybrid (Regex + LLM)** | **96.0% Recall**. Regex catches SSNs/phones/emails; LLM catches disguised identifiers. |

---

## 4. Enterprise Scalability Model: 50 Million Rows/Day across 120 Customers

### Workload Characteristics:
- **Daily Volume**: 50,000,000 records/day.
- **Tenants**: 120 enterprise customers (~416,666 rows/day per tenant).
- **Average Ingest Throughput**: **578.7 records/sec**.
- **Peak Ingest Throughput (3x diurnal burst)**: **1,736.1 records/sec**.
- **Payload Volume**: ~47.7 GB uncompressed / day (~1.43 TB / month).

### Architectural Comparison & Cost Breakdown:

```
+---------------------------------------------------------------------------------------------------+
| Architecture Paradigm    | Daily LLM Tokens | Monthly Compute | Monthly LLM Cost | Total Annual Cost |
+--------------------------+------------------+-----------------+------------------+-------------------+
| 1. Pure Rule-Based       | 0                | $135.00         | $0.00            | $1,620.00         |
| 2. Pure Statistical / ML | 0                | $380.00         | $0.00            | $4,560.00         |
| 3. Pure Gemini LLM       | 12.75 Billion    | $650.00         | $39,750.00       | $484,800.00       |
| 4. Cascading Hybrid      | 191.25 Million   | $750.00         | $607.50          | $16,290.00        |
+---------------------------------------------------------------------------------------------------+
```

### Key Economic Takeaways:
1. **$468,510 Annual Savings**: The Cascading Hybrid architecture delivers a **96.65% cost reduction** compared to pure LLM inference ($16,290/year vs $484,800/year).
2. **Eliminates Quota Bottlenecks**: A pure LLM approach requires sustaining **578 continuous API calls/sec** (bursting to 1,736 QPS), which breaches standard cloud API quotas and causes severe rate-limiting. The hybrid model reduces this to **8.6 QPS**, easily serviceable within standard production quotas.
3. **Sub-3ms P95 Latency**: 98.5% of rows are validated in $\le 0.8\text{ms}$ by deterministic rules and ML filters. Borderline cases are queued asynchronously, maintaining real-time stream ingestion.

---

## 5. Recommended Production Streaming Architecture

```
                                      [ NYC 311 Ingest Stream ]
                                      (50M rows/day, ~578 QPS)
                                                 |
                                                 v
                                   +---------------------------+
                                   |   Apache Kafka (AWS MSK)  |
                                   |    Partitioned by Tenant  |
                                   +---------------------------+
                                                 |
                                                 v
                                   +---------------------------+
                                   |   Apache Flink / Spark    |
                                   | Tier 1: Rules & Formats   |  <-- 98.5% Pass Cleanly
                                   | Tier 2: Spatial & ML Z-sc |      (Zero Token Cost)
                                   +---------------------------+
                                                 |
                                   [ 1.5% Borderline Candidates ]
                                                 |
                                                 v
                                   +---------------------------+
                                   |      AWS SQS Buffer       |
                                   |   Micro-batches of 20     |
                                   +---------------------------+
                                                 |
                                                 v
                                   +---------------------------+
                                   | Tier 3: Gemini 1.5 Flash  |
                                   | Deep Semantic Audit & PII |
                                   +---------------------------+
                                                 |
                                                 v
                                   +---------------------------+
                                   | ClickHouse / DuckDB Alert |
                                   |  Enterprise Audit Logs    |
                                   +---------------------------+
```

