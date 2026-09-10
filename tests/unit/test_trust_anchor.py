"""Phase 17 tests: Trust Anchor.

Tests investigate the smallest explicit trust-anchor model required
to replace the implicit hardcoded authority root without introducing
authority regress.

Key finding: Authority origin, trust anchor, and delegation are three
distinct concepts. Two sovereign domains can coexist without one being
subordinate. Delegation can terminate at a bounded depth. Trust anchor
rotation does not require regress. Self-authorization remains possible
without explicit prevention.
"""

import pytest
from examples.sovereign_agent.trust_anchor import (
    AnchorStatus,
    AnchorType,
    AuthorityDomain,
    TerminatedDelegationChain,
    TerminatedDelegationLink,
    TrustAnchor,
    TrustAnchorEngine,
    TrustAnchorExperimentResult,
    run_all_phase17_experiments,
    run_distinguish_three_concepts,
    run_test_anchor_compromise,
    run_test_anchor_rotation,
    run_test_anchor_scope,
    run_test_anchor_temporality,
    run_test_authority_conservation,
    run_test_cross_domain_delegation,
    run_test_delegate_vs_execute,
    run_test_delegation_termination,
    run_test_non_self_authorization,
    run_test_oracle_separation,
    run_test_sovereign_domains,
)


class TestTrustAnchor:
    """Test trust anchor records."""

    def test_genesis_anchor(self):
        """Test genesis anchor creation."""
        engine = TrustAnchorEngine()
        anchor = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin",
            domain="production",
            authority_scope="*",
        )
        assert anchor.is_active is True
        assert anchor.anchor_type == AnchorType.GENESIS
        assert anchor.non_delegable is True

    def test_anchor_delegation_rights(self):
        """Test anchor delegation rights."""
        engine = TrustAnchorEngine()
        anchor = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin",
            domain="production",
            authority_to_delegate=True,
            max_delegation_depth=3,
        )
        assert anchor.can_delegate is True

    def test_anchor_no_delegation(self):
        """Test anchor without delegation rights."""
        engine = TrustAnchorEngine()
        anchor = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin",
            domain="production",
            authority_to_delegate=False,
            max_delegation_depth=0,
        )
        assert anchor.can_delegate is False

    def test_anchor_scope(self):
        """Test anchor scope boundaries."""
        engine = TrustAnchorEngine()
        anchor = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin",
            domain="production",
            authority_scope="production",
        )
        assert anchor.can_delegate_to("production") is True
        assert anchor.can_delegate_to("staging") is False

    def test_anchor_cross_domain(self):
        """Test anchor cross-domain delegation."""
        engine = TrustAnchorEngine()
        anchor = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin",
            domain="domain_a",
            authority_scope="domain_a",
            metadata={"cross_domain_delegation": True},
        )
        assert anchor.can_delegate_to("domain_b") is True

    def test_expired_anchor(self):
        """Test expired anchor is not active."""
        engine = TrustAnchorEngine()
        anchor = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin",
            domain="production",
            status=AnchorStatus.EXPIRED,
        )
        assert anchor.is_active is False
        assert anchor.can_delegate is False


class TestAuthorityDomain:
    """Test authority domains."""

    def test_sovereign_domain(self):
        """Test sovereign domain creation."""
        engine = TrustAnchorEngine()
        anchor = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin",
            domain="production",
        )
        domain = engine.create_authority_domain(
            domain_id="production",
            trust_anchor=anchor,
        )
        assert domain.is_sovereign is True

    def test_cross_domain_authority(self):
        """Test cross-domain authority detection."""
        engine = TrustAnchorEngine()
        anchor_a = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin_a",
            domain="domain_a",
        )
        anchor_b = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin_b",
            domain="domain_b",
        )
        domain_a = engine.create_authority_domain(
            domain_id="domain_a",
            trust_anchor=anchor_a,
        )
        domain_b = engine.create_authority_domain(
            domain_id="domain_b",
            trust_anchor=anchor_b,
            metadata={"delegated_from": ["domain_a"]},
        )
        assert domain_b.has_cross_domain_authority(domain_a) is False
        assert domain_a.has_cross_domain_authority(domain_b) is False


