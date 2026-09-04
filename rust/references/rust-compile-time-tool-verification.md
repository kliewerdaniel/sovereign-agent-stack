# Rust Compile-Time Verification Layer (2026-09-04)

Session-specific detail for the `sas-core-rs` Rust workspace added to the
Sovereign Agent Stack. This file captures the full architecture: derive macro,
typestate capability enforcement, policy hooks, state machine macro, sovereignty
assertions, test patterns, PyO3 bindings, and macOS linking pitfalls.

## Workspace Layout

```
/tmp/sas-review/rust/
├── Cargo.toml              # Workspace manifest
├── .cargo/config.toml      # macOS Python linking flags
├── sas-macros/
│   ├── Cargo.toml          # proc-macro = true
│   └── src/
│       ├── lib.rs          # #[derive(Tool)] implementation
│       └── attrs.rs        # Attribute parsing helpers
├── sas-core-rs/
│   ├── Cargo.toml          # Core types + optional pyo3 feature
│   └── src/
│       ├── lib.rs          # Tool trait, ExecutionContext, AgentStateMachine
│       ├── capability.rs   # Typestate capability enforcement
│       ├── state_machine.rs # transitions! macro
│       ├── policy.rs       # Policy hook typestate markers
│       └── sovereignty.rs  # Sovereignty compile-time assertions
├── sas-core-rs/tests/
│   ├── unit_tests.rs       # 28 tests
│   └── integration_tests.rs # 19 tests
├── sas-core-py/
│   ├── Cargo.toml          # PyO3 extension module
│   └── src/lib.rs          # Python bindings
└── target/release/
    └── libsas_core_py.dylib  # Built extension
```

## Derive Macro (`sas-macros`)

The `#[derive(Tool)]` macro generates an impl of `sas_core_rs::Tool` for any
struct with named fields. It parses `#[tool(description = "...")]` on the
struct and `#[tool(description = "...")]` / `#[tool(default = "...")]` on
fields.

**Key implementation details:**

1. **Snake-case name**: `to_snake_case()` converts struct name to tool name
2. **JSON Schema generation**: `generate_schema()` builds `JsonSchema` with
   required/optional fields, types, descriptions, defaults
3. **Type mapping**: `type_to_json_type()` maps Rust types to JSON Schema types
   - `String` → `"string"`, `u32`/`i64` → `"integer"`, `f64` → `"number"`
   - `bool` → `"boolean"`, `Vec` → `"array"`, `Option<T>` → inner type
4. **Validation generation**: `generate_validate()` produces code that checks
   required fields exist and types match
5. **Execute generation**: `generate_execute()` produces code that extracts
   fields from JSON input, constructs the struct, and calls `run()`

**FieldInfo parsing:**
- `required` is false if type is `Option<T>` OR if `#[tool(default = "...")]` is present
- `description` comes from `#[tool(description = "...")]`
- `default` comes from `#[tool(default = "...")]` (string literal, parsed at runtime)

## Core Types (`sas-core-rs/src/lib.rs`)

### Tool Trait
```rust
pub trait Tool: Send + Sync + 'static {
    fn name() -> &'static str;
    fn description() -> &'static str;
    fn schema() -> JsonSchema;
    fn validate(input: &serde_json::Value) -> Result<(), ValidationError>;
    fn execute(input: serde_json::Value) -> Result<serde_json::Value, ToolError>;
}
```

### Error Types
- `ValidationError`: `MissingField(String)`, `InvalidType { field, expected }`, `Custom(String)`
- `ToolError`: `ParseError(String)`, `ExecutionError(String)`, `CapabilityDenied(String)`
- `StateError`: `InvalidTransition { from, to }`
- `From<ValidationError> for ToolError` converts validation errors to parse errors

## Typestate Capability Enforcement (`capability.rs`)

Uses Rust's type system to enforce that tools can only perform operations they
have been explicitly granted capabilities for.

### Core Mechanism

```rust
// Zero-sized capability markers
pub trait Capability: Send + Sync + 'static {}
pub struct ReadFilesystem; impl Capability for ReadFilesystem {}
pub struct WriteFilesystem; impl Capability for WriteFilesystem {}
pub struct DispatchNetwork; impl Capability for DispatchNetwork {}
pub struct ExecuteCommands; impl Capability for ExecuteCommands {}
pub struct ProcessPayments; impl Capability for ProcessPayments {}
pub struct EmitEvents; impl Capability for EmitEvents {}
pub struct ReadKnowledge; impl Capability for ReadKnowledge {}
pub struct WriteKnowledge; impl Capability for WriteKnowledge {}
pub struct NoCapability; impl Capability for NoCapability {}

// Proof type — can only be constructed by CapabilityRegistry
pub struct Proof<C: Capability> { _marker: PhantomData<C> }

// Tool trait parameterized by capability
pub trait Tool<C: Capability>: Send + Sync + 'static {
    fn execute(_proof: Proof<C>, input: serde_json::Value)
        -> Result<serde_json::Value, crate::ToolError>;
}
```

### CapabilityRegistry

