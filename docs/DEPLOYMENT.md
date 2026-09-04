# Deployment Guide

This guide covers deploying the Sovereign Agent Stack in production.

## Prerequisites

- Python 3.11+
- Docker Desktop (for compute substrate)
- Ollama (for local model inference)
- 16GB+ RAM recommended (8GB for model, 8GB for desktop container)

## Quick Start

```bash
# Install from PyPI (or source)
pip install sovereign-agent-stack

# Create a template configuration
python -m sas init --output sas.yaml

# Edit sas.yaml to match your deployment
# Then run the sovereignty dashboard
python -m sas dashboard --config sas.yaml --verbose
```

## Production Deployment

### 1. Local Model Server

Run Ollama as a systemd service or Docker container:

```bash
# Start Ollama with your preferred model
docker run -d \
  --name ollama \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  ollama/ollama:latest

# Pull the model
docker exec ollama ollama pull llama3.1:8b
```

### 2. Knowledge Graph

```bash
# Create your knowledge directory
mkdir -p ~/sas-knowledge

# Add markdown files with wikilinks
# The graph compiles automatically via the cron schedule in sas.yaml
```

### 3. Auth Vault

```bash
# Initialize the vault (done automatically on first run)
# Location: ~/.sas/vault.db
# Encryption: libsodium (via PyNaCl)
```

### 4. Compute Substrate

```bash
# Build the desktop container image
docker build -t sas-desktop:latest -f docker/Dockerfile .

# The substrate manages containers automatically via SAS
```

### 5. Identity

```bash
# Provision email inbox via AgentMail
# Provision phone number via AgentPhone
# Store API keys in the auth vault
```

### 6. Payments

```bash
# For virtual card: configure Ramp API keys
# For MPP: configure Stripe MPP credentials
```

## Monitoring

Run the sovereignty dashboard on a schedule:

```bash
# Check sovereignty score daily
python -m sas dashboard --config sas.yaml --cache ~/.sas

# Output JSON for monitoring systems
python -m sas dashboard --config sas.yaml --cache ~/.sas --json
```

## Backup

Critical data to back up:

- `~/.sas/vault.db` — encrypted credential vault
- `~/.sas/sovereignty_score.json` — score history for drift detection
- `~/sas-knowledge/` — knowledge graph source files
- `sas.yaml` — your configuration

## Scaling

SAS is single-tenant by design. To run multiple agents:

1. Create separate `sas.yaml` files per agent
2. Use separate knowledge directories
3. Run separate Ollama instances (or shard by GPU)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Ollama not reachable | Check `docker ps` and port 11434 |
| Vault permission denied | Ensure `~/.sas/` is writable by the agent |
| Container won't boot | Check Docker Desktop is running |
| Knowledge graph empty | Verify `sas.yaml` has correct `source` path |
