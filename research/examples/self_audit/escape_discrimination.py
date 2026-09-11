"""Authority Escape Discrimination Engine."""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class EscapeClassification(str, Enum):
    FALSE_POSITIVE = "false_positive"
    NONCONSEQUENTIAL = "nonconsequential"
    UNREACHABLE = "unreachable"
    CONTROLLED_BY_AUTHORITY = "controlled_by_authority"
    REAL_ESCAPE = "real_escape"
    INCONCLUSIVE = "inconclusive"


class EscapeSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ConsequenceType(str, Enum):
    PROCESS_EXECUTION = "process_execution"
    NETWORK_MUTATION = "network_mutation"
    FILESYSTEM_MUTATION = "filesystem_mutation"
    CREDENTIAL_ACCESS = "credential_access"
    IDENTITY_MUTATION = "identity_mutation"
    EXTERNAL_API_CALL = "external_api_call"
    BROKER_ACCESS = "broker_access"
    SUBSTRATE_ACCESS = "substrate_access"
    CONFIGURATION_MUTATION = "configuration_mutation"
    AUTHORITY_MUTATION = "authority_mutation"
    READ_ONLY = "read_only"
    INFORMATIONAL = "informational"


@dataclass(frozen=True)
class EscapeHypothesis:
    hypothesis_id: str
    source: str
    target: str
    dependency_type: str
    consequence_type: ConsequenceType
    severity: EscapeSeverity
    claim: str
    static_evidence: str
    source_location: str
    target_location: str
    alternatives: list[str]
    required_experiment: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "hypothesis_id": self.hypothesis_id,
            "source": self.source,
            "target": self.target,
            "dependency_type": self.dependency_type,
            "consequence_type": self.consequence_type.value,
            "severity": self.severity.value,
            "claim": self.claim,
            "static_evidence": self.static_evidence,
            "source_location": self.source_location,
            "target_location": self.target_location,
            "alternatives": self.alternatives,
            "required_experiment": self.required_experiment,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class EscapeEvidence:
    evidence_id: str
    hypothesis_id: str
    evidence_type: str
    description: str
    source: str
    result: str
    raw_output: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "hypothesis_id": self.hypothesis_id,
            "evidence_type": self.evidence_type,
            "description": self.description,
            "source": self.source,
            "result": self.result,
            "raw_output": self.raw_output,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class EscapeClassificationResult:
    classification_id: str
    hypothesis: EscapeHypothesis
    classification: EscapeClassification
    confidence: float
    evidence: list[EscapeEvidence]
    intervention: str
    scope: str
    environment: str
    temporal_boundary: str
    remediation: str
    verification_result: str
    provenance_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "classification_id": self.classification_id,
            "hypothesis": self.hypothesis.to_dict(),
            "classification": self.classification.value,
            "confidence": self.confidence,
            "evidence": [e.to_dict() for e in self.evidence],
            "intervention": self.intervention,
            "scope": self.scope,
            "environment": self.environment,
            "temporal_boundary": self.temporal_boundary,
            "remediation": self.remediation,
            "verification_result": self.verification_result,
            "provenance_id": self.provenance_id,
            "created_at": self.created_at,
        }


