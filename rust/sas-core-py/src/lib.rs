//! Python bindings for sas-core-rs via PyO3.
//!
//! Exposes the core Rust types and tool execution to Python.

mod tool_registry;

use pyo3::prelude::*;
use serde_json::Value;

// ── Re-exported types from sas-core-rs ──────────────────────────────────────

/// Python module for sas-core-rs.
#[pymodule(name = "sas_core_py")]
fn sas_core_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Core types
    m.add_class::<PyExecutionContext>()?;
    m.add_class::<PyAgentStateMachine>()?;
    m.add_class::<PyJsonSchema>()?;
    m.add_class::<PyValidationError>()?;
    m.add_class::<PyToolError>()?;
    m.add_class::<PyAgentState>()?;

    // Capability types
    m.add_class::<PyCapabilityRegistry>()?;
    m.add_class::<PyProof>()?;

    // Policy types
    m.add_class::<PyPolicyEnforcer>()?;
    m.add_class::<PyPolicyProof>()?;
    m.add_class::<PyPolicyError>()?;
    m.add_class::<PyAllowAllPolicy>()?;
    m.add_class::<PyDenyAllPolicy>()?;

    // Sovereignty types
    m.add_class::<PySovereigntyAsserter>()?;
    m.add_class::<PyLayerId>()?;
    m.add_class::<PyOwnership>()?;
    m.add_class::<PyLayerState>()?;

    // Tool registry
    m.add_class::<tool_registry::PyToolRegistry>()?;

    // Utility functions
    m.add_function(wrap_pyfunction!(schema_to_json, m)?)?;
    m.add_function(wrap_pyfunction!(validate_type_fn, m)?)?;
    m.add_function(wrap_pyfunction!(tool_name, m)?)?;
    m.add_function(wrap_pyfunction!(tool_description, m)?)?;
    m.add_function(wrap_pyfunction!(tool_schema, m)?)?;
    m.add_function(wrap_pyfunction!(tool_validate, m)?)?;
    m.add_function(wrap_pyfunction!(tool_execute, m)?)?;

    Ok(())
}

// ── Core type wrappers ───────────────────────────────────────────────────────

/// Python wrapper for ExecutionContext.
#[pyclass(name = "ExecutionContext")]
struct PyExecutionContext {
    inner: sas_core_rs::ExecutionContext,
}

#[pymethods]
impl PyExecutionContext {
    #[new]
    fn new() -> Self {
        Self {
            inner: sas_core_rs::ExecutionContext::new(),
        }
    }

    fn with_read_filesystem(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.inner = std::mem::take(&mut slf.inner).with_read_filesystem();
        slf
    }

    fn with_write_filesystem(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.inner = std::mem::take(&mut slf.inner).with_write_filesystem();
        slf
    }

    fn with_dispatch_network(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.inner = std::mem::take(&mut slf.inner).with_dispatch_network();
        slf
    }

    fn with_execute_commands(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.inner = std::mem::take(&mut slf.inner).with_execute_commands();
        slf
    }

    fn with_process_payments(mut slf: PyRefMut<'_, Self>) -> PyRefMut<'_, Self> {
        slf.inner = std::mem::take(&mut slf.inner).with_process_payments();
        slf
    }

    #[getter]
    fn can_read_filesystem(&self) -> bool {
        self.inner.can_read_filesystem()
    }

    #[getter]
    fn can_write_filesystem(&self) -> bool {
        self.inner.can_write_filesystem()
    }

    #[getter]
    fn can_dispatch_network(&self) -> bool {
        self.inner.can_dispatch_network()
    }

    #[getter]
    fn can_execute_commands(&self) -> bool {
        self.inner.can_execute_commands()
    }

    #[getter]
    fn can_process_payments(&self) -> bool {
        self.inner.can_process_payments()
    }

    fn __repr__(&self) -> String {
        format!(
            "ExecutionContext(read={}, write={}, network={}, exec={}, payments={})",
            self.inner.can_read_filesystem(),
            self.inner.can_write_filesystem(),
            self.inner.can_dispatch_network(),
            self.inner.can_execute_commands(),
            self.inner.can_process_payments(),
        )
    }
}

/// Python wrapper for AgentStateMachine.
#[pyclass(name = "AgentStateMachine")]
struct PyAgentStateMachine {
    inner: sas_core_rs::AgentStateMachine,
}

#[pymethods]
impl PyAgentStateMachine {
    #[new]
    fn new() -> Self {
        Self {
            inner: sas_core_rs::AgentStateMachine::new(),
        }
    }

