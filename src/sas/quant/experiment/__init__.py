"""Governed research experiment infrastructure.

This package provides tools for running controlled experiments
with governed research agents, including:

- metrics: Compute experimental metrics from governed experiments
- runner: Execute matrices of experimental configurations
- analysis: Compare results across experimental conditions
- synthetic_worlds: Generate worlds with known data generating processes
- validation: Verify experiments are statistically and causally sound
- governed_comparison: Compare governed vs ungoverned research
- calibration: Measure false acceptance rate and true acceptance rate
- gate_ablation: Systematic gate ablation experiments
- gate_analysis: Gate-level operating characteristic decomposition
- signal_calibration: Measure true acceptance rate across signal strengths
"""
from sas.quant.experiment.analysis import (
    ComparativeAnalysis,
    ComparativeFinding,
    analyze_matrix,
    compare_reflection_settings,
    compare_trial_budgets,
    compare_universes,
    generate_report,
)
from sas.quant.experiment.calibration import (
    CalibrationBatch,
    CalibrationMatrix,
    CalibrationResult,
    generate_calibration_report,
    run_null_calibration,
)
from sas.quant.experiment.gate_ablation import (
    AblationBatch,
    AblationConfiguration,
    AblationMatrix,
    AblationResult,
    evaluate_with_configuration,
    generate_ablation_report,
    get_standard_configurations,
    run_ablation_matrix,
)
from sas.quant.experiment.gate_analysis import (
    GateAnalysisResult,
    GateOperatingCharacteristic,
    GateRecord,
    analyze_gate_operating_characteristics,
    generate_gate_analysis_report,
)
from sas.quant.experiment.governed_comparison import (
    ComparisonResult,
    run_comparison,
    run_governed_experiment,
    run_ungoverned_experiment,
)
from sas.quant.experiment.signal_calibration import (
    SignalCalibrationBatch,
    SignalCalibrationMatrix,
    SignalCalibrationResult,
    generate_signal_calibration_report,
    run_signal_calibration,
)
from sas.quant.experiment.metrics import (
    ExperimentMetrics,
    IncumbentTurnover,
    NominalVsDefensible,
    ReflectionImpact,
    StrategyDiversity,
    TrialEfficiency,
    compute_experiment_metrics,
    compute_incumbent_turnover,
    compute_nominal_vs_defensible,
    compute_reflection_impact,
    compute_strategy_diversity,
    compute_trial_efficiency,
)
from sas.quant.experiment.runner import (
    ExperimentMatrix,
    ExperimentResult,
    ExperimentRunner,
    ExperimentSpec,
    generate_experiment_matrix,
    run_experimental_suite,
)
from sas.quant.experiment.synthetic_worlds import (
    DataGeneratingProcess,
    SyntheticWorld,
    generate_null_world,
    generate_signal_world,
    run_confounder_matrix,
)
from sas.quant.experiment.hypothesis import (
    HypothesisArtifact,
    create_null_hypothesis,
    create_signal_hypothesis,
)
from sas.quant.experiment.mechanism_attribution import (
    MechanismAttributionResult,
    StrategyResult,
    generate_mechanism_attribution_report,
    run_mechanism_attribution_matrix,
    run_momentum_strategy,
    run_oracle_strategy,
    run_random_strategy,
    run_buy_and_hold,
    run_agent_strategy,
)
from sas.quant.experiment.mechanism_investigation import (
    MechanismInvestigationResult,
    run_feature_ablation,
    run_permutation_test,
    run_competing_mechanism_test,
    run_temporal_perturbation,
    run_all_investigations,
)
from sas.quant.experiment.mechanism_challenge import (
    ChallengeResult,
    build_challenge_worlds,
    run_challenge,
    run_challenge_suite,
    generate_challenge_report,
)
from sas.quant.experiment.evidence_sufficiency import (
    ConditionResult,
    ExperimentalCondition,
    MonotonicityResult,
    analyze_monotonicity,
    compute_aggregate_metrics,
    compute_conditional_metrics,
    generate_evidence_sufficiency_report,
    run_evidence_sufficiency_experiment,
    run_single_condition,
)
from sas.quant.experiment.proposition_evidence import (
    DualPathResult,
    PropositionEvidence,
    PropositionEvaluation,
    analyze_dual_path_results,
    evaluate_proposition,
    generate_proposition_evidence_report,
    run_dual_path_comparison,
    run_proposition_evidence_experiment,
)
from sas.quant.experiment.intervention_discovery import (
    AgentHypothesis,
    HypothesisType,
    InterventionDiscoveryResult,
    DiscoveryExperimentResult,
    generate_candidate_hypotheses,
    select_intervention_target,
    run_intervention_discovery_test,
    run_intervention_discovery_experiment,
    generate_discovery_experiment_report,
)
from sas.quant.experiment.intervention_semantics import (
    FeatureIntervention,
    IdentifiabilityResult,
    MechanismIntervention,
    PairedWorld,
    analyze_identifiability_results,
    apply_mechanism_intervention,
    generate_identifiability_report,
    generate_paired_worlds,
    run_identifiability_experiment,
    run_identifiability_test,
    run_mechanism_intervention_test,
)
from sas.quant.experiment.typed_propositions import (
    EvidenceBundle,
    ImpossibilityResult,
    InterventionType,
    PropositionType,
    TypedEpistemicResult,
    TypedProposition,
    evaluate_typed_proposition,
    generate_authority_matrix_report,
    run_all_impossibility_proofs,
)
from sas.quant.experiment.experimental_design import (
    DesignAuthorityResult,
    DesignAuthorityExperiment,
    DesignSufficiencyResult,
    ExperimentalDesignArtifact,
    FailureType,
    FailureClassification,
    analyze_confounders,
    identify_competing_mechanisms,
    compute_discriminative_power,
    evaluate_design_sufficiency,
    run_design_authority_experiment,
    generate_design_authority_report,
)
from sas.quant.experiment.epistemic_adversarial import (
    AttackResult,
    AttackType,
    BoundaryType,
    run_adversarial_suite,
    generate_adversarial_report,
)
from sas.quant.experiment.substrate_validation import (
    RealizedDistribution,
    characterize_substrate,
    generate_substrate_characterization_report,
)
from sas.quant.experiment.validation import (
    ValidationCheck,
    ValidationReport,
    validate_decision_derivation,
    validate_experiment,
    validate_holdout_integrity,
    validate_matrix,
    validate_provenance_completeness,
    validate_statistical_inputs,
    validate_temporal_isolation,
    validate_trial_population,
)