class StaticEscapeAnalyzer:
    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)
        self.src_root = self.repo_root / "src" / "sas"

    def find_potential_escapes(self) -> list[EscapeHypothesis]:
        escapes = []
        escape_patterns = [
            {
                "name": "BrokerAdapter Direct Access",
                "pattern": r"class\s+.*BrokerAdapter",
                "target_pattern": r"submit_trade|submit_order",
                "consequence_type": ConsequenceType.BROKER_ACCESS,
                "severity": EscapeSeverity.HIGH,
                "dependency_type": "direct_call",
            },
            {
                "name": "Subprocess Execution",
                "pattern": r"subprocess\.",
                "target_pattern": r"run|Popen|call|check_output|check_call",
                "consequence_type": ConsequenceType.PROCESS_EXECUTION,
                "severity": EscapeSeverity.CRITICAL,
                "dependency_type": "process_execution",
            },
            {
                "name": "Network Mutation",
                "pattern": r"httpx\.|requests\.",
                "target_pattern": r"post|put|delete|patch",
                "consequence_type": ConsequenceType.NETWORK_MUTATION,
                "severity": EscapeSeverity.HIGH,
                "dependency_type": "network_call",
            },
            {
                "name": "Filesystem Mutation",
                "pattern": r"open\s*\(|os\.remove|os\.unlink|os\.rename|shutil\.",
                "target_pattern": r"w|a|write|truncate",
                "consequence_type": ConsequenceType.FILESYSTEM_MUTATION,
                "severity": EscapeSeverity.MEDIUM,
                "dependency_type": "filesystem_call",
            },
        ]

        for py_file in self.src_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                rel_path = py_file.relative_to(self.repo_root)

                for pattern_def in escape_patterns:
                    for match in re.finditer(pattern_def["pattern"], content, re.IGNORECASE):
                        start = max(0, match.start() - 200)
                        end = min(len(content), match.end() + 200)
                        context = content[start:end]

                        if re.search(pattern_def["target_pattern"], context, re.IGNORECASE):
                            escapes.append(EscapeHypothesis(
                                hypothesis_id=f"hyp_{len(escapes)+1:04d}",
                                source=str(rel_path),
                                target=match.group(0),
                                dependency_type=pattern_def["dependency_type"],
                                consequence_type=pattern_def["consequence_type"],
                                severity=pattern_def["severity"],
                                claim=f"Potential {pattern_def['name']} escape: {match.group(0)} in {rel_path}",
                                static_evidence=context[:500],
                                source_location=str(rel_path),
                                target_location=f"line {content[:match.start()].count(chr(10)) + 1}",
                                alternatives=[
                                    "Path is wrapped by capability-bound executor",
                                    "Path is only reachable from trusted computing base",
                                    "Path is test-only and not reachable in production",
                                    "Path is informational (read-only)",
                                ],
                                required_experiment=f"Attempt direct invocation of {match.group(0)} without authorization",
                            ))
            except Exception:
                pass

        return escapes


@dataclass(frozen=True)
class TCBComponent:
    component_id: str
    name: str
    privilege: str
    consequence_types: list[str]
    callers: list[str]
    trust_assumption: str
    authority_derivation: str
    verification_mechanism: str
    provenance: str
    attack_surface: str
    can_create_authority: bool
    can_bypass_capability: bool
    can_mutate_authority_state: bool

    def to_dict(self) -> dict:
        return {
            "component_id": self.component_id,
            "name": self.name,
            "privilege": self.privilege,
            "consequence_types": self.consequence_types,
            "callers": self.callers,
            "trust_assumption": self.trust_assumption,
            "authority_derivation": self.authority_derivation,
            "verification_mechanism": self.verification_mechanism,
            "provenance": self.provenance,
            "attack_surface": self.attack_surface,
            "can_create_authority": self.can_create_authority,
            "can_bypass_capability": self.can_bypass_capability,
            "can_mutate_authority_state": self.can_mutate_authority_state,
        }