class TestTerminatedDelegationChain:
    """Test terminated delegation chains."""

    def test_chain_depth(self):
        """Test chain depth."""
        engine = TrustAnchorEngine()
        anchor = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin",
            domain="production",
        )
        link1 = TerminatedDelegationLink(
            link_id="link_001",
            delegator_id=anchor.anchor_id,
            delegate_id="level_1",
            capability="delegate",
            scope="production",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
            delegation_right=True,
        )
        link2 = TerminatedDelegationLink(
            link_id="link_002",
            delegator_id="level_1",
            delegate_id="level_2",
            capability="delegate",
            scope="production",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
        )
        chain = engine.create_delegation_chain(
            anchor_id=anchor.anchor_id,
            links=[link1, link2],
            max_depth=3,
        )
        assert chain.depth == 2
        assert chain.can_continue is False  # last link has no delegation_right

    def test_terminated_chain(self):
        """Test terminated chain."""
        engine = TrustAnchorEngine()
        anchor = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin",
            domain="production",
        )
        link1 = TerminatedDelegationLink(
            link_id="link_001",
            delegator_id=anchor.anchor_id,
            delegate_id="level_1",
            capability="execute",
            scope="production",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
            is_terminal=True,
        )
        chain = engine.create_delegation_chain(
            anchor_id=anchor.anchor_id,
            links=[link1],
        )
        assert chain.is_terminated is True

    def test_recursive_chain(self):
        """Test recursive chain detection."""
        engine = TrustAnchorEngine()
        anchor = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin",
            domain="production",
        )
        # Create chain: anchor → admin → anchor (cycle back to anchor)
        link1 = TerminatedDelegationLink(
            link_id="link_001",
            delegator_id=anchor.anchor_id,
            delegate_id="admin",
            capability="modify_anchor",
            scope="production",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
        )
        link2 = TerminatedDelegationLink(
            link_id="link_002",
            delegator_id="admin",
            delegate_id=anchor.anchor_id,  # Cycles back to anchor
            capability="modify_anchor",
            scope="production",
            valid_from="2026-01-01T00:00:00Z",
            valid_until="2026-12-31T23:59:59Z",
        )
        chain = engine.create_delegation_chain(
            anchor_id=anchor.anchor_id,
            links=[link1, link2],
        )
        assert chain.is_recursive is True

    def test_depth_bound(self):
        """Test depth bound enforcement."""
        engine = TrustAnchorEngine()
        anchor = engine.create_trust_anchor(
            anchor_type=AnchorType.GENESIS,
            identity="admin",
            domain="production",
        )
        links = []
        for i in range(5):
            link = TerminatedDelegationLink(
                link_id=f"link_{i:03d}",
                delegator_id=f"level_{i}" if i > 0 else anchor.anchor_id,
                delegate_id=f"level_{i+1}",
                capability="delegate",
                scope="production",
                valid_from="2026-01-01T00:00:00Z",
                valid_until="2026-12-31T23:59:59Z",
                delegation_right=True,
            )
            links.append(link)
        chain = engine.create_delegation_chain(
            anchor_id=anchor.anchor_id,
            links=links,
            max_depth=3,
        )
        assert chain.depth == 5
        assert chain.is_terminated is True
        assert chain.depth > chain.max_depth


class TestDistinguishThreeConcepts:
    """Test distinguishing authority origin, trust anchor, delegation."""

    def test_three_concepts(self):
        """Test that three concepts are distinguished."""
        engine = TrustAnchorEngine()
        result = run_distinguish_three_concepts(engine)
        assert result.result == TrustAnchorExperimentResult.ANCHOR_EXPLICIT
        assert result.trust_anchor is not None
        assert result.trust_anchor.anchor_type == AnchorType.GENESIS


class TestNonSelfAuthorization:
    """Test non-self-authorization."""

    def test_self_authorization_possible(self):
        """Test that self-authorization is detected."""
        engine = TrustAnchorEngine()
        result = run_test_non_self_authorization(engine)
        assert result.result == TrustAnchorExperimentResult.SELF_AUTHORIZATION_POSSIBLE
        assert result.self_authorization_possible is True


