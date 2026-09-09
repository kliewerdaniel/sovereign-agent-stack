# Plugin Security Model

> **Status:** Initial Model
> **Last Updated:** 2026-09-09
> **Phase:** Consequence Protocol Closure II

This document defines the security model for the plugin system. The plugin system is the highest-risk remaining boundary because it allows arbitrary Python execution.

---

## Core Distinction

> **AUTHORIZATION CONTROL ≠ EXECUTION ISOLATION**

A capability system alone does not sandbox arbitrary Python. Conversely, a sandbox alone does not establish protocol authority.

This document defines both properties explicitly.

---

## Threat Model

### In-Process Plugins

Plugins loaded via `exec_module` execute in the same Python process as SAS. This means they have:

- Full access to Python interpreter
- Access to all imports
- Access to all memory
- Access to filesystem (subject to OS permissions)
- Access to network (subject to OS permissions)
- Access to environment variables
- Ability to spawn subprocesses
- Ability to monkey-patch code

### Attack Surface

```
Plugin code (arbitrary Python)
    ↓
Import broker adapter
    ↓
Call submit_trade() directly
    ↓
External effect (bypasses CapabilityBoundBroker)
```

```
Plugin code
    ↓
Import auth broker
    ↓
Call get_credentials() directly
    ↓
Credential theft
```

```
Plugin code
    ↓
Import substrate
    ↓
Call execute() directly
    ↓
Arbitrary command execution
```

---

## Plugin Trust Levels

### Trusted Plugin

- Executes in-process under the documented TCB
- May access all SAS internals
- Must be shipped with SAS or from a trusted source
- Registration is informational, not authority-management

### Untrusted Plugin

- Must not receive ambient process privileges
- Must execute in an isolated environment (subprocess/container)
- Registration is authority-management
- All operations require capability verification

---

## Authority Control

### Registration

Registration is AUTHORITY-MANAGEMENT because it changes future execution capability.

```
register_plugin
    ↓
AUTHORITY_MUTATION
    ↓
explicit capability
    ↓
authorization
    ↓
verification
```

A plugin must not become executable merely because it was registered.

### Discovery

Discovery is INFORMATIONAL.

```
plugin discovery ≠ plugin execution
```

### Invocation

Plugin invocation is PLUGIN_EXECUTION and requires a capability bound to:

- plugin identity
- plugin version
- content digest (SHA-256 of source)
- requested operation
- resource scope
- arguments
- actor
- domain
- temporal validity
- delegation
- replay state

### Plugin Provenance

Execution is bound to:

- plugin_id
- version
- content digest
- source provenance
- registration provenance
- authorization provenance

Changing plugin bytes invalidates the previously derived execution capability unless the protocol explicitly authorizes that transition.

---

## Execution Isolation

### Current State

The current plugin system loads plugins in-process via `exec_module`. This means:

- Plugins have full process privileges
- Capability checks are the only authority boundary
- There is no memory or process isolation

### Target State

For untrusted plugins:

- Subprocess execution via the substrate authority model
- Or container isolation via Docker
- Communication via IPC (pipes, sockets, shared memory)

The substrate authority model provides:

- Machine binding
- Command class binding
- Filesystem scope binding
- Network scope binding
- Resource limits
- Duration limits

---

## Capability Binding

A plugin execution capability must bind:

| Field | Description |
|-------|-------------|
| `plugin_id` | Unique plugin identifier |
| `version` | Plugin version |
| `content_digest` | SHA-256 of plugin source |
| `operation` | Requested operation |
| `resource` | Resource scope |
| `arguments` | Operation arguments |
| `actor` | Actor performing the operation |
| `domain` | Protocol domain |
| `temporal_interval` | When the capability is valid |
| `delegation_chain` | Delegation chain |
| `nonce` | Replay protection |

---

## Invariants

### Registration

> **REGISTRATION MUST NEVER CREATE AUTHORITY BY ITSELF.**

Registration is authority-management and requires explicit authorization.

### Execution

> **PLUGIN_EXECUTION requires capability bound to plugin identity, version, content digest, and operation.**

A capability for plugin A must not authorize plugin B.

### Content Integrity

> **Changing plugin bytes invalidates previously derived capabilities.**

The content digest binds the capability to specific plugin code.

### Privilege

> **A plugin must not inherit ambient process authority.**

Plugins must not access broker, auth, substrate, or other consequential components without traversing the canonical authority protocol.

---

## Adversarial Tests

### Plugin Escape

```
Plugin code
    ↓
Import broker adapter
    ↓
Call submit_trade() directly
    ↓
MUST FAIL (raw broker not accessible)
```

### Plugin Credential Theft

```
Plugin code
    ↓
Import auth broker
    ↓
Call get_credentials() directly
    ↓
MUST FAIL (raw auth broker not accessible)
```

### Plugin Substrate Escape

```
Plugin code
    ↓
Import substrate
    ↓
Call execute() directly
    ↓
MUST FAIL (raw substrate not accessible)
```

### Plugin Identity Substitution

```
Capability for plugin A
    ↓
Execute plugin B
    ↓
MUST FAIL (plugin_id mismatch)
```

### Plugin Version Substitution

```
Capability for plugin v1.0.0
    ↓
Execute plugin v2.0.0
    ↓
MUST FAIL (version mismatch)
```

### Plugin Content Tampering

```
Capability for plugin with digest X
    ↓
Plugin source modified (digest Y)
    ↓
Execute plugin
    ↓
MUST FAIL (digest mismatch)
```

---

## Migration Path

1. **Phase 1:** Capability-bound plugin execution (current)
   - All plugin operations require capability
   - Plugin registration is authority-management
   - Content digest binding

2. **Phase 2:** Subprocess isolation for untrusted plugins
   - Plugins execute in subprocess
   - Communication via IPC
   - Substrate authority model provides isolation

3. **Phase 3:** Container isolation for high-risk plugins
   - Plugins execute in Docker containers
   - Full filesystem and network isolation
   - Resource limits enforced by container runtime

---

## Honest Security Claims

This system does NOT claim to defend against:

- A fully compromised operating system
- Arbitrary memory corruption
- A malicious Python interpreter
- Root-equivalent host compromise
- Compromised hardware

This system DOES claim:

> **Within the defined execution boundary, no plugin operation is authorized unless its authority is derivable and verifiable from the sovereign protocol.**

And:

> **Plugins cannot access consequential components (broker, auth, substrate, payments, identity) without traversing the canonical authority protocol.**