```rust
pub struct CapabilityRegistry {
    granted: HashSet<TypeId>,
}

impl CapabilityRegistry {
    pub fn grant<C: Capability>(&mut self);
    pub fn is_granted<C: Capability>(&self) -> bool;
    pub fn proof<C: Capability>(&self) -> Option<Proof<C>>;
    pub fn require<C: Capability>(&self) -> Proof<C>;  // panics if not granted
}
```

**Key design decisions:**
- `NoCapability` is always granted (represents no requirement)
- `Proof<C>` is `Copy + Clone + Default` but can only be constructed by the registry
- Combined capabilities via `ReadWriteFilesystem`, `ReadFilesystemOrNetwork`, `FullAccess` structs

### Pitfall: Naming collision with `Option::None`

When naming a "no capability" struct, `None` collides with `Option::None`.
**Fix**: Use `NoCapability` instead, and use `Option::None` explicitly in return
positions.

## State Machine Macro (`state_machine.rs`)

The `transitions!` macro generates a state machine with compile-time
exhaustiveness checking.

### Usage

```rust
transitions! {
    AgentState {
        Idle => [Compiling, Executing],
        Compiling => [Executing, Failed],
        Executing => [Verifying, Failed],
        Verifying => [Completed, Failed, Executing], // retry
        Failed => [Idle],  // reset
        Completed => [Idle],  // reset
    }
}
```

### Generated Code

- `AgentState` enum with all variants
- `can_transition(&self, target: &AgentState) -> bool` method
- `valid_targets(&self) -> &'static [AgentState]` method
- `StateMachine` struct with `new()`, `transition()`, `history()`, `is_terminal()`
- `Transition` struct with `from`, `to`, `timestamp`, `reason`
- `StateError` enum with `InvalidTransition { from, to }`
- `Default` impl uses the **first** variant (e.g., `Idle`)

### Pitfall: Default impl requires first variant to be `Idle`

The generated `Default` impl uses `$state_enum::Start` (or whatever the first
variant is). If your state machine doesn't have `Idle` as the first variant,
you must provide a custom `Default` impl.

## Policy Hook Typestate Markers (`policy.rs`)

Enforces that policy hooks are checked before privileged operations.

### Core Mechanism

```rust
// Policy hook markers
pub struct PreWrite; impl PolicyHook for PreWrite {}
pub struct PreExec; impl PolicyHook for PreExec {}
pub struct PreDispatch; impl PolicyHook for PreDispatch {}
pub struct PrePayment; impl PolicyHook for PrePayment {}
pub struct PreRead; impl PolicyHook for PreRead {}
pub struct PreCompile; impl PolicyHook for PreCompile {}

// Proof type
pub struct PolicyProof<H: PolicyHook> { _marker: PhantomData<H> }

// Policy enforcer
pub struct PolicyEnforcer { checker: Box<dyn PolicyChecker> }
impl PolicyEnforcer {
    pub fn check_write(&self, path: &str, content: &[u8])
        -> PolicyResult<PolicyProof<PreWrite>>;
    pub fn check_exec(&self, command: &str, args: &[&str])
        -> PolicyResult<PolicyProof<PreExec>>;
    pub fn check_dispatch(&self, url: &str, method: &str)
        -> PolicyResult<PolicyProof<PreDispatch>>;
    pub fn check_payment(&self, amount: f64, currency: &str, recipient: &str)
        -> PolicyResult<PolicyProof<PrePayment>>;
    // ...
}
```

### Policy-Gated Operations

```rust
pub struct WriteOperation<'a> { path: &'a str, content: &'a [u8] }
impl<'a> WriteOperation<'a> {
    pub fn perform(self, _proof: PolicyProof<PreWrite>) -> std::io::Result<()>;
}
```

The typestate pattern ensures you cannot call `perform()` without first
obtaining a `PolicyProof<PreWrite>` from the policy enforcer.

### Built-in Policy Checkers

- `AllowAllPolicy` — permits everything (for testing)
- `DenyAllPolicy` — denies everything (for testing)

### Pitfall: `PolicyProof` must implement `Debug`

Derive `Debug` manually since `PhantomData<H>` doesn't auto-derive when `H`
doesn't impl `Debug`:
```rust
impl<H: PolicyHook> std::fmt::Debug for PolicyProof<H> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("PolicyProof").finish()
    }
}
```

## Sovereignty Compile-Time Assertions (`sovereignty.rs`)

Provides macros and types for asserting sovereignty properties at compile time.

### Core Types

```rust
pub enum Ownership { Owned, Rented, Unset }
pub enum LayerId { Model, Harness, Compute, Identity, ShortTermMemory, LongTermKnowledge, Auth, Payments }

pub struct SovereigntyAsserter {
    layers: Vec<LayerState>,
}

impl SovereigntyAsserter {
    pub fn with_layer(mut self, layer: LayerId, ownership: Ownership) -> Self;
    pub fn assert_all_owned(&self) -> Result<(), SovereigntyError>;
    pub fn assert_score_above(&self, threshold: f64) -> Result<(), SovereigntyError>;
    pub fn calculate_score(&self) -> f64;
    pub fn owned_count(&self) -> usize;
    pub fn total_count(&self) -> usize;
}
```

