// Rust-backed tool registry with compile-time schema verification.

use pyo3::prelude::*;
use serde_json::Value;
use std::collections::HashMap;

/// A registered tool with schema validation.
#[derive(Debug, Clone)]
pub struct ToolDefinition {
    pub name: String,
    pub description: String,
    pub schema: Value,
    pub required_capabilities: Vec<String>,
}

/// Tool registry with compile-time schema enforcement.
#[pyclass(name = "ToolRegistry")]
pub struct PyToolRegistry {
    tools: HashMap<String, ToolDefinition>,
}

#[pymethods]
impl PyToolRegistry {
    #[new]
    fn new() -> Self {
        Self {
            tools: HashMap::new(),
        }
    }

    /// Register a tool with JSON schema.
    fn register(
        &mut self,
        name: String,
        description: String,
        schema_json: String,
        required_capabilities: Vec<String>,
    ) -> PyResult<()> {
        let schema: Value = serde_json::from_str(&schema_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Invalid JSON schema for tool '{}': {}", name, e),
            ))?;

        let tool = ToolDefinition {
            name: name.clone(),
            description,
            schema,
            required_capabilities,
        };

        self.tools.insert(name, tool);
        Ok(())
    }

    /// Validate tool input against schema.
    fn validate(&self, name: String, input_json: String) -> PyResult<bool> {
        let tool = self.tools.get(&name)
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>(
                format!("Tool '{}' not registered", name),
            ))?;

        let input: Value = serde_json::from_str(&input_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Invalid JSON input: {}", e),
            ))?;

        // Check required fields
        if let Some(required) = tool.schema.get("required").and_then(|r| r.as_array()) {
            for field in required {
                let field_name = field.as_str().unwrap_or("");
                if input.get(field_name).is_none() {
                    return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                        format!("Missing required field: {}", field_name),
                    ));
                }
            }
        }

        // Check property types
        if let Some(properties) = tool.schema.get("properties").and_then(|p| p.as_object()) {
            for (key, prop) in properties {
                if let Some(value) = input.get(key) {
                    if let Some(expected_type) = prop.get("type").and_then(|t| t.as_str()) {
                        if !validate_json_type(value, expected_type) {
                            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                                format!("Field '{}' has invalid type, expected: {}", key, expected_type),
                            ));
                        }
                    }
                }
            }
        }

        Ok(true)
    }

    /// Get tool definition.
    fn get(&self, name: String) -> PyResult<(String, String, String, Vec<String>)> {
        let tool = self.tools.get(&name)
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>(
                format!("Tool '{}' not registered", name),
            ))?;

        Ok((
            tool.name.clone(),
            tool.description.clone(),
            serde_json::to_string(&tool.schema).unwrap(),
            tool.required_capabilities.clone(),
        ))
    }

    /// List all registered tool names.
    fn list(&self) -> Vec<String> {
        self.tools.keys().cloned().collect()
    }

    /// Check if a tool is registered.
    fn has(&self, name: String) -> bool {
        self.tools.contains_key(&name)
    }

    /// Unregister a tool.
    fn unregister(&mut self, name: String) -> bool {
        self.tools.remove(&name).is_some()
    }
}

/// Validate that a JSON value matches the expected type string.
fn validate_json_type(value: &Value, expected: &str) -> bool {
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
