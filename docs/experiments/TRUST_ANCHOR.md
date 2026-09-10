# Phase 17: Trust Anchor — Report

**Date:** 2026-09-10
**Tests:** 2,610 passing (2,582 prior + 28 new)

---

## Central Research Question

> **What makes an authority root a root?**

Phase 16 established `AUTHORITY_ROOT_IMPLICIT`: the effective authority root is the hardcoded `admin` principal. The root is not explicitly governed. Self-creation of root authority is possible. Delegation termination is not enforced. The existing `AuthorityRoot` type is not integrated into the production governance authority path.

Phase 17 asks: **Can a trust anchor be explicitly represented without requiring another authority to authorize the trust anchor?**

---

## Executive Summary

**Authority origin, trust anchor, and delegation are three distinct concepts.**

12 experiments demonstrate:

1. **Three concepts distinguished** — Authority origin (where), trust anchor (assumption), delegation (how) are not identical.
2. **Self-authorization possible** — Without explicit prevention, a trust anchor can delegate authority to modify itself.
3. **Delegation terminates** — With explicit bounded depth and terminal links.
4. **Sovereign domains valid** — Two independent trust anchors can coexist without one being subordinate.
5. **Rotation without regress** — A new anchor can be independently established, not derived from the old.
6. **Cross-domain sovereignty** — Explicit cross-domain delegation preserves sovereignty of both domains.
7. **Authority to delegate ≠ authority to execute** — The anchor can delegate payment execution without executing payments itself.

---

## The Experimental Result

| Metric | Value |
|--------|-------|
| Total experiments | 12 |
| Anchor explicit | 4 |
| Anchor implicit | 1 |
| Self-authorization possible | 1 |
| Delegation terminates | 1 |
| Sovereign domains valid | 2 |
| Authority delegation distinct | 2 |
| Rotation without regress | 1 |

---

## The Three Concepts Distinguished

### Authority Origin

**Question:** Where did this authority claim originate?

**Answer:** A descriptive claim about the source of an authority assertion. The origin is the historical point where the claim first appeared in the system.

### Trust Anchor

**Question:** What non-derived assumption does the system accept as a starting point for authority derivation?

**Answer:** A normative starting condition. Not derived from another authority. The architecture states what it trusts and preserves that assumption explicitly.

### Authority Delegation

**Question:** How does authority move from one principal or authority domain to another?

**Answer:** A derived mechanism. Delegation requires explicit authority to delegate. It operates within the constraints of the trust anchor.

**Critical distinction:** Conflating these three concepts creates ambiguity between descriptive claims (origin), normative assumptions (anchor), and derived mechanisms (delegation).

---

## The Trust Anchor Model

```python
@dataclass(frozen=True)
class TrustAnchor:
    anchor_id: str
    anchor_type: AnchorType        # GENESIS, CRYPTOGRAPHIC, ORGANIZATIONAL, HARDWARE, COMPOSITE
    status: AnchorStatus          # ACTIVE, EXPIRED, REVOKED, ROTATED, COMPROMISED, SUPERSEDED
    identity: str                 # Who or what this anchor represents
    domain: str                   # The domain this anchor governs
    authority_scope: str          # Scope of authority
    temporal_bounds: dict         # Validity interval
    cryptographic_identity: str   # Optional cryptographic binding
    genesis_reference: str        # Reference to genesis state
    provenance: tuple             # Immutable provenance chain
    non_delegable: bool           # Anchor itself cannot be delegated
    authority_to_delegate: bool   # Can this anchor delegate authority
    authority_to_govern: bool     # Can this anchor govern downstream
    max_delegation_depth: int     # Maximum delegation depth (0 = no delegation)
    metadata: dict                # Additional metadata
```

### Key Properties

| Property | Meaning | Invariant |
|----------|---------|-----------|
| `non_delegable` | The anchor itself cannot be delegated | Trust anchor ≠ delegable object |
| `authority_to_delegate` | Can delegate authority to others | Authority to delegate ≠ authority to execute |
| `authority_to_govern` | Can govern downstream authority | Governance authority ≠ operational capability |
| `max_delegation_depth` | Limits chain length | Delegation terminates |

---

## Authority Domain Model

