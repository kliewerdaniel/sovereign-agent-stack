//! Integration tests for sas-core-rs + sas-macros derive.

use sas_core_rs::{JsonSchema, SchemaProperty, Tool, ToolError, ValidationError};
use std::collections::HashMap;

// Example tools using the derive macro

#[derive(Clone)]
struct QueryKnowledgeInput {
    query: String,
    limit: u32,
}

impl QueryKnowledgeInput {
    fn run(&self) -> Result<serde_json::Value, ToolError> {
        Ok(serde_json::json!({
            "results": [],
            "query": self.query,
            "limit": self.limit
        }))
    }
}

// Manual Tool implementation (without derive, for testing)
impl Tool for QueryKnowledgeInput {
    fn name() -> &'static str {
        "query_knowledge"
    }

    fn description() -> &'static str {
        "Query the compile-time knowledge graph"
    }

    fn schema() -> JsonSchema {
        JsonSchema {
            name: "query_knowledge".to_string(),
            description: Some("Query the compile-time knowledge graph".to_string()),
            required: Some(vec!["query".to_string()]),
            properties: HashMap::from([
                ("query".to_string(), SchemaProperty {
                    ty: "string".to_string(),
                    description: Some("The search query".to_string()),
                    default: None,
                }),
                ("limit".to_string(), SchemaProperty {
                    ty: "integer".to_string(),
                    description: Some("Max results to return".to_string()),
                    default: Some(serde_json::json!(10)),
                }),
            ]),
        }
    }

    fn validate(input: &serde_json::Value) -> Result<(), ValidationError> {
        if input.get("query").is_none() {
            return Err(ValidationError::MissingField("query".to_string()));
        }
        let query = input.get("query").unwrap();
        if !query.is_string() {
            return Err(ValidationError::InvalidType {
                field: "query".to_string(),
                expected: "string".to_string(),
            });
        }
        if let Some(limit) = input.get("limit") {
            if !limit.is_u64() {
                return Err(ValidationError::InvalidType {
                    field: "limit".to_string(),
                    expected: "integer".to_string(),
                });
            }
        }
        Ok(())
    }

    fn execute(input: serde_json::Value) -> Result<serde_json::Value, ToolError> {
        Self::validate(&input)?;
        let query: String = serde_json::from_value(
            input.get("query").cloned().unwrap_or(serde_json::Value::Null)
        ).map_err(|e| ToolError::ParseError(e.to_string()))?;
        let limit: u32 = if let Some(v) = input.get("limit") {
            serde_json::from_value(v.clone()).map_err(|e| ToolError::ParseError(e.to_string()))?
        } else {
            10
        };
        let instance = Self { query, limit };
        instance.run()
    }
}

#[cfg(test)]
mod tool_trait_tests {
    use super::*;
    use sas_core_rs::schema_to_json;

    #[test]
    fn tool_name_is_snake_case() {
        assert_eq!(QueryKnowledgeInput::name(), "query_knowledge");
    }

    #[test]
    fn tool_description_matches() {
        assert_eq!(QueryKnowledgeInput::description(), "Query the compile-time knowledge graph");
    }

    #[test]
    fn tool_schema_has_required_fields() {
        let schema = QueryKnowledgeInput::schema();
        assert_eq!(schema.required.as_ref().unwrap(), &vec!["query".to_string()]);
    }

    #[test]
    fn tool_schema_properties_complete() {
        let schema = QueryKnowledgeInput::schema();
        assert!(schema.properties.contains_key("query"));
        assert!(schema.properties.contains_key("limit"));
        assert_eq!(schema.properties["query"].ty, "string");
        assert_eq!(schema.properties["limit"].ty, "integer");
    }

    #[test]
    fn validate_rejects_missing_required_field() {
        let input = serde_json::json!({"limit": 10});
        let result = QueryKnowledgeInput::validate(&input);
        assert!(result.is_err());
        match result.unwrap_err() {
            ValidationError::MissingField(field) => assert_eq!(field, "query"),
            _ => panic!("Expected MissingField error"),
        }
    }

    #[test]
    fn validate_rejects_wrong_type() {
        let input = serde_json::json!({"query": 123});
        let result = QueryKnowledgeInput::validate(&input);
        assert!(result.is_err());
    }

    #[test]
    fn validate_accepts_valid_input() {
        let input = serde_json::json!({"query": "test", "limit": 5});
        assert!(QueryKnowledgeInput::validate(&input).is_ok());
    }

    #[test]
    fn validate_accepts_input_without_optional() {
        let input = serde_json::json!({"query": "test"});
        assert!(QueryKnowledgeInput::validate(&input).is_ok());
    }

    #[test]
    fn execute_success_path() {
        let input = serde_json::json!({"query": "AI agents", "limit": 5});
        let result = QueryKnowledgeInput::execute(input).unwrap();
        assert_eq!(result["query"], "AI agents");
        assert_eq!(result["limit"], 5);
        assert!(result["results"].is_array());
    }

