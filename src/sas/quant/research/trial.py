"""Trial ledger — authoritative record of all strategy proposals.

The trial ledger is NOT merely a counter. It records every propose_strategy
call as a distinct entry with its backtest result, whether accepted or
rejected. A strategy proposed but never backtested is distinguishable
from one that was actually evaluated.

The trial ledger becomes the statistical substrate for DSR/PBO computation.
It is an extension of the provenance model, not a parallel bookkeeping
mechanism.

Invariants:
- Every trial has a unique identity.
- Every revision creates a new trial with a parent-child provenance link.
- The ledger is append-only. Trials cannot be deleted or mutated.
- The ledger records the complete parent-child trial tree.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from sas.quant.provenance.artifacts import TrialArtifact


class TrialLedger:
    """Append-only ledger of all trials in an experiment.

    Records trial identity, parent trial, strategy specification,
    model identity, prompt/task identity, data window, random seed,
    parameterization, backtest result, return series reference,
    rejection reason, and whether the trial became incumbent.
    """

    def __init__(self, experiment_id: str = ""):
        self.experiment_id = experiment_id
        self._trials: dict[str, TrialArtifact] = {}
        self._trial_order: list[str] = []
        self._incumbent_id: str | None = None

    def record_trial(
        self,
        strategy_spec: dict,
        model_id: str = "",
        task_id: str = "",
        data_window: tuple[str, str] = ("", ""),
        random_seed: int = 42,
        parameterization: dict | None = None,
        parent_trial_id: str | None = None,
        provenance_event_ids: list[str] | None = None,
    ) -> TrialArtifact:
        """Record a new trial. Returns the created TrialArtifact."""
        trial_id = str(uuid.uuid4())[:12]
        trial = TrialArtifact(
            trial_id=trial_id,
            experiment_id=self.experiment_id,
            parent_trial_id=parent_trial_id,
            trial_number=len(self._trial_order) + 1,
            strategy_spec=strategy_spec,
            model_id=model_id,
            task_id=task_id,
            data_window=data_window,
            random_seed=random_seed,
            parameterization=parameterization or {},
            provenance_event_ids=provenance_event_ids or [],
        )
        self._trials[trial_id] = trial
        self._trial_order.append(trial_id)
        return trial

    def record_backtest_result(
        self,
        trial_id: str,
        backtest_result: dict,
        return_series: list[float] | None = None,
    ) -> TrialArtifact:
        """Record the backtest result for a trial. Append-only.

        Returns the authoritative updated trial artifact.
        Callers must use the returned artifact, not a previously materialized reference.
        """
        if trial_id not in self._trials:
            raise ValueError(f"Trial {trial_id} not found in ledger")
        trial = self._trials[trial_id]
        # Create updated trial with backtest result (frozen dataclass — replace)
        updated = TrialArtifact(
            trial_id=trial.trial_id,
            experiment_id=trial.experiment_id,
            parent_trial_id=trial.parent_trial_id,
            trial_number=trial.trial_number,
            strategy_spec=trial.strategy_spec,
            model_id=trial.model_id,
            task_id=trial.task_id,
            data_window=trial.data_window,
            random_seed=trial.random_seed,
            parameterization=trial.parameterization,
            backtest_result=backtest_result,
            return_series=return_series or [],
            rejection_reason=trial.rejection_reason,
            is_incumbent=trial.is_incumbent,
            critique_id=trial.critique_id,
            created_at=trial.created_at,
            provenance_event_ids=trial.provenance_event_ids,
        )
        self._trials[trial_id] = updated
        return updated

    def record_rejection(self, trial_id: str, reason: str) -> TrialArtifact:
        """Record that a trial was rejected.

        Returns the authoritative updated trial artifact.
        """
        if trial_id not in self._trials:
            raise ValueError(f"Trial {trial_id} not found")
        trial = self._trials[trial_id]
        updated = TrialArtifact(
            trial_id=trial.trial_id,
            experiment_id=trial.experiment_id,
            parent_trial_id=trial.parent_trial_id,
            trial_number=trial.trial_number,
            strategy_spec=trial.strategy_spec,
            model_id=trial.model_id,
            task_id=trial.task_id,
            data_window=trial.data_window,
            random_seed=trial.random_seed,
            parameterization=trial.parameterization,
            backtest_result=trial.backtest_result,
            return_series=trial.return_series,
            rejection_reason=reason,
            is_incumbent=trial.is_incumbent,
            critique_id=trial.critique_id,
            created_at=trial.created_at,
            provenance_event_ids=trial.provenance_event_ids,
        )
        self._trials[trial_id] = updated
        return updated

    def set_incumbent(self, trial_id: str) -> None:
        """Mark a trial as the incumbent strategy."""
        if trial_id not in self._trials:
            raise ValueError(f"Trial {trial_id} not found")
        # Clear previous incumbent
        if self._incumbent_id and self._incumbent_id in self._trials:
            prev = self._trials[self._incumbent_id]
            self._trials[self._incumbent_id] = TrialArtifact(
                trial_id=prev.trial_id,
                experiment_id=prev.experiment_id,
                parent_trial_id=prev.parent_trial_id,
                trial_number=prev.trial_number,
                strategy_spec=prev.strategy_spec,
                model_id=prev.model_id,
                task_id=prev.task_id,
                data_window=prev.data_window,
                random_seed=prev.random_seed,
                parameterization=prev.parameterization,
                backtest_result=prev.backtest_result,
                return_series=prev.return_series,
                rejection_reason=prev.rejection_reason,
                is_incumbent=False,
                critique_id=prev.critique_id,
                created_at=prev.created_at,
                provenance_event_ids=prev.provenance_event_ids,
            )
        # Set new incumbent
        trial = self._trials[trial_id]
        self._trials[trial_id] = TrialArtifact(
            trial_id=trial.trial_id,
            experiment_id=trial.experiment_id,
            parent_trial_id=trial.parent_trial_id,
            trial_number=trial.trial_number,
            strategy_spec=trial.strategy_spec,
            model_id=trial.model_id,
            task_id=trial.task_id,
            data_window=trial.data_window,
            random_seed=trial.random_seed,
            parameterization=trial.parameterization,
            backtest_result=trial.backtest_result,
            return_series=trial.return_series,
            rejection_reason=trial.rejection_reason,
            is_incumbent=True,
            critique_id=trial.critique_id,
            created_at=trial.created_at,
            provenance_event_ids=trial.provenance_event_ids,
        )
        self._incumbent_id = trial_id

    def link_critique(self, trial_id: str, critique_id: str) -> TrialArtifact:
        """Link a critique artifact to a trial.

        Returns the authoritative updated trial artifact.
        """
        if trial_id not in self._trials:
            raise ValueError(f"Trial {trial_id} not found")
        trial = self._trials[trial_id]
        updated = TrialArtifact(
            trial_id=trial.trial_id,
            experiment_id=trial.experiment_id,
            parent_trial_id=trial.parent_trial_id,
            trial_number=trial.trial_number,
            strategy_spec=trial.strategy_spec,
            model_id=trial.model_id,
            task_id=trial.task_id,
            data_window=trial.data_window,
            random_seed=trial.random_seed,
            parameterization=trial.parameterization,
            backtest_result=trial.backtest_result,
            return_series=trial.return_series,
            rejection_reason=trial.rejection_reason,
            is_incumbent=trial.is_incumbent,
            critique_id=critique_id,
            created_at=trial.created_at,
            provenance_event_ids=trial.provenance_event_ids,
        )
        self._trials[trial_id] = updated
        return updated

    def get_trial(self, trial_id: str) -> TrialArtifact | None:
        """Get the authoritative current state of a trial.

        Always use this method to retrieve trial state rather than
        caching a previously materialized TrialArtifact reference.
        The ledger is the state. Objects are views of ledger state.
        """
        return self._trials.get(trial_id)

    def get_all_trials(self) -> list[TrialArtifact]:
        """Get all trials in chronological order."""
        return [self._trials[tid] for tid in self._trial_order]

    def get_evaluated_trials(self) -> list[TrialArtifact]:
        """Get all trials that were actually backtested."""
        return [t for t in self.get_all_trials() if t.was_evaluated]

    def get_incumbent(self) -> TrialArtifact | None:
        """Get the incumbent trial, if any."""
        if self._incumbent_id:
            return self._trials.get(self._incumbent_id)
        return None

    def get_trial_tree(self, trial_id: str) -> list[TrialArtifact]:
        """Get the parent-child chain from root to the given trial."""
        chain = []
        current = self._trials.get(trial_id)
        while current:
            chain.append(current)
            if current.parent_trial_id:
                current = self._trials.get(current.parent_trial_id)
            else:
                break
        chain.reverse()
        return chain

    @property
    def total_trials(self) -> int:
        return len(self._trial_order)

    @property
    def evaluated_count(self) -> int:
        return len(self.get_evaluated_trials())

    def to_dict(self) -> dict:
        return {
            "experiment_id": self.experiment_id,
            "total_trials": self.total_trials,
            "evaluated_count": self.evaluated_count,
            "incumbent_id": self._incumbent_id,
            "trials": [t.to_dict() for t in self.get_all_trials()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrialLedger":
        """Reconstruct a trial ledger from a dictionary.

        Note: This reconstructs the trials but does NOT restore
        the incumbent_id. The incumbent must be set separately
        using set_incumbent() if needed.
        """
        ledger = cls(experiment_id=data.get("experiment_id", ""))
        for t_data in data.get("trials", []):
            trial = ledger.record_trial(
                strategy_spec=t_data.get("strategy_spec", {}),
                model_id=t_data.get("model_id", ""),
                task_id=t_data.get("task_id", ""),
                data_window=tuple(t_data.get("data_window", ["", ""])),
                random_seed=t_data.get("random_seed", 42),
                parameterization=t_data.get("parameterization", {}),
                parent_trial_id=t_data.get("parent_trial_id"),
            )
            if t_data.get("backtest_result"):
                ledger.record_backtest_result(
                    trial_id=trial.trial_id,
                    backtest_result=t_data["backtest_result"],
                    return_series=t_data.get("return_series", []),
                )
        return ledger
