"""Failure Taxonomy & Root Cause Diagnostic Engine for Razorpay Revive."""
from typing import Optional
from app.models.schemas import FailureEvent, DiagnosisResult, FailureCategory


class FailureClassifier:
    """Diagnoses payment drop-offs and failures into strict fintech taxonomy categories."""

    def __init__(self, llm_client: Optional[object] = None):
        self.llm_client = llm_client

    def diagnose(self, event: FailureEvent) -> DiagnosisResult:
        """Deterministically classifies failure root causes with rich domain logic."""
        code = (event.error_code or "").upper()
        desc = (event.error_description or "").upper()
        method = event.payment_method.value if hasattr(event.payment_method, "value") else str(event.payment_method)
        combined = f"{code} {desc}"

        # 1. Fraud or Hard Card/Account Block (Check first for security)
        if any(term in combined for term in ["FRAUD", "STOLEN", "BLOCKED", "RISK_REJECTED", "LOST_CARD", "HOTLIST", "DECLINED_SECURITY"]):
            return DiagnosisResult(
                event_id=event.event_id,
                category=FailureCategory.FRAUD_OR_CARD_BLOCKED,
                confidence_score=0.98,
                is_transient=False,
                root_cause_explanation="Hard block triggered by issuing bank risk sentinel. Strictly non-retryable to prevent chargeback risk.",
                recommended_recovery_window_minutes=0,
            )

        # 2. B2B Overdue Invoices
        if "b2b" in method or any(term in combined for term in ["INVOICE_OVERDUE", "DUE_DATE_PASSED", "B2B_PENDING", "TERMS_EXCEEDED", "NET30", "ACCOUNTS_PAYABLE"]):
            return DiagnosisResult(
                event_id=event.event_id,
                category=FailureCategory.B2B_OVERDUE_INVOICE,
                confidence_score=0.95,
                is_transient=False,
                root_cause_explanation="Commercial B2B invoice pending accounts payable clearance. Requires structured dunning sequence.",
                recommended_recovery_window_minutes=1440,  # Next business morning
            )

        # 3. Mandate / UPI Autopay Expiry or Revocation
        if "autopay" in method or any(term in combined for term in ["MANDATE", "AUTOPAY", "REVOKED", "LIMIT_BREACHED", "SUBSCRIPTION"]):
            return DiagnosisResult(
                event_id=event.event_id,
                category=FailureCategory.MANDATE_EXPIRED_OR_REVOKED,
                confidence_score=0.94,
                is_transient=False,
                root_cause_explanation="Recurring mandate inactive or limit breached. Direct gateway re-charge will fail without re-authorization or alternate payment link.",
                recommended_recovery_window_minutes=15,
            )

        # 4. Checkout / Cart Abandonment
        if any(term in combined for term in ["CART", "CHECKOUT", "DROP_OFF", "PAGE_CLOSED", "EXIT_INTENT", "ABANDONED", "STEP_2"]):
            return DiagnosisResult(
                event_id=event.event_id,
                category=FailureCategory.CHECKOUT_ABANDONMENT,
                confidence_score=0.92,
                is_transient=False,
                root_cause_explanation="Customer abandoned checkout flow during intent phase. High conversion potential via personalized conversational nudge.",
                recommended_recovery_window_minutes=10,
            )

        # 5. OTP / 2FA Auth Timeout
        if any(term in combined for term in ["OTP", "2FA", "AUTH_TIMEOUT", "AUTH_SESSION", "USER_DROPPED_AUTH", "PAYMENT_TIMED_OUT", "3DS"]):
            return DiagnosisResult(
                event_id=event.event_id,
                category=FailureCategory.AUTH_OR_OTP_TIMEOUT,
                confidence_score=0.96,
                is_transient=True,
                root_cause_explanation="Session expired during 2FA / OTP entry. Friction can be eliminated via 1-click Razorpay dynamic payment link or UPI intent.",
                recommended_recovery_window_minutes=3,
            )

        # 6. Insufficient Funds / Low Balance
        if any(term in combined for term in ["INSUFFICIENT", "LOW_BALANCE", "DECLINED_BY_BANK", "NOT_ENOUGH", "BALANCE_LOW", "DAILY_LIMIT"]):
            return DiagnosisResult(
                event_id=event.event_id,
                category=FailureCategory.INSUFFICIENT_FUNDS,
                confidence_score=0.93,
                is_transient=True,
                root_cause_explanation="Transaction declined due to customer account balance. Optimal intervention requires timed retry after morning salary credits or low-friction UPI link.",
                recommended_recovery_window_minutes=360,  # 6 hours later or next morning
            )

        # 7. Transient Bank / Network Downtime
        if any(term in combined for term in ["TIMEOUT", "GATEWAY", "DOWNTIME", "SWITCH", "BUSY", "CONGESTION", "SERVER_ERROR", "503", "504", "NPCI", "NETWORK", "BAD_GATEWAY", "UNAVAILABLE"]):
            return DiagnosisResult(
                event_id=event.event_id,
                category=FailureCategory.TRANSIENT_BANK_DOWNTIME,
                confidence_score=0.97,
                is_transient=True,
                root_cause_explanation="Temporary issuing bank or NPCI switch outage. Highly recoverable via intelligent retry backoff once telemetry clears.",
                recommended_recovery_window_minutes=20,
            )

        # Fallback / Generic
        return DiagnosisResult(
            event_id=event.event_id,
            category=FailureCategory.GENERIC_UNKNOWN_FAILURE,
            confidence_score=0.75,
            is_transient=True,
            root_cause_explanation=f"General transaction drop-off ({event.error_code}). Standard multi-channel recovery flow recommended.",
            recommended_recovery_window_minutes=15,
        )