class TCBInventory:
    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)
        self.src_root = self.repo_root / "src" / "sas"
        self.components: list[TCBComponent] = []

    def build_inventory(self) -> list[TCBComponent]:
        self.components = []
        tcb_patterns = {
            "capability_verifier": {
                "pattern": r"class\s+CapabilityVerifier",
                "privilege": "Verify execution capabilities",
                "consequence_types": ["verification"],
                "can_create_authority": False,
                "can_bypass_capability": False,
                "can_mutate_authority_state": False,
            },
            "runtime_authority_gate": {
                "pattern": r"class\s+RuntimeAuthorityGate",
                "privilege": "Gate all runtime authority decisions",
                "consequence_types": ["authority_management"],
                "can_create_authority": False,
                "can_bypass_capability": False,
                "can_mutate_authority_state": False,
            },
            "capability_bound_broker": {
                "pattern": r"class\s+CapabilityBoundBroker",
                "privilege": "Wrap broker adapter with capability enforcement",
                "consequence_types": ["trade", "external_api_call"],
                "can_create_authority": False,
                "can_bypass_capability": False,
                "can_mutate_authority_state": False,
            },
            "capability_bound_substrate": {
                "pattern": r"class\s+CapabilityBoundSubstrate",
                "privilege": "Wrap substrate execution with capability enforcement",
                "consequence_types": ["process_execution", "compute_execution"],
                "can_create_authority": False,
                "can_bypass_capability": False,
                "can_mutate_authority_state": False,
            },
            "capability_bound_auth": {
                "pattern": r"class\s+CapabilityBoundAuthBroker",
                "privilege": "Wrap credential access with capability enforcement",
                "consequence_types": ["credential_access"],
                "can_create_authority": False,
                "can_bypass_capability": False,
                "can_mutate_authority_state": False,
            },
            "consequence_executor": {
                "pattern": r"class\s+ConsequenceExecutor",
                "privilege": "Execute consequential effects through protocol",
                "consequence_types": ["external_consequential", "state_transforming"],
                "can_create_authority": False,
                "can_bypass_capability": False,
                "can_mutate_authority_state": False,
            },
            "broker_adapter": {
                "pattern": r"class\s+.*BrokerAdapter",
                "privilege": "Direct broker access (lower-level)",
                "consequence_types": ["trade", "external_api_call"],
                "can_create_authority": False,
                "can_bypass_capability": True,
                "can_mutate_authority_state": False,
            },
            "simulated_broker": {
                "pattern": r"class\s+SimulatedBroker",
                "privilege": "Simulated broker for testing",
                "consequence_types": ["trade"],
                "can_create_authority": False,
                "can_bypass_capability": True,
                "can_mutate_authority_state": False,
            },
        }

        for py_file in self.src_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                rel_path = py_file.relative_to(self.repo_root)

                for component_name, component_def in tcb_patterns.items():
                    if re.search(component_def["pattern"], content):
                        self.components.append(TCBComponent(
                            component_id=f"tcb_{len(self.components)+1:03d}",
                            name=component_name,
                            privilege=component_def["privilege"],
                            consequence_types=component_def["consequence_types"],
                            callers=self._find_callers(content, component_name),
                            trust_assumption=f"Component is trusted to enforce {component_def['privilege']}",
                            authority_derivation="Derived from formal protocol specification",
                            verification_mechanism="Static analysis + adversarial tests",
                            provenance=str(rel_path),
                            attack_surface=self._find_attack_surface(content),
                            can_create_authority=component_def["can_create_authority"],
                            can_bypass_capability=component_def["can_bypass_capability"],
                            can_mutate_authority_state=component_def["can_mutate_authority_state"],
                        ))
            except Exception:
                pass

        return self.components

    def _find_callers(self, content: str, class_name: str) -> list[str]:
        callers = []
        for match in re.finditer(r"from\s+(\S+)\s+import\s+.*" + re.escape(class_name), content):
            callers.append(match.group(1))
        return callers

    def _find_attack_surface(self, content: str) -> str:
        surfaces = []
        if "subprocess" in content:
            surfaces.append("process_execution")
        if "httpx" in content or "requests" in content:
            surfaces.append("network")
        if "open(" in content:
            surfaces.append("filesystem")
        if "os.environ" in content:
            surfaces.append("environment")
        return ", ".join(surfaces) if surfaces else "minimal"


