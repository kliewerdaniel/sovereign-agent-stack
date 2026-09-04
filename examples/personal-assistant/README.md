# Personal Assistant — Balanced Sovereignty

A balanced configuration for a personal AI assistant. Prioritizes convenience without fully sacrificing ownership.

## Sovereignty Profile

| Layer | Status | Implementation |
|-------|--------|----------------|
| Model | ✅ Owned | Ollama local (llama3.1:8b) |
| Harness | ✅ Owned | ARGO self-hosted |
| Compute | ✅ Owned | Local Docker desktop |
| Identity | ⚪ Rented | AgentMail + AgentPhone |
| Short-term Memory | ⚪ Rented | Honcho cloud (managed) |
| Long-term Knowledge | ✅ Owned | Compile-time graph |
| Auth | ⚪ Rented | Composio (managed) |
| Payments | ⚪ Rented | Virtual card (Ramp) |

**Score:** 3/6 scorable = 50% (Partially sovereign)

## Trade-offs

- **Honcho cloud memory:** Better UX (zero-config, syncs across devices) but memory is processed by Honcho's servers. Swap to `honcho_self_hosted` or `local_rag` to reclaim.
- **Composio auth:** Fast to set up, no local vault to manage. But credentials transit Composio's infrastructure. Swap to `local_mcp_gateway` to reclaim.
- **Virtual card for payments:** Same as agency worker.

## Usage

```bash
cp examples/personal-assistant/sas.yaml sas.yaml
python -m sas dashboard --config sas.yaml --verbose
```

## Path to Full Sovereignty

1. Swap `memory.short_term.provider` to `local_rag` (+1)
2. Swap `auth.broker` to `local_mcp_gateway` (+1)
3. Optional: self-host Honcho for `honcho_self_hosted` (+0, already counted)

**Result:** 5/6 = 83% (Sovereign target)
