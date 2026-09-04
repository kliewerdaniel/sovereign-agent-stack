# ARGO Skill Pack for SAS

ARGO (xark-argo/argo) is the harness layer for SAS. This skill pack integrates SAS sovereignty scoring, compile-time knowledge graph, and payments abstraction into ARGO's MCP server.

## Integration Points

### 1. Sovereignty Dashboard as ARGO Skill

The SAS sovereignty dashboard runs as an ARGO skill that can be invoked by the agent:

```python
# ARGO skill: check_sovereignty
from sas.core.scoring import generate_report
from sas.core.config import parse_sas_yaml

def check_sovereignty(config_path: str = "sas.yaml") -> dict:
    """Check the current sovereignty score."""
    config = parse_sas_yaml(Path(config_path))
    report = generate_report(config)
    return {
        "score": report.score,
        "verdict": report.verdict,
        "layers": [{"name": l.name, "status": l.scored_as.value} for l in report.layers]
    }
```

### 2. Compile-Time Knowledge Graph as ARGO Tool

The knowledge graph compiles markdown into queryable nodes that ARGO can search:

```python
# ARGO tool: query_knowledge
from sas.layers.knowledge import CompileTimeKnowledge

_knowledge = CompileTimeKnowledge()

def query_knowledge(query: str) -> list[dict]:
    """Query the compile-time knowledge graph."""
    graph = _knowledge.compile(Path("~/sas-knowledge"))
    results = _knowledge.query(graph, query)
    return [{"label": r.label, "content": r.properties.get("content", "")} for r in results]
```

### 3. Payments Abstraction as ARGO Tool

The payments adapter integrates with ARGO's tool system:

```python
# ARGO tool: pay_for_resource
from sas.layers.payments import VirtualCardAdapter

_adapter = VirtualCardAdapter()

def pay_for_resource(resource: str, price: float, currency: str = "USD") -> dict:
    """Pay for a resource using the virtual card."""
    receipt = _adapter.pay(PaymentRequirement(
        resource=resource,
        price=price,
        currency=currency,
        methods=["card"],
        cadence="one_shot",
        metadata={},
    ))
    return {"payment_id": receipt.payment_id, "status": receipt.status}
```

## Installation

```bash
# Install SAS with ARGO support
pip install "sovereign-agent-stack[argo]"

# Configure ARGO to use SAS
# In ARGO config:
#   mcp_servers:
#     sas:
#       command: python
#       args: ["-m", "sas.mcp_server"]
```

## Configuration

```yaml
# sas.yaml with ARGO integration
harness:
  type: argo
  mcp_server: true
  tools:
    - check_sovereignty
    - query_knowledge
    - pay_for_resource
```

## MCP Server Mode

SAS can run as an MCP server for ARGO:

```bash
python -m sas.mcp_server --config sas.yaml
```

This exposes all SAS tools via MCP protocol, allowing ARGO to discover and invoke them automatically.

## Skill Manifest

```json
{
  "name": "sovereign-agent-stack",
  "version": "0.1.0",
  "description": "Local-first, compile-time AI agent framework",
  "author": "Daniel Kliewer",
  "license": "MIT",
  "tools": [
    {
      "name": "check_sovereignty",
      "description": "Check the current sovereignty score and get layer status",
      "parameters": {
        "type": "object",
        "properties": {
          "config_path": {
            "type": "string",
            "description": "Path to sas.yaml"
          }
        }
      }
    },
    {
      "name": "query_knowledge",
      "description": "Query the compile-time knowledge graph",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Query text"
          }
        },
        "required": ["query"]
      }
    },
    {
      "name": "pay_for_resource",
      "description": "Pay for a resource using the virtual card",
      "parameters": {
        "type": "object",
        "properties": {
          "resource": {
            "type": "string",
            "description": "Resource identifier"
          },
          "price": {
            "type": "number",
            "description": "Price to pay"
          },
          "currency": {
            "type": "string",
            "description": "Currency (default: USD)",
            "default": "USD"
          }
        },
        "required": ["resource", "price"]
      }
    }
  ]
}
```
