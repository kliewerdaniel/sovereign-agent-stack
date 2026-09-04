# Plugin Development Guide

This guide explains how to build and publish plugins for the Sovereign Agent Stack.

## Plugin Types

SAS supports plugins for any of the 8 layers:

| Layer | ID | Protocol |
|-------|----|----------|
| Model | `layer_1_model` | `ModelProvider` |
| Harness | `layer_2_harness` | `Harness` |
| Compute | `layer_3_compute` | `ComputeSubstrate` |
| Identity | `layer_4_identity` | `EmailIdentity` / `PhoneIdentity` |
| Short-term Memory | `layer_5_short_term_memory` | `ShortTermMemory` |
| Long-term Knowledge | `layer_6_long_term_knowledge` | `KnowledgeGraph` |
| Auth | `layer_7_auth` | `AuthBroker` |
| Payments | `layer_8_payments` | `PaymentAdapter` |

## Quick Start

### 1. Create Your Plugin

```python
# my_plugin.py
"""Custom payment adapter plugin."""

from sas.plugins import LayerPlugin, PluginSource, register_plugin
from sas.layers.payments import PaymentAdapter, PaymentRequirement, Receipt

class MyCustomPaymentAdapter(PaymentAdapter):
    """Custom payment adapter for XYZ processor."""

    def __init__(self, config: dict = None) -> None:
        self.config = config or {}

    def pay(self, requirement: PaymentRequirement) -> Receipt:
        # Your payment logic here
        ...

# Plugin metadata
SAS_PLUGIN = {
    "name": "my-custom-payments",
    "layer_id": "layer_8_payments",
    "version": "0.1.0",
    "description": "Custom payment adapter for XYZ",
    "author": "yourname",
    "url": "https://github.com/yourname/sas-payments-custom",
}

# Auto-register when loaded
register_plugin(LayerPlugin(
    name=SAS_PLUGIN["name"],
    layer_id=SAS_PLUGIN["layer_id"],
    version=SAS_PLUGIN["version"],
    description=SAS_PLUGIN["description"],
    source=PluginSource.LOCAL,
    author=SAS_PLUGIN["author"],
    url=SAS_PLUGIN["url"],
    factory=lambda: MyCustomPaymentAdapter(),
))
```

### 2. Install Locally

```bash
# Copy to plugins directory
mkdir -p ~/.sas/plugins/
cp my_plugin.py ~/.sas/plugins/
```

### 3. Verify It Loads

```python
from sas.plugins import discover_plugins, auto_register_discovered

auto_register_discovered()
plugin = get_plugin("layer_8_payments")
print(plugin.name)  # "my-custom-payments"
```

## Publishing to PyPI

### 1. Configure Entry Point

```toml
# pyproject.toml
[project.entry-points."sas.layers"]
sas_payments = "my_package.my_module:get_layer"
```

### 2. Implement Factory

```python
# my_package/my_module.py
def get_layer():
    from my_package.adapter import MyCustomPaymentAdapter
    return MyCustomPaymentAdapter()
```

### 3. Publish

```bash
python -m build
twine upload dist/*
```

Users can then install with:
```bash
pip install sas-payments-custom
```

## Plugin Discovery Order

1. **Built-in** — Shipped with SAS (`source=BUILTIN`)
2. **Pip** — Installed via `pip install` (`source=PIP`)
3. **Local** — Files in `~/.sas/plugins/` (`source=LOCAL`)

Higher priority plugins override lower priority ones. A local development version overrides a pip-installed version.

## Best Practices

1. **Follow the protocol** — Your plugin must implement the layer protocol interface
2. **Handle errors gracefully** — Don't crash the agent if your service is down
3. **Document configuration** — Users need to know what `sas.yaml` options to set
4. **Test thoroughly** — Ship tests with your plugin
5. **Don't hardcode secrets** — Use the auth broker for credentials
6. **Version semantically** — Use semantic versioning (MAJOR.MINOR.PATCH)

## Example: Payment Adapter Plugin

```python
"""Example payment adapter plugin."""

from sas.plugins import LayerPlugin, PluginSource, register_plugin
from sas.layers.payments import (
    PaymentAdapter,
    PaymentRequirement,
    Receipt,
    SpendingLimit,
)

class ExamplePaymentAdapter(PaymentAdapter):
    """Example payment adapter."""

    def __init__(self, config: dict = None) -> None:
        self.config = config or {}
        self._spending = 0.0

    def pay(self, requirement: PaymentRequirement) -> Receipt:
        if requirement.price > self.config.get("max_transaction", 100):
            raise ValueError("Exceeds maximum")

        return Receipt(
            payment_id="example_123",
            resource=requirement.resource,
            amount=requirement.price,
            currency=requirement.currency,
            method="example",
            timestamp="2026-09-04T00:00:00Z",
            status="completed",
        )

    def authorize(self, limit: SpendingLimit) -> None:
        self.config["max_transaction"] = limit.per_transaction

    def receipt(self, payment_id: str) -> Receipt | None:
        return None

SAS_PLUGIN = {
    "name": "example-payments",
    "layer_id": "layer_8_payments",
    "version": "0.1.0",
    "description": "Example payment adapter",
    "author": "SAS Community",
    "url": "https://github.com/example/sas-payments-example",
}

register_plugin(LayerPlugin(
    name=SAS_PLUGIN["name"],
    layer_id=SAS_PLUGIN["layer_id"],
    version=SAS_PLUGIN["version"],
    description=SAS_PLUGIN["description"],
    source=PluginSource.LOCAL,
    author=SAS_PLUGIN["author"],
    url=SAS_PLUGIN["url"],
    factory=lambda: ExamplePaymentAdapter(),
))
```

## Testing Your Plugin

```python
# tests/test_my_plugin.py
from sas.plugins import discover_plugins, get_plugin

def test_plugin_discovers():
    plugins = discover_plugins()
    assert any(p.layer_id == "layer_8_payments" for p in plugins)

def test_plugin_works():
    plugin = get_plugin("layer_8_payments")
    assert plugin is not None

    layer = plugin.factory()
    # Test your layer implementation
```

## See Also

- [LAYER_REGISTRY.md](LAYER_REGISTRY.md) — Community layer registry
- [Plugins API Reference](../src/sas/plugins.py) — Plugin system implementation
- [CONTRIBUTING.md](../CONTRIBUTING.md) — How to contribute
