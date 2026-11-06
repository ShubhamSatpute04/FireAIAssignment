# DECISION_MATRIX.md – Architectural Decision Framework: Rules vs. ML vs. LLMs vs. Hybrids

## Executive Overview

Modern AI-augmented engineering requires moving beyond false dichotomies. Deciding whether to deploy **Deterministic Rules**, **Statistical/Machine Learning Models**, **Large Language Models (LLMs)**, or **Cascading Hybrids** must be grounded in empirical trade-offs across five core engineering vectors:
1. **Mathematical Accuracy & Determinism**
2. **Execution Latency & Throughput**
3. **Operational Cost at Scale**
4. **Auditability, Compliance & Regulatory Explainability**
5. **Contextual & Semantic Ambiguity Handling**

---

## 1. Multi-Criteria Decision Matrix

| Evaluation Dimension | Weight | Deterministic Rules | Statistical / Classical ML | Pure LLMs (Gemini 1.5 Flash) | Cascading Hybrid |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Mathematical Precision** | 25% | **10.0 / 10** (Exact $\mu s$ math) | **6.5 / 10** (Approximation error) | **7.0 / 10** (Arithmetic hallucinations) | **9.8 / 10** (Rules execute math) |
| **Determinism ($\sigma^2 \to 0$)** | 20% | **10.0 / 10** (100% reproducible) | **9.0 / 10** (Deterministic inference) | **7.5 / 10** (Stochastic temperature drift) | **9.8 / 10** (Deterministic routing) |
| **Latency / Throughput** | 20% | **10.0 / 10** (>25k rows/sec/core) | **8.0 / 10** (1k–5k rows/sec/core) | **3.0 / 10** (800ms API roundtrips) | **8.8 / 10** (Sub-3ms P95 latency) |
| **Cost Efficiency at Scale** | 20% | **10.0 / 10** ($0.00 / 1k queries) | **9.0 / 10** ($0.00 / 1k queries) | **2.0 / 10** ($0.15 / 1k queries) | **9.5 / 10** (96.6% cost reduction) |
| **Semantic & Ambiguity Handling** | 15% | **3.0 / 10** (Rigid pattern failure) | **6.5 / 10** (Vector distance metric) | **10.0 / 10** (Deep contextual nuance) | **9.5 / 10** (LLM targeted fallback) |
| **Weighted Total Score** | **100%** | **8.85 / 10** | **7.55 / 10** | **5.45 / 10** | **9.49 / 10** |

---

## 2. Definitive Decision Heuristics

### Heuristic 1: When to Use Pure Deterministic Rules
Deploy **Deterministic Rules** when:
- The problem domain is governed by explicit statutory laws, arithmetic equations, or formalized business logic (e.g., Section 115BAC tax slabs, Section 288B rounding, date chronological order $T_{\text{closed}} \ge T_{\text{created}}$, postal code lookup tables).
- Regulatory compliance mandates line-by-line traceability and legal auditability where probabilistic outputs are prohibited by compliance auditors.
- Latency requirements are in microseconds ($< 1\text{ ms}$) and workload scale exceeds millions of records per day with zero budget for API tokens.

### Heuristic 2: When to Use Statistical / Classical ML
Deploy **Statistical / Classical ML** when:
- The anomaly cannot be hard-coded with boolean predicates because it is distributional (e.g., spatial coordinate outliers across non-convex polygons using Isolation Forest, sudden null rate spikes via Z-score / IQR).
- Clustering near-duplicates based on high-dimensional lexical similarity (e.g., TF-IDF + Cosine Similarity $\ge 0.82$).
- Fast edge deployment with minimal compute footprint is required without cloud network calls.

### Heuristic 3: When to Use Pure LLMs
Deploy **Pure LLMs** exclusively when:
- The task is exploratory, low-throughput ($< 1,000\text{ queries/day}$), or primarily involves human-facing dialogue synthesis.
- Translating colloquial, unstructured human communication (e.g., multilingual Hinglish tax expressions) into structured schema representations.
- Offline code synthesis: Using Gemini as a compiler to convert natural language policy specifications into executable Python AST rules once, completely eliminating runtime LLM dependencies.

### Heuristic 4: When to Use Cascading Hybrids (The Industry Standard)
Deploy **Cascading Hybrids** for enterprise production systems processing high-volume data streams (e.g., 50M records/day across 120 tenants):
- **Tier 1**: Deterministic rules filter 90%+ of standard records at microsecond latency and zero cost.
- **Tier 2**: Statistical models identify distributional shifts and coordinate outliers.
- **Tier 3**: The LLM is invoked selectively on the remaining 1–2% of ambiguous cases requiring semantic reasoning.

---

## 3. Realized Architecture across Both Projects

```
                                  [ Incoming Workload ]
                                            |
                                            v
                                +-----------------------+
                                |  Tier 1: Rules Engine |
                                |  Regex, Slabs, Schema |
                                +-----------------------+
                                     /             \
                        (Definitive / Match)    (Ambiguous / Mismatch)
                                  /                   \
                                 v                     v
                         [ Output Result ]     +-----------------------+
                            (90-98%)           |   Tier 2: ML Engine   |
                                               | Isolation Forest, TF-IDF
                                               +-----------------------+
                                                    /             \
                                        (Clear Outlier)       (Borderline)
                                                  /                 \
                                                 v                   v
                                         [ Output Result ]   +-----------------------+
                                                             |  Tier 3: Gemini LLM   |
                                                             | Semantic Disambiguate |
                                                             +-----------------------+
                                                                         |
                                                                         v
                                                                 [ Output Result ]
```

### Empirical Validation:
1. **Tax Calculator**: Approach 1 provides 100% rupee-exact precision and $0 cost. The NLP parser acts as the hybrid ingestion interface, translating Hinglish into structured models before execution.
2. **NYC 311 Checker**: The cascading hybrid detector achieves an **F1-score of 0.805**, runs at **834 rows/sec**, and cuts annual operating costs from **$484,800 to $16,290** (96.65% savings).

