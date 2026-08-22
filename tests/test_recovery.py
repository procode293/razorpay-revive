"""Unit & Integration Tests for Razorpay Revive (AI Revenue Recovery Engine)."""
import pytest
from datetime import datetime, timezone
from app.models.schemas import (
    FailureEvent,
    CustomerProfile,
    PaymentMethod,
    CustomerSegment,
    FailureCategory,
    InterventionActionType,
    InterventionPlan,
)
from app.engine.classifier import FailureClassifier
from app.engine.planner import InterventionPlanner
from app.engine.guardrails import FintechGuardrailEngine
from app.engine.executor import ActionExecutor
from app.engine.pipeline import RevenueRecoveryPipeline
from app.storage.audit_log import AuditStore
from pydantic import ValidationError


@pytest.fixture
def sample_customer():
    return CustomerProfile(
        customer_id="cust_test_001",
        name="Rohan Mehta",
        phone="+919876543210",
        email="rohan.mehta@example.com",
        segment=CustomerSegment.HIGH_LTV,
    )


@pytest.fixture
def sample_transient_event(sample_customer):
    return FailureEvent(
        event_id="evt_test_001",
        order_id="order_test_101",
        amount=1499.0,
        payment_method=PaymentMethod.UPI,
        error_code="GATEWAY_TIMEOUT_HDFC",
        error_description="HDFC switch timed out during response packet read",
        retry_count=0,
        customer=sample_customer,
    )


def test_failure_classifier_categories(sample_customer):
    classifier = FailureClassifier()

    # 1. Transient Downtime
    res1 = classifier.diagnose(FailureEvent(
        event_id="e1", order_id="o1", amount=500, payment_method=PaymentMethod.UPI,
        error_code="NPCI_SWITCH_BUSY", error_description="503 bank busy", customer=sample_customer
    ))
    assert res1.category == FailureCategory.TRANSIENT_BANK_DOWNTIME
    assert res1.is_transient is True

    # 2. Insufficient Funds
    res2 = classifier.diagnose(FailureEvent(
        event_id="e2", order_id="o2", amount=500, payment_method=PaymentMethod.DEBIT_CARD,
        error_code="INSUFFICIENT_FUNDS_SBI", error_description="Declined low balance", customer=sample_customer
    ))
    assert res2.category == FailureCategory.INSUFFICIENT_FUNDS

    # 3. OTP Timeout
    res3 = classifier.diagnose(FailureEvent(
        event_id="e3", order_id="o3", amount=500, payment_method=PaymentMethod.CREDIT_CARD,
        error_code="OTP_EXPIRED_2FA", error_description="Auth window timed out", customer=sample_customer
    ))
    assert res3.category == FailureCategory.AUTH_OR_OTP_TIMEOUT

    # 4. Fraud Block
    res4 = classifier.diagnose(FailureEvent(
        event_id="e4", order_id="o4", amount=500, payment_method=PaymentMethod.CREDIT_CARD,
        error_code="FRAUD_HOTLISTED_CARD", error_description="Stolen card decline", customer=sample_customer
    ))
    assert res4.category == FailureCategory.FRAUD_OR_CARD_BLOCKED
    assert res4.is_transient is False

    # 5. Cart Abandonment
    res5 = classifier.diagnose(FailureEvent(
        event_id="e5", order_id="o5", amount=1200, payment_method=PaymentMethod.UPI,
        error_code="CART_DROP_OFF_HIGH_INTENT", error_description="Step 2 exit", customer=sample_customer
    ))
    assert res5.category == FailureCategory.CHECKOUT_ABANDONMENT

    # 6. B2B Overdue Invoice
    res6 = classifier.diagnose(FailureEvent(
        event_id="e6", order_id="o6", amount=55000, payment_method=PaymentMethod.B2B_INVOICE,
        error_code="INVOICE_NET30_OVERDUE", error_description="Accounts payable term passed", customer=sample_customer
    ))
    assert res6.category == FailureCategory.B2B_OVERDUE_INVOICE


def test_guardrails_enforce_max_retry_limit(sample_customer):
    guardrails = FintechGuardrailEngine()
    classifier = FailureClassifier()
    planner = InterventionPlanner()

    # Event already tried 3 times
    event_exhausted = FailureEvent(
        event_id="e_max", order_id="o_max", amount=999, payment_method=PaymentMethod.UPI,
        error_code="GATEWAY_TIMEOUT_HDFC", error_description="Timed out",
        retry_count=3, customer=sample_customer
    )

    diag = classifier.diagnose(event_exhausted)
    plan = planner.create_plan(event_exhausted, diag)
    assert plan.action_type == InterventionActionType.HARD_STOP_ESCALATE

    verdict = guardrails.verify_plan(event_exhausted, plan)
    assert verdict.is_approved is True  # Allowed as ESCALATE stop rule


def test_guardrails_schema_and_policy_bounds(sample_customer):
    guardrails = FintechGuardrailEngine()
    event = FailureEvent(
        event_id="e_disc", order_id="o_disc", amount=1000, payment_method=PaymentMethod.UPI,
        error_code="CART_DROP_OFF", error_description="Abandoned cart",
        customer=sample_customer
    )

    # 1. Pydantic level validation rejects discount > 10%
    with pytest.raises(ValidationError):
        InterventionPlan(
            plan_id="p_illegal",
            event_id="e_disc",
            action_type=InterventionActionType.BOUNDED_DISCOUNT_OFFER,
            channel="WHATSAPP",
            delay_minutes=0,
            discount_percentage=25.0,  # Breaches <= 10.0 schema constraint
            expected_success_probability=0.8,
            cost_of_intervention_inr=0.5,
            explanation="Attempted excessive discount",
        )

    # 2. Guardrail verifies valid bounded 5% discount passes
    valid_plan = InterventionPlan(
        plan_id="p_valid",
        event_id="e_disc",
        action_type=InterventionActionType.BOUNDED_DISCOUNT_OFFER,
        channel="WHATSAPP",
        delay_minutes=0,
        discount_percentage=5.0,
        expected_success_probability=0.8,
        cost_of_intervention_inr=0.5,
        explanation="Bounded 5% promotional incentive",
    )
    verdict = guardrails.verify_plan(event, valid_plan)
    assert verdict.is_approved is True


def test_end_to_end_pipeline_execution(sample_transient_event, tmp_path):
    db_file = str(tmp_path / "test_audit.db")
    audit_store = AuditStore(db_path=db_file)
    pipeline = RevenueRecoveryPipeline(audit_store=audit_store)

    result = pipeline.process_event(sample_transient_event, deterministic_outcome=True)

    assert result["event"]["event_id"] == "evt_test_001"
    assert result["diagnosis"]["category"] == FailureCategory.TRANSIENT_BANK_DOWNTIME.value
    assert result["guardrail_verdict"]["is_approved"] is True
    assert result["execution"]["status"] == "RECOVERED"
    assert result["execution"]["money_recovered_inr"] == 1499.0

    # Verify audit store record
    traces = audit_store.get_recent_traces(10)
    assert len(traces) == 1
    assert traces[0]["status"] == "RECOVERED"