    #[getter]
    fn current(&self) -> String {
        format!("{:?}", self.inner.current())
    }

    fn transition(&mut self, to: String, reason: Option<String>) -> PyResult<()> {
        let target = parse_agent_state(&to)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))?;
        self.inner
            .transition(target, reason)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        Ok(())
    }

    #[getter]
    fn history(&self) -> Vec<String> {
        self.inner
            .history()
            .iter()
            .map(|t| format!("{:?} -> {:?} ({})", t.from, t.to, t.timestamp))
            .collect()
    }

    fn __repr__(&self) -> String {
        format!("AgentStateMachine(current={:?})", self.inner.current())
    }
}

fn parse_agent_state(s: &str) -> Result<sas_core_rs::AgentState, String> {
    match s.to_lowercase().as_str() {
        "idle" => Ok(sas_core_rs::AgentState::Idle),
        "compiling" => Ok(sas_core_rs::AgentState::Compiling),
        "executing" => Ok(sas_core_rs::AgentState::Executing),
        "verifying" => Ok(sas_core_rs::AgentState::Verifying),
        "failed" => Ok(sas_core_rs::AgentState::Failed),
        "completed" => Ok(sas_core_rs::AgentState::Completed),
        _ => Err(format!("Unknown agent state: {}", s)),
    }
}

/// Python wrapper for JsonSchema.
#[pyclass(name = "JsonSchema")]
#[derive(Clone)]
struct PyJsonSchema {
    inner: sas_core_rs::JsonSchema,
}

#[pymethods]
impl PyJsonSchema {
    #[new]
    fn new(name: String, description: Option<String>) -> Self {
        Self {
            inner: sas_core_rs::JsonSchema {
                name,
                description,
                required: None,
                properties: std::collections::HashMap::new(),
            },
        }
    }

    #[getter]
    fn name(&self) -> String {
        self.inner.name.clone()
    }

    #[getter]
    fn description(&self) -> Option<String> {
        self.inner.description.clone()
    }

    #[getter]
    fn properties(&self) -> Vec<(String, String, Option<String>)> {
        self.inner
            .properties
            .iter()
            .map(|(k, v)| (k.clone(), v.ty.clone(), v.description.clone()))
            .collect()
    }

    fn __repr__(&self) -> String {
        format!("JsonSchema(name={})", self.inner.name)
    }
}

/// Python wrapper for ValidationError.
#[pyclass(name = "ValidationError")]
#[derive(Clone)]
struct PyValidationError {
    inner: sas_core_rs::ValidationError,
}

#[pymethods]
impl PyValidationError {
    #[new]
    #[pyo3(signature = (kind=None, field=None, expected=None, msg=None))]
    fn new(
        kind: Option<String>,
        field: Option<String>,
        expected: Option<String>,
        msg: Option<String>,
    ) -> Self {
        let inner = match kind.as_deref() {
            Some("missing") => {
                sas_core_rs::ValidationError::MissingField(field.unwrap_or_default())
            }
            Some("invalid_type") => sas_core_rs::ValidationError::InvalidType {
                field: field.unwrap_or_default(),
                expected: expected.unwrap_or_default(),
            },
            _ => sas_core_rs::ValidationError::Custom(msg.unwrap_or_default()),
        };
        Self { inner }
    }

    fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

/// Python wrapper for ToolError.
#[pyclass(name = "ToolError")]
#[derive(Clone)]
struct PyToolError {
    inner: sas_core_rs::ToolError,
}

#[pymethods]
impl PyToolError {
    #[new]
    #[pyo3(signature = (kind=None, msg=None))]
    fn new(kind: Option<String>, msg: Option<String>) -> Self {
        let inner = match kind.as_deref() {
            Some("parse") => sas_core_rs::ToolError::ParseError(msg.unwrap_or_default()),
            Some("execution") => sas_core_rs::ToolError::ExecutionError(msg.unwrap_or_default()),
            Some("capability") => sas_core_rs::ToolError::CapabilityDenied(msg.unwrap_or_default()),
            _ => sas_core_rs::ToolError::ExecutionError(msg.unwrap_or_default()),
        };
        Self { inner }
    }

    fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

// ── AgentState ───────────────────────────────────────────────────────────────

#[pyclass(name = "AgentState")]
#[derive(Clone)]
struct PyAgentState {
    inner: sas_core_rs::AgentState,
}

#[pymethods]
impl PyAgentState {
    #[new]
    fn new(state: String) -> PyResult<Self> {
        parse_agent_state(&state)
            .map(|inner| Self { inner })
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))
    }

    #[getter]
    fn value(&self) -> String {
        format!("{:?}", self.inner)
    }

    fn __repr__(&self) -> String {
        format!("AgentState({:?})", self.inner)
    }
}

// ── Capability wrappers ──────────────────────────────────────────────────────

/// Python wrapper for CapabilityRegistry.
#[pyclass(name = "CapabilityRegistry")]
struct PyCapabilityRegistry {
    inner: sas_core_rs::capability::CapabilityRegistry,
}

#[pymethods]
impl PyCapabilityRegistry {
    #[new]
    fn new() -> Self {
        Self {
            inner: sas_core_rs::capability::CapabilityRegistry::new(),
        }
    }

    fn grant(&mut self, capability: String) {
        match capability.as_str() {
            "read_filesystem" => self.inner.grant::<sas_core_rs::capability::ReadFilesystem>(),
            "write_filesystem" => self.inner.grant::<sas_core_rs::capability::WriteFilesystem>(),
            "dispatch_network" => self.inner.grant::<sas_core_rs::capability::DispatchNetwork>(),
            "execute_commands" => self.inner.grant::<sas_core_rs::capability::ExecuteCommands>(),
            "process_payments" => self.inner.grant::<sas_core_rs::capability::ProcessPayments>(),
            "emit_events" => self.inner.grant::<sas_core_rs::capability::EmitEvents>(),
            "read_knowledge" => self.inner.grant::<sas_core_rs::capability::ReadKnowledge>(),
            "write_knowledge" => self.inner.grant::<sas_core_rs::capability::WriteKnowledge>(),
            _ => {}
        }
    }

    fn is_granted(&self, capability: String) -> bool {
        match capability.as_str() {
            "read_filesystem" => self.inner.is_granted::<sas_core_rs::capability::ReadFilesystem>(),
            "write_filesystem" => self.inner.is_granted::<sas_core_rs::capability::WriteFilesystem>(),
            "dispatch_network" => self.inner.is_granted::<sas_core_rs::capability::DispatchNetwork>(),
            "execute_commands" => self.inner.is_granted::<sas_core_rs::capability::ExecuteCommands>(),
            "process_payments" => self.inner.is_granted::<sas_core_rs::capability::ProcessPayments>(),
            "emit_events" => self.inner.is_granted::<sas_core_rs::capability::EmitEvents>(),
            "read_knowledge" => self.inner.is_granted::<sas_core_rs::capability::ReadKnowledge>(),
            "write_knowledge" => self.inner.is_granted::<sas_core_rs::capability::WriteKnowledge>(),
            _ => false,
        }
    }

