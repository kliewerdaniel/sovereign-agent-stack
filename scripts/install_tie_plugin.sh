#!/bin/bash
# Install the TIE knowledge plugin for SAS.
#
# Copies the plugin module into ~/.sas/plugins/ so SAS discovers it
# via PluginRegistry.discover().
#
# Usage:
#   bash scripts/install_tie_plugin.sh
#
# After install, verify with:
#   python3 -c "from sas.plugins import discover_plugins; print([p.name for p in discover_plugins()])"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

SRC="$PROJECT_ROOT/sas_tie_knowledge/plugin.py"
DEST_DIR="$HOME/.sas/plugins"
DEST="$DEST_DIR/tie_knowledge.py"

mkdir -p "$DEST_DIR"

cp "$SRC" "$DEST"
echo "Installed: $DEST"

# Find a Python interpreter with sas installed
find_python() {
    # Candidates in order of preference
    local candidates=(
        "$1"                    # Explicit argument (for testing)
        "$(command -v python3 2>/dev/null)"
        "$(command -v python 2>/dev/null)"
        "$PROJECT_ROOT/.venv/bin/python"
        "$PROJECT_ROOT/venv/bin/python"
        "$HOME/.hermes/hermes-agent/venv/bin/python"
        "$HOME/.local/share/virtualenvs/$(basename "$PROJECT_ROOT")/bin/python"
    )

    for candidate in "${candidates[@]}"; do
        if [[ -z "$candidate" ]]; then continue; fi
        if [[ ! -x "$candidate" ]]; then continue; fi
        if "$candidate" -c "import sas" 2>/dev/null; then
            echo "$candidate"
            return 0
        fi
    done

    return 1
}

PYTHON="$(find_python "")"

if [[ -z "$PYTHON" ]]; then
    echo "ERROR: Could not find a Python interpreter with 'sas' installed." >&2
    echo "Activate your virtual environment first, or install SAS:" >&2
    echo "  pip install -e $PROJECT_ROOT" >&2
    exit 1
fi

echo "Using Python: $PYTHON"

# Verify
if "$PYTHON" -c "
from sas.plugins import discover_plugins
plugins = discover_plugins()
tie = [p for p in plugins if p.name == 'tie-knowledge']
if tie:
    print(f'Discovered: {tie[0].name} at {tie[0].layer_id} (source={tie[0].source.name})')
else:
    print('ERROR: tie-knowledge not discovered')
    exit(1)
" 2>&1; then
    echo "Plugin registered successfully."
else
    echo "Plugin registration failed."
    exit 1
fi
