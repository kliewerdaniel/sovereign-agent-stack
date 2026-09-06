# Operations Runbook

## Sovereign Agent Stack v0.1.0

### Daily Operations

#### Check Sovereignty Drift
```bash
python -m sas dashboard --config sas.yaml --cache ~/.sas --verbose
```
- Score should be stable. A drop indicates a layer changed ownership (e.g., model switched from local to API).
- Drift detection compares against the last cached score at `~/.sas/sovereignty_score.json`.

#### Compile Knowledge Graph
```bash
python -m sas knowledge compile ~/vault --store ~/.sas/knowledge.db
```
- Run on a cron schedule (every 6 hours recommended).
- Verify with: `python -m sas knowledge audit --store ~/.sas/knowledge.db`

#### Rotate Credentials
```bash
python -m sas auth list
python -m sas auth get github
python -m sas auth register github --token $NEW_TOKEN  # Overwrites
```

### Weekly Operations

#### Audit Trail Review
```bash
python -m sas auth audit
```
- Review all credential-bearing requests.
- Look for unexpected tools or paths.

#### Substrate Cleanup
```bash
python -m sas substrate list
python -m sas substrate destroy <machine_id>
```
- Idle machines auto-destroy after 300s (configurable).
- Manually destroy long-running machines to free resources.

#### Payment Reconciliation
```bash
python -m sas payments limit --daily 500 --per-transaction 100
```
- Adjust spending limits based on usage.
- Virtual card: daily limit resets every 24h.

### Monthly Operations

#### Full Stack Integration Test
```bash
python -m pytest tests/integration/test_full_stack.py -v
```
- Verifies all 8 layers work together.
- Run before and after config changes.

#### Security Audit
```bash
# Check credential encryption
python -c "from sas.layers.auth import LocalAuthBroker; b = LocalAuthBroker(); print('Vault OK')"

# Check knowledge graph integrity
python -m sas knowledge audit --store ~/.sas/knowledge.db

# Check sovereignty score
python -m sas dashboard --config sas.yaml --cache ~/.sas --json
```

### Incident Response

| Symptom | Action |
|---|---|
| Score drops to 0/6 | Check `sas.yaml` — model/compute may have switched to API |
| Auth 401 errors | Re-register: `python -m sas auth register <tool> --token $TOKEN` |
| Payment declined | Check limits: `python -m sas payments limit --daily X --per-transaction Y` |
| Knowledge graph empty | Re-compile: `python -m sas knowledge compile <source> --store ~/.sas/knowledge.db` |
| Machine stuck | `python -m sas substrate destroy <id>` |
| High drift | `python -m sas dashboard --verbose` to see which layer changed |

### Backup

```bash
# Credentials
cp ~/.sas/vault.db ~/.sas/backup/vault-$(date +%Y%m%d).db

# Knowledge graph
cp ~/.sas/knowledge.db ~/.sas/backup/knowledge-$(date +%Y%m%d).db

# Config
cp sas.yaml ~/.sas/backup/sas-$(date +%Y%m%d).yaml

# Sovereignty cache
cp ~/.sas/sovereignty_score.json ~/.sas/backup/
```

### Monitoring

```bash
# JSON output for monitoring systems
python -m sas dashboard --config sas.yaml --cache ~/.sas --json | jq '.score'

# Check specific layer
python -c "
from sas.core.config import parse_sas_yaml
from sas.layers import LayerRegistry
from pathlib import Path
r = LayerRegistry(parse_sas_yaml(Path('sas.yaml')))
print('Model owned:', r.is_owned('layer_1'))
print('Auth owned:', r.is_owned('layer_7'))
print('Score:', r.sovereignty_score())
"
```
