# Dependency Epistemic Model

> **Date:** 2026-09-09
> **Phase:** Knowledge Acquisition Specimen

This document explains the epistemic model underlying the Payment Infrastructure Dependency Auditor.

---

## Core Distinctions

The dependency epistemic model is built on several critical distinctions that must NOT be collapsed:

### 1. Observation ≠ Reference ≠ Dependency ≠ Necessity ≠ Causality ≠ Criticality ≠ Generalization ≠ Authority

Each of these represents a different epistemic category. Evidence for one does NOT automatically authorize another.

```
OBSERVATION: "Code mentions X"
     ↓ (requires evidence)
REFERENCE: "Code references X"
     ↓ (requires evidence)
DEPENDENCY: "System depends on X"
     ↓ (requires evidence)
NECESSITY: "System requires X for operation"
     ↓ (requires evidence)
CAUSALITY: "X causes Y to happen"
     ↓ (requires evidence)
CRITICALITY: "X is critical for operation"
     ↓ (requires evidence)
GENERALIZATION: "This holds across environments"
     ↓ (requires evidence)
AUTHORITY: "We are authorized to claim this"
```

### 2. Static Reference ≠ Runtime Dependency

The most common error in dependency analysis is conflating "code mentions X" with "system requires X."

```python
# This is a STATIC REFERENCE:
import some_library

# This does NOT prove a RUNTIME DEPENDENCY:
# - The import might be conditional
# - The code might be dead
# - The library might be optional
# - The import might be unused
```

### 3. Runtime Dependency ≠ Operational Necessity

A system may depend on something at runtime without being unable to operate when that dependency disappears.

```python
# Example: feature flags
# - Runtime dependency: YES (code calls feature-flags service)
# - Operational necessity: NO (system works with defaults if service unavailable)
```

### 4. Dependency Existence ≠ Dependency Criticality

```python
# A service may have many dependencies
# Only some are critical for operation
# Criticality requires failure analysis
```

### 5. Documentation ≠ Ground Truth

Documentation may be:
- Outdated
- Incomplete
- Wrong about mechanism
- Wrong about environment
- Missing conditionals
- Overstating criticality

---

## Type System

### Dependency Types

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

## Authority Matrix

The authority matrix defines which observation methods can establish which proposition types:

| Observation Method | Can Establish |
|-------------------|---------------|
| Static Analysis | STATIC_REFERENCE |
| Configuration Parse | CONFIGURATION_DEPENDENCY |
| Documentation Parse | STATIC_REFERENCE |
| Runtime Test | RUNTIME_DEPENDENCY, OPERATIONAL_DEPENDENCY |
| Failure Injection | FAILURE_DEPENDENCY |
| Manual Verification | Any (with evidence) |

**Critical Rule:** Evidence for one proposition type CANNOT automatically authorize another.

---

## Evidence Scope

### Environment Scope

Evidence gathered in one environment does NOT automatically generalize to another:

```python
# Staging evidence
edge = DependencyEdge(
    source="payments",
    target="feature-flags",
    environment="staging",  # Scope: staging only
    scope="Staging environment only",
)

# CANNOT automatically become:
edge = DependencyEdge(
    source="payments",
    target="feature-flags",
    environment="production",  # Different scope!
    scope="Production",  # Requires separate evidence
)
```

### Temporal Scope

Evidence gathered at one time does NOT automatically generalize to all times:

```python
# Startup-only dependency
edge = DependencyEdge(
    source="payments",
    target="config-service",
    proposition_type=TEMPORAL_DEPENDENCY,
    scope="Startup only",
)
```

### Conditional Scope

Evidence gathered under one condition does NOT automatically generalize:

```python
# International-only dependency
edge = DependencyEdge(
    source="payments",
    external-tax",
    proposition_type=ENVIRONMENT_DEPENDENCY,
    scope="International transactions only",
)
```

---

## Documentation Drift

### Types

