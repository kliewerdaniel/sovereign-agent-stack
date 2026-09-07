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
