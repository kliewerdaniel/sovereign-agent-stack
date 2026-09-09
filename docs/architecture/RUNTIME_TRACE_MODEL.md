# Runtime Trace Model

> **Date:** 2026-09-09
> **Phase:** Runtime Epistemology
> **Tests:** 1,827 passing

---

## Purpose

The runtime trace model provides bounded instrumentation for recording actual system behavior during controlled experiments. It is the empirical foundation for distinguishing **static authority topology** from **runtime authority topology**.

---

## Core Invariant

> **Runtime traces are observations.**
> They are NOT automatically:
> - authorization
> - evidence of legitimacy
> - proof of correctness
> - proof of necessity
> - proof that an action was permitted

A trace saying `process X called subprocess.run()` establishes an observation. It does NOT establish `process X was authorized to do so`.

---

## Trace Event Structure

Every runtime observation contains:

| Field | Type | Purpose |
|-------|------|---------|
| `event_id` | str | Unique identifier |
| `timestamp` | str | UTC ISO 8601 |
| `event_type` | TraceEventType | Category of event |
| `actor` | str | Who initiated |
| `component` | str | Which component |
| `operation` | str | What operation |
| `resource` | str | What resource |
| `consequence_type` | ConsequenceType | Effect classification |
| `parent_event` | Optional[str] | Parent in call tree |
| `call_path` | list[str] | Full call stack |
| `authority_context` | dict | Authority metadata |
| `capability_id` | Optional[str] | If capability verified |
| `authorization_id` | Optional[str] | If authorization derived |
| `provenance_id` | Optional[str] | If provenance recorded |
| `environment` | str | local/test/production |
| `process_id` | int | OS process ID |
| `thread_id` | int | Thread identity |
| `result` str | Outcome |
| `scope` | str | Observation scope |
| `limitations` | str | Known limitations |
| `raw_evidence` | str | Raw evidence (no secrets) |

---

## Event Types

### Consequential Events
| Type | Description |
|------|-------------|
| SUBPROCESS_CREATE | New process spawned |
| SUBPROCESS_COMPLETE | Process finished |
| NETWORK_REQUEST | Outbound network call |
| NETWORK_RESPONSE | Response received |
| FILESYSTEM_WRITE | File modified/created |
| BROKER_CALL | Trade/order submitted |
| BROKER_RESPONSE | Broker response |
| PAYMENT_PROCESS | Payment processed |
| IDENTITY_MUTATION | Identity changed |
| SUBSTRATE_OPERATION | Compute substrate action |

### Authority Events
| Type | Description |
|------|-------------|
| CAPABILITY_VERIFICATION | Capability checked |
| AUTHORIZATION_DERIVATION | Authorization derived |
| CONSEQUENCE_ENTER | Entered consequence boundary |
| CONSEQUENCE_EXIT | Exited consequence boundary |
| EXECUTION_RECEIPT | Receipt produced |
| PROVENANCE_RECORD | Provenance recorded |

### Discovery Events
| Type | Description |
|------|-------------|
| DYNAMIC_IMPORT | Runtime import |
| REFLECTION_CALL | Reflection invocation |
| DISPATCH_CALL | Dispatch table invocation |
| CONFIG_ACCESS | Configuration accessed |
| CREDENTIAL_ACCESS | Credential accessed |
| CLI_DISPATCH | CLI command dispatched |
| FILESYSTEM_READ | File read |

---

## Instrumentation Components

### RuntimeTraceRecorder
Core recorder. Thread-safe. Parent stack for call tree.

### SubprocessInstrument
Wraps `subprocess.run()` with trace recording.

### FilesystemInstrument
Wraps `open()` with trace recording.

### BrokerInstrument
Wraps `submit_trade()` with trace recording.

### CapabilityInstrument
Records capability verification events.

### AuthorizationInstrument
Records authorization derivation events.

### ProvenanceInstrument
Records provenance recording events.

### InstrumentationSuite
Unified entry point for all instruments.

---

## Consequence Type Taxonomy

| Type | Authority Required | Examples |
|------|-------------------|----------|
| EXTERNAL_CONSEQUENTIAL | Yes | Trade, payment, subprocess, network mutation |
| AUTHORITY_MANAGEMENT | Yes | Register plugin, grant capability |
| STATE_TRANSFORMING | Context-dependent | Write config, update cache |
| INFORMATIONAL | No | Read file, query status |
| NON_CONSEQUENTIAL | No | Pure computation |

---

## Trace Integrity vs Authorization

> **TRACE INTEGRITY ≠ AUTHORIZATION**

A perfectly authentic runtime trace can demonstrate that an unauthorized effect occurred.

Therefore:
- **TRACE AUTHENTICITY** — the trace is complete and unmodified
- **EFFECT AUTHORIZATION** — the effect was permitted
- **EPISTEMIC VALIDITY** — the claim is justified

These three must remain separate.

---

## Limitations

1. **Single-process scope**: Cannot trace across process boundaries without OS-level instrumentation
2. **Python-only**: Cannot trace non-Python subprocesses
3. **Synchronous only**: Async execution may lose parent context
4. **No secret recording**: Credentials and tokens are never recorded
5. **Observation only**: Traces do not prevent actions, only record them

---

## Usage Pattern

```python
from examples.self_audit.runtime_trace import InstrumentationSuite

suite = InstrumentationSuite("my_experiment", scope="controlled_local")
suite.start()

# Capability verification
suite.capability.verify(capability_id="cap_123", actor="agent")

# Authorization derivation
suite.authorization.derive(authorization_id="auth_456", actor="agent")

# Subprocess execution
result = suite.subprocess.run(
    cmd=["echo", "hello"],
    actor="agent",
    component="my_component",
    consequence_type=ConsequenceType.INFORMATIONAL,
    capability_id="cap_123",
    authorization_id="auth_456",
)

# Provenance recording
suite.provenance.record(provenance_id="prov_789", actor="agent")

suite.stop()

# Analyze
trace = suite.to_dict()
```

---

## Relationship to Static Analysis

| Static Analysis | Runtime Trace |
|----------------|---------------|
| Predicts what COULD happen | Records what DID happen |
| Source code as evidence | Execution as evidence |
| May have false positives | May miss unexercised paths |
| Marks hypotheses | Provides evidence |
| Cheaper to run | More expensive |
| Complete coverage | Partial coverage |

Both are necessary. Neither is sufficient.
