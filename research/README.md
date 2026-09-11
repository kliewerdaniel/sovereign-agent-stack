# Research

This directory contains exploratory work on authority/epistemic graph theory that is **independent of the shipping product**.

## What's here

- `architecture/` — Design documents for authority graphs, epistemic governance, temporal frontiers, and related formalisms.
- `experiments/` — Self-contained experimental modules exploring authority path reconstruction, divergence detection, independent reconstruction reconciliation, and related concepts.
- `examples/sovereign_agent/` — Investigative specimens (authority genesis, escape discrimination, frontier semantics, etc.).
- `examples/self_audit/` — Recursive self-audit tools and runtime topology experiments.
- `examples/counterexamples/` — Counterexample corpus for dependency/authority graph boundaries.
- `examples/payment_dependency_auditor/` — Payment infrastructure dependency analysis.

## Relationship to the product

This work informed the architecture of the Sovereign Agent Stack but is **not part of the demo path** and is not required for the shipping product to function. It is preserved here for future reference and may be returned to when the core product is stable.

The shipping product lives in `src/sas/` and is demonstrated via `python -m sas dashboard serve`.
