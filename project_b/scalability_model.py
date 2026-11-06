"""
Enterprise Scalability and Cost Model for NYC 311 Data Quality Checker.
Models performance, throughput, infrastructure architecture, and operational cost
for 50 million rows/day across 120 enterprise customers.
"""

from typing import Dict, Any


def calculate_enterprise_scalability_model(
    daily_rows: int = 50_000_000,
    num_customers: int = 120,
    peak_multiplier: float = 3.0,
    llm_sample_routing_pct: float = 1.5
) -> Dict[str, Any]:
    """
    Computes rigorous throughput, hardware sizing, and cost breakdown
    for 50 million records/day across Rule, ML, LLM, and Cascading Hybrid architectures.
    """
    # 1. Throughput Dynamics
    seconds_per_day = 86400
    avg_qps = daily_rows / seconds_per_day
    peak_qps = avg_qps * peak_multiplier
    rows_per_customer_day = daily_rows / num_customers

    # 2. Infrastructure Sizing & Cloud Compute (AWS / GCP pricing baseline)
    # Rule engine: 25,000 rows/sec/core
    rule_cores_needed = max(4, int(peak_qps / 25000) * 2 + 2)
    # ML engine: 3,500 rows/sec/core
    ml_cores_needed = max(8, int(peak_qps / 3500) * 2 + 4)

    # 3. Pure LLM Architecture Costs (Gemini 1.5 Flash: $0.075/1M input, $0.30/1M output)
    # Average row: 220 input tokens, 35 output tokens
    pure_llm_daily_input_tokens = (daily_rows * 220)
    pure_llm_daily_output_tokens = (daily_rows * 35)
    pure_llm_daily_cost = (
        (pure_llm_daily_input_tokens / 1_000_000 * 0.075) +
        (pure_llm_daily_output_tokens / 1_000_000 * 0.30)
    )
    pure_llm_monthly_cost = pure_llm_daily_cost * 30.0
    pure_llm_annual_cost = pure_llm_daily_cost * 365.0

    # 4. Cascading Hybrid Architecture Costs
    # Rules + ML filter 98.5% of rows; only 1.5% routed to Gemini for ambiguous semantic verification
    hybrid_llm_daily_rows = daily_rows * (llm_sample_routing_pct / 100.0)
    hybrid_daily_input_tokens = hybrid_llm_daily_rows * 220
    hybrid_daily_output_tokens = hybrid_llm_daily_rows * 35
    hybrid_daily_llm_cost = (
        (hybrid_daily_input_tokens / 1_000_000 * 0.075) +
        (hybrid_daily_output_tokens / 1_000_000 * 0.30)
    )
    hybrid_monthly_llm_cost = hybrid_daily_llm_cost * 30.0

    # Compute & Stream Processing Infrastructure (Kafka cluster + Flink/Spark workers + Storage)
    kafka_monthly_cost = 280.0  # Managed AWS MSK 3-broker cluster
    stream_compute_monthly_cost = 320.0  # 4x c6g.2xlarge compute instances
    storage_monitoring_monthly = 150.0  # S3 tiered storage + CloudWatch metrics
    base_infra_monthly = kafka_monthly_cost + stream_compute_monthly_cost + storage_monitoring_monthly

    hybrid_total_monthly = base_infra_monthly + hybrid_monthly_llm_cost
    hybrid_annual_cost = hybrid_total_monthly * 12.0

    # 5. Comparative Economic Summary
    savings_monthly = pure_llm_monthly_cost - hybrid_total_monthly
    savings_annual = pure_llm_annual_cost - hybrid_annual_cost
    savings_pct = (savings_monthly / pure_llm_monthly_cost) * 100.0

    return {
        "workload_profile": {
            "daily_volume_records": f"{daily_rows:,}",
            "enterprise_tenants": num_customers,
            "mean_records_per_tenant_day": f"{int(rows_per_customer_day):,}",
            "average_throughput_qps": round(avg_qps, 1),
            "peak_throughput_qps_3x": round(peak_qps, 1),
            "daily_uncompressed_data_gb": round(daily_rows * 1.0 / (1024 * 1024), 1)  # ~47.7 GB/day
        },
        "pure_rule_based_architecture": {
            "compute_spec": f"{rule_cores_needed} vCPUs (2x AWS c6g.xlarge)",
            "monthly_compute_cost_usd": 135.0,
            "monthly_token_cost_usd": 0.0,
            "total_monthly_cost_usd": 135.0,
            "total_annual_cost_usd": 1620.0,
            "latency_p95_ms": 0.8,
            "strengths": "Ultra-low cost, deterministic, microsecond latency",
            "limitations": "Rigid; misses novel semantic variations and complex PII"
        },
        "pure_ml_statistical_architecture": {
            "compute_spec": f"{ml_cores_needed} vCPUs (4x AWS c6g.2xlarge)",
            "monthly_compute_cost_usd": 380.0,
            "monthly_token_cost_usd": 0.0,
            "total_monthly_cost_usd": 380.0,
            "total_annual_cost_usd": 4560.0,
            "latency_p95_ms": 4.5,
            "strengths": "Captures spatial outliers, clustering, null spikes without hard rules",
            "limitations": "False positives on multimodal data; black-box explanations"
        },
        "pure_gemini_llm_architecture": {
            "compute_spec": "32 vCPUs HTTP dispatch workers + massive connection pooling",
            "monthly_compute_cost_usd": 650.0,
            "monthly_token_cost_usd": round(pure_llm_monthly_cost, 2),
            "total_monthly_cost_usd": round(pure_llm_monthly_cost + 650.0, 2),
            "total_annual_cost_usd": round(pure_llm_annual_cost + 7800.0, 2),
            "daily_token_volume": f"{(pure_llm_daily_input_tokens + pure_llm_daily_output_tokens) / 1e9:.2f} Billion tokens/day",
            "latency_p95_ms": 650.0,
            "strengths": "Superior semantic understanding and human-like explainability",
            "limitations": "Prohibitive financial cost (~$42k+/month), massive rate limit pressure, high latency"
        },
        "cascading_hybrid_architecture": {
            "compute_spec": "Managed Kafka (MSK) + Apache Flink + 4x c6g.2xlarge + Gemini 1.5 Flash micro-batch pool",
            "monthly_compute_infra_cost_usd": base_infra_monthly,
            "monthly_token_cost_usd": round(hybrid_monthly_llm_cost, 2),
            "total_monthly_cost_usd": round(hybrid_total_monthly, 2),
            "total_annual_cost_usd": round(hybrid_annual_cost, 2),
            "latency_p95_ms": 2.2,
            "llm_workload_reduction_pct": f"{100.0 - llm_sample_routing_pct:.1f}%",
            "monthly_savings_vs_pure_llm_usd": round(savings_monthly, 2),
            "annual_savings_vs_pure_llm_usd": round(savings_annual, 2),
            "savings_pct": round(savings_pct, 2),
            "production_architecture_recommendation": (
                "Deploy Kafka + Apache Flink for real-time Tier 1 rule validation. "
                "Route 1.5% borderline semantic flags into an asynchronous SQS queue "
                "drained by worker pods calling Gemini 1.5 Flash in micro-batches of 20."
            )
        }
    }


if __name__ == "__main__":
    import json
    model = calculate_enterprise_scalability_model()
    print("=== NYC 311 50M ROWS/DAY ENTERPRISE SCALABILITY MODEL ===")
    print(json.dumps(model, indent=2))

