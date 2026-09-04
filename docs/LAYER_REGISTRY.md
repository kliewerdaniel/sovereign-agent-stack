# Community Layer Registry

The SAS community layer registry is a curated list of layer implementations contributed by the community. Anyone can submit a layer implementation for inclusion.

## How It Works

1. **Fork** the [sas-layers](https://github.com/kliewerdaniel/sas-layers) registry repo (or create your own)
2. **Implement** your layer adapter (see template below)
3. **Publish** to PyPI with the `sas_layer_*` entry point convention
4. **Submit a PR** to the registry repo with your implementation details

## Entry Point Convention

When you publish your plugin to PyPI, add an entry point in your `pyproject.toml`:

```toml
[project.entry-points."sas.layers"]
sas_payments = "my_package.my_module:get_layer"
```

The entry point should return a callable that accepts a layer ID and returns the layer implementation.

## Submission Template

Create a markdown file in the `layers/` directory of the registry repo:

```markdown
# My Custom Payment Adapter

- **Author:** yourname
- **Layer:** Payments (layer_8)
- **Repo:** https://github.com/yourname/sas-payments-custom
- **PyPI:** sas-payments-custom
- **License:** MIT
- **Description:** A payment adapter for XYZ payment processor

## Installation

```bash
pip install sas-payments-custom
```

## Configuration

```yaml
payments:
  adapter: virtual_card
  custom:
    api_key: YOUR_API_KEY
```

## Verification

- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Plugin loads via entry point
- [ ] No hardcoded secrets
- [ ] Documentation complete
```

## Registered Layers

### Official

| Layer | Implementation | Source | Status |
|-------|---------------|--------|--------|
| Payments | VirtualCardAdapter | Built-in | ✅ |
| Payments | MPPAdapter | Built-in | ✅ |
| Auth | LocalAuthBroker | Built-in | ✅ |
| Knowledge | CompileTimeKnowledge | Built-in | ✅ |
| Substrate | LocalDockerSubstrate | Built-in | ✅ |
| Identity | AgentMailAdapter | Built-in | ✅ |
| Identity | MockEmailAdapter | Built-in | ✅ |

### Community

*No community submissions yet. Be the first!*

## Rating Criteria

Submissions are reviewed on:

1. **Correctness** — Does it correctly implement the layer protocol?
2. **Security** — Are credentials handled safely?
3. **Documentation** — Is the configuration well-documented?
4. **Testing** — Are there tests with >80% coverage?
5. **Maintenance** — Is the implementation actively maintained?

## Governance

- SAS core team reviews submissions
- Approved implementations are merged into the registry
- Implementations that become unmaintained may be flagged
- Critical security issues result in immediate delisting
