# Payment Infrastructure Dependency Auditor

> **Date:** 2026-09-09
> **Phase:** Knowledge Acquisition Specimen
> **Tests:** 1,843 passing (50 new tests for this specimen)

This document describes the Sovereign Payment Infrastructure Dependency Auditor, the second real-world specimen for the Sovereign Agent Stack.

---

## Purpose

The Sovereign Payment Infrastructure Dependency Auditor demonstrates that SAS can govern **knowledge acquisition** — not just operational decisions.

The central question:

> **Can a sovereign agent investigate a complex software system and produce dependency claims whose epistemic status, evidence, scope, alternatives, experimental basis, and provenance are all mechanically reconstructible?**

This is fundamentally different from the Sovereign Operations Agent:

| Sovereign Operations Agent | Payment Dependency Auditor |
|---------------------------|---------------------------|
| Governs actions | Governs knowledge acquisition |
| Constrains execution | Constrains claims |
| Model proposes, governance decides | Model hypothesizes, evidence discriminates |
| Authority → execution | Evidence → epistemic state |

---

## Architectural Invariants

### Core Distinctions

```
STATIC_REFERENCE ≠ RUNTIME_DEPENDENCY ≠ OPERATIONAL_NECESSITY

MODEL OUTPUT ≠ AUTHORITY

CONFIDENCE ≠ EVIDENCE

DEPENDENCY_EXISTENCE ≠ DEPENDENCY_CRITICALITY

DOCUMENTATION ≠ GROUND_TRUTH
```

### Authority Boundary

The system is **READ-ONLY** with respect to the target infrastructure:

- Never executes a payment
- Never modifies the target repository
- Never treats model-generated dependency claims as authoritative
- Only creates local analysis artifacts

---

## System Architecture

### Dependency Ontology

The auditor defines a typed dependency taxonomy:

```python
class DependencyType(Enum):
    IMPORT = "import"              # Code imports
    CALL = "call"                  # Function calls
    NETWORK = "network"            # HTTP/gRPC calls
    DATABASE = "database"          # Database connections
    QUEUE = "queue"                # Message queues
    FILESYSTEM = "filesystem"      # File access
    PROCESS = "process"            # Subprocesses
    CONFIGURATION = "configuration"  # Config references
    CREDENTIAL = "credential"      # Credential access
    IDENTITY = "identity"          # Auth dependencies
    SERVICE = "service"            # Service-to-service
    SCHEMA = "schema"              # Schema references
    TEMPORAL = "temporal"          # Time-dependent
    ENVIRONMENT = "environment"    # Environment-specific
    DOCUMENTATION = "documentation"  # Doc references
    TEST = "test"                  # Test fixtures
    TRANSITIVE = "transitive"      # Transitive deps
```

### Epistemic States

```python
class EpistemicState(Enum):
    DOCUMENTED = "documented"                    # In documentation
    OBSERVED = "observed"                        # Observed in code
    INFERRED = "inferred"                        # Inferred from patterns
    HYPOTHESIZED = "hypothesized"                # Proposed, unverified
    EXPERIMENTALLY_SUPPORTED = "experimentally_supported"  # Experiment
    CONTRADICTED = "contradicted"                # Contradicted
    INCONCLUSIVE = "inconclusive"                # Insufficient evidence
    UNKNOWN = "unknown"                          # No evidence
```

### Proposition Types

```python
class PropositionType(Enum):
    STATIC_REFERENCE = "static_reference"        # Code mentions it
    CONFIGURATION_DEPENDENCY = "configuration_dependency"  # Config refs
    RUNTIME_DEPENDENCY = "runtime_dependency"    # Required at runtime
    OPERATIONAL_DEPENDENCY = "operational_dependency"  # Required for operation
    FAILURE_DEPENDENCY = "failure_dependency"    # Causes failure if gone
    TEMPORAL_DEPENDENCY = "temporal_dependency"  # Only at specific times
    ENVIRONMENT_DEPENDENCY = "environment_dependency"  # Only some envs
    TRANSITIVE_DEPENDENCY = "transitive_dependency"  # Through another
```

---

## Target System

### Fixture Structure

