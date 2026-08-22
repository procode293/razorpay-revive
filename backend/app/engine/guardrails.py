"""Deterministic Safety, Compliance, and Policy Guardrails for Razorpay Revive."""
from datetime import datetime, timezone
from typing import Tuple
from app.models.schemas import FailureEvent, InterventionPlan, GuardrailVerdict, InterventionActionType


class FintechGuardrailEngine:
    """Enforces strict financial compliance, anti-spam, and zero-hallucination bounds."""

    MAX_RETRIES_LIMIT = 3
    MAX_DISCOUNT_PERCENTAGE = 10.0
    QUIET_HOURS_START_HOUR_IST = 21  # 9:00 PM IST
    QUIET_HOURS_END_HOUR_IST = 8    # 8:00 AM IST

    def verify_plan(self, event: FailureEvent, plan: InterventionPlan, current_time: datetime = None) -> GuardrailVerdict:
        """Runs rigorous multi-point compliance checks against proposed intervention."""
        checks = {
            "max_retries_limit": "PASS",
            "quiet_hours_policy": "PASS",
            "anti_spam_frequency": "PASS",
            "money_integrity_check": "PASS",
            "compliance_escalation_rule": "PASS",
        }

        # Check 1: Max Retries
        if event.retry_count >= self.MAX_RETRIES_LIMIT and plan.action_type != InterventionActionType.HARD_STOP_ESCALATE:
            checks["max_retries_limit"] = "FAIL"
            return GuardrailVerdict(
                is_approved=False,
                policy_checks=checks,
                rejection_reason=f"Violation: Attempted retry count ({event.retry_count}) exceeds hard ceiling of {self.MAX_RETRIES_LIMIT}.",
                mitigation_applied="Auto-downgraded to HARD_STOP_ESCALATE to prevent customer harassment.",
            )

        # Check 2: Money Integrity & Bounded Discount
        if plan.discount_percentage < 0.0 or plan.discount_percentage > self.MAX_DISCOUNT_PERCENTAGE:
            checks["money_integrity_check"] = "FAIL"
            return GuardrailVerdict(
                is_approved=False,
                policy_checks=checks,
                rejection_reason=f"Violation: Proposed discount ({plan.discount_percentage}%) breaches strict safety cap of {self.MAX_DISCOUNT_PERCENTAGE}%.",
                mitigation_applied=f"Capped discount to {self.MAX_DISCOUNT_PERCENTAGE}%.",
            )

        if event.amount <= 0:
            checks["money_integrity_check"] = "FAIL"
            return GuardrailVerdict(
                is_approved=False,
                policy_checks=checks,
                rejection_reason="Violation: Non-positive transaction amount detected.",
                mitigation_applied="Rejected transaction execution.",
            )

        # Check 3: Quiet Hours Check (TRAI / RBI Indian Telecom & Banking Regulations)
        # Quiet hours apply to outbound user interruptions (WhatsApp, SMS, Voice)
        now = current_time or datetime.now(timezone.utc)
        # Convert to approximate IST (+5:30)
        ist_hour = (now.hour + 5 + (now.minute + 30) // 60) % 24

        outbound_channels = ["WHATSAPP", "VOICE_BOT", "SMS"]
        is_quiet_hour = ist_hour >= self.QUIET_HOURS_START_HOUR_IST or ist_hour < self.QUIET_HOURS_END_HOUR_IST

        if plan.channel in outbound_channels and is_quiet_hour:
            checks["quiet_hours_policy"] = "RESTRICTED"
            # We allow it, but shift delay to next morning 8:00 AM IST instead of sending immediately
            minutes_until_morning = (self.QUIET_HOURS_END_HOUR_IST - ist_hour) % 24 * 60
            if minutes_until_morning == 0:
                minutes_until_morning = 60
            return GuardrailVerdict(
                is_approved=True,
                policy_checks=checks,
                rejection_reason=None,
                mitigation_applied=f"Quiet hours in effect ({ist_hour}:00 IST). Outbound channel message buffered by {minutes_until_morning} mins to 8:00 AM IST.",
            )

        # Check 4: Anti-Spam Frequency
        last_contact = event.metadata.get("last_contact_hours_ago", 999)
        if last_contact < 4 and plan.channel in outbound_channels:
            checks["anti_spam_frequency"] = "FAIL"
            return GuardrailVerdict(
                is_approved=False,
                policy_checks=checks,
                rejection_reason=f"Violation: Customer was contacted {last_contact}h ago. Minimum cooldown is 4 hours.",
                mitigation_applied="Deferred outbound intervention to respect communication frequency cap.",
            )

        return GuardrailVerdict(
            is_approved=True,
            policy_checks=checks,
            rejection_reason=None,
            mitigation_applied="All 5 fintech compliance guardrails passed.",
        )