```python
@dataclass(frozen=True)
class AuthorityDomain:
    domain_id: str
    trust_anchor: TrustAnchor
    policy_authority: str
    effect_authority: str
    governance_authority: str
    execution_authority: str
    metadata: dict
```

Two domains can coexist independently:

```
DOMAIN_A                    DOMAIN_B
TRUST_ANCHOR_A              TRUST_ANCHOR_B
    │                           │
POLICY_AUTHORITY_A          POLICY_AUTHORITY_A
    │                           │
EFFECT_AUTHORITY_A          EFFECT_AUTHORITY_B
    │                           │
GOVERNANCE_A                GOVERNANCE_B
    │                           │
EXECUTION_A                 EXECUTION_B
```

**Neither domain is subordinate to the other.** Cross-domain authority requires explicit delegation.

---

## The Dangerous Finding: Self-Authorization Remains Possible

```
TRUST_ANCHOR
      ↓
AUTHORITY TO MODIFY ANCHOR (delegated to policy_admin)
      ↓
POLICY_ADMIN modifies ANCHOR
      ↓
ANCHOR is now different
```

Without explicit prevention, the trust anchor can participate in its own derivation. This is the same finding as Phase 16, now confirmed in the trust anchor model.

**Prevention requires explicit:**
- Non-delegable anchor property
- No delegation of `modify_anchor` capability
- Cycle detection in delegation chains

---

## Delegation Termination

The delegation chain terminates when:

| Condition | Mechanism |
|-----------|-----------|
| Terminal link | `is_terminal=True` — no further delegation allowed |
| No delegation right | `delegation_right=False` — delegate cannot re-delegate |
| Max depth exceeded | `depth >= max_depth` — hard limit on chain length |
| Anchor reached | `delegate_id == anchor_id` — cycle detected |

This is a semantic requirement, not yet enforced by the production architecture.

---

## Trust Anchor Rotation Without Regress

```
ANCHOR_A (active)  →  ANCHOR_B (active)
```

**Question:** Is B derived from A?

**Answer:** No. B is independently established with its own provenance. The system can represent this without regress:

- A has status `ROTATED`
- B has status `ACTIVE`
- B's provenance is `("independent_establishment", "key_rotation")`
- B is NOT derived from A

This avoids the infinite regress problem: `admin → root_admin → genesis_admin → ...`

---

## Cross-Domain Delegation

```
DOMAIN_A → explicit delegation → DOMAIN_B
```

| Scenario | A→B | B→A | Sovereignty Preserved? |
|----------|-----|-----|------------------------|
| A delegates to B | ✅ | ❌ | ✅ Yes |
| B delegates to A | ❌ | ✅ | ✅ Yes |
| Mutual delegation | ✅ | ✅ | ⚠️ Depends on scope |
| No delegation | ❌ | ❌ | ✅ Yes |

**Key insight:** Cross-domain delegation is explicit and unidirectional by default. Both domains remain sovereign within their own scope.

---

## Authority to Delegate ≠ Authority to Execute

A trust anchor can have:

```python
authority_to_delegate=True
authority_to_govern=True
# But the anchor itself does NOT execute payments
```

This is semantically meaningful:
- The anchor governs the delegation system
- The anchor does not perform operational actions
- Payment execution is delegated to a service
- The service has `is_terminal=True` (cannot further delegate)

---

## Comparison with Phase 16

| Property | Phase 16 (Authority Root) | Phase 17 (Trust Anchor) |
|----------|---------------------------|-------------------------|
| Root type | Hardcoded `admin` | Explicit `TrustAnchor` |
| Integration | Not integrated | Experimental model |
| Self-authorization | Possible | Still possible (needs prevention) |
| Delegation termination | Not enforced | Explicitly modeled |
| Sovereign domains | Not represented | Explicitly modeled |
| Rotation | Not implemented | Modeled without regress |
| Cross-domain | Not addressed | Explicit delegation |

---

## Underspecifications Discovered

