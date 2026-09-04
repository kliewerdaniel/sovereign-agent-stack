# Agency Worker — High-Sovereignty, High-Autonomy

This example configures SAS for an autonomous agency worker: an AI agent that handles client deliverables, communicates via email/phone, and makes purchases on behalf of the agency.

## Sovereignty Profile

| Layer | Status | Implementation |
|-------|--------|----------------|
| Model | ✅ Owned | Ollama local (llama3.1:8b) |
| Harness | ✅ Owned | ARGO self-hosted |
| Compute | ✅ Owned | Local Docker desktop |
| Identity | ⚪ Rented | AgentMail + AgentPhone |
| Short-term Memory | ✅ Owned | Local RAG |
| Long-term Knowledge | ✅ Owned | Compile-time graph |
| Auth | ✅ Owned | Local MCP gateway |
| Payments | ⚪ Rented | Virtual card (Ramp) |

**Score:** 6/6 scorable = 100% (Fully Sovereign)

## Trade-offs

- **Local model only:** No API fallback means if Ollama is down, the agent is down. Add a cloud fallback for production.
- **Virtual card for payments:** Requires computer-use to fill checkout forms. Future: swap to MPP for machine-native payments.
- **Compile-time knowledge:** Facts update every 6 hours, not in real-time. Acceptable for stable knowledge domains.

## Usage

```bash
# Copy this config to your working directory
cp examples/agency-worker/sas.yaml sas.yaml

# Initialize and run the dashboard
python -m sas dashboard --config sas.yaml --verbose
```

## Customization

- Increase `auto_destroy` if you want the desktop container to persist longer.
- Add `overrides` for any layer you're self-hosting differently than the default expects.
- The `knowledge/` folder is where you put markdown files for the compile-time graph.
