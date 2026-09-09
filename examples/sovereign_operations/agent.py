"""Sovereign Operations Agent — the first real-world specimen.

This agent exercises the entire SAS protocol end-to-end:

    Local Knowledge
          ↓
    Observation
          ↓
    Hypothesis
          ↓
    Evidence
          ↓
    Epistemic Evaluation
          ↓
    Recommendation
          ↓
    Governance
          ↓
    Authorization
          ↓
    Capability
          ↓
    Consequence Request
          ↓
    Capability Verification
          ↓
    Execution
          ↓
    Receipt
          ↓
    Provenance

The central invariant: MODEL OUTPUT ≠ AUTHORITY
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from sas.quant.capability_bound_auth import (
    CapabilityBoundAuthBroker,
    CredentialUseRequest,
    create_capability_bound_auth_broker,
)
from sas.quant.capability_verifier import (
    CapabilityVerifier,
    ReplayProtectionStore,
    create_capability_verifier,
    create_replay_protection_store,
)
from sas.quant.experiment.execution_capability import (
    CapabilityConstraints,
    CapabilityScope,
    CapabilityType,
    ExecutionCapability,
    ExecutionReceipt,
    ExecutionStatus,
    ExecutorBinding,
    ReplayGuard,
    ReplayProtectionType,
)
from sas.quant.experiment.protocol_lineage import (
    DomainType,
    DomainValidityInterval,
    ProtocolDomain,
    create_protocol_domain,
)
from sas.layers.auth import Credentials, LocalAuthBroker


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HypothesisArtifact:
    """A hypothesis proposed by the model."""
    hypothesis_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    description: str = ""
    proposed_by: str = "model"
    confidence: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class ObservedEvidence:
    """Evidence observed by the agent."""
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    evidence_type: str = ""
    source: str = ""
    content: Any = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class RecommendationArtifact:
    """A recommendation proposed by the model."""
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    action: str = ""
    parameters: dict = field(default_factory=dict)
    rationale: str = ""
    proposed_by: str = "model"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class GovernanceDecision:
    """A decision made by the governance layer."""
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    approved: bool = False
    reason: str = ""
    policy_references: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


# ---------------------------------------------------------------------------
# Sovereign Operations Agent
# ---------------------------------------------------------------------------


class SovereignOperationsAgent:
    """Agent that investigates support tickets and potentially acts on them.

    The agent follows the complete SAS protocol:
    1. Observe: Read support tickets and operational data
    2. Hypothesize: Propose explanations
    3. Evidence: Gather supporting/contradicting evidence
    4. Evaluate: Assess epistemic state
    5. Recommend: Propose actions
    6. Govern: Check policy compliance
    7. Authorize: Derive authority
    8. Capability: Materialize bounded capability
    9. Verify: Validate capability
    10. Execute: Perform the action
    11. Receipt: Record execution
    12. Provenance: Persist lineage
    """

    def __init__(
        self,
        data_dir: Path,
        knowledge_dir: Path,
        policy_path: Path,
        domain: ProtocolDomain | None = None,
    ):
        self._data_dir = data_dir
        self._knowledge_dir = knowledge_dir
        self._policy_path = policy_path
        self._domain = domain or create_protocol_domain("operations-domain", DomainType.SOVEREIGN)

        # Authority components
        self._verifier = create_capability_verifier(self._domain)
        self._replay_store = create_replay_protection_store()

        # Credential broker
        self._auth_broker = LocalAuthBroker()
        self._credential_broker = create_capability_bound_auth_broker(self._auth_broker)

        # State
        self._hypotheses: list[HypothesisArtifact] = []
        self._evidence: list[ObservedEvidence] = []
        self._recommendations: list[RecommendationArtifact] = []
        self._governance_decisions: list[GovernanceDecision] = []
        self._receipts: list[ExecutionReceipt] = []
        self._provenance: list[dict] = []

        # Load policy
        self._policy = json.loads(policy_path.read_text())

    def investigate(self, ticket_id: str) -> dict:
        """Investigate a support ticket.

        This is the main entry point. The agent:
        1. Observes the ticket
        2. Forms hypotheses
        3. Gathers evidence
        4. Evaluates epistemic state
        5. Makes a recommendation
        6. Checks governance
        7. If authorized, executes

        Returns a complete trace of the investigation.
        """
        trace = {
            "ticket_id": ticket_id,
            "observations": [],
            "hypotheses": [],
            "evidence": [],
            "epistemic_state": None,
            "recommendation": None,
            "governance_decision": None,
            "authorization": None,
            "capability": None,
            "verification": None,
            "execution": None,
            "receipt": None,
        }

        # Step 1: Observe
        ticket = self._read_support_ticket(ticket_id)
        if ticket is None:
            trace["error"] = f"Ticket {ticket_id} not found"
            return trace
        trace["observations"].append(ticket)

        # Step 2: Hypothesize (model proposes)
        hypotheses = self._form_hypotheses(ticket)
        trace["hypotheses"] = [h.__dict__ for h in hypotheses]

        # Step 3: Gather evidence
        evidence = self._gather_evidence(ticket)
        trace["evidence"] = [e.__dict__ for e in evidence]

        # Step 4: Evaluate epistemic state
        epistemic_state = self._evaluate_epistemic_state(hypotheses, evidence)
        trace["epistemic_state"] = epistemic_state

        # Step 5: Recommend (model proposes)
        recommendation = self._make_recommendation(ticket, evidence, epistemic_state)
        trace["recommendation"] = recommendation.__dict__ if recommendation else None

        # Step 6: Governance decision
        governance = self._evaluate_governance(recommendation, evidence, epistemic_state)
        trace["governance_decision"] = governance.__dict__

        if not governance.approved:
            trace["result"] = "REJECTED"
            trace["reason"] = governance.reason
            return trace

        # Step 7: Authorize
        authorization = self._derive_authorization(recommendation, evidence, governance)
        trace["authorization"] = authorization

        if authorization is None:
            trace["result"] = "NO_AUTHORIZATION"
            return trace

        # Step 8: Materialize capability
        capability = self._materialize_capability(recommendation, authorization)
        trace["capability"] = {
            "capability_id": capability.capability_id,
            "action": capability.scope.action,
            "resource": capability.scope.resource,
            "constraints": {
                "max_quantity": capability.scope.constraints.max_quantity,
                "allowed_actions": capability.scope.constraints.allowed_actions,
            },
        }

        # Step 9: Verify capability
        verification = self._verifier.verify(
            capability=capability,
            action=capability.scope.action,
            resource=capability.scope.resource,
            arguments=recommendation.parameters,
        )
        trace["verification"] = {
            "is_permitted": verification.is_permitted,
            "conflicts": verification.conflicts,
        }

        if not verification.is_permitted:
            trace["result"] = "VERIFICATION_FAILED"
            trace["conflicts"] = verification.conflicts
            return trace

        # Step 10: Execute
        execution_result = self._execute(recommendation, capability)
        trace["execution"] = execution_result

        # Step 11: Record receipt
        if execution_result.get("receipt"):
            trace["receipt"] = execution_result["receipt"].__dict__

        # Step 12: Record provenance
        provenance_entry = self._record_provenance(trace)
        trace["provenance_id"] = provenance_entry["provenance_id"]

        trace["result"] = "COMPLETED"
        return trace

    def _read_support_ticket(self, ticket_id: str) -> dict | None:
        """Read a support ticket from the data store."""
        tickets_path = self._data_dir / "support_tickets.json"
        if not tickets_path.exists():
            return None
        tickets = json.loads(tickets_path.read_text())
        for ticket in tickets.get("support_tickets", []):
            if ticket["ticket_id"] == ticket_id:
                return ticket
        return None

    def _form_hypotheses(self, ticket: dict) -> list[HypothesisArtifact]:
        """Form hypotheses about the ticket.

        In a real implementation, this would use the model.
        For the specimen, we use deterministic logic.
        """
        hypotheses = []

        order_id = ticket.get("order_id", "")
        customer_id = ticket.get("customer_id", "")

        # Hypothesis 1: Payment succeeded but fulfillment failed
        hypotheses.append(HypothesisArtifact(
            description=f"Payment succeeded but fulfillment failed for order {order_id}",
            proposed_by="model",
            confidence=0.8,
        ))

        # Hypothesis 2: Inventory unavailable
        hypotheses.append(HypothesisArtifact(
            description=f"Inventory unavailable for items in order {order_id}",
            proposed_by="model",
            confidence=0.6,
        ))

        # Hypothesis 3: Customer not entitled to refund
        hypotheses.append(HypothesisArtifact(
            description=f"Customer {customer_id} not entitled to refund under policy",
            proposed_by="model",
            confidence=0.3,
        ))

        self._hypotheses.extend(hypotheses)
        return hypotheses

    def _gather_evidence(self, ticket: dict) -> list[ObservedEvidence]:
        """Gather evidence from operational data.

        IMPORTANT: Credential material is stripped from evidence before recording.
        The model must never see credential material.
        """
        evidence = []
        order_id = ticket.get("order_id", "")
        customer_id = ticket.get("customer_id", "")

        # Read orders
        orders = json.loads((self._data_dir / "orders.json").read_text())
        order = None
        for o in orders.get("orders", []):
            if o["order_id"] == order_id:
                order = o
                break

        if order:
            evidence.append(ObservedEvidence(
                evidence_type="order_record",
                source="orders.json",
                content=order,
            ))

            # Check fulfillment
            evidence.append(ObservedEvidence(
                evidence_type="fulfillment_record",
                source="orders.json",
                content={"fulfilled": order.get("fulfilled", False)},
            ))

        # Read transactions
        transactions = json.loads((self._data_dir / "transactions.json").read_text())
        for txn in transactions.get("transactions", []):
            if txn["order_id"] == order_id:
                evidence.append(ObservedEvidence(
                    evidence_type="payment_transaction",
                    source="transactions.json",
                    content=txn,
                ))

        # Read customers - STRIP CREDENTIAL MATERIAL
        customers = json.loads((self._data_dir / "customers.json").read_text())
        for cust in customers.get("customers", []):
            if cust["customer_id"] == customer_id:
                # Strip credential material from customer record
                safe_cust = {
                    "customer_id": cust.get("customer_id"),
                    "name": cust.get("name"),
                    "email": cust.get("email"),
                    "verified": cust.get("verified"),
                    "created_at": cust.get("created_at"),
                    # DO NOT include payment_methods or tokens
                }
                evidence.append(ObservedEvidence(
                    evidence_type="customer_record",
                    source="customers.json",
                    content=safe_cust,
                ))

        # Read inventory
        if order:
            inventory = json.loads((self._data_dir / "inventory.json").read_text())
            for item in order.get("items", []):
                for inv in inventory.get("inventory", []):
                    if inv["sku"] == item["sku"]:
                        evidence.append(ObservedEvidence(
                            evidence_type="inventory_record",
                            source="inventory.json",
                            content=inv,
                        ))

        # Check prior refunds
        prior_refund_check = self._check_prior_refunds(order_id)
        evidence.append(ObservedEvidence(
            evidence_type="prior_refund_check",
            source="agent",
            content=prior_refund_check,
        ))

        self._evidence.extend(evidence)
        return evidence

    def _check_prior_refunds(self, order_id: str) -> dict:
        """Check if there are prior refunds for this order."""
        # In a real implementation, this would check the transaction history
        return {"order_id": order_id, "has_prior_refund": False}

    def _evaluate_epistemic_state(
        self,
        hypotheses: list[HypothesisArtifact],
        evidence: list[ObservedEvidence],
    ) -> dict:
        """Evaluate the epistemic state based on evidence.

        Returns a structured assessment of what the evidence supports.
        """
        # Count evidence types
        evidence_types = {e.evidence_type for e in evidence}

        # Check for key evidence
        has_payment = "payment_transaction" in evidence_types
        has_order = "order_record" in evidence_types
        has_fulfillment = "fulfillment_record" in evidence_types
        has_customer = "customer_record" in evidence_types
        has_inventory = "inventory_record" in evidence_types
        has_prior_refund = "prior_refund_check" in evidence_types

        # Determine fulfillment status
        fulfilled = False
        for e in evidence:
            if e.evidence_type == "fulfillment_record":
                fulfilled = e.content.get("fulfilled", False)

        # Determine payment status
        payment_completed = False
        payment_amount = 0.0
        for e in evidence:
            if e.evidence_type == "payment_transaction":
                if e.content.get("status") == "completed":
                    payment_completed = True
                    payment_amount = e.content.get("amount", 0.0)

        # Determine inventory status
        inventory_available = True
        for e in evidence:
            if e.evidence_type == "inventory_record":
                if e.content.get("available", 0) <= 0:
                    inventory_available = False

        # Determine prior refund status
        has_prior_refund = False
        for e in evidence:
            if e.evidence_type == "prior_refund_check":
                has_prior_refund = e.content.get("has_prior_refund", False)

        # Calculate evidence score
        evidence_count = len([e for e in evidence if e.evidence_type in {
            "payment_transaction", "order_record", "fulfillment_record",
            "customer_record", "inventory_record", "prior_refund_check"
        }])

        # Determine epistemic state
        if payment_completed and not fulfilled and not has_prior_refund:
            state = "SUPPORTED"
        elif payment_completed and fulfilled:
            state = "REFUTED"
        elif not payment_completed:
            state = "INCONCLUSIVE"
        else:
            state = "PARTIALLY_SUPPORTED"

        return {
            "state": state,
            "evidence_count": evidence_count,
            "has_payment": has_payment,
            "has_order": has_order,
            "has_fulfillment": has_fulfillment,
            "has_customer": has_customer,
            "has_inventory": has_inventory,
            "has_prior_refund_check": has_prior_refund,
            "fulfilled": fulfilled,
            "payment_completed": payment_completed,
            "payment_amount": payment_amount,
            "inventory_available": inventory_available,
            "has_prior_refund": has_prior_refund,
        }

    def _make_recommendation(
        self,
        ticket: dict,
        evidence: list[ObservedEvidence],
        epistemic_state: dict,
    ) -> RecommendationArtifact | None:
        """Make a recommendation based on evidence and epistemic state.

        In a real implementation, this would be the model's recommendation.
        For the specimen, we derive it from the evidence.
        """
        if epistemic_state["state"] not in ("SUPPORTED", "PARTIALLY_SUPPORTED"):
            return None

        order_id = ticket.get("order_id", "")
        customer_id = ticket.get("customer_id", "")
        payment_amount = epistemic_state.get("payment_amount", 0.0)

        recommendation = RecommendationArtifact(
            action="issue_refund",
            parameters={
                "order_id": order_id,
                "customer_id": customer_id,
                "amount": payment_amount,
                "currency": "USD",
            },
            rationale=f"Payment completed but order not fulfilled. Refund of ${payment_amount:.2f} recommended.",
            proposed_by="model",
        )

        self._recommendations.append(recommendation)
        return recommendation

    def _evaluate_governance(
        self,
        recommendation: RecommendationArtifact | None,
        evidence: list[ObservedEvidence],
        epistemic_state: dict,
    ) -> GovernanceDecision:
        """Evaluate whether the recommendation satisfies governance policy."""
        if recommendation is None:
            return GovernanceDecision(
                approved=False,
                reason="No recommendation made",
            )

        # Check epistemic state
        if epistemic_state["state"] == "REFUTED":
            return GovernanceDecision(
                approved=False,
                reason="Epistemic state is REFUTED",
                policy_references=["refund_policy.eligibility"],
            )

        if epistemic_state["state"] == "INCONCLUSIVE":
            return GovernanceDecision(
                approved=False,
                reason="Epistemic state is INCONCLUSIVE",
                policy_references=["refund_policy.eligibility"],
            )

        # Check amount thresholds
        amount = recommendation.parameters.get("amount", 0.0)
        threshold_tier1 = self._policy["refund_policy"]["automatic_authorization_threshold"]
        threshold_tier2 = self._policy["refund_policy"]["evidence_required_threshold"]
        threshold_tier3 = self._policy["refund_policy"]["human_approval_threshold"]

        if amount > threshold_tier3:
            return GovernanceDecision(
                approved=False,
                reason=f"Amount ${amount:.2f} exceeds human approval threshold (${threshold_tier3:.2f})",
                policy_references=["refund_policy.tier3"],
            )

        if amount > threshold_tier2:
            return GovernanceDecision(
                approved=False,
                reason=f"Amount ${amount:.2f} exceeds evidence required threshold (${threshold_tier2:.2f})",
                policy_references=["refund_policy.tier2"],
            )

        # Check evidence requirements
        evidence_count = epistemic_state.get("evidence_count", 0)
        if amount > threshold_tier1 and evidence_count < self._policy["refund_policy"]["evidence_required_minimum"]:
            return GovernanceDecision(
                approved=False,
                reason=f"Insufficient evidence ({evidence_count} items, minimum {self._policy['refund_policy']['evidence_required_minimum']} required)",
                policy_references=["refund_policy.evidence_requirements"],
            )

        # Check prior refund
        if epistemic_state.get("has_prior_refund"):
            return GovernanceDecision(
                approved=False,
                reason="Prior refund exists for this order",
                policy_references=["refund_policy.prohibited_refunds"],
            )

        # Check fulfillment
        if epistemic_state.get("fulfilled"):
            return GovernanceDecision(
                approved=False,
                reason="Order has been fulfilled",
                policy_references=["refund_policy.prohibited_refunds"],
            )

        # All checks passed
        return GovernanceDecision(
            approved=True,
            reason="All governance checks passed",
            policy_references=["refund_policy.eligibility", "refund_policy.tier1"],
        )

    def _derive_authorization(
        self,
        recommendation: RecommendationArtifact,
        evidence: list[ObservedEvidence],
        governance: GovernanceDecision,
    ) -> dict | None:
        """Derive authorization from governance decision and evidence."""
        if not governance.approved:
            return None

        authorization = {
            "authorization_id": f"auth-{uuid.uuid4().hex[:12]}",
            "action": recommendation.action,
            "parameters": recommendation.parameters,
            "governance_decision_id": governance.decision_id,
            "evidence_ids": [e.evidence_id for e in evidence],
            "created_at": datetime.now(UTC).isoformat(),
            "expires_at": None,  # Will be set by capability
        }

        return authorization

    def _materialize_capability(
        self,
        recommendation: RecommendationArtifact,
        authorization: dict,
    ) -> ExecutionCapability:
        """Materialize an execution capability from authorization."""
        amount = recommendation.parameters.get("amount", 0.0)
        validity_hours = self._policy["refund_policy"]["capability_validity_hours"]
        valid_until = datetime.now(UTC) + timedelta(hours=validity_hours)

        scope = CapabilityScope(
            domain_id=self._domain.domain_id,
            lineage_id=self._domain.lineage_hash,
            actor_id="operations-agent",
            action=recommendation.action,
            resource=recommendation.parameters.get("order_id", ""),
            arguments=recommendation.parameters,
            constraints=CapabilityConstraints(
                allowed_actions=[recommendation.action],
                max_quantity=amount,
                min_quantity=0,
            ),
            temporal_interval=DomainValidityInterval(
                valid_from=datetime.now(UTC).isoformat(),
                valid_until=valid_until.isoformat(),
            ),
            authorization_ref=authorization["authorization_id"],
        )

        replay_guard = ReplayGuard(
            guard_type=ReplayProtectionType.SINGLE_USE,
            nonce=f"nonce-{uuid.uuid4().hex[:16]}",
            max_uses=1,
        )

        binding = ExecutorBinding(
            binding_id=f"binding-{uuid.uuid4().hex[:12]}",
            executor_id="operations-agent",
            resource_id=recommendation.parameters.get("order_id", ""),
            bound_resources=[recommendation.parameters.get("order_id", "")],
        )

        return ExecutionCapability(
            capability_id=f"cap-{uuid.uuid4().hex[:12]}",
            authorization_ref=authorization["authorization_id"],
            scope=scope,
            capability_type=CapabilityType.EXECUTE,
            replay_guard=replay_guard,
            actor_identity_ref="operations-agent",
            resource_binding=binding,
            domain_id=self._domain.domain_id,
            lineage_id=self._domain.lineage_hash,
            authority_root=authorization["authorization_id"],
            derived_at=datetime.now(UTC).isoformat(),
            derived_by="operations-agent",
        )

    def _execute(
        self,
        recommendation: RecommendationArtifact,
        capability: ExecutionCapability,
    ) -> dict:
        """Execute the recommended action."""
        result = {
            "status": "unknown",
            "receipt": None,
        }

        if recommendation.action == "issue_refund":
            # Execute refund through credential broker
            refund_result = self._execute_refund(recommendation, capability)
            result.update(refund_result)
        else:
            result["status"] = "unknown_action"

        return result

    def _execute_refund(
        self,
        recommendation: RecommendationArtifact,
        capability: ExecutionCapability,
    ) -> dict:
        """Execute a refund through the credential-bound payment adapter."""
        # In a real implementation, this would use the credential broker
        # to access the payment adapter. For the specimen, we simulate.

        # Create a simulated payment adapter
        class SimulatedPaymentAdapter:
            def refund(self, order_id: str, amount: float, currency: str) -> dict:
                return {
                    "status": "completed",
                    "transaction_id": f"refund-{uuid.uuid4().hex[:12]}",
                    "order_id": order_id,
                    "amount": amount,
                    "currency": currency,
                }

        adapter = SimulatedPaymentAdapter()

        # Execute the refund
        try:
            payment_result = adapter.refund(
                order_id=recommendation.parameters.get("order_id", ""),
                amount=recommendation.parameters.get("amount", 0.0),
                currency=recommendation.parameters.get("currency", "USD"),
            )

            # Create receipt
            receipt = ExecutionReceipt(
                receipt_id=f"receipt_{uuid.uuid4().hex[:12]}",
                capability_ref=capability.capability_id,
                authorization_ref=capability.authorization_ref,
                domain_id=capability.domain_id,
                lineage_id=capability.lineage_id,
                actor_id=capability.scope.actor_id,
                executor_id="simulated-payment-adapter",
                resource_id=recommendation.parameters.get("order_id", ""),
                action=recommendation.action,
                arguments_hash=str(hash(str(recommendation.parameters)))[:16],
                start_time=datetime.now(UTC).isoformat(),
                completion_time=datetime.now(UTC).isoformat(),
                effect_summary=f"Refund executed: {payment_result['transaction_id']}",
                status=ExecutionStatus.COMPLETED,
                intended_effect=f"refund {recommendation.parameters}",
                observed_effect=str(payment_result),
                reported_result=payment_result["status"],
                provenance_hash=capability.compute_hash(),
            )

            self._receipts.append(receipt)

            return {
                "status": "completed",
                "payment_result": payment_result,
                "receipt": receipt,
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }

    def _record_provenance(self, trace: dict) -> dict:
        """Record provenance for the investigation."""
        provenance_entry = {
            "provenance_id": f"provenance-{uuid.uuid4().hex[:12]}",
            "ticket_id": trace.get("ticket_id"),
            "timestamp": datetime.now(UTC).isoformat(),
            "trace": trace,
        }
        self._provenance.append(provenance_entry)
        return provenance_entry

    def get_receipts(self) -> list[ExecutionReceipt]:
        """Get all execution receipts."""
        return list(self._receipts)

    def get_provenance(self) -> list[dict]:
        """Get all provenance entries."""
        return list(self._provenance)
