"""Tests for sovereignty dashboard."""

import json
from pathlib import Path

import pytest
import yaml

from sas.core.config import generate_template
from sas.dashboard.report import (
    run_dashboard,
    run_dashboard_json,
)


class TestRunDashboard:
    """Tests for the dashboard runner."""

    def test_dashboard_with_default_config(self, tmp_path: Path) -> None:
        """Dashboard runs with a default-generated config."""
        config_path = tmp_path / "sas.yaml"
        generate_template(config_path)
        cache_dir = tmp_path / ".sas"

        report_md = run_dashboard(config_path, cache_dir, verbose=True)

        assert "Sovereignty Report" in report_md
        assert "Score:" in report_md
        assert "Verdict:" in report_md

    def test_dashboard_json_output(self, tmp_path: Path) -> None:
        """Dashboard produces valid JSON."""
        config_path = tmp_path / "sas.yaml"
        generate_template(config_path)
        cache_dir = tmp_path / ".sas"

        result = run_dashboard_json(config_path, cache_dir)

        assert "score" in result
        assert "layers" in result
        assert "verdict" in result
        assert isinstance(result["score"], float)
        assert len(result["layers"]) == 8

    def test_dashboard_drift_detection(self, tmp_path: Path) -> None:
        """Dashboard detects score drift between runs."""
        config_path = tmp_path / "sas.yaml"
        cache_dir = tmp_path / ".sas"

        # First run with sovereign config
        config_data = {
            "compute": {"substrate": "local_docker"},
            "memory": {
                "short_term": {"provider": "local_rag"},
                "long_term": {"provider": "compile_time_graph"},
            },
            "auth": {"broker": "local_mcp_gateway"},
        }
        config_path.write_text(yaml.safe_dump(config_data))
        run_dashboard(config_path, cache_dir)

        # Second run with rented config
        config_data["compute"]["substrate"] = "orgo_cloud"
        config_data["memory"]["short_term"]["provider"] = "honcho_cloud"
        config_data["auth"]["broker"] = "composio"
        config_path.write_text(yaml.safe_dump(config_data))
        result = run_dashboard_json(config_path, cache_dir)

        assert result["previous_score"] is not None
        assert result["drift"] is not None
        assert result["drift"] < 0  # Score should have decreased

    def test_dashboard_creates_cache(self, tmp_path: Path) -> None:
        """Dashboard creates cache directory and score file."""
        config_path = tmp_path / "sas.yaml"
        generate_template(config_path)
        cache_dir = tmp_path / ".sas"

        run_dashboard(config_path, cache_dir)

        score_file = cache_dir / "sovereignty_score.json"
        assert score_file.exists()

        data = json.loads(score_file.read_text())
        assert "score" in data
        assert "timestamp" in data
