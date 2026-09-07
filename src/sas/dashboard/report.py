"""Sovereignty dashboard CLI and report generator."""

from __future__ import annotations

import json
from pathlib import Path

from sas.core.config import parse_sas_yaml
from sas.core.scoring import (
    Ownership,
    SovereigntyReport,
    generate_report,
)


def _load_previous_score(cache_dir: Path) -> float | None:
    """Load the previous sovereignty score from cache."""
    score_file = cache_dir / "sovereignty_score.json"
    if score_file.exists():
        try:
            data = json.loads(score_file.read_text())
            return data.get("score")
        except (json.JSONDecodeError, KeyError):
            return None
    return None


def _save_current_score(cache_dir: Path, score: float, report: SovereigntyReport) -> None:
    """Save the current sovereignty score to cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    score_file = cache_dir / "sovereignty_score.json"
    data = {
        "score": score,
        "timestamp": report.timestamp.isoformat(),
        "owned": report.owned_count,
        "total": report.total_count,
    }
    score_file.write_text(json.dumps(data, indent=2))


def _format_layer_line(layer, verbose: bool = False) -> str:
    """Format a single layer for the report."""
    icon = "✅" if layer.scored_as == Ownership.OWNED else "🔴"
    if layer.unavoidable_rental:
        icon = "⚪"

    line = f"{icon} **{layer.name}** — {layer.scored_as.value}"

    if verbose:
        line += f"\n   - {layer.reasoning}"

    return line


def generate_markdown_report(report: SovereigntyReport, verbose: bool = False) -> str:
    """Generate a markdown-formatted sovereignty report."""
    lines = [
        "# Sovereignty Report",
        "",
        f"**Generated:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Score:** {report.owned_count}/{report.total_count} ({report.score:.0%})",
        f"**Verdict:** {report.verdict}",
        "",
    ]

    if report.previous_score is not None:
        drift_str = f"{report.drift:+.0%}" if report.drift is not None else "N/A"
        lines.append(f"**Previous score:** {report.previous_score:.0%} (drift: {drift_str})")
        lines.append("")

    lines.append("## Layers")
    lines.append("")

    for layer in report.layers:
        lines.append(_format_layer_line(layer, verbose=verbose))
        lines.append("")

    lines.append("## Methodology")
    lines.append("")
    lines.append("- ✅ = Owned (compile-time, local, inspectable)")
    lines.append("- 🔴 = Rented (runtime, hosted, re-derived)")
    lines.append("- ⚪ = Unavoidably rented (excluded from score)")
    lines.append("")
    lines.append("See docs/SOVEREIGNTY.md for the full scoring methodology.")
    lines.append("")

    return "\n".join(lines)


def run_dashboard(config_path: Path, cache_dir: Path, verbose: bool = False) -> str:
    """Run the sovereignty dashboard and return the markdown report."""
    config = parse_sas_yaml(config_path)
    previous_score = _load_previous_score(cache_dir)
    report = generate_report(config, previous_score=previous_score)

    # Save current score for next run
    _save_current_score(cache_dir, report.score, report)

    return generate_markdown_report(report, verbose=verbose)


def run_dashboard_json(config_path: Path, cache_dir: Path) -> dict:
    """Run the sovereignty dashboard and return JSON-serializable results."""
    config = parse_sas_yaml(config_path)
    previous_score = _load_previous_score(cache_dir)
    report = generate_report(config, previous_score=previous_score)

    _save_current_score(cache_dir, report.score, report)

    return {
        "timestamp": report.timestamp.isoformat(),
        "score": report.score,
        "owned": report.owned_count,
        "total": report.total_count,
        "verdict": report.verdict,
        "previous_score": report.previous_score,
        "drift": report.drift,
        "layers": [
            {
                "id": layer.layer_id.value,
                "name": layer.name,
                "ownership": layer.ownership.value,
                "scored_as": layer.scored_as.value,
                "unavoidable_rental": layer.unavoidable_rental,
                "reasoning": layer.reasoning,
            }
            for layer in report.layers
        ],
    }