### Type-Level Assertions

```rust
pub struct AssertOwned<Layer>(PhantomData<Layer>);
pub struct AssertRented<Layer>(PhantomData<Layer>);
pub struct AssertUnset<Layer>(PhantomData<Layer>);

pub type ModelOwned = AssertOwned<ModelLayer>;
pub type HarnessOwned = AssertOwned<HarnessLayer>;
pub type ComputeOwned = AssertOwned<ComputeLayer>;
pub type AuthOwned = AssertOwned<AuthLayer>;
```

### Macros

```rust
assert_sovereignty!(Harness, Owned);  // Compile-time check
assert_owned!(Model);                  // Shorthand
assert_rented!(Payments);              // Shorthand
```

## PyO3 Bindings (`sas-core-py`)

Exposes Rust types to Python via PyO3:

| Rust Type | Python Class | Notes |
|-----------|--------------|-------|
| `ExecutionContext` | `ExecutionContext` | Builder methods return `PyRefMut` for chaining |
| `AgentStateMachine` | `AgentStateMachine` | `transition()` takes string state name |
| `JsonSchema` | `JsonSchema` | Properties as list of tuples |
| `ValidationError` | `ValidationError` | Constructor takes `kind`, `field`, `expected`, `msg` |
| `ToolError` | `ToolError` | Constructor takes `kind`, `msg` |

**Important PyO3 patterns:**
- `#[pyo3(signature = (...))]` for constructors with optional args
- `Bound<'_, PyAny>` for generic Python values
- `PyRefMut<'_, Self>` for mutable self references in builder methods
- `extract::<String>()` for type conversion from Python

## Test Patterns

### Unit Tests (`sas-core-rs/tests/unit_tests.rs`)
- **execution_context_tests**: 4 tests for capability grants
- **agent_state_machine_tests**: 12 tests for valid/invalid transitions + history
- **validate_type_tests**: 7 tests for JSON type validation
- **schema_tests**: 3 tests for JSON Schema generation
- **capability_token_tests**: 1 test for Send+Sync bounds

### Integration Tests (`sas-core-rs/tests/integration_tests.rs`)
- **tool_trait_tests**: 11 tests for manual Tool impl (validate, execute, schema)
- **tool_registry_tests**: 1 test for multiple tool coexistence
- **state_machine_integration_tests**: 3 tests for full lifecycle, retry, recovery
- **error_display_tests**: 3 tests for error message formatting

### Capability Tests (in `capability.rs`)
- 5 tests: grant/check, proof generation, panic on missing, combined, no-capability

### State Machine Tests (in `state_machine.rs`)
- 6 tests: enum generation, state machine, invalid transition, history, valid targets

### Policy Tests (in `policy.rs`)
- 6 tests: allow-all, deny-all, proof consumption, error display

### Sovereignty Tests (in `sovereignty.rs`)
- 7 tests: layer tracking, all-owned, score-above, type-level assertions

**Key test patterns:**
- Use `serde_json::json!` macro for test input
- Test both success and error paths
- Verify state machine history records all transitions
- Test default values for optional fields
- Use `#[should_panic(expected = "...")]` for negative tests

## macOS Linking Pitfall

**Symptom**: `ld: symbol(s) not found for architecture arm64` — Python symbols
like `_PyBaseObject_Type`, `_PyBytes_AsString`, etc.

**Cause**: PyO3's build script can't find the Python shared library, or links
against the wrong one (system Python 3.9 vs homebrew Python 3.14).

**Fix**: `.cargo/config.toml` with explicit link flags:
```toml
[target.aarch64-apple-darwin]
rustflags = ["-C", "link-args=-L/opt/homebrew/opt/python@3.14/Frameworks/Python.framework/Versions/3.14/lib -lpython3.14"]
```

**Build command**:
```bash
PYO3_PYTHON=/opt/homebrew/bin/python3.14 cargo build --release -p sas-core-py
```

**Verification**:
```bash
cp target/release/libsas_core_py.dylib /tmp/sas/sas_core_py.so
/opt/homebrew/bin/python3.14 -c "import sas_core_py as sas; print(sas.ExecutionContext())"
```

## Verification Results (2026-09-04)

```
Rust tests:     68 passed (21 capability + 19 integration + 28 unit + 6 state_machine + 6 policy + 7 sovereignty)
Python interop:  sas_core_py module loaded — ExecutionContext, AgentStateMachine,
                ValidationError, ToolError all functional
Build:          release binary compiled (libsas_core_py.dylib)
```

## Next Steps (Not Yet Implemented)

1. **Tool registry**: Global registry that maps tool names to `Box<dyn Tool>`
2. **JSON Schema validation**: Use `jsonschema` crate for runtime validation
   against the generated schema
3. **Serde integration**: Derive `Serialize`/`Deserialize` for all types
4. **Async support**: `async fn execute()` for non-blocking tool execution
5. **WASM target**: Compile to WebAssembly for browser-based verification
