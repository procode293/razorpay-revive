"""Command-line Batch Benchmark Runner for Razorpay Revive (Track 03 Submission)."""
import os
import sys
import json
from pathlib import Path

# Ensure UTF-8 output on all platforms (including Windows cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from benchmarks.generate_dataset import generate_benchmark_dataset
from benchmarks.evaluator import BenchmarkEvaluator


def main():
    print("=" * 80)
    print("  RAZORPAY REVIVE -- AUTONOMOUS AI REVENUE RECOVERY BENCHMARK SUITE")
    print("  Track 03: AI Revenue Recovery | Batch Evaluation across 100+ Transactions")
    print("=" * 80)

    dataset_path = Path(__file__).parent / "benchmarks" / "dataset_100.json"
    if not dataset_path.exists():
        print("[*] Generating 100 synthetic payment failure test cases...")
        dataset = generate_benchmark_dataset(100, seed=42)
        with open(dataset_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2)
    else:
        print(f"[*] Loading existing benchmark dataset from {dataset_path}...")
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

    print(f"[*] Executing autonomous recovery pipeline across {len(dataset)} transactions...\n")
    evaluator = BenchmarkEvaluator()
    summary = evaluator.evaluate_dataset(dataset)

    print("-" * 80)
    print("  BATCH PERFORMANCE SUMMARY (THE BAR EVALUATION METRICS)")
    print("-" * 80)
    print(f"  * Total Failed Transactions Processed : {summary.total_transactions_processed}")
    print(f"  * Total Value at Risk                 : INR {summary.total_value_at_risk_inr:,.2f}")
    print(f"  * Total Value Recovered               : INR {summary.total_value_recovered_inr:,.2f}")
    print(f"  * Gross Recovery Rate                 : {summary.gross_recovery_rate_pct:.2f}%")
    print(f"  * Total Intervention Cost (API/Nudge) : INR {summary.total_intervention_cost_inr:,.2f}")
    print(f"  * Net Economic Value Added            : INR {summary.net_economic_value_inr:,.2f}")
    print(f"  * Net ROI Multiple                    : {summary.roi_multiple:.1f}x")
    print(f"  * Fintech Guardrail Adherence         : {summary.guardrail_adherence_pct:.2f}%")
    print("-" * 80)

    print("\n  BREAKDOWN BY FAILURE TAXONOMY CATEGORY:")
    print(f"  {'Category':<30} | {'Count':<5} | {'At Risk (INR)':<14} | {'Recovered (INR)':<15} | {'Rec Rate':<8}")
    print("  " + "-" * 80)
    for cat, data in summary.breakdown_by_category.items():
        print(
            f"  {cat:<30} | {data['count']:<5} | INR {data['at_risk_inr']:>10,.2f} | INR {data['recovered_inr']:>11,.2f} | {data['recovery_rate_pct']:>6.1f}%"
        )
    print("  " + "-" * 80)

    out_file = Path(__file__).parent / "benchmarks" / "benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary.model_dump(mode="json"), f, indent=2)

    print(f"\n[✓] Benchmark execution complete. Report exported to: {out_file}\n")


if __name__ == "__main__":
    main()
