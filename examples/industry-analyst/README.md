# Industry Analyst — Research-First, High-Knowledge

A configuration for an AI industry analyst that prioritizes knowledge graph depth and long-term memory. Runs research queries, compiles findings into the knowledge graph, and produces reports.

## Sovereignty Profile

| Layer | Status | Implementation |
|-------|--------|----------------|
| Model | ✅ Owned | Ollama local (llama3.1:8b) |
| Harness | ✅ Owned | ARGO self-hosted |
| Compute | ✅ Owned | Local Docker desktop |
| Identity | ⚪ Rented | AgentMail + AgentPhone |
| Short-term Memory | ✅ Owned | Local RAG |
| Long-term Knowledge | ✅ Owned | Compile-time graph (deep) |
| Auth | ✅ Owned | Local MCP gateway |
| Payments | ⚪ Rented | MPP native (Stripe) |

**Score:** 5/6 scorable = 83% (Sovereign target)

## Trade-offs

- **MPP native payments:** Uses Stripe MPP for machine-native payments (HTTP 402 flows). Requires stablecoin settlement. More complex setup but no computer-use needed for payments.
- **Deep knowledge graph:** Compiles every hour instead of every 6 hours. More CPU usage but fresher knowledge.
- **No API fallback:** Pure local model. If Ollama is down, the agent is down.

## Usage

```bash
cp examples/industry-analyst/sas.yaml sas.yaml
python -m sas dashboard --config sas.yaml --verbose
```

## Customization

- The `knowledge/` folder is where research notes and findings go.
- Add `overrides` for any layer you're self-hosting differently.
- For real-time knowledge, reduce `compile_cron` to `"0 * * * *"` (every hour).