class EscapeDiscriminationEngine:
    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)
        self.src_root = self.repo_root / "src" / "sas"
        self.static_analyzer = StaticEscapeAnalyzer(repo_root)
        self.tcb_inventory = TCBInventory(repo_root)
        self.classifications: list[EscapeClassificationResult] = []

    def run_discrimination(self) -> list[EscapeClassificationResult]:
        print("=" * 70)
        print("AUTHORITY ESCAPE DISCRIMINATION")
        print("=" * 70)

        print("\n[Phase 1] Finding potential escapes...")
        hypotheses = self.static_analyzer.find_potential_escapes()
        print(f"  Found {len(hypotheses)} potential escapes")

        print("\n[Phase 2] Building TCB inventory...")
        tcb_components = self.tcb_inventory.build_inventory()
        print(f"  Found {len(tcb_components)} TCB components")

        print("\n[Phase 3] Discriminating escapes...")
        for hypothesis in hypotheses:
            result = self._discover_escape(hypothesis, tcb_components)
            self.classifications.append(result)

        print("\n[Phase 4] Generating report...")
        self._print_summary()

        return self.classifications

    def _discover_escape(
        self,
        hypothesis: EscapeHypothesis,
        tcb_components: list[TCBComponent],
    ) -> EscapeClassificationResult:
        evidence = []
        classification = EscapeClassification.INCONCLUSIVE
        confidence = 0.0
        remediation = ""
        verification_result = ""

        tcb_component = self._find_tcb_component(hypothesis.target, tcb_components)

        if tcb_component:
            if tcb_component.can_bypass_capability:
                classification = EscapeClassification.REAL_ESCAPE
                confidence = 0.7
                evidence.append(EscapeEvidence(
                    evidence_id=f"ev_{hypothesis.hypothesis_id}_tcb",
                    hypothesis_id=hypothesis.hypothesis_id,
                    evidence_type="tcb_analysis",
                    description=f"TCB component '{tcb_component.name}' can bypass capability verification",
                    source=tcb_component.provenance,
                    result="POTENTIAL_ESCAPE",
                ))
                remediation = f"Wrap {tcb_component.name} with capability enforcement"
            else:
                classification = EscapeClassification.CONTROLLED_BY_AUTHORITY
                confidence = 0.8
                evidence.append(EscapeEvidence(
                    evidence_id=f"ev_{hypothesis.hypothesis_id}_tcb",
                    hypothesis_id=hypothesis.hypothesis_id,
                    evidence_type="tcb_analysis",
                    description=f"TCB component '{tcb_component.name}' cannot bypass capability verification",
                    source=tcb_component.provenance,
                    result="CONTROLLED",
                ))
        else:
            if self._is_reachable(hypothesis):
                if self._is_wrapped(hypothesis):
                    classification = EscapeClassification.CONTROLLED_BY_AUTHORITY
                    confidence = 0.75
                    evidence.append(EscapeEvidence(
                        evidence_id=f"ev_{hypothesis.hypothesis_id}_wrap",
                        hypothesis_id=hypothesis.hypothesis_id,
                        evidence_type="wrapping_analysis",
                        description="Path is wrapped by capability-bound executor",
                        source=hypothesis.source_location,
                        result="WRAPPED",
                    ))
                else:
                    classification = EscapeClassification.REAL_ESCAPE
                    confidence = 0.6
                    evidence.append(EscapeEvidence(
                        evidence_id=f"ev_{hypothesis.hypothesis_id}_reach",
                        hypothesis_id=hypothesis.hypothesis_id,
                        evidence_type="reachability_analysis",
                        description="Path is reachable without capability enforcement",
                        source=hypothesis.source_location,
                        result="REACHABLE",
                    ))
                    remediation = f"Add capability enforcement to {hypothesis.target}"
            else:
                classification = EscapeClassification.UNREACHABLE
                confidence = 0.7
                evidence.append(EscapeEvidence(
                    evidence_id=f"ev_{hypothesis.hypothesis_id}_reach",
                    hypothesis_id=hypothesis.hypothesis_id,
                    evidence_type="reachability_analysis",
                    description="Path is not reachable from any caller",
                    source=hypothesis.source_location,
                    result="UNREACHABLE",
                ))

        return EscapeClassificationResult(
            classification_id=f"cls_{hypothesis.hypothesis_id}",
            hypothesis=hypothesis,
            classification=classification,
            confidence=confidence,
            evidence=evidence,
            intervention=f"Static analysis of {hypothesis.target}",
            scope="SAS codebase",
            environment="all",
            temporal_boundary="static",
            remediation=remediation,
            verification_result=verification_result,
            provenance_id=f"prov_{hypothesis.hypothesis_id}",
        )

    def _find_tcb_component(
        self,
        target: str,
        tcb_components: list[TCBComponent],
    ) -> Optional[TCBComponent]:
        for component in tcb_components:
            if component.name in target or target in component.name:
                return component
            if component.provenance in target:
                return component
        return None

    def _is_reachable(self, hypothesis: EscapeHypothesis) -> bool:
        try:
            source_file = self.repo_root / hypothesis.source
            if source_file.exists():
                content = source_file.read_text()
                target_name = hypothesis.target.split(".")[-1] if "." in hypothesis.target else hypothesis.target
                if target_name in content:
                    return True
        except Exception:
            pass
        return False

    def _is_wrapped(self, hypothesis: EscapeHypothesis) -> bool:
        try:
            source_file = self.repo_root / hypothesis.source
            if source_file.exists():
                content = source_file.read_text()
                wrappers = [
                    "CapabilityBoundBroker",
                    "CapabilityBoundSubstrate",
                    "CapabilityBoundAuthBroker",
                    "CapabilityBoundTool",
                    "CapabilityBoundPluginExecutor",
                    "RuntimeAuthorityGate",
                    "ConsequenceExecutor",
                ]
                for wrapper in wrappers:
                    if wrapper in content:
                        return True
        except Exception:
            pass
        return False

    def _print_summary(self):
        print("\n" + "=" * 70)
        print("ESCAPE DISCRIMINATION SUMMARY")
        print("=" * 70)

        classification_counts = {}
        for result in self.classifications:
            cls = result.classification.value
            classification_counts[cls] = classification_counts.get(cls, 0) + 1

        print(f"\nTotal potential escapes: {len(self.classifications)}")
        print("\nClassifications:")
        for cls, count in sorted(classification_counts.items()):
            print(f"  {cls}: {count}")

        print("\nDetailed Results:")
        for result in self.classifications:
            print(f"\n  [{result.classification.value.upper()}] {result.hypothesis.claim[:80]}")
            print(f"    Confidence: {result.confidence:.2f}")
            print(f"    Severity: {result.hypothesis.severity.value}")
            print(f"    Consequence: {result.hypothesis.consequence_type.value}")
            if result.remediation:
                print(f"    Remediation: {result.remediation}")

    def generate_report(self) -> dict:
        classification_counts = {}
        for r in self.classifications:
            cls = r.classification.value
            classification_counts[cls] = classification_counts.get(cls, 0) + 1

        severity_counts = {}
        for r in self.classifications:
            sev = r.hypothesis.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "repository": str(self.repo_root),
                "total_classifications": len(self.classifications),
            },
            "classifications": [c.to_dict() for c in self.classifications],
            "tcb_inventory": [c.to_dict() for c in self.tcb_inventory.components],
            "summary": {
                "classification_counts": classification_counts,
                "severity_counts": severity_counts,
                "remediation_required": sum(1 for r in self.classifications if r.remediation),
            },
        }


def run_escape_discrimination(repo_root: str | Path) -> dict:
    engine = EscapeDiscriminationEngine(repo_root)
    engine.run_discrimination()
    return engine.generate_report()


if __name__ == "__main__":
    import json
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    report = run_escape_discrimination(repo)
    print(json.dumps(report, indent=2))
