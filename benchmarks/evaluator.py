"""Quantitative Batch Evaluator for Razorpay Revive (Meets Track 03 'The Bar')."""
import os
import json
from collections import defaultdict
from typing import List, Dict, Any, Optional
from app.models.schemas import FailureEvent, BatchBenchmarkSummary
from app.engine.pipeline import RevenueRecoveryPipeline
from app.storage.audit_log import AuditStore


class BenchmarkEvaluator:
    """Runs automated batch evaluations over synthetic failed payment records."""

    def __init__(self, db_path: Optional[str] = None):
        # Allow AuditStore to default to /tmp on Vercel serverless environment
        self.audit_store = AuditStore(db_path=db_path)
        self.pipeline = RevenueRecoveryPipeline(audit_store=self.audit_store)

    def evaluate_dataset(self, dataset: List[Dict[str, Any]], seed: int = 42) -> BatchBenchmarkSummary:
        """Executes full evaluation across all records in the batch."""
        self.audit_store.clear()
        
        total_at_risk = 0.0
        total_recovered = 0.0
        total_cost = 0.0
        guardrail_passes = 0
        category_stats = defaultdict(lambda: {
            "count": 0,
            "at_risk_inr": 0.0,
            "recovered_inr": 0.0,
            "cost_inr": 0.0,
            "recovered_count": 0,
            "actions": defaultdict(int),
        })

        for record in dataset:
            event = FailureEvent(**record)
            total_at_risk += event.amount

            # Run through full autonomous pipeline
            result = self.pipeline.process_event(event)

            cat = result["diagnosis"]["category"]
            act = result["plan"]["action_type"]
            cost = result["plan"]["cost_of_intervention_inr"]
            rec_money = result["execution"]["money_recovered_inr"]
            is_approved = result["guardrail_verdict"]["is_approved"]

            total_recovered += rec_money
            total_cost += cost
            if is_approved:
                guardrail_passes += 1

            cat_dict = category_stats[cat]
            cat_dict["count"] += 1
            cat_dict["at_risk_inr"] += event.amount
            cat_dict["recovered_inr"] += rec_money
            cat_dict["cost_inr"] += cost
            cat_dict["actions"][act] += 1
            if result["execution"]["status"] == "RECOVERED":
                cat_dict["recovered_count"] += 1

        total_txns = len(dataset)
        gross_rate = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0.0
        net_value = total_recovered - total_cost
        roi_multiple = (total_recovered / total_cost) if total_cost > 0 else 999.0
        guardrail_pct = (guardrail_passes / total_txns * 100) if total_txns > 0 else 100.0

        formatted_categories = {}
        for cat, data in category_stats.items():
            cat_rate = (data["recovered_inr"] / data["at_risk_inr"] * 100) if data["at_risk_inr"] > 0 else 0.0
            formatted_categories[cat] = {
                "count": data["count"],
                "at_risk_inr": round(data["at_risk_inr"], 2),
                "recovered_inr": round(data["recovered_inr"], 2),
                "recovery_rate_pct": round(cat_rate, 2),
                "intervention_cost_inr": round(data["cost_inr"], 2),
                "dominant_actions": dict(data["actions"]),
            }

        return BatchBenchmarkSummary(
            total_transactions_processed=total_txns,
            total_value_at_risk_inr=round(total_at_risk, 2),
            total_value_recovered_inr=round(total_recovered, 2),
            gross_recovery_rate_pct=round(gross_rate, 2),
            total_intervention_cost_inr=round(total_cost, 2),
            net_economic_value_inr=round(net_value, 2),
            roi_multiple=round(roi_multiple, 2),
            guardrail_adherence_pct=round(guardrail_pct, 2),
            breakdown_by_category=formatted_categories,
        )
