# Deployment Guide

## Sovereign Agent Stack v0.1.0

### Quick Start

```bash
# Install
pip install sovereign-agent-stack

# Initialize config
python -m sas init --output sas.yaml

# Edit sas.yaml to match your deployment
# See examples/ for reference configs

# Run dashboard
python -m sas dashboard --config sas.yaml --cache ~/.sas

# Compile knowledge graph
python -m sas knowledge compile ~/notes --store ~/.sas/knowledge.db

# Register auth credentials
python -m sas auth register github --token ghp_xxx --scopes repo,user

# Provision identity
python -m sas identity provision-email myagent --domain agentmail.to --mock
python -m sas identity provision-phone --region US --mock
```

### Configuration

`sas.yaml` declares all 8 layers:

```yaml
model:
  primary:
    provider: ollama
    name: llama3.1:8b
    location: local

compute:
  substrate: local_docker
  resources:
    cpu: 4
    memory: 8Gi
  auto_destroy: 300

memory:
  short_term:
    provider: local_rag
  long_term:
    provider: compile_time_graph
    source: ~/sas-knowledge

auth:
  broker: local_mcp_gateway
  vault: ~/.sas/vault.db
  encryption: libsodium

payments:
  adapter: virtual_card
  virtual_card:
    provider: ramp
    limit: 100

identity:
  email:
    provider: agentmail
    domain: agentmail.to
  phone:
    provider: agentphone
    region: US
```

### Production Deployment

1. **Knowledge Layer** — Compile your markdown vault into the graph:
   ```bash
   python -m sas knowledge compile ~/vault --store ~/.sas/knowledge.db
   ```

2. **Auth Broker** — Register tools with encrypted credential storage:
   ```bash
   python -m sas auth register github --token $GITHUB_TOKEN
   python -m sas auth register stripe --auth-type api_key --token $STRIPE_KEY
   ```

3. **Substrate** — Boot a local desktop container:
   ```bash
   python -m sas substrate boot --template xfce
   ```

4. **Payments** — Configure virtual card or MPP adapter in `sas.yaml`.

5. **Monitor** — Track sovereignty drift:
   ```bash
   python -m sas dashboard --config sas.yaml --cache ~/.sas --json
   ```

### Example Configurations

| Use Case | Config |
|---|---|
| Agency Worker | `examples/agency-worker/sas.yaml` |
| Personal Assistant | `examples/personal-assistant/sas.yaml` |
| Industry Analyst | `examples/industry-analyst/sas.yaml` |

### Security Notes

- Auth credentials are encrypted at rest (libsodium envelope encryption).
- Knowledge graph persists to SQLite (file permissions: 600).
- Virtual card payments enforce daily + per-transaction limits.
- Audit trail captures all credential-bearing requests.

### Troubleshooting

| Issue | Command |
|---|---|
| Sovereignty score drops | `python -m sas dashboard --verbose` |
| Knowledge graph empty | `python -m sas knowledge audit --store ~/.sas/knowledge.db` |
| Auth failures | `python -m sas auth list` |
| Payment declined | Check `payments.pay` error message |
| Machine unresponsive | `python -m sas substrate list` then `destroy` |
