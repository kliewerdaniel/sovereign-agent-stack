"""Compile-time knowledge for quant policies.

Markdown policy files → structured knowledge graph.
Policies are inspectable, versionable, attributable.
"""
from __future__ import annotations

import os
from pathlib import Path

from sas.layers.knowledge import CompileTimeKnowledge, Node

# Policy file templates
POLICY_TEMPLATES = {
    "investment-policy.md": """---
title: Investment Policy
version: 1.0.0
updated: 2026-09-05
---

# Investment Policy

## Universe
- Approved tickers: {universe}
- Minimum liquidity: ${min_liquidity}

## Constraints
- Maximum position weight: {max_position_weight}
- Maximum gross exposure: {max_gross_exposure}
- Maximum leverage: {max_leverage}

## Mandates
- {mandate}
""",
    "risk-policy.md": """---
title: Risk Policy
version: 1.0.0
updated: 2026-09-05
---

# Risk Policy

## Limits
- Maximum drawdown: {max_drawdown}
- Maximum daily loss: {max_daily_loss}
- Maximum position concentration: {max_concentration}
- Minimum positions: {min_positions}

## Stop-Loss
- Daily stop: {daily_stop}
- Trailing stop: {trailing_stop}
""",
    "research-policy.md": """---
title: Research Policy
version: 1.0.0
updated: 2026-09-05
---

# Research Policy

## Methodology
- Backtest periods: train={train}, validate={validate}, test={test}
- Overfitting detection: enabled
- Survivorship bias: {survivorship}

## Data Quality
- Minimum observations: {min_obs}
- Null handling: {null_handling}
""",
}


class QuantKnowledgeCompiler:
    """Compile quant policy markdown into structured knowledge."""

    def __init__(self, policy_dir: str | Path | None = None):
        self.policy_dir = Path(policy_dir) if policy_dir else Path()
        self.compiler = CompileTimeKnowledge()
        self._policies: dict[str, dict] = {}

    def compile_policies(self, policy_dir: Path) -> dict[str, Node]:
        """Compile all policy markdown files into knowledge nodes."""
        nodes = {}
        if not policy_dir.exists():
            return nodes

        for md_file in sorted(policy_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            result = self.compiler.parser.parse(content, str(md_file))
            for node in result.nodes:
                nodes[node.label] = node

        self._policies = nodes
        return nodes

    def get_policy(self, name: str) -> dict | None:
        """Get a policy by name."""
        node = self._policies.get(name)
        if node:
            return node.properties
        return None

    def list_policies(self) -> list[str]:
        """List all compiled policies."""
        return list(self._policies.keys())

    def answer_why(self, question: str) -> list[str]:
        """Answer a policy question with traceable reasoning."""
        answers = []
        for name, props in self._policies.items():
            content = props.get("content", "")
            if question.lower() in content.lower():
                answers.append(f"Policy '{name}': {content[:200]}")
        return answers if answers else ["No matching policy found"]

    def create_policy(self, name: str, content: str) -> None:
        """Create a new policy file."""
        path = self.policy_dir / f"{name}.md"
        path.write_text(content, encoding="utf-8")
        self._policies[name] = {"content": content, "file": str(path)}

    def compile(self, source: Path) -> dict:
        """Compile knowledge from a source directory."""
        return self.compiler.compile(source)