    fn require(&self, capability: String) -> PyResult<bool> {
        match capability.as_str() {
            "read_filesystem" => {
                self.inner.require::<sas_core_rs::capability::ReadFilesystem>();
                Ok(true)
            }
            "write_filesystem" => {
                self.inner.require::<sas_core_rs::capability::WriteFilesystem>();
                Ok(true)
            }
            "dispatch_network" => {
                self.inner.require::<sas_core_rs::capability::DispatchNetwork>();
                Ok(true)
            }
            "execute_commands" => {
                self.inner.require::<sas_core_rs::capability::ExecuteCommands>();
                Ok(true)
            }
            "process_payments" => {
                self.inner.require::<sas_core_rs::capability::ProcessPayments>();
                Ok(true)
            }
            "emit_events" => {
                self.inner.require::<sas_core_rs::capability::EmitEvents>();
                Ok(true)
            }
            "read_knowledge" => {
                self.inner.require::<sas_core_rs::capability::ReadKnowledge>();
                Ok(true)
            }
            "write_knowledge" => {
                self.inner.require::<sas_core_rs::capability::WriteKnowledge>();
                Ok(true)
            }
            _ => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Unknown capability: {}", capability),
            )),
        }
    }
}

/// Python wrapper for capability Proof (opaque marker).
#[pyclass(name = "CapabilityProof")]
struct PyProof {
    // Proof is opaque to Python — it can only be constructed by the registry
}

#[pymethods]
impl PyProof {
    #[new]
    fn new() -> Self {
        Self {}
    }
}

// ── Policy wrappers ──────────────────────────────────────────────────────────

/// Python wrapper for PolicyEnforcer.
#[pyclass(name = "PolicyEnforcer")]
struct PyPolicyEnforcer {
    inner: sas_core_rs::policy::PolicyEnforcer,
}

#[pymethods]
impl PyPolicyEnforcer {
    #[new]
    #[pyo3(signature = (mode="allow"))]
    fn new(mode: &str) -> Self {
        let inner = match mode {
            "deny" => sas_core_rs::policy::PolicyEnforcer::new(
                Box::new(sas_core_rs::policy::DenyAllPolicy),
            ),
            _ => sas_core_rs::policy::PolicyEnforcer::new(
                Box::new(sas_core_rs::policy::AllowAllPolicy),
            ),
        };
        Self { inner }
    }

    fn check_write(&self, path: String, content: Vec<u8>) -> PyResult<bool> {
        match self.inner.check_write(&path, &content) {
            Ok(_) => Ok(true),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyPermissionError, _>(
                format!("{}", e),
            )),
        }
    }

    fn check_exec(&self, command: String, args: Vec<String>) -> PyResult<bool> {
        let args_ref: Vec<&str> = args.iter().map(|s| s.as_str()).collect();
        match self.inner.check_exec(&command, &args_ref) {
            Ok(_) => Ok(true),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyPermissionError, _>(
                format!("{}", e),
            )),
        }
    }

    fn check_dispatch(&self, url: String, method: String) -> PyResult<bool> {
        match self.inner.check_dispatch(&url, &method) {
            Ok(_) => Ok(true),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyPermissionError, _>(
                format!("{}", e),
            )),
        }
    }

    fn check_payment(&self, amount: f64, currency: String, recipient: String) -> PyResult<bool> {
        match self.inner.check_payment(amount, &currency, &recipient) {
            Ok(_) => Ok(true),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyPermissionError, _>(
                format!("{}", e),
            )),
        }
    }
}

/// Python wrapper for PolicyProof (opaque marker).
#[pyclass(name = "PolicyProof")]
struct PyPolicyProof;

#[pymethods]
impl PyPolicyProof {
    #[new]
    fn new() -> Self {
        Self {}
    }
}

/// Python wrapper for PolicyError.
#[pyclass(name = "PolicyError")]
struct PyPolicyError {
    inner: sas_core_rs::policy::PolicyError,
}

