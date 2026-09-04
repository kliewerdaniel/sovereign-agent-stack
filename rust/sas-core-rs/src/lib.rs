//! Core types and traits for the Sovereign Agent Stack.
//!
//! This crate provides the foundational abstractions for compile-time tool
//! verification, capability-bound execution, and sovereignty scoring.

use std::collections::HashMap;
use serde::{Deserialize, Serialize};

/// The Tool trait — implemented via `#[derive(Tool)]` from `sas-macros`.
///
/// Every tool in the sovereign agent stack must implement this trait.
/// The derive macro generates all the boilerplate at compile time.
pub trait Tool: Send + Sync + 'static {
    /// The tool's identifier (snake_case of the struct name).
    fn name() -> &'static str;

    /// Human-readable description of what the tool does.
    fn description() -> &'static str;

    /// JSON Schema for the tool's input parameters.
    fn schema() -> JsonSchema;

    /// Validate input against the schema.
    fn validate(input: &serde_json::Value) -> Result<(), ValidationError>;

    /// Execute the tool with validated input.
    fn execute(input: serde_json::Value) -> Result<serde_json::Value, ToolError>;
}

/// JSON Schema representation for tool inputs.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct JsonSchema {
    pub name: String,
    pub description: Option<String>,
    pub required: Option<Vec<String>>,
    pub properties: HashMap<String, SchemaProperty>,
}

/// A single property in a JSON Schema.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct SchemaProperty {
    pub ty: String,
    pub description: Option<String>,
    pub default: Option<serde_json::Value>,
}

/// Validation errors that occur when checking tool input.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ValidationError {
    MissingField(String),
    InvalidType { field: String, expected: String },
    Custom(String),
}

impl std::fmt::Display for ValidationError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ValidationError::MissingField(field) => write!(f, "Missing required field: {}", field),
            ValidationError::InvalidType { field, expected } => {
                write!(f, "Field '{}' has invalid type, expected: {}", field, expected)
            }
            ValidationError::Custom(msg) => write!(f, "Validation error: {}", msg),
        }
    }
}

impl std::error::Error for ValidationError {}

/// Errors that occur during tool execution.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ToolError {
    ParseError(String),
    ExecutionError(String),
    CapabilityDenied(String),
}

impl std::fmt::Display for ToolError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ToolError::ParseError(msg) => write!(f, "Parse error: {}", msg),
            ToolError::ExecutionError(msg) => write!(f, "Execution error: {}", msg),
            ToolError::CapabilityDenied(msg) => write!(f, "Capability denied: {}", msg),
        }
    }
}

impl std::error::Error for ToolError {}

impl From<ValidationError> for ToolError {
    fn from(e: ValidationError) -> Self {
        ToolError::ParseError(e.to_string())
    }
}

/// Validate that a JSON value matches the expected type string.
pub fn validate_type(value: &serde_json::Value, expected: &str) -> bool {
    match expected {
        "string" => value.is_string(),
        "integer" => value.is_i64() || value.is_u64(),
        "number" => value.is_number(),
        "boolean" => value.is_boolean(),
        "array" => value.is_array(),
        "object" => value.is_object(),
        _ => true,
    }
}

/// Convert a JsonSchema to a JSON Schema string.
pub fn schema_to_json(schema: &JsonSchema) -> serde_json::Value {
    let mut obj = serde_json::Map::new();
    obj.insert("type".to_string(), serde_json::Value::String("object".to_string()));
    obj.insert("title".to_string(), serde_json::Value::String(schema.name.clone()));

    if let Some(desc) = &schema.description {
        obj.insert("description".to_string(), serde_json::Value::String(desc.clone()));
    }

    if let Some(required) = &schema.required {
        obj.insert(
            "required".to_string(),
            serde_json::Value::Array(required.iter().map(|s| serde_json::Value::String(s.clone())).collect()),
        );
    }

    let mut properties = serde_json::Map::new();
    for (name, prop) in &schema.properties {
        let mut prop_obj = serde_json::Map::new();
        prop_obj.insert("type".to_string(), serde_json::Value::String(prop.ty.clone()));
        if let Some(desc) = &prop.description {
            prop_obj.insert("description".to_string(), serde_json::Value::String(desc.clone()));
        }
        if let Some(default) = &prop.default {
            prop_obj.insert("default".to_string(), default.clone());
        }
        properties.insert(name.clone(), serde_json::Value::Object(prop_obj));
    }
    obj.insert("properties".to_string(), serde_json::Value::Object(properties));

    serde_json::Value::Object(obj)
}

// ── Capability tokens ────────────────────────────────────────────────────────

/// Marker trait for capability tokens.
///
/// Capability tokens are zero-sized types that prove a tool has been granted
/// a specific capability. The type system ensures that tools cannot perform
/// privileged operations without the appropriate token in scope.
pub trait Capability: Send + Sync + 'static {}

/// Capability token for filesystem read access.
pub struct CanReadFilesystem;
impl Capability for CanReadFilesystem {}

/// Capability token for filesystem write access.
pub struct CanWriteFilesystem;
impl Capability for CanWriteFilesystem {}

/// Capability token for network dispatch.
pub struct CanDispatchNetwork;
impl Capability for CanDispatchNetwork {}