```
fixture/
├── services/
│   ├── checkout/         # Customer order intake
│   ├── payments/         # Core payment processing
│   ├── ledger/           # Double-entry bookkeeping
│   ├── refunds/          # Refund processing
│   ├── notifications/    # Email/SMS notifications
│   ├── fraud/            # Fraud evaluation
│   └── reconciliation/   # Settlement reconciliation
├── config/
│   ├── production.yaml   # Production configuration
│   └── staging.yaml      # Staging configuration
├── schemas/
│   ├── payment.json      # Payment schema
│   └── ledger.json       # Ledger entry schema
├── docs/
│   ├── architecture.md   # Architecture documentation
│   ├── payment-flow.md   # Payment flow documentation
│   └── runbook.md        # Operations runbook
├── infra/
│   ├── docker-compose.yaml
│   └── deployment.yaml
├── tests/
│   ├── integration/
│   └── unit/
└── scripts/
    ├── reconciliation.py
    └── settlement.py
```

### Intentional Discrepancies

The fixture contains deliberate differences between documentation and implementation:

#### Documented
```
checkout → payments
payments → ledger, fraud
refunds → payments, ledger
reconciliation → ledger, payments
```

#### Actually Present in Code
```
checkout → payments, customer-profile, feature-flags
payments → ledger, fraud, customer-profile, feature-flags, external-tax, redis
refunds → payments, ledger, customer-profile, feature-flags
reconciliation → ledger, payments, external-provider
fraud → ml-model-service
notifications → sendgrid, twilio
```

#### Key Undocumented Dependencies

| Dependency | Type | Why Undocumented |
|------------|------|------------------|
| payments → feature-flags | NETWORK | Gradual rollout, not in architecture |
| payments → customer-profile | NETWORK | KYC verification, considered internal |
| payments → external-tax | NETWORK | International only, not in main flow |
| payments → redis | DATABASE | Caching layer, considered infrastructure |
| checkout → feature-flags | NETWORK | New checkout flow, not documented |
| refunds → customer-profile | NETWORK | Eligibility check, not documented |
| fraud → ml-model-service | NETWORK | External model, considered black box |
| reconciliation → external-provider | NETWORK | Settlement files, not documented |

---

## Ingestion Layer

### Supported Artifacts

| Artifact | Analysis | Status |
|----------|----------|--------|
| Python | Imports, HTTP, DB, Redis, env vars, URLs | Full |
| TypeScript/JavaScript | Imports | Full |
| YAML | Service deps, endpoints | Full |
| JSON | Schema refs | Full |
| Markdown | Dependency mentions | Full |
| Dockerfile | Base images | Full |
| Docker Compose | Service deps | Full |
| Shell | curl/wget calls | Full |

### Observation Authority

Each observation is labeled with its actual authority:

```python
@dataclass(frozen=True)
class RawObservation:
    source: str
    target: str
    observation_type: str
    artifact: str
    location: str
    context: str
    environment: str
```

**Critical:** Observations are NOT dependency claims. They are evidence that may support dependency claims after epistemic evaluation.

---

## Dependency Graph

### Structure

The graph is NOT a conventional dependency graph. Every edge carries complete epistemic provenance:

```python
@dataclass(frozen=True)
class DependencyEdge:
    source: str
    target: str
    dependency_type: DependencyType
    source_artifact: str
    source_location: str
    observation_method: ObservationMethod
    environment: str
    epistemic_state: EpistemicState
    proposition_type: PropositionType
    evidence: list[str]
    alternatives: list[str]
    experiment: Optional[str]
    scope: str
    limitations: list[str]
    provenance_id: str
    confidence: float  # NOT authority
```

### Documentation Drift Detection

The auditor detects and classifies documentation drift:

```python
class DriftType(Enum):
    DOCUMENTED_EXISTS = "documented_exists"
    DOCUMENTED_REMOVED = "documented_removed"
    UNDISCOVERED = "undiscovered"
    WRONG_MECHANISM = "wrong_mechanism"
    WRONG_ENVIRONMENT = "wrong_environment"
    MISSING_CONDITIONAL = "missing_conditional"
    WRONG_CRITICALITY = "wrong_criticality"
```

---

## Epistemic Rules

### Static Reference ≠ Runtime Dependency

```python
# CRITICAL RULE:
# Static analysis alone cannot prove runtime behavior.
# Evidence for STATIC_REFERENCE cannot authorize RUNTIME_DEPENDENCY.
```

### Scope Preservation

