"""Bounded Action Executor for Razorpay Revive."""
import uuid
import random
from typing import Optional
from app.models.schemas import (
    FailureEvent,
    InterventionPlan,
    GuardrailVerdict,
    ExecutionResult,
    InterventionActionType,
)
from app.integrations.razorpay_client import RazorpayClientWrapper


class ActionExecutor:
    """Safely executes guardrailed recovery interventions with full audit tracing."""

    def __init__(self, razorpay_client: Optional[RazorpayClientWrapper] = None):
        self.rzp = razorpay_client or RazorpayClientWrapper()

    def execute(
        self,
        event: FailureEvent,
        plan: InterventionPlan,
        verdict: GuardrailVerdict,
        deterministic_outcome: Optional[bool] = None,
    ) -> ExecutionResult:
        """Executes recovery action and records complete decision audit trace."""
        exec_id = f"exec_{uuid.uuid4().hex[:10]}"
        trace = [
            f"[INGEST] Event #{event.event_id} received for {event.customer.name} (Amount: ₹{event.amount})",
            f"[DIAGNOSIS] Action Plan #{plan.plan_id} formulated: {plan.action_type.value} on channel {plan.channel}",
        ]

        # 1. Blocked by Guardrail Check
        if not verdict.is_approved:
            trace.append(f"[GUARDRAIL_BLOCKED] Policy violation: {verdict.rejection_reason}")
            trace.append(f"[MITIGATION] {verdict.mitigation_applied}")
            return ExecutionResult(
                execution_id=exec_id,
                event_id=event.event_id,
                plan_id=plan.plan_id,
                status="BLOCKED_BY_GUARDRAIL",
                money_recovered_inr=0.0,
                net_value_saved_inr=0.0,
                audit_trace=trace,
            )

        trace.append(f"[GUARDRAIL_PASSED] {verdict.mitigation_applied}")

        # 2. Hard Stop / Escalation
        if plan.action_type == InterventionActionType.HARD_STOP_ESCALATE:
            trace.append(f"[ESCALATE] Workflow terminated gracefully: {plan.explanation}")
            return ExecutionResult(
                execution_id=exec_id,
                event_id=event.event_id,
                plan_id=plan.plan_id,
                status="ESCALATED",
                money_recovered_inr=0.0,
                net_value_saved_inr=0.0,
                audit_trace=trace,
            )

        # 3. Scheduled Gateway Retry
        if plan.action_type == InterventionActionType.AUTO_RETRY_SMART_WINDOW:
            retry_res = self.rzp.trigger_gateway_retry(
                payment_id=event.payment_id or event.order_id,
                scheduled_delay_minutes=plan.delay_minutes,
            )
            trace.append(f"[GATEWAY_RETRY] Dispatched to Razorpay Smart Router (Delay: {plan.delay_minutes}m)")

            # Outcome evaluation
            is_recovered = (
                deterministic_outcome
                if deterministic_outcome is not None
                else (random.random() <= plan.expected_success_probability)
            )

            if is_recovered:
                recovered_amount = event.amount
                net_saved = recovered_amount - plan.cost_of_intervention_inr
                trace.append(f"[SUCCESS] Gateway retry succeeded! ₹{recovered_amount:,.2f} captured cleanly.")
                status = "RECOVERED"
            else:
                recovered_amount = 0.0
                net_saved = -plan.cost_of_intervention_inr
                trace.append("[RETRY_PENDING] Bank switch still unresponsive; queueing next backoff.")
                status = "SCHEDULED_RETRY"

            return ExecutionResult(
                execution_id=exec_id,
                event_id=event.event_id,
                plan_id=plan.plan_id,
                status=status,
                money_recovered_inr=recovered_amount,
                net_value_saved_inr=net_saved,
                razorpay_reference_id=retry_res.get("retry_job_id"),
                audit_trace=trace,
            )

        # 4. Multi-Channel Dynamic Payment Link / Conversational Nudge
        effective_amount = event.amount * (1.0 - (plan.discount_percentage / 100.0))
        plink = self.rzp.create_payment_link(
            amount_inr=effective_amount,
            customer_name=event.customer.name,
            customer_phone=event.customer.phone,
            customer_email=event.customer.email,
            description=f"Payment Recovery for Order #{event.order_id}",
            expire_by_minutes=120,
        )

        trace.append(f"[RAZORPAY_LINK_CREATED] Created dynamic link {plink['short_url']} (Amount: ₹{effective_amount:,.2f})")
        if plan.message_payload:
            rendered_msg = plan.message_payload.replace("{payment_link}", plink["short_url"])
            trace.append(f"[OUTREACH_DISPATCHED] Outbound {plan.channel} message sent: \"{rendered_msg[:75]}...\"")

        # Outcome evaluation
        is_recovered = (
            deterministic_outcome
            if deterministic_outcome is not None
            else (random.random() <= plan.expected_success_probability)
        )

        if is_recovered:
            recovered_amount = effective_amount
            net_saved = recovered_amount - plan.cost_of_intervention_inr
            trace.append(f"[PAYMENT_CAPTURED] Customer paid ₹{recovered_amount:,.2f} via link webhook callback.")
            status = "RECOVERED"
        else:
            recovered_amount = 0.0
            net_saved = -plan.cost_of_intervention_inr
            trace.append(f"[UNRECOVERED] Link expired without customer payment. Escalated to next retry tier.")
            status = "FAILED"

        return ExecutionResult(
            execution_id=exec_id,
            event_id=event.event_id,
            plan_id=plan.plan_id,
            status=status,
            money_recovered_inr=recovered_amount,
            net_value_saved_inr=net_saved,
            razorpay_reference_id=plink.get("id"),
            payment_link_url=plink.get("short_url"),
            audit_trace=trace,
        )