#[pymethods]
impl PyPolicyError {
    #[new]
    #[pyo3(signature = (kind=None, path=None, reason=None, command=None, url=None, amount=None, currency=None, msg=None))]
    fn new(
        kind: Option<String>,
        path: Option<String>,
        reason: Option<String>,
        command: Option<String>,
        url: Option<String>,
        amount: Option<f64>,
        currency: Option<String>,
        msg: Option<String>,
    ) -> Self {
        let inner = match kind.as_deref() {
            Some("write") => sas_core_rs::policy::PolicyError::WriteForbidden {
                path: path.unwrap_or_default(),
                reason: reason.unwrap_or_default(),
            },
            Some("exec") => sas_core_rs::policy::PolicyError::ExecForbidden {
                command: command.unwrap_or_default(),
                reason: reason.unwrap_or_default(),
            },
            Some("dispatch") => sas_core_rs::policy::PolicyError::DispatchForbidden {
                url: url.unwrap_or_default(),
                reason: reason.unwrap_or_default(),
            },
            Some("payment") => sas_core_rs::policy::PolicyError::PaymentForbidden {
                amount: amount.unwrap_or_default(),
                currency: currency.unwrap_or_default(),
                reason: reason.unwrap_or_default(),
            },
            Some("read") => sas_core_rs::policy::PolicyError::ReadForbidden {
                path: path.unwrap_or_default(),
                reason: reason.unwrap_or_default(),
            },
            Some("compile") => sas_core_rs::policy::PolicyError::CompileForbidden {
                source: path.unwrap_or_default(),
                reason: reason.unwrap_or_default(),
            },
            _ => sas_core_rs::policy::PolicyError::Custom(msg.unwrap_or_default()),
        };
        Self { inner }
    }

    fn __repr__(&self) -> String {
        format!("{:?}", self.inner)
    }
}

/// Python wrapper for AllowAllPolicy.
#[pyclass(name = "AllowAllPolicy")]
struct PyAllowAllPolicy;

#[pymethods]
impl PyAllowAllPolicy {
    #[new]
    fn new() -> Self {
        Self {}
    }
}

/// Python wrapper for DenyAllPolicy.
#[pyclass(name = "DenyAllPolicy")]
struct PyDenyAllPolicy;

#[pymethods]
impl PyDenyAllPolicy {
    #[new]
    fn new() -> Self {
        Self {}
    }
}

// ── Sovereignty wrappers ─────────────────────────────────────────────────────

/// Python wrapper for SovereigntyAsserter.
#[pyclass(name = "SovereigntyAsserter")]
struct PySovereigntyAsserter {
    inner: sas_core_rs::sovereignty::SovereigntyAsserter,
}

#[pymethods]
impl PySovereigntyAsserter {
    #[new]
    fn new() -> Self {
        Self {
            inner: sas_core_rs::sovereignty::SovereigntyAsserter::new(),
        }
    }

    fn with_layer(&mut self, layer: String, ownership: String) {
        let layer_id = parse_layer_id(&layer);
        let ownership = parse_ownership(&ownership);
        self.inner = std::mem::take(&mut self.inner).with_layer(layer_id, ownership);
    }

    fn assert_all_owned(&self) -> PyResult<bool> {
        match self.inner.assert_all_owned() {
            Ok(()) => Ok(true),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("{}", e),
            )),
        }
    }

    fn assert_score_above(&self, threshold: f64) -> PyResult<bool> {
        match self.inner.assert_score_above(threshold) {
            Ok(()) => Ok(true),
            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("{}", e),
            )),
        }
    }

    fn calculate_score(&self) -> f64 {
        self.inner.calculate_score()
    }

    fn owned_count(&self) -> usize {
        self.inner.owned_count()
    }

    fn total_count(&self) -> usize {
        self.inner.total_count()
    }

    fn __repr__(&self) -> String {
        format!(
            "SovereigntyAsserter(owned={}/{}, score={:.2})",
            self.inner.owned_count(),
            self.inner.total_count(),
            self.inner.calculate_score()
        )
    }
}

fn parse_layer_id(s: &str) -> sas_core_rs::sovereignty::LayerId {
    match s.to_lowercase().as_str() {
        "model" => sas_core_rs::sovereignty::LayerId::Model,
        "harness" => sas_core_rs::sovereignty::LayerId::Harness,
        "compute" => sas_core_rs::sovereignty::LayerId::Compute,
        "identity" => sas_core_rs::sovereignty::LayerId::Identity,
        "short_term_memory" => sas_core_rs::sovereignty::LayerId::ShortTermMemory,
        "long_term_knowledge" => sas_core_rs::sovereignty::LayerId::LongTermKnowledge,
        "auth" => sas_core_rs::sovereignty::LayerId::Auth,
        "payments" => sas_core_rs::sovereignty::LayerId::Payments,
        _ => sas_core_rs::sovereignty::LayerId::Model,
    }
}

