"""End-to-End Revenue Recovery Pipeline Orchestrator for Razorpay Revive."""
from typing import Dict, Any, Optional
from app.models.schemas import FailureEvent, ExecutionResult
from app.engine.classifier import FailureClassifier
from app.engine.planner import InterventionPlanner
from app.engine.guardrails import FintechGuardrailEngine
from app.engine.executor import ActionExecutor
from app.storage.audit_log import AuditStore
from app.integrations.razorpay_client import RazorpayClientWrapper


class RevenueRecoveryPipeline:
    """Orchestrates ingestion, root-cause diagnosis, guardrailed planning, execution, and audit logging."""

    def __init__(
        self,
        classifier: Optional[FailureClassifier] = None,
        planner: Optional[InterventionPlanner] = None,
        guardrails: Optional[FintechGuardrailEngine] = None,
        executor: Optional[ActionExecutor] = None,
        audit_store: Optional[AuditStore] = None,
        razorpay_client: Optional[RazorpayClientWrapper] = None,
    ):
        self.rzp = razorpay_client or RazorpayClientWrapper()
        self.classifier = classifier or FailureClassifier()
        self.planner = planner or InterventionPlanner()
        self.guardrails = guardrails or FintechGuardrailEngine()
        self.executor = executor or ActionExecutor(razorpay_client=self.rzp)
        self.audit_store = audit_store or AuditStore()

    def process_event(
        self, event: FailureEvent, deterministic_outcome: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Runs complete autonomous recovery loop for a single failure event."""
        # 1. Failure Taxonomy Classification
        diagnosis = self.classifier.diagnose(event)

        # 2. Dynamic Intervention Formulation
        plan = self.planner.create_plan(event, diagnosis)

        # 3. Deterministic Compliance Guardrails
        verdict = self.guardrails.verify_plan(event, plan)

        # 4. Bounded Action Execution
        execution = self.executor.execute(
            event, plan, verdict, deterministic_outcome=deterministic_outcome
        )

        # 5. Immutable Audit Trail Sinking
        self.audit_store.record_cycle(event, diagnosis, plan, verdict, execution)

        return {
            "event": event.model_dump(mode="json"),
            "diagnosis": diagnosis.model_dump(mode="json"),
            "plan": plan.model_dump(mode="json"),
            "guardrail_verdict": verdict.model_dump(mode="json"),
            "execution": execution.model_dump(mode="json"),
        }