    #[test]
    fn execute_uses_default_for_optional() {
        let input = serde_json::json!({"query": "test"});
        let result = QueryKnowledgeInput::execute(input).unwrap();
        assert_eq!(result["limit"], 10);
    }

    #[test]
    fn execute_fails_on_invalid_input() {
        let input = serde_json::json!({"limit": 10});
        let result = QueryKnowledgeInput::execute(input);
        assert!(result.is_err());
    }

    #[test]
    fn schema_to_json_roundtrip() {
        let schema = QueryKnowledgeInput::schema();
        let json = schema_to_json(&schema);
        assert_eq!(json["type"], "object");
        assert_eq!(json["title"], "query_knowledge");
        assert!(json["required"].is_array());
        assert!(json["properties"].is_object());
    }
}

#[cfg(test)]
mod tool_registry_tests {
    use super::*;

    /// Test that multiple tools can coexist and be registered.
    #[test]
    fn multiple_tools_coexist() {
        let schema1 = QueryKnowledgeInput::schema();
        
        // Simulate another tool
        let schema2 = JsonSchema {
            name: "check_sovereignty".to_string(),
            description: Some("Check sovereignty score".to_string()),
            required: None,
            properties: HashMap::new(),
        };

        assert_ne!(schema1.name, schema2.name);
        assert_eq!(schema1.name, "query_knowledge");
        assert_eq!(schema2.name, "check_sovereignty");
    }
}

#[cfg(test)]
mod state_machine_integration_tests {
    use sas_core_rs::{AgentState, AgentStateMachine};

    /// Test a full happy-path execution lifecycle.
    #[test]
    fn full_execution_lifecycle() {
        let mut sm = AgentStateMachine::new();

        // Start
        assert_eq!(sm.current(), AgentState::Idle);
        
        // Begin compilation
        sm.transition(AgentState::Compiling, Some("New sources detected".to_string())).unwrap();
        assert_eq!(sm.current(), AgentState::Compiling);
        
        // Start executing
        sm.transition(AgentState::Executing, None).unwrap();
        assert_eq!(sm.current(), AgentState::Executing);
        
        // Verify results
        sm.transition(AgentState::Verifying, None).unwrap();
        assert_eq!(sm.current(), AgentState::Verifying);
        
        // Complete
        sm.transition(AgentState::Completed, None).unwrap();
        assert_eq!(sm.current(), AgentState::Completed);
        
        // Verify history
        assert_eq!(sm.history().len(), 4);
    }

    /// Test execution with retry.
    #[test]
    fn execution_with_retry() {
        let mut sm = AgentStateMachine::new();

        sm.transition(AgentState::Executing, None).unwrap();
        sm.transition(AgentState::Verifying, None).unwrap();
        // Verification failed, retry
        sm.transition(AgentState::Executing, Some("Retry after failure".to_string())).unwrap();
        sm.transition(AgentState::Verifying, None).unwrap();
        sm.transition(AgentState::Completed, None).unwrap();

        assert_eq!(sm.history().len(), 5);
    }

    /// Test execution failure and recovery.
    #[test]
    fn failure_and_recovery() {
        let mut sm = AgentStateMachine::new();

        sm.transition(AgentState::Executing, None).unwrap();
        sm.transition(AgentState::Failed, Some("Network error".to_string())).unwrap();
        assert_eq!(sm.current(), AgentState::Failed);
        
        sm.transition(AgentState::Idle, None).unwrap();
        assert_eq!(sm.current(), AgentState::Idle);
        
        // Try again
        sm.transition(AgentState::Executing, None).unwrap();
        sm.transition(AgentState::Verifying, None).unwrap();
        sm.transition(AgentState::Completed, None).unwrap();

        assert_eq!(sm.history().len(), 6);
    }
}

#[cfg(test)]
mod error_display_tests {
    use sas_core_rs::{AgentState, StateError, ToolError, ValidationError};

    #[test]
    fn validation_error_display() {
        let err = ValidationError::MissingField("query".to_string());
        assert!(format!("{}", err).contains("query"));
        
        let err = ValidationError::InvalidType {
            field: "limit".to_string(),
            expected: "integer".to_string(),
        };
        let msg = format!("{}", err);
        assert!(msg.contains("limit"));
        assert!(msg.contains("integer"));
    }

    #[test]
    fn tool_error_display() {
        let err = ToolError::ParseError("bad json".to_string());
        assert!(format!("{}", err).contains("bad json"));
        
        let err = ToolError::CapabilityDenied("read".to_string());
        assert!(format!("{}", err).contains("read"));
    }

    #[test]
    fn state_error_display() {
        let err = StateError::InvalidTransition {
            from: AgentState::Idle,
            to: AgentState::Completed,
        };
        let msg = format!("{}", err);
        assert!(msg.contains("Idle"));
        assert!(msg.contains("Completed"));
    }
}
