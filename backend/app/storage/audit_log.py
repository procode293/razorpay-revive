"""Immutable Audit Trail & Recovery Storage for Razorpay Revive."""
import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.models.schemas import (
    FailureEvent,
    DiagnosisResult,
    InterventionPlan,
    GuardrailVerdict,
    ExecutionResult,
)


class AuditStore:
    """Thread-safe SQLite store for financial audit logging and recovery metrics."""

    def __init__(self, db_path: Optional[str] = None):
        # On Vercel / serverless lambda, write to writable /tmp directory
        if db_path is None:
            if os.getenv("VERCEL"):
                self.db_path = "/tmp/revive_audit.db"
            else:
                self.db_path = "revive_audit.db"
        else:
            self.db_path = db_path

        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recovery_traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE,
                    order_id TEXT,
                    customer_name TEXT,
                    amount REAL,
                    payment_method TEXT,
                    error_code TEXT,
                    category TEXT,
                    action_type TEXT,
                    channel TEXT,
                    guardrail_approved INTEGER,
                    status TEXT,
                    money_recovered REAL,
                    net_value_saved REAL,
                    razorpay_ref TEXT,
                    payment_link TEXT,
                    trace_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def record_cycle(
        self,
        event: FailureEvent,
        diagnosis: DiagnosisResult,
        plan: InterventionPlan,
        verdict: GuardrailVerdict,
        execution: ExecutionResult,
    ):
        """Atomically records a full recovery lifecycle execution with immutable trace."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO recovery_traces (
                    event_id, order_id, customer_name, amount, payment_method, error_code,
                    category, action_type, channel, guardrail_approved, status,
                    money_recovered, net_value_saved, razorpay_ref, payment_link, trace_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event.event_id,
                    event.order_id,
                    event.customer.name,
                    event.amount,
                    event.payment_method.value if hasattr(event.payment_method, "value") else str(event.payment_method),
                    event.error_code,
                    diagnosis.category.value if hasattr(diagnosis.category, "value") else str(diagnosis.category),
                    plan.action_type.value if hasattr(plan.action_type, "value") else str(plan.action_type),
                    plan.channel,
                    1 if verdict.is_approved else 0,
                    execution.status,
                    execution.money_recovered_inr,
                    execution.net_value_saved_inr,
                    execution.razorpay_reference_id,
                    execution.payment_link_url,
                    json.dumps(execution.audit_trace),
                ),
            )
            conn.commit()

    def get_recent_traces(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent recovery operations."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM recovery_traces ORDER BY id DESC LIMIT ?", (limit,)
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["trace"] = json.loads(item["trace_json"]) if item.get("trace_json") else []
                results.append(item)
            return results

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Calculates macro recovery metrics for dashboard & reporting."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_events,
                    COALESCE(SUM(amount), 0.0) as total_at_risk,
                    COALESCE(SUM(money_recovered), 0.0) as total_recovered,
                    COALESCE(SUM(net_value_saved), 0.0) as net_saved,
                    COALESCE(SUM(CASE WHEN status = 'RECOVERED' THEN 1 ELSE 0 END), 0) as recovered_count,
                    COALESCE(SUM(CASE WHEN guardrail_approved = 1 THEN 1 ELSE 0 END), 0) as approved_count
                FROM recovery_traces
            """)
            row = cursor.fetchone()
            total = row["total_events"]
            total_at_risk = row["total_at_risk"]
            total_rec = row["total_recovered"]
            net_saved = row["net_saved"]
            rec_count = row["recovered_count"]
            appr_count = row["approved_count"]

            rec_rate = (total_rec / total_at_risk * 100) if total_at_risk > 0 else 0.0
            guardrail_pct = (appr_count / total * 100) if total > 0 else 100.0

            return {
                "total_events": total,
                "total_at_risk_inr": round(total_at_risk, 2),
                "total_recovered_inr": round(total_rec, 2),
                "net_value_saved_inr": round(net_saved, 2),
                "recovered_count": rec_count,
                "recovery_rate_pct": round(rec_rate, 2),
                "guardrail_compliance_pct": round(guardrail_pct, 2),
            }

    def clear(self):
        """Clears test data from the audit store."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recovery_traces")
            conn.commit()