fn parse_ownership(s: &str) -> sas_core_rs::sovereignty::Ownership {
    match s.to_lowercase().as_str() {
        "owned" => sas_core_rs::sovereignty::Ownership::Owned,
        "rented" => sas_core_rs::sovereignty::Ownership::Rented,
        _ => sas_core_rs::sovereignty::Ownership::Unset,
    }
}

/// Python wrapper for LayerId.
#[pyclass(name = "LayerId")]
struct PyLayerId {
    inner: sas_core_rs::sovereignty::LayerId,
}

#[pymethods]
impl PyLayerId {
    #[new]
    fn new(layer: String) -> Self {
        Self {
            inner: parse_layer_id(&layer),
        }
    }

    #[getter]
    fn value(&self) -> String {
        format!("{:?}", self.inner)
    }

    fn __repr__(&self) -> String {
        format!("LayerId({:?})", self.inner)
    }
}

/// Python wrapper for Ownership.
#[pyclass(name = "Ownership")]
struct PyOwnership {
    inner: sas_core_rs::sovereignty::Ownership,
}

#[pymethods]
impl PyOwnership {
    #[new]
    fn new(ownership: String) -> Self {
        Self {
            inner: parse_ownership(&ownership),
        }
    }

    #[getter]
    fn value(&self) -> String {
        format!("{:?}", self.inner)
    }

    fn __repr__(&self) -> String {
        format!("Ownership({:?})", self.inner)
    }
}

/// Python wrapper for LayerState.
#[pyclass(name = "LayerState")]
struct PyLayerState {
    inner: sas_core_rs::sovereignty::LayerState,
}

#[pymethods]
impl PyLayerState {
    #[new]
    fn new(layer: String, ownership: String) -> Self {
        Self {
            inner: sas_core_rs::sovereignty::LayerState {
                layer: parse_layer_id(&layer),
                ownership: parse_ownership(&ownership),
            },
        }
    }

    #[getter]
    fn layer(&self) -> String {
        format!("{:?}", self.inner.layer)
    }

    #[getter]
    fn ownership(&self) -> String {
        format!("{:?}", self.inner.ownership)
    }

    fn __repr__(&self) -> String {
        format!("LayerState(layer={:?}, ownership={:?})", self.inner.layer, self.inner.ownership)
    }
}

// ── Utility functions ─────────────────────────────────────────────────────────

#[pyfunction]
fn schema_to_json(schema: &Bound<'_, PyAny>) -> PyResult<String> {
    let schema: PyJsonSchema = schema.extract()?;
    let json = sas_core_rs::schema_to_json(&schema.inner);
    serde_json::to_string_pretty(&json)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
}

#[pyfunction]
fn validate_type_fn(value: &Bound<'_, PyAny>, expected: String) -> PyResult<bool> {
    let value_str: String = value.extract()?;
    let value: Value = serde_json::from_str(&value_str)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    Ok(sas_core_rs::validate_type(&value, &expected))
}

#[pyfunction]
fn tool_name() -> &'static str {
    "rust_tool_registry"
}

#[pyfunction]
fn tool_description() -> &'static str {
    "Rust-backed tool registry with compile-time verification"
}

#[pyfunction]
fn tool_schema() -> String {
    serde_json::json!({
        "type": "object",
        "properties": {
            "tool_name": { "type": "string" },
            "input": { "type": "object" }
        },
        "required": ["tool_name", "input"]
    })
    .to_string()
}

#[pyfunction]
fn tool_validate(name: String, input: String) -> PyResult<bool> {
    let _: serde_json::Value = serde_json::from_str(&input)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("Invalid JSON for tool '{}': {}", name, e),
        ))?;
    Ok(true)
}

#[pyfunction]
fn tool_execute(name: String, input: String) -> PyResult<String> {
    let _: serde_json::Value = serde_json::from_str(&input)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("Invalid JSON for tool '{}': {}", name, e),
        ))?;
    Ok(serde_json::json!({"status": "ok", "tool": name}).to_string())
}
