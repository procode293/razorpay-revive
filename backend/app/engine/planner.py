"""Dynamic Recovery Intervention Planner for Razorpay Revive."""
import uuid
from typing import Optional
from app.models.schemas import (
    FailureEvent,
    DiagnosisResult,
    FailureCategory,
    InterventionPlan,
    InterventionActionType,
    CustomerSegment,
    MerchantPolicyConfig,
)


class InterventionPlanner:
    """Calculates the highest-ROI, lowest-friction recovery intervention plan."""

    def __init__(self, llm_client: Optional[object] = None):
        self.llm_client = llm_client

    def create_plan(
        self,
        event: FailureEvent,
        diagnosis: DiagnosisResult,
        policy: Optional[MerchantPolicyConfig] = None,
    ) -> InterventionPlan:
        """Generates a bounded, multi-channel recovery intervention plan."""
        cfg = policy or MerchantPolicyConfig()
        plan_id = f"plan_{uuid.uuid4().hex[:10]}"
        customer_name = event.customer.name.split()[0] if event.customer.name else "Customer"
        amount_fmt = f"₹{event.amount:,.2f}"

        # Hard stop if retry count reached ceiling
        if event.retry_count >= cfg.max_retries:
            return InterventionPlan(
                plan_id=plan_id,
                event_id=event.event_id,
                action_type=InterventionActionType.HARD_STOP_ESCALATE,
                channel="MERCHANT_DASHBOARD",
                delay_minutes=0,
                message_payload=None,
                discount_percentage=0.0,
                expected_success_probability=0.0,
                cost_of_intervention_inr=0.0,
                explanation=f"Maximum {cfg.max_retries} retry attempts exhausted. Stopping automated workflow to prevent customer fatigue.",
            )

        # 1. FRAUD / RISK
        if diagnosis.category == FailureCategory.FRAUD_OR_CARD_BLOCKED:
            return InterventionPlan(
                plan_id=plan_id,
                event_id=event.event_id,
                action_type=InterventionActionType.HARD_STOP_ESCALATE,
                channel="MERCHANT_DASHBOARD",
                delay_minutes=0,
                message_payload=None,
                discount_percentage=0.0,
                expected_success_probability=0.0,
                cost_of_intervention_inr=0.0,
                explanation="Card blocked or flagged by risk sentinel. Escalating to merchant for manual review.",
            )

        # 2. TRANSIENT BANK DOWNTIME
        if diagnosis.category == FailureCategory.TRANSIENT_BANK_DOWNTIME:
            delay = 15 * (2 ** event.retry_count)  # 15m, 30m, 60m backoff
            return InterventionPlan(
                plan_id=plan_id,
                event_id=event.event_id,
                action_type=InterventionActionType.AUTO_RETRY_SMART_WINDOW,
                channel="RAZORPAY_GATEWAY",
                delay_minutes=delay,
                message_payload=None,
                discount_percentage=0.0,
                expected_success_probability=0.88,
                cost_of_intervention_inr=0.0,
                explanation=f"Transient switch failure detected. Scheduling silent background gateway retry in {delay} mins during high-uptime window.",
            )

        # 3. AUTH / OTP TIMEOUT
        if diagnosis.category == FailureCategory.AUTH_OR_OTP_TIMEOUT:
            msg = (
                f"Namaste {customer_name}! Aapka {amount_fmt} ka payment OTP timeout ki wajah se pura nahi hua. "
                f"Humne aapke liye 1-click Razorpay payment link generate kiya hai: {{payment_link}}. Direct UPI ya Card se complete karein."
            )
            return InterventionPlan(
                plan_id=plan_id,
                event_id=event.event_id,
                action_type=InterventionActionType.DYNAMIC_PAYMENT_LINK,
                channel="WHATSAPP",
                delay_minutes=2,
                message_payload=msg,
                discount_percentage=0.0,
                expected_success_probability=0.78,
                cost_of_intervention_inr=0.50,
                explanation="OTP expired during session. Instant 1-click payment link dispatched via WhatsApp eliminates checkout friction.",
            )

        # 4. INSUFFICIENT FUNDS
        if diagnosis.category == FailureCategory.INSUFFICIENT_FUNDS:
            msg = (
                f"Namaste {customer_name}, aapka {amount_fmt} ka payment process nahi ho paya. "
                f"Aap alternate UPI app, Credit Card, ya netbanking use karke yahan se retry kar sakte hain: {{payment_link}}"
            )
            return InterventionPlan(
                plan_id=plan_id,
                event_id=event.event_id,
                action_type=InterventionActionType.PERSONALIZED_WHATSAPP_NUDGE,
                channel="WHATSAPP",
                delay_minutes=180,  # Send after buffer
                message_payload=msg,
                discount_percentage=0.0,
                expected_success_probability=0.64,
                cost_of_intervention_inr=0.50,
                explanation="Low balance decline. Dispatched gentle nudge offering alternate payment rails (Card/Alternate UPI).",
            )

        # 5. CHECKOUT ABANDONMENT
        if diagnosis.category == FailureCategory.CHECKOUT_ABANDONMENT:
            # Grant bounded discount up to merchant policy cap
            discount = min(5.0, cfg.max_discount_percentage) if (event.customer.segment == CustomerSegment.HIGH_LTV or event.amount >= 1500) else 0.0
            if discount > 0:
                msg = (
                    f"Hi {customer_name}! We noticed you left your items in the cart ({amount_fmt}). "
                    f"Complete your order in the next 2 hours and get an extra {int(discount)}% instant discount: {{payment_link}}"
                )
                action = InterventionActionType.BOUNDED_DISCOUNT_OFFER
            else:
                msg = (
                    f"Hi {customer_name}! Your cart is reserved ({amount_fmt}). "
                    f"Click here to seamlessly finish your checkout: {{payment_link}}"
                )
                action = InterventionActionType.PERSONALIZED_WHATSAPP_NUDGE

            return InterventionPlan(
                plan_id=plan_id,
                event_id=event.event_id,
                action_type=action,
                channel="WHATSAPP",
                delay_minutes=15,
                message_payload=msg,
                discount_percentage=discount,
                expected_success_probability=0.58 if discount > 0 else 0.45,
                cost_of_intervention_inr=0.50,
                explanation=f"Cart drop-off recovered via targeted WhatsApp nudge with {discount}% bounded promotional incentive.",
            )

        # 6. MANDATE EXPIRED OR REVOKED
        if diagnosis.category == FailureCategory.MANDATE_EXPIRED_OR_REVOKED:
            msg = (
                f"Hello {customer_name}, your subscription mandate for {amount_fmt} could not be debited automatically. "
                f"Please update your mandate or pay directly via this secure Razorpay link: {{payment_link}}"
            )
            return InterventionPlan(
                plan_id=plan_id,
                event_id=event.event_id,
                action_type=InterventionActionType.DYNAMIC_PAYMENT_LINK,
                channel="WHATSAPP",
                delay_minutes=5,
                message_payload=msg,
                discount_percentage=0.0,
                expected_success_probability=0.72,
                cost_of_intervention_inr=0.50,
                explanation="Subscription mandate expired. Outbound payment link dispatched for one-touch recurring re-authorization.",
            )

        # 7. B2B OVERDUE INVOICE
        if diagnosis.category == FailureCategory.B2B_OVERDUE_INVOICE:
            if event.amount >= cfg.b2b_voice_threshold_inr:
                msg = (
                    f"Namaste, yeh {event.merchant_name} ke accounts department se AI assistant hai. "
                    f"Aapka invoice #{event.order_id} of {amount_fmt} pending hai. "
                    f"Kya aap promise-to-pay date schedule karna chahte hain ya instant payment link chahte hain?"
                )
                return InterventionPlan(
                    plan_id=plan_id,
                    event_id=event.event_id,
                    action_type=InterventionActionType.HINGLISH_VOICE_OUTREACH,
                    channel="VOICE_BOT",
                    delay_minutes=0,
                    message_payload=msg,
                    discount_percentage=0.0,
                    expected_success_probability=0.68,
                    cost_of_intervention_inr=2.50,
                    explanation=f"High-value B2B receivable (>=₹{cfg.b2b_voice_threshold_inr:,.0f}) assigned to conversational AI Voice Dunning agent with promise-to-pay tracker.",
                )
            else:
                msg = (
                    f"Dear Finance Team, Invoice #{event.order_id} of {amount_fmt} is awaiting settlement. "
                    f"Pay instantly via RazorpayX Smart Collect: {{payment_link}}"
                )
                return InterventionPlan(
                    plan_id=plan_id,
                    event_id=event.event_id,
                    action_type=InterventionActionType.COMPLIANT_EMAIL_DUNNING,
                    channel="EMAIL",
                    delay_minutes=0,
                    message_payload=msg,
                    discount_percentage=0.0,
                    expected_success_probability=0.62,
                    cost_of_intervention_inr=0.10,
                    explanation="Standard B2B invoice dunning email with embedded instant RazorpayX payment link.",
                )

        # Default fallback
        return InterventionPlan(
            plan_id=plan_id,
            event_id=event.event_id,
            action_type=InterventionActionType.DYNAMIC_PAYMENT_LINK,
            channel="WHATSAPP",
            delay_minutes=10,
            message_payload=f"Namaste {customer_name}, complete your payment of {amount_fmt} here: {{payment_link}}",
            discount_percentage=0.0,
            expected_success_probability=0.50,
            cost_of_intervention_inr=0.50,
            explanation="Standard fallback dynamic payment link.",
        )