```python
class DriftType(Enum):
    DOCUMENTED_EXISTS = "documented_exists"           # Doc says exists, does
    DOCUMENTED_REMOVED = "documented_removed"          # Doc says exists, removed
    UNDISCOVERED = "undiscovered"                      # Exists but not documented
    WRONG_MECHANISM = "wrong_mechanism"                # Doc describes wrong mechanism
    WRONG_ENVIRONMENT = "wrong_environment"            # Doc says wrong environment
    MISSING_CONDITIONAL = "missing_conditional"        # Doc omits conditional
    WRONG_CRITICALITY = "wrong_criticality"            # Doc says required but optional
```

### Epistemic Status

Each drift item has an epistemic status:

- **UNDISCOVERED:** Observed in code, not in documentation
  - Epistemic state: OBSERVED
  - Scope: What was actually observed
  - Limitations: Static analysis cannot prove runtime behavior

- **DOCUMENTED_REMOVED:** In documentation, not in code
  - Epistemic state: DOCUMENTED (but may be stale)
  - Scope: Documentation reference
  - Limitations: Documentation may be outdated

---

## Confidence vs Authority

The `confidence` field exists on dependency edges but is NOT authoritative:

```python
@dataclass(frozen=True)
class DependencyEdge:
    ...
    confidence: float = 0.0  # NOT authority
```

**Rule:** A model can have 99% confidence and still possess insufficient evidence.

Confidence is a stated certainty. Authority is derived from evidence and epistemic evaluation.

---

## Provenance

Every dependency edge must be reconstructible:

```python
@dataclass(frozen=True)
class DependencyEdge:
    source: str
    target: str
    dependency_type: DependencyType
    source_artifact: str
    source_location: str
    observation_method: ObservationMethod
    evidence: list[str]
    alternatives: list[str]
    experiment: Optional[str]
    scope: str
    limitations: list[str]
    provenance_id: str
```

**Reconstruction questions:**
1. Who proposed this dependency?
2. What files were observed?
3. What observations were extracted?
4. What hypotheses existed?
5. What alternatives were considered?
6. What experiment was selected?
7. Why was that experiment authoritative?
8. What happened?
9. What evidence resulted?
10. How did the epistemic state transition?
11. What remains unknown?

---

## Adversarial Protections

### Model Cannot Create Authority

```python
# ATTACK: Model says "X depends on Y"
# RESULT: Creates HYPOTHESIZED edge, not SUPPORTED
edge = DependencyEdge(
    source="model_claim",
    target="feature-flags",
    epistemic_state=EpistemicState.HYPOTHESIZED,
    proposition_type=PropositionType.STATIC_REFERENCE,
    confidence=0.99,  # High confidence
    limitations=["No evidence"],  # But no evidence
)
# epistemic_state remains HYPOTHESIZED
```

### Static ≠ Runtime

```python
# ATTACK: "There's an import, so it's a runtime dependency"
# RESULT: Import creates STATIC_REFERENCE, not RUNTIME_DEPENDENCY
edge = DependencyEdge(
    source="payments",
    target="httpx",
    dependency_type=DependencyType.IMPORT,
    proposition_type=PropositionType.STATIC_REFERENCE,  # Not RUNTIME
)
```

### Scope Preservation

```python
# ATTACK: "Tested in staging, so it's true in production"
# RESULT: Scope is preserved
edge = DependencyEdge(
    source="payments",
    target="feature-flags",
    environment="staging",  # Staging only
    scope="Staging environment only",
)
# Cannot generalize to production without evidence
```

---

## Conclusion

The Dependency Epistemic Model ensures that:

1. **Every dependency claim carries its evidence**
2. **Every edge has bounded authority**
3. **Static analysis cannot prove runtime behavior**
4. **Model confidence is not authority**
5. **Scope is preserved across transformations**
6. **Documentation is not ground truth**
7. **All claims are reconstructible from provenance**

> **A dependency is not authoritative because code mentions it. It becomes authoritative only to the extent that the protocol can establish what kind of dependency it is, what evidence supports it, what alternatives have been discriminated, and where the claim's authority ends.**
