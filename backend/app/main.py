"""FastAPI Application Entrypoint for Razorpay Revive."""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import FailureEvent, CustomerProfile, PaymentMethod
from app.engine.pipeline import RevenueRecoveryPipeline
from app.storage.audit_log import AuditStore
from benchmarks.generate_dataset import generate_benchmark_dataset
from benchmarks.evaluator import BenchmarkEvaluator

app = FastAPI(
    title="Razorpay Revive — Autonomous AI Revenue Recovery Engine",
    description="Track 03 Submission for Razorpay AI Buildathon",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent Audit Store & Pipeline
audit_store = AuditStore()
pipeline = RevenueRecoveryPipeline(audit_store=audit_store)

# Static file mount for Dashboard UI
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Serves the interactive Razorpay Revive Dashboard UI."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Razorpay Revive API is live. Dashboard under /static/index.html"}


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Razorpay Revive",
        "track": "Track 03 — AI Revenue Recovery",
        "engine_version": "1.0.0",
    }


@app.post("/api/events/ingest")
async def ingest_failure_event(event: FailureEvent):
    """Ingests a live payment drop-off / failure and executes autonomous recovery."""
    try:
        result = pipeline.process_event(event)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.post("/api/recovery/simulate")
async def simulate_scenario(payload: Dict[str, Any]):
    """Simulates realistic scenarios from the interactive playground."""
    scenario_type = payload.get("scenario_type", "transient_hdfc")
    amount = float(payload.get("amount", 1999.0))
    customer_name = payload.get("customer_name", "Aarav Sharma")
    phone = payload.get("phone", "+919876543210")
    email = payload.get("email", "aarav.sharma@example.com")
    retry_count = int(payload.get("retry_count", 0))

    scenarios = {
        "transient_hdfc": {
            "error_code": "GATEWAY_TIMEOUT_HDFC",
            "desc": "HDFC UPI switch timed out during payment authorization",
            "method": PaymentMethod.UPI,
        },
        "insufficient_funds": {
            "error_code": "INSUFFICIENT_FUNDS_SBI",
            "desc": "Declined by bank due to insufficient funds in payer account",
            "method": PaymentMethod.DEBIT_CARD,
        },
        "otp_timeout": {
            "error_code": "OTP_EXPIRED_2FA",
            "desc": "Customer session expired while waiting for 2FA SMS code",
            "method": PaymentMethod.CREDIT_CARD,
        },
        "cart_abandoned": {
            "error_code": "CART_DROP_OFF_HIGH_INTENT",
            "desc": "User closed checkout modal after reviewing shipping info",
            "method": PaymentMethod.UPI,
        },
        "mandate_expired": {
            "error_code": "MANDATE_EXPIRED_SUB",
            "desc": "Recurring OTT subscription debit failed due to expired mandate",
            "method": PaymentMethod.UPI_AUTOPAY,
        },
        "b2b_overdue": {
            "error_code": "INVOICE_NET30_OVERDUE",
            "desc": "Enterprise invoice #INV-4902 passed 30-day payment term",
            "method": PaymentMethod.B2B_INVOICE,
        },
        "fraud_alert": {
            "error_code": "FRAUD_HOTLISTED_CARD",
            "desc": "Card declined by issuing bank fraud surveillance engine",
            "method": PaymentMethod.CREDIT_CARD,
        },
    }

    config = scenarios.get(scenario_type, scenarios["transient_hdfc"])
    event = FailureEvent(
        event_id=f"sim_{os.urandom(4).hex()}",
        order_id=f"order_sim_{os.urandom(3).hex()}",
        amount=amount,
        payment_method=config["method"],
        error_code=config["error_code"],
        error_description=config["desc"],
        retry_count=retry_count,
        customer=CustomerProfile(
            customer_id=f"cust_sim_{os.urandom(3).hex()}",
            name=customer_name,
            phone=phone,
            email=email,
        ),
    )

    result = pipeline.process_event(event)
    return JSONResponse(content=result)


@app.get("/api/audit-logs")
async def get_audit_logs(limit: int = 50):
    """Retrieves recent recovery execution traces for auditability."""
    traces = audit_store.get_recent_traces(limit=limit)
    return {"traces": traces}


@app.get("/api/metrics")
async def get_metrics():
    """Retrieves aggregate revenue recovery KPIs."""
    metrics = audit_store.get_metrics_summary()
    return metrics


@app.post("/api/benchmark/run")
async def trigger_benchmark_run():
    """Executes the full 100-record batch benchmark and returns comparative metrics."""
    dataset = generate_benchmark_dataset(100, seed=42)
    evaluator = BenchmarkEvaluator()
    summary = evaluator.evaluate_dataset(dataset)
    return summary.model_dump(mode="json")


@app.post("/api/audit-logs/clear")
async def clear_audit_logs():
    """Resets audit store for clean benchmark demonstrations."""
    audit_store.clear()
    return {"message": "Audit logs cleared successfully"}
