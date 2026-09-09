# Sovereign Operations Specimen

> **Date:** 2026-09-09
> **Phase:** Consequence Protocol Closure II
> **Tests:** 1,793 passing

This document describes the first real-world specimen for the Sovereign Agent Stack.

---

## Purpose

The Sovereign Operations Agent demonstrates that SAS can govern a local-first agent performing real operational work without allowing the model itself to become an authority source.

The central invariant: **MODEL OUTPUT ≠ AUTHORITY**

---

## Operational Scenario

Acme Goods is a small e-commerce business. The agent receives support tickets and investigates them. When a refund is warranted, the agent follows the complete protocol:

```
Customer Complaint
        ↓
Agent Observation
        ↓
Evidence Retrieval
        ↓
Hypothesis
        ↓
Epistemic State
        ↓
Recommendation
        ↓
Governance Decision
        ↓
Authorization Artifact
        ↓
Execution Capability
        ↓
Consequence Request
        ↓
Capability Verification
        ↓
Execution
        ↓
Execution Receipt
        ↓
Provenance
```

---

## Knowledge Model

### Knowledge Files

- `knowledge/business.md` — Business overview
- `knowledge/refund_policy.md` — Authoritative refund policy
- `knowledge/fulfillment_policy.md` — Fulfillment rules

### Data Files

- `data/orders.json` — Order records
- `data/customers.json` — Customer records (credential material stripped)
- `data/inventory.json` — Inventory records
- `data/transactions.json` — Payment transactions
- `data/support_tickets.json` — Support tickets

### Governance Policy

- `policies/governance.json` — Machine-readable governance policy

---

## Epistemic Flow

### Observation

The agent reads support tickets and operational data. Credential material is stripped before evidence is recorded.

### Hypothesis

The model proposes hypotheses:
- H1: Payment succeeded but fulfillment failed
- H2: Inventory unavailable
- H3: Customer not entitled to refund

### Evidence

Evidence is gathered from multiple sources:
- Payment transaction records
- Order records
- Fulfillment records
- Customer records (credentials stripped)
- Inventory records
- Prior refund checks

### Epistemic State

The evidence is evaluated:
- **SUPPORTED** — All conditions met
- **PARTIALLY_SUPPORTED** — Some conditions met
- **INCONCLUSIVE** — Insufficient evidence
- **REFUTED** — Evidence contradicts hypothesis

### Recommendation

The model recommends an action (e.g., "Refund $17.42"). This is NOT authority.

---

## Governance Policy

### Refund Tiers

| Tier | Amount | Requirements |
|------|--------|--------------|
| Tier 1 | ≤ $25 | Automatic authorization |
| Tier 2 | $25.01 - $100 | 3+ evidence items |
| Tier 3 | > $100 | Human approval required |

### Prohibited Refunds

- Refunds to different destination
- Refunds exceeding original amount
- Refunds for fulfilled orders
- Refunds after 30 days
- Refunds when epistemic state is INCONCLUSIVE/REFUTED
- Refunds when customer identity unverified
- Duplicate refunds

---

## Authorization Derivation

Authorization is derived from:
1. Governance decision (policy satisfied)
2. Epistemic state (SUPPORTED or PARTIALLY_SUPPORTED)
3. Evidence (sufficient and consistent)

The authorization creates an `AuthorizationArtifact` with:
- Action: `issue_refund`
- Parameters: order_id, customer_id, amount, currency
- Governance decision reference
- Evidence references

---

## Capability

The capability binds:
- **Action:** `issue_refund`
- **Resource:** Order ID
- **Max quantity:** Refund amount (from evidence)
- **Temporal validity:** 24 hours
- **Authorization reference:** Parent authorization

---

## Consequence

The consequence type is `PAYMENT` (external-consequential).

Even though the first implementation is simulated, the authority path is real.

---

## Credential Boundary

Credentials are NEVER exposed to the model:
- Credential material is stripped from customer records
- Credentials never appear in evidence
- Credentials never appear in recommendations
- Credentials never appear in receipts
- Credentials never appear in provenance

The credential flow:
```
Authorization → Capability → Credential Broker → Payment Adapter
```

---

## Execution Path

```
Agent investigates ticket
        ↓
Evidence gathered
        ↓
Epistemic state evaluated
        ↓
Recommendation made
        ↓
Governance evaluated
        ↓
Authorization derived
        ↓
Capability materialized
        ↓
Capability verified
        ↓
Refund executed (simulated)
        ↓
Receipt generated
        ↓
Provenance recorded
```

---

## Provenance Graph

The final artifact allows reconstruction:

```
Customer Complaint
    ↓
Evidence
    ↓
Hypothesis
    ↓
Epistemic State
    ↓
Recommendation
    ↓
Governance Decision
    ↓
Authorization Artifact
    ↓
Execution Capability
    ↓
Consequence Request
    ↓
Execution Receipt
    ↓
Payment Result
```

---

## Adversarial Experiments

### Model Cannot Create Authority

| Attack | Result |
|--------|--------|
| Model recommends refund for fulfilled order | ✅ REJECTED |
| Model recommends refund above threshold | ✅ REJECTED |
| Model attempts to bypass governance | ✅ REJECTED |
| Model attempts to create capability | ✅ REJECTED |
| Model attempts to create receipt | ✅ REJECTED |

### Credential Boundary

| Attack | Result |
|--------|--------|
| Credential material in evidence | ✅ STRIPPED |
| Credential material in recommendation | ✅ ABSENT |
| Credential material in receipt | ✅ ABSENT |

### Argument Derivation

| Attack | Result |
|--------|--------|
| Model proposes amount ≠ evidence | ✅ REJECTED |
| Amount exceeds evidence | ✅ REJECTED |

### Natural Language Variation

| Test | Result |
|------|--------|
| Same evidence → same authority | ✅ VERIFIED |

---

## Architectural Findings

### What Worked

1. **Complete protocol loop** — The entire chain from observation to provenance functions correctly
2. **Epistemic boundary** — Model output does not create authority
3. **Governance boundary** — Policy is enforced independently of model recommendations
4. **Credential boundary** — Credentials are never exposed to the model
5. **Evidence stripping** — Credential material is stripped before evidence recording

### What Was Hard

1. **Credential stripping** — Required explicit attention to never expose credential material
2. **Evidence derivation** — Amounts must come from evidence, not model output
3. **Temporal validity** — Capability expiration must be enforced

### Limitations

1. **Simulated payment** — The payment adapter is simulated, not real
2. **No real model** — The "model" is deterministic logic, not an LLM
3. **No process restart** — Restart experiment not yet implemented
4. **No tampering** — Tampering experiment not yet implemented

---

## Remaining Open Boundaries

| Boundary | Status |
|----------|--------|
| ARGO | Open |
| MCP | Open |
| Payments | Open |
| Identity | Open |

---

## Conclusion

The Sovereign Operations Specimen demonstrates that the SAS protocol can govern a real operational workflow. The model proposes, evidence constrains, governance decides, authority derives, capability binds, execution effects, and provenance remembers.

The key finding: **AUTHORITY IS NOT A PROPERTY OF THE MODEL. AUTHORITY IS A DERIVED PROPERTY OF THE PROTOCOL STATE.**
