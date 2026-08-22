"""Pydantic schemas and domain models for Razorpay Revive."""
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


def utc_now():
    return datetime.now(timezone.utc)


class FailureCategory(str, Enum):
    TRANSIENT_BANK_DOWNTIME = "TRANSIENT_BANK_DOWNTIME"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    MANDATE_EXPIRED_OR_REVOKED = "MANDATE_EXPIRED_OR_REVOKED"
    AUTH_OR_OTP_TIMEOUT = "AUTH_OR_OTP_TIMEOUT"
    CHECKOUT_ABANDONMENT = "CHECKOUT_ABANDONMENT"
    B2B_OVERDUE_INVOICE = "B2B_OVERDUE_INVOICE"
    FRAUD_OR_CARD_BLOCKED = "FRAUD_OR_CARD_BLOCKED"
    GENERIC_UNKNOWN_FAILURE = "GENERIC_UNKNOWN_FAILURE"


class PaymentMethod(str, Enum):
    UPI = "upi"
    UPI_AUTOPAY = "upi_autopay"
    CREDIT_CARD = "card_credit"
    DEBIT_CARD = "card_debit"
    NETBANKING = "netbanking"
    B2B_INVOICE = "b2b_invoice"
    WALLET = "wallet"


class CustomerSegment(str, Enum):
    HIGH_LTV = "HIGH_LTV"
    MEDIUM_LTV = "MEDIUM_LTV"
    STANDARD = "STANDARD"


class CustomerProfile(BaseModel):
    customer_id: str
    name: str
    phone: str
    email: str
    preferred_language: str = "hinglish"  # 'en', 'hi', 'hinglish'
    segment: CustomerSegment = CustomerSegment.STANDARD
    historical_payment_success_rate: float = 0.85


class FailureEvent(BaseModel):
    event_id: str
    order_id: str
    payment_id: Optional[str] = None
    merchant_id: str = "rzp_merch_demo"
    merchant_name: str = "Acme Store India"
    amount: float = Field(..., gt=0, description="Amount in INR")
    currency: str = "INR"
    payment_method: PaymentMethod
    error_code: str
    error_description: str
    timestamp: datetime = Field(default_factory=utc_now)
    retry_count: int = 0
    customer: CustomerProfile
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DiagnosisResult(BaseModel):
    event_id: str
    category: FailureCategory
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    is_transient: bool
    root_cause_explanation: str
    recommended_recovery_window_minutes: int
    diagnosed_at: datetime = Field(default_factory=utc_now)


class InterventionActionType(str, Enum):
    AUTO_RETRY_SMART_WINDOW = "AUTO_RETRY_SMART_WINDOW"
    DYNAMIC_PAYMENT_LINK = "DYNAMIC_PAYMENT_LINK"
    PERSONALIZED_WHATSAPP_NUDGE = "PERSONALIZED_WHATSAPP_NUDGE"
    COMPLIANT_EMAIL_DUNNING = "COMPLIANT_EMAIL_DUNNING"
    HINGLISH_VOICE_OUTREACH = "HINGLISH_VOICE_OUTREACH"
    BOUNDED_DISCOUNT_OFFER = "BOUNDED_DISCOUNT_OFFER"
    HARD_STOP_ESCALATE = "HARD_STOP_ESCALATE"


class InterventionPlan(BaseModel):
    plan_id: str
    event_id: str
    action_type: InterventionActionType
    channel: str  # 'RAZORPAY_GATEWAY', 'WHATSAPP', 'EMAIL', 'VOICE_BOT', 'MERCHANT_DASHBOARD'
    delay_minutes: int = 0
    message_payload: Optional[str] = None
    discount_percentage: float = Field(0.0, ge=0.0, le=10.0, description="Strictly capped at 10%")
    expected_success_probability: float = Field(..., ge=0.0, le=1.0)
    cost_of_intervention_inr: float = Field(..., ge=0.0)
    explanation: str


class GuardrailVerdict(BaseModel):
    is_approved: bool
    policy_checks: Dict[str, str] = Field(
        default_factory=lambda: {
            "max_retries_limit": "PASS",
            "quiet_hours_policy": "PASS",
            "anti_spam_frequency": "PASS",
            "money_integrity_check": "PASS",
            "compliance_escalation_rule": "PASS",
        }
    )
    rejection_reason: Optional[str] = None
    mitigation_applied: Optional[str] = None
    evaluated_at: datetime = Field(default_factory=utc_now)


class ExecutionResult(BaseModel):
    execution_id: str
    event_id: str
    plan_id: str
    status: str  # 'RECOVERED', 'SCHEDULED_RETRY', 'FAILED', 'BLOCKED_BY_GUARDRAIL', 'ESCALATED'
    money_recovered_inr: float = 0.0
    net_value_saved_inr: float = 0.0
    razorpay_reference_id: Optional[str] = None
    payment_link_url: Optional[str] = None
    audit_trace: List[str] = Field(default_factory=list)
    executed_at: datetime = Field(default_factory=utc_now)


class BatchBenchmarkSummary(BaseModel):
    total_transactions_processed: int
    total_value_at_risk_inr: float
    total_value_recovered_inr: float
    gross_recovery_rate_pct: float
    total_intervention_cost_inr: float
    net_economic_value_inr: float
    roi_multiple: float
    guardrail_adherence_pct: float
    breakdown_by_category: Dict[str, Dict[str, Any]]
    generated_at: datetime = Field(default_factory=utc_now)
