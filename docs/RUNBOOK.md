# Operations Runbook

Daily, weekly, and monthly operations for a Sovereign Agent Stack deployment.

---

## Daily Operations

### Health Check

```bash
# Quick sovereignty score check
python -m sas dashboard --config sas.yaml --cache ~/.sas

# Expected output: score >= 0.625 (Sovereign target)
# If drift detected, investigate layer changes
```

### Vault Audit

```bash
# Check credential expiration
# (The auth broker logs audit entries to ~/.sas/vault.db)
```

### Knowledge Graph Freshness

```bash
# Verify recent compilation
ls -la ~/sas-knowledge/

# If files were modified but graph wasn't recompiled,
# the cron schedule in sas.yaml may need adjustment
```

---

## Weekly Operations

### 1. Full Sovereignty Report

```bash
python -m sas dashboard --config sas.yaml --verbose
```

Review each layer for unexpected changes. Common drift causes:
- New API key added to Composio instead of local vault
- Switched from local model to cloud-only model
- Compute substrate moved to cloud VM

### 2. Backup Verification

```bash
# Verify backups exist
ls -la ~/.sas/backups/

# Test restore from backup (weekly)
cp ~/.sas/vault.db ~/.sas/backups/vault-$(date +%Y%m%d).db
```

### 3. Knowledge Graph Audit

```bash
# Run audit via Python
python -c "
from sas.layers.knowledge import CompileTimeKnowledge
from pathlib import Path
k = CompileTimeKnowledge()
graph = k.compile(Path.home() / 'sas-knowledge')
audit = k.audit(graph)
print(f'Nodes: {audit.total_nodes}, Edges: {audit.total_edges}')
print(f'Orphaned: {len(audit.orphaned_nodes)}, Stale: {len(audit.stale_nodes)}')
"
```

Review orphaned nodes — they may need links or removal.

### 4. Payment Receipts Reconciliation

```bash
# Review spending against receipts
# The VirtualCardAdapter and MPPAdapter track all receipts
```

---

## Monthly Operations

### 1. Credential Rotation

```bash
# Rotate OAuth tokens via the refresh mechanism
# Review audit trail for suspicious calls
```

### 2. Model Updates

```bash
# Update local model (if needed)
docker exec ollama ollama pull llama3.1:8b
```

### 3. Docker Image Updates

```bash
# Rebuild desktop container image
docker build -t sas-desktop:latest -f docker/Dockerfile .
```

### 4. Security Review

```bash
# Review auth broker audit trail
# Check for unusual patterns in tool calls
# Verify encryption keys are rotated
```

---

## Incident Response

### Sovereignty Score Drop

1. Run `python -m sas dashboard --verbose` to identify which layer changed
2. Check `sas.yaml` for accidental modifications
3. If drift is expected (intentional change), update baseline:
   ```bash
   rm ~/.sas/sovereignty_score.json
   python -m sas dashboard --config sas.yaml  # establishes new baseline
   ```

### Vault Compromise

1. **Immediately:** Unregister all tools
   ```bash
   # Via Python
   from sas.layers.auth import LocalAuthBroker
   broker = LocalAuthBroker(store_path="~/.sas/vault.db")
   for tool in broker.list_tools():
       broker.unregister_tool(tool)
   ```
2. Rotate all API keys and OAuth tokens
3. Re-register tools with new credentials
4. Investigate breach vector

### Model Server Down

1. Check Ollama: `docker ps | grep ollama`
2. If Ollama is down, start it: `docker start ollama`
3. If using API fallback, verify connectivity
4. Check disk space: `df -h`

### Knowledge Graph Corruption

1. Stop the compile cron
2. Backup current graph store
3. Recompile from source:
   ```bash
   rm ~/.sas/knowledge_graph.db
   python -c "from sas.layers.knowledge import CompileTimeKnowledge; CompileTimeKnowledge().compile(Path.home() / 'sas-knowledge')"
   ```
4. Resume compile cron

---

## Monitoring Metrics

Track these metrics over time:

| Metric | Target | Warning |
|--------|--------|---------|
| Sovereignty score | >= 0.625 | < 0.375 |
| Knowledge graph nodes | Growing | Stale (>30 days) |
| Orphaned nodes | 0 | > 5 |
| Credential refresh success | 100% | < 95% |
| Daily spending | < limit | > 80% limit |
| Vault audit entries | All expected | Unexpected calls |

---

## Contact

- **Security issues:** See SECURITY.md
- **Bug reports:** https://github.com/kliewerdaniel/sovereign-agent-stack/issues
- **Discussions:** https://github.com/kliewerdaniel/sovereign-agent-stack/discussions
