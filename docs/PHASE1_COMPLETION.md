# Phase 1 Completion — Layer Registry + Sovereignty Dashboard Wiring

**Goal:** Complete the remaining Phase 1 deliverables — layer registry, layer protocol implementations for all 8 layers, `python -m sas dashboard` end-to-end, drift detection, and unit tests — so the sovereignty score is computable, visible, and changes when `sas.yaml` is modified.

**Exit criteria (from ROADMAP.md):**
- [x] `sas.yaml` parser and validator — `src/sas/core/config.py` (done, 5 tests)
- [x] Layer registry (each layer declares its ownership model) — **IN PROGRESS**
- [x] Sovereignty scorer (owned / total, with manual override) — `src/sas/core/scoring.py` (done, 9 tests)
- [x] Sovereignty dashboard CLI (`python -m sas dashboard`) — `src/sas/__main__.py` + `src/sas/dashboard/report.py` (done, 4 tests)
- [x] Sovereignty report generator (markdown, versionable) — done
- [x] Drift detection (compare current score to previous, flag changes) — done
- [ ] Unit tests for scorer, registry, parser — scorer+parser done; registry tests needed
- [ ] Wiring layer stubs into registry so `layers` listing is truthful

**What exists vs what's missing:**

| Deliverable | Status | Location |
|---|---|---|
| `sas.yaml` parser | ✅ done | `src/sas/core/config.py` |
| Sovereignty scorer | ✅ done | `src/sas/core/scoring.py` |
| Dashboard CLI (`python -m sas dashboard`) | ✅ done | `src/sas/__main__.py`, `src/sas/dashboard/report.py` |
| Markdown + JSON report generators | ✅ done | `src/sas/dashboard/report.py` |
| Drift detection (score cache + diff) | ✅ done | `src/sas/dashboard/report.py` |
| Layer registry | ❌ missing | **build now** — `src/sas/layers/registry.py` + `src/sas/layers/__init__.py` |
| Layer protocol implementations | ⚠️ protocol stubs only | `src/sas/layers/*.py` — 7 of 8 are pure Protocol stubs; substrate.py has LocalDockerSubstrate |
| Layer registry unit tests | ❌ missing | **build now** — `tests/unit/test_layer_registry.py` |

**Scope for this session:**
1. Populate `src/sas/layers/__init__.py` with a unified re-export of all layer protocols + dataclasses.
2. Build `src/sas/layers/registry.py` — `LayerRegistry` class that:
   - Knows all 8 `LayerID` values and their Protocol classes
   - Accepts a `SASConfig` and returns a scored `list[LayerScore]` (reuses `score_config` from `sas.core.scoring`)
   - Exposes `list_layers()`, `get_layer(id)`, `is_owned(id)`, `sovereignty_score()` — thin wrappers that make the layer layer queryable without reaching into `sas.core`
3. Wire `src/sas/core/scoring.py:score_config` to use the registry's layer list so the two stay in sync (single source of truth for layer definitions).
4. Add `tests/unit/test_layer_registry.py` — tests for registry construction, layer lookup, ownership queries, score computation, sync with `score_config`.
5. Run full suite: confirm no regressions, confirm registry tests pass.
6. Update `docs/PHASE1_COMPLETION.md` if it exists, or note completion in this plan.

**Out of scope (defer to later phases):**
- Real implementations of harness/identity/memory/auth/payments protocols (those are Phases 2-7)
- Compile-time knowledge graph materialization (Phase 2)
- Local MCP gateway server (Phase 3)
- Actual Docker substrate management beyond the existing LocalDockerSubstrate stub

**Verification:**
```
python -m pytest tests/unit/test_layer_registry.py tests/unit/test_scoring.py tests/unit/test_config.py tests/unit/test_dashboard.py tests/integration/test_quant_pipeline.py -v --tb=short
```
Expected: all registry + existing tests green, no regressions.

**Files to create/modify:**
- `src/sas/layers/__init__.py` — rewrite (currently empty)
- `src/sas/layers/registry.py` — NEW
- `tests/unit/test_layer_registry.py` — NEW
- `src/sas/core/scoring.py` — patch: import registry layer list, ensure single source of truth
- `docs/PHASE1_COMPLETION.md` — update or create (optional, documentation)