__all__ = [
    # Metrics
    "ExperimentMetrics",
    "TrialEfficiency",
    "IncumbentTurnover",
    "StrategyDiversity",
    "NominalVsDefensible",
    "ReflectionImpact",
    "compute_experiment_metrics",
    "compute_trial_efficiency",
    "compute_incumbent_turnover",
    "compute_strategy_diversity",
    "compute_nominal_vs_defensible",
    "compute_reflection_impact",
    # Runner
    "ExperimentSpec",
    "ExperimentResult",
    "ExperimentMatrix",
    "ExperimentRunner",
    "generate_experiment_matrix",
    "run_experimental_suite",
    # Analysis
    "ComparativeAnalysis",
    "ComparativeFinding",
    "analyze_matrix",
    "compare_trial_budgets",
    "compare_reflection_settings",
    "compare_universes",
    "generate_report",
    # Synthetic Worlds
    "DataGeneratingProcess",
    "SyntheticWorld",
    "generate_null_world",
    "generate_signal_world",
    "run_confounder_matrix",
    # Hypothesis
    "HypothesisArtifact",
    "create_null_hypothesis",
    "create_signal_hypothesis",
    # Mechanism Attribution
    "MechanismAttributionResult",
    "StrategyResult",
    "generate_mechanism_attribution_report",
    "run_mechanism_attribution_matrix",
    "run_momentum_strategy",
    "run_oracle_strategy",
    "run_random_strategy",
    "run_buy_and_hold",
    "run_agent_strategy",
    # Mechanism Investigation
    "MechanismInvestigationResult",
    "run_feature_ablation",
    "run_permutation_test",
    "run_competing_mechanism_test",
    "run_temporal_perturbation",
    "run_all_investigations",
    # Mechanism Challenge
    "ChallengeResult",
    "build_challenge_worlds",
    "run_challenge",
    "run_challenge_suite",
    "generate_challenge_report",
    # Evidence Sufficiency
    "ConditionResult",
    "ExperimentalCondition",
    "MonotonicityResult",
    "analyze_monotonicity",
    "compute_aggregate_metrics",
    "compute_conditional_metrics",
    "generate_evidence_sufficiency_report",
    "run_evidence_sufficiency_experiment",
    "run_single_condition",
    # Proposition Evidence
    "DualPathResult",
    "PropositionEvidence",
    "PropositionEvaluation",
    "analyze_dual_path_results",
    "evaluate_proposition",
    "generate_proposition_evidence_report",
    "run_dual_path_comparison",
    "run_proposition_evidence_experiment",
    # Intervention Semantics
    "FeatureIntervention",
    "MechanismIntervention",
    "PairedWorld",
    "IdentifiabilityResult",
    "apply_mechanism_intervention",
    "run_mechanism_intervention_test",
    "generate_paired_worlds",
    "run_identifiability_test",
    "run_identifiability_experiment",
    "analyze_identifiability_results",
    "generate_identifiability_report",
    # Intervention Discovery
    "AgentHypothesis",
    "HypothesisType",
    "InterventionDiscoveryResult",
    "DiscoveryExperimentResult",
    "generate_candidate_hypotheses",
    "select_intervention_target",
    "run_intervention_discovery_test",
    "run_intervention_discovery_experiment",
    "generate_discovery_experiment_report",
    # Typed Propositions
    "EvidenceBundle",
    "ImpossibilityResult",
    "InterventionType",
    "PropositionType",
    "TypedEpistemicResult",
    "TypedProposition",
    "evaluate_typed_proposition",
    "generate_authority_matrix_report",
    "run_all_impossibility_proofs",
    # Experimental Design
    "DesignAuthorityResult",
    "DesignAuthorityExperiment",
    "DesignSufficiencyResult",
    "ExperimentalDesignArtifact",
    "FailureType",
    "FailureClassification",
    "analyze_confounders",
    "identify_competing_mechanisms",
    "compute_discriminative_power",
    "evaluate_design_sufficiency",
    "run_design_authority_experiment",
    "generate_design_authority_report",
    # Epistemic Adversarial
    "AttackResult",
    "AttackType",
    "BoundaryType",
    "run_adversarial_suite",
    "generate_adversarial_report",
    # Substrate Validation
    "RealizedDistribution",
    "characterize_substrate",
    "generate_substrate_characterization_report",
    # Validation
    "ValidationCheck",
    "ValidationReport",
    "validate_decision_derivation",
    "validate_experiment",
    "validate_holdout_integrity",
    "validate_matrix",
    "validate_provenance_completeness",
    "validate_statistical_inputs",
    "validate_temporal_isolation",
    "validate_trial_population",
]