class TestDelegationTermination:
    """Test delegation termination."""

    def test_delegation_terminates(self):
        """Test that delegation terminates at max depth."""
        engine = TrustAnchorEngine()
        result = run_test_delegation_termination(engine)
        assert result.result == TrustAnchorExperimentResult.DELEGATION_TERMINATES


class TestSovereignDomains:
    """Test sovereign domain coexistence."""

    def test_sovereign_domains(self):
        """Test that two sovereign domains can coexist."""
        engine = TrustAnchorEngine()
        result = run_test_sovereign_domains(engine)
        assert result.result == TrustAnchorExperimentResult.SOVEREIGN_DOMAINS_VALID
        assert result.domain_a is not None
        assert result.domain_b is not None


class TestDelegateVsExecute:
    """Test authority to delegate vs authority to execute."""

    def test_delegate_vs_execute(self):
        """Test that delegation is distinct from execution."""
        engine = TrustAnchorEngine()
        result = run_test_delegate_vs_execute(engine)
        assert result.result == TrustAnchorExperimentResult.AUTHORITY_DELEGATION_DISTINCT


class TestAnchorRotation:
    """Test trust anchor rotation."""

    def test_rotation_without_regress(self):
        """Test that anchor rotation does not create regress."""
        engine = TrustAnchorEngine()
        result = run_test_anchor_rotation(engine)
        assert result.result == TrustAnchorExperimentResult.ROTATION_WITHOUT_REGRESS


class TestCrossDomainDelegation:
    """Test cross-domain delegation."""

    def test_cross_domain(self):
        """Test cross-domain delegation preserves sovereignty."""
        engine = TrustAnchorEngine()
        result = run_test_cross_domain_delegation(engine)
        assert result.result == TrustAnchorExperimentResult.SOVEREIGN_DOMAINS_VALID


class TestAnchorScope:
    """Test trust anchor scope."""

    def test_anchor_scope(self):
        """Test anchor scope boundaries."""
        engine = TrustAnchorEngine()
        result = run_test_anchor_scope(engine)
        assert result.result == TrustAnchorExperimentResult.ANCHOR_EXPLICIT


class TestAnchorTemporality:
    """Test trust anchor temporality."""

    def test_anchor_temporality(self):
        """Test anchor temporality."""
        engine = TrustAnchorEngine()
        result = run_test_anchor_temporality(engine)
        assert result.result == TrustAnchorExperimentResult.ANCHOR_EXPLICIT


class TestAnchorCompromise:
    """Test trust anchor compromise."""

    def test_anchor_compromise(self):
        """Test anchor compromise detection."""
        engine = TrustAnchorEngine()
        result = run_test_anchor_compromise(engine)
        assert result.result == TrustAnchorExperimentResult.ANCHOR_IMPLICIT


class TestAuthorityConservation:
    """Test authority conservation."""

    def test_authority_conservation(self):
        """Test authority conservation with trust anchor."""
        engine = TrustAnchorEngine()
        result = run_test_authority_conservation(engine)
        assert result.result == TrustAnchorExperimentResult.AUTHORITY_DELEGATION_DISTINCT


class TestOracleSeparation:
    """Test oracle separation."""

    def test_oracle_separation(self):
        """Test oracle separation maintenance."""
        engine = TrustAnchorEngine()
        result = run_test_oracle_separation(engine)
        assert result.result == TrustAnchorExperimentResult.ANCHOR_EXPLICIT


class TestAllPhase17Experiments:
    """Test all Phase 17 experiments."""

    def test_all_experiments_run(self):
        """Test that all Phase 17 experiments run."""
        results = run_all_phase17_experiments()
        assert results["total_experiments"] == 12

    def test_anchor_explicit(self):
        """Test that anchor is explicit."""
        results = run_all_phase17_experiments()
        assert results["anchor_explicit_count"] >= 4

    def test_sovereign_domains_valid(self):
        """Test that sovereign domains are valid."""
        results = run_all_phase17_experiments()
        assert results["sovereign_domains_valid_count"] >= 1

    def test_rotation_without_regress(self):
        """Test that rotation does not create regress."""
        results = run_all_phase17_experiments()
        assert results["rotation_without_regress_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