| Distinction | Status | Impact |
|-------------|--------|--------|
| Authority origin vs trust anchor vs delegation | ✅ Distinguished | Three concepts separated |
| Non-delegable anchor | ✅ Modeled | Anchor cannot be delegated |
| Self-authorization prevention | ❌ Not prevented | Anchor can still self-authorize |
| Delegation termination | ✅ Modeled | Chain terminates at bounded depth |
| Sovereign domains | ✅ Modeled | Two domains coexist independently |
| Cross-domain delegation | ✅ Modeled | Explicit and unidirectional |
| Anchor rotation | ✅ Modeled | No regress required |
| Anchor compromise recovery | ❌ Not implemented | No recovery mechanism |
| Derived authority invalidation on anchor expiration | ❌ Not implemented | Semantic requirement only |
| Oracle separation | ✅ Maintained | Normative assumptions explicit |

---

## Required Invariants (Status After Phase 17)

| Invariant | Status |
|-----------|--------|
| AUTHORITY ORIGIN ≠ TRUST ANCHOR ≠ DELEGATION | ✅ Distinguished |
| TRUST ANCHOR IS NON-DERIVED | ✅ By definition |
| TRUST ANCHOR MAY BE NON-DELEGABLE | ✅ Modeled |
| AUTHORITY TO DELEGATE ≠ AUTHORITY TO EXECUTE | ✅ Verified |
| DELEGATION MUST TERMINATE | ✅ Modeled |
| TWO TRUST ANCHORS CAN COEXIST | ✅ Verified |
| CROSS-DELEGATION REQUIRES EXPLICIT RIGHT | ✅ Verified |
| ANCHOR ROTATION WITHOUT REGRESS | ✅ Verified |
| SELF-AUTHORIZATION MUST BE PREVENTED | ❌ Still possible |
| DERIVED AUTHORITY DOES NOT SURVIVE ANCHOR EXPIRATION | ❌ Not enforced |

---

## The Answer to the Central Question

> **What makes an authority root a root?**

**It is a normative starting condition that does not require another authority to authorize its existence.**

> **Can a trust anchor be explicitly represented without regress?**

**Yes.** The trust anchor is represented as an explicit data structure with:
- Identity, domain, scope
- Non-delegable property
- Delegation rights and limits
- Provenance (installation-time, key-based, organizational)
- Temporal bounds

The trust anchor does not need to prove its legitimacy internally. The architecture states what it trusts and preserves that assumption explicitly.

> **What terminates delegation?**

**Explicit termination conditions:**
- Non-delegable anchor
- Max delegation depth
- Terminal links
- No delegation right

> **Can authority domains coexist independently?**

**Yes.** Two trust anchors can coexist without one being subordinate. Cross-domain authority requires explicit delegation.

> **Can the trust anchor delegate authority without possessing operational capability?**

**Yes.** The anchor can delegate `PAYMENT_EXECUTION_AUTHORITY` without itself executing payments.

---

## The Phase 17 Architecture

```
TRUST ANCHOR (non-derived assumption)
      │
      ├→ AUTHORITY DELEGATION (derived mechanism)
      │       │
      │       ↓
      │   POLICY AUTHORITY
      │       │
      │       ↓
      │   EFFECT AUTHORITY
      │       │
      │       ↓
      │   GOVERNANCE
      │       │
      │       ↓
      │   DOWNSTREAM AUTHORITY
      │       │
      │       ↓
      │   CAPABILITY
      │       │
      │       ↓
      │   EXECUTION
      │
      ├→ GOVERNANCE AUTHORITY (over delegation system)
      │
      └→ CROSS-DOMAIN DELEGATION (explicit, unidirectional)
              │
              ↓
          OTHER SOVEREIGN DOMAIN
              │
          ITS OWN TRUST ANCHOR
```

---

## The Sovereignty Thesis

Phase 17 is where the word "sovereign" starts becoming technically meaningful rather than rhetorical.

If two independent trust anchors can coexist, maintain separate authority domains, and only acquire cross-domain authority through explicit delegation, then we have something much deeper than a local authorization framework.

**Sovereignty is not the absence of dependencies. It is the ability to make the authority boundary itself explicit, inspectable, bounded, and non-transferable except through an explicit act of delegation.**

This connects the deepest part of the current research directly back to the original Sovereign Agent Stack thesis.

---

## Phase 17 Classification

**Result:** `TRUST_ANCHOR_EXPLICIT`