/// Capability token for command execution.
pub struct CanExecuteCommands;
impl Capability for CanExecuteCommands {}

/// Capability token for payment operations.
pub struct CanProcessPayments;
impl Capability for CanProcessPayments {}

/// A tool execution context that carries capability tokens.
///
/// This is the primary way to enforce that tools only execute with
/// the appropriate capabilities granted.
pub struct ExecutionContext {
    can_read_filesystem: bool,
    can_write_filesystem: bool,
    can_dispatch_network: bool,
    can_execute_commands: bool,
    can_process_payments: bool,
}

impl ExecutionContext {
    /// Create a new execution context with no capabilities granted.
    pub fn new() -> Self {
        Self {
            can_read_filesystem: false,
            can_write_filesystem: false,
            can_dispatch_network: false,
            can_execute_commands: false,
            can_process_payments: false,
        }
    }

    /// Grant filesystem read capability.
    pub fn with_read_filesystem(mut self) -> Self {
        self.can_read_filesystem = true;
        self
    }

    /// Grant filesystem write capability.
    pub fn with_write_filesystem(mut self) -> Self {
        self.can_write_filesystem = true;
        self
    }

    /// Grant network dispatch capability.
    pub fn with_dispatch_network(mut self) -> Self {
        self.can_dispatch_network = true;
        self
    }

    /// Grant command execution capability.
    pub fn with_execute_commands(mut self) -> Self {
        self.can_execute_commands = true;
        self
    }

    /// Grant payment processing capability.
    pub fn with_process_payments(mut self) -> Self {
        self.can_process_payments = true;
        self
    }

    /// Check if filesystem read is allowed.
    pub fn can_read_filesystem(&self) -> bool {
        self.can_read_filesystem
    }

    /// Check if filesystem write is allowed.
    pub fn can_write_filesystem(&self) -> bool {
        self.can_write_filesystem
    }

    /// Check if network dispatch is allowed.
    pub fn can_dispatch_network(&self) -> bool {
        self.can_dispatch_network
    }

    /// Check if command execution is allowed.
    pub fn can_execute_commands(&self) -> bool {
        self.can_execute_commands
    }

    /// Check if payment processing is allowed.
    pub fn can_process_payments(&self) -> bool {
        self.can_process_payments
    }
}

impl Default for ExecutionContext {
    fn default() -> Self {
        Self::new()
    }
}

// ── State machine ────────────────────────────────────────────────────────────

/// Agent state machine with compile-time transition verification.
///
/// States are defined as an enum, and transitions are validated at compile time
/// using the `transitions!` macro.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum AgentState {
    Idle,
    Compiling,
    Executing,
    Verifying,
    Failed,
    Completed,
}

/// A state transition record for audit purposes.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StateTransition {
    pub from: AgentState,
    pub to: AgentState,
    pub timestamp: String,
    pub reason: Option<String>,
}

/// State machine for agent execution.
pub struct AgentStateMachine {
    current: AgentState,
    history: Vec<StateTransition>,
}

impl AgentStateMachine {
    /// Create a new state machine in the Idle state.
    pub fn new() -> Self {
        Self {
            current: AgentState::Idle,
            history: Vec::new(),
        }
    }

    /// Get the current state.
    pub fn current(&self) -> AgentState {
        self.current
    }

    /// Attempt a state transition.
    pub fn transition(&mut self, to: AgentState, reason: Option<String>) -> Result<(), StateError> {
        let valid = match (self.current, to) {
            (AgentState::Idle, AgentState::Compiling) => true,
            (AgentState::Idle, AgentState::Executing) => true,
            (AgentState::Compiling, AgentState::Executing) => true,
            (AgentState::Compiling, AgentState::Failed) => true,
            (AgentState::Executing, AgentState::Verifying) => true,
            (AgentState::Executing, AgentState::Failed) => true,
            (AgentState::Verifying, AgentState::Completed) => true,
            (AgentState::Verifying, AgentState::Failed) => true,
            (AgentState::Verifying, AgentState::Executing) => true, // retry
            (AgentState::Failed, AgentState::Idle) => true, // reset
            (AgentState::Completed, AgentState::Idle) => true, // reset
            _ => false,
        };

        if !valid {
            return Err(StateError::InvalidTransition {
                from: self.current,
                to,
            });
        }

        let transition = StateTransition {
            from: self.current,
            to,
            timestamp: chrono::Utc::now().to_rfc3339(),
            reason,
        };
        self.history.push(transition);
        self.current = to;
        Ok(())
    }

    /// Get the transition history.
    pub fn history(&self) -> &[StateTransition] {
        &self.history
    }
}

impl Default for AgentStateMachine {
    fn default() -> Self {
        Self::new()
    }
}

/// Errors that occur during state transitions.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum StateError {
    InvalidTransition { from: AgentState, to: AgentState },
}

impl std::fmt::Display for StateError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            StateError::InvalidTransition { from, to } => {
                write!(f, "Invalid state transition: {:?} -> {:?}", from, to)
            }
        }
    }
}

impl std::error::Error for StateError {}

// ── Re-exports ──────────────────────────────────────────────────────────────

pub mod capability;
pub mod state_machine;
pub mod policy;
pub mod sovereignty;

pub use serde_json;