```python
# Evidence scope is preserved across transformations.
# Staging evidence does NOT automatically generalize to production.
```

### Confidence ≠ Authority

```python
# A model can have 99% confidence and still possess insufficient evidence.
# The confidence field exists but is NOT authoritative.
```

### Proposition Type Preservation

```python
# Different proposition types remain distinct.
# Evidence for one type cannot authorize another.
```

---

## Adversarial Tests

### Model Cannot Create Authority

| Attack | Result |
|--------|--------|
| Model says "X depends on Y" | Does NOT create SUPPORTED dependency |
| Model has 99% confidence | Does NOT elevate epistemic state |
| Model claims runtime dependency | Stays HYPOTHESIZED without evidence |

### Static ≠ Runtime

| Attack | Result |
|--------|--------|
| Import statement alone | Does NOT prove runtime dependency |
| Dead code reference | Produces observation, not dependency |
| Configuration reference | Does NOT prove operational necessity |

### Scope Preservation

| Attack | Result |
|--------|--------|
| Staging evidence → production claim | Blocked by scope |
| Single environment → all environments | Blocked by scope |
| Conditional → universal | Blocked by scope |

### Evidence Integrity

| Attack | Result |
|--------|--------|
| Conflicting evidence | Produces INCONCLUSIVE, not arbitrary choice |
| Contradictory experiments | Preserved as contradiction |
| Tampering detection | Detected via provenance |

---

## Results Summary

### Test Count: 1,843

- **Unit tests:** ~1,600
- **Integration tests:** ~160
- **Adversarial tests:** ~83

### New Tests This Phase

| Test File | Tests | Purpose |
|-----------|-------|---------|
| `test_payment_dependency_auditor.py` | 32 | Integration tests |
| `test_payment_dependency_auditor_attacks.py` | 18 | Adversarial tests |

### Audit Results (Fixture)

| Metric | Value |
|--------|-------|
| Files analyzed | 15 |
| Lines analyzed | 1,405 |
| Total observations | 105 |
| Dependency edges | 105 |
| Documented dependencies | 25 |
| Documentation drift items | 130 |
| Undocumented dependencies | 8 |

---

## Key Findings

### What Worked

1. **Complete epistemic loop** — Observation → Hypothesis → Evidence → Epistemic State → Provenance
2. **Static ≠ Runtime** — Type system prevents automatic elevation
3. **Scope preservation** — Evidence scope is preserved across transformations
4. **Confidence ≠ Authority** — High confidence without evidence stays HYPOTHESIZED
5. **Documentation drift** — Undocumented dependencies detected with epistemic status
6. **Read-only** — System never modifies target infrastructure

### What Was Hard

1. **Markdown parsing** — Documentation is free-form, requires flexible patterns
2. **Service vs file granularity** — Raw observations are file-level, but dependencies are service-level
3. **Transitive dependencies** — Not fully resolved in this version
4. **Dead code detection** — Static analysis cannot prove code is dead

### Limitations

1. **No runtime experiments** — Static analysis only; runtime experiments are future work
2. **No real model** — The "model" is deterministic logic, not an LLM
3. **Limited language coverage** — Python, YAML, JSON, Markdown only
4. **No transitive resolution** — Transitive dependencies are noted but not fully traced

---

## Architectural Significance

This specimen demonstrates a major transition:

**The system no longer merely governs actions. It governs how an agent acquires authority to make claims about another system.**

The complete investigative loop:

```
SYSTEM → OBSERVATION → DEPENDENCY GRAPH → ANOMALY →
HYPOTHESIS → ALTERNATIVE HYPOTHESES → EXPERIMENT SELECTION →
INTERVENTION → OBSERVATION → EVIDENCE → EPISTEMIC STATE → PROVENANCE
```

This connects directly to the broader Sovereign Intelligence / Knowledge Compiler / agentic GraphRAG work: not just "retrieve relevant context," but construct a graph where **every edge has epistemic provenance and bounded authority**.

---

## Conclusion

> **A dependency is not authoritative because code mentions it. It becomes authoritative only to the extent that the protocol can establish what kind of dependency it is, what evidence supports it, what alternatives have been discriminated, and where the claim's authority ends.**

The Sovereign Payment Infrastructure Dependency Auditor demonstrates that SAS can produce bounded, provenance-backed knowledge about systems — not just govern their operation.