The trust anchor can be explicitly represented without introducing authority regress. Three concepts are distinguished: authority origin, trust anchor, delegation. Two sovereign domains can coexist. Delegation terminates at bounded depth. Rotation does not require regress. Self-authorization remains possible without explicit prevention.

---

## The Conceptual Progression

```
Phase 12  POLICY
Phase 13  POLICY GOVERNANCE
Phase 14  POLICY → AUTHORITY AMPLIFICATION
Phase 15  EFFECT BOUNDARY
Phase 16  AUTHORITY ROOT (implicit)
Phase 17  TRUST ANCHOR (explicit)  ← we are here
```

Phase 17 makes the trust anchor explicit. The architecture now has a model for representing the non-derived starting condition from which authority delegation begins.

---

## Next Boundary (Phase 18)

**Anchor Enforcement** — The architecture must eventually address:

1. **Self-authorization prevention** — explicit mechanism to prevent anchor self-modification
2. **Derived authority invalidation** — invalidate derived authority on anchor expiration/revocation
3. **Anchor compromise recovery** — principled recovery mechanism
4. **Production integration** — integrate the trust anchor model into `PolicyGovernanceEngine` and `RuntimeAuthorityGate`
5. **Cryptographic binding** — bind trust anchors to cryptographic identities
6. **Genesis state representation** — explicit genesis state for installation-time anchors

The goal is not to eliminate the trust anchor. It is to make the trust anchor explicit, bounded, and recoverable.

---

## Pause Point

The experimental record now establishes through Phase 17:

1. **Set composition is safe** — it does not amplify authority.
2. **Set composition is lossy** — it destroys semantic information.
3. **Provenance-preserving composition is feasible** — it fits within existing types.
4. **The frontier is a review surface** — not the final epistemic object.
5. **Governance is projection-sufficient** — the current binary predicate consumes only membership.
6. **Epistemic conditions change governance outcomes** — scope, provenance, and disagreement are legitimate governance inputs.
7. **Epistemic quality ≠ authority** — better conditions do not mint more authority.
8. **Governance policy is declarative** — explicit predicates produce dispositions.
9. **Policy evaluation ≠ authorization** — the policy engine never creates authority.
10. **Policy lifecycle is governed** — CREATE, MODIFY, DELETE, ACTIVATE, DEACTIVATE, SUPERSEDE, ROLLBACK, OVERRIDE all require explicit authority.
11. **Policy deletion ≠ historical erasure** — deleted policies remain addressable.
12. **Scope authority is bounded** — production authority cannot expand to staging.
13. **Override ≠ governance bypass** — emergency override remains inside the architecture.
14. **The authority loop is NOT closed** — legitimate policy authority can amplify downstream execution authority.
15. **The policy mechanism is an authority amplification mechanism** — without an effect boundary.
16. **Authority is multi-dimensional** — AuthoritySurface captures principal, operation, resource, scope, temporal interval, conditions, provenance, policy lineage, and capability class.
17. **Authority envelopes bound downstream effects** — AuthorityEnvelope provides the mechanism for checking policy transformations.
18. **Effect authority must be bounded** — even explicit meta-authority requires envelope enforcement.
19. **The transformation algebra is experimentally derived** — identity is the only conservative transformation; all others require new authority.
20. **Capability class transitions are always amplifying** — no implicit ordering grants higher capability classes from lower ones.
21. **The authority root is implicit** — the root is a hardcoded bootstrap assumption, not a governed mechanism.
22. **Self-creation is possible** — authority derivation can cycle back to itself.
23. **Delegation termination is not enforced** — the chain terminates by assumption, not by enforcement.
24. **The root is a normative trust assumption** — it is assumed rather than derived.
25. **Authority origin, trust anchor, and delegation are distinct** — three concepts separated.
26. **Two sovereign domains can coexist** — independent trust anchors without subordination.
27. **Delegation can terminate at bounded depth** — explicit termination conditions.
28. **Anchor rotation does not require regress** — independent establishment possible.
29. **Authority to delegate ≠ authority to execute** — semantically meaningful distinction.
30. **Cross-domain sovereignty** — explicit delegation preserves sovereignty of both domains.

The architecture has made the trust anchor explicit. The next phase must enforce the trust anchor's invariants in the production governance path.
