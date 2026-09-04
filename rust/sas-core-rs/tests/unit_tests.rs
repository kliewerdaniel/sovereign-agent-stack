//! Unit tests for sas-core-rs.

#[cfg(test)]
mod execution_context_tests {
    use sas_core_rs::ExecutionContext;

    #[test]
    fn new_context_has_no_capabilities() {
        let ctx = ExecutionContext::new();
        assert!(!ctx.can_read_filesystem());
        assert!(!ctx.can_write_filesystem());
        assert!(!ctx.can_dispatch_network());
        assert!(!ctx.can_execute_commands());
        assert!(!ctx.can_process_payments());
    }

    #[test]
    fn builder_pattern_grants_capabilities() {
        let ctx = ExecutionContext::new()
            .with_read_filesystem()
            .with_write_filesystem()
            .with_dispatch_network()
            .with_execute_commands()
            .with_process_payments();

        assert!(ctx.can_read_filesystem());
        assert!(ctx.can_write_filesystem());
        assert!(ctx.can_dispatch_network());
        assert!(ctx.can_execute_commands());
        assert!(ctx.can_process_payments());
    }

    #[test]
    fn builder_pattern_selective_grants() {
        let ctx = ExecutionContext::new()
            .with_read_filesystem()
            .with_dispatch_network();

        assert!(ctx.can_read_filesystem());
        assert!(!ctx.can_write_filesystem());
        assert!(ctx.can_dispatch_network());
        assert!(!ctx.can_execute_commands());
        assert!(!ctx.can_process_payments());
    }

    #[test]
    fn default_is_same_as_new() {
        let ctx: ExecutionContext = Default::default();
        assert!(!ctx.can_read_filesystem());
    }
}

#[cfg(test)]
mod agent_state_machine_tests {
    use sas_core_rs::{AgentState, AgentStateMachine, StateError};

    #[test]
    fn new_is_idle() {
        let sm = AgentStateMachine::new();
        assert_eq!(sm.current(), AgentState::Idle);
    }

    #[test]
    fn idle_to_compiling_is_valid() {
        let mut sm = AgentStateMachine::new();
        assert!(sm.transition(AgentState::Compiling, None).is_ok());
        assert_eq!(sm.current(), AgentState::Compiling);
    }

    #[test]
    fn idle_to_executing_is_valid() {
        let mut sm = AgentStateMachine::new();
        assert!(sm.transition(AgentState::Executing, None).is_ok());
        assert_eq!(sm.current(), AgentState::Executing);
    }

    #[test]
    fn compiling_to_executing_is_valid() {
        let mut sm = AgentStateMachine::new();
        sm.transition(AgentState::Compiling, None).unwrap();
        assert!(sm.transition(AgentState::Executing, None).is_ok());
        assert_eq!(sm.current(), AgentState::Executing);
    }

    #[test]
    fn executing_to_verifying_is_valid() {
        let mut sm = AgentStateMachine::new();
        sm.transition(AgentState::Executing, None).unwrap();
        assert!(sm.transition(AgentState::Verifying, None).is_ok());
        assert_eq!(sm.current(), AgentState::Verifying);
    }

    #[test]
    fn verifying_to_completed_is_valid() {
        let mut sm = AgentStateMachine::new();
        sm.transition(AgentState::Executing, None).unwrap();
        sm.transition(AgentState::Verifying, None).unwrap();
        assert!(sm.transition(AgentState::Completed, None).is_ok());
        assert_eq!(sm.current(), AgentState::Completed);
    }

    #[test]
    fn verifying_to_executing_retry_is_valid() {
        let mut sm = AgentStateMachine::new();
        sm.transition(AgentState::Executing, None).unwrap();
        sm.transition(AgentState::Verifying, None).unwrap();
        assert!(sm
            .transition(AgentState::Executing, Some("retry".to_string()))
            .is_ok());
        assert_eq!(sm.current(), AgentState::Executing);
    }

    #[test]
    fn failed_to_idle_reset_is_valid() {
        let mut sm = AgentStateMachine::new();
        sm.transition(AgentState::Executing, None).unwrap();
        sm.transition(AgentState::Failed, None).unwrap();
        assert!(sm.transition(AgentState::Idle, None).is_ok());
        assert_eq!(sm.current(), AgentState::Idle);
    }

    #[test]
    fn completed_to_idle_reset_is_valid() {
        let mut sm = AgentStateMachine::new();
        sm.transition(AgentState::Executing, None).unwrap();
        sm.transition(AgentState::Verifying, None).unwrap();
        sm.transition(AgentState::Completed, None).unwrap();
        assert!(sm.transition(AgentState::Idle, None).is_ok());
        assert_eq!(sm.current(), AgentState::Idle);
    }

    #[test]
    fn idle_to_completed_is_invalid() {
        let mut sm = AgentStateMachine::new();
        let result = sm.transition(AgentState::Completed, None);
        assert!(result.is_err());
        assert_eq!(sm.current(), AgentState::Idle);
    }

    #[test]
    fn compiling_to_verifying_is_invalid() {
        let mut sm = AgentStateMachine::new();
        sm.transition(AgentState::Compiling, None).unwrap();
        let result = sm.transition(AgentState::Verifying, None);
        assert!(result.is_err());
    }

    #[test]
    fn history_records_transitions() {
        let mut sm = AgentStateMachine::new();
        sm.transition(AgentState::Compiling, Some("start".to_string()))
            .unwrap();
        sm.transition(AgentState::Executing, None).unwrap();
        sm.transition(AgentState::Verifying, Some("check".to_string()))
            .unwrap();
        sm.transition(AgentState::Completed, None).unwrap();

        let history = sm.history();
        assert_eq!(history.len(), 4);
        assert_eq!(history[0].from, AgentState::Idle);
        assert_eq!(history[0].to, AgentState::Compiling);
        assert_eq!(history[0].reason, Some("start".to_string()));
        assert_eq!(history[3].from, AgentState::Verifying);
        assert_eq!(history[3].to, AgentState::Completed);
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

#[cfg(test)]
mod validate_type_tests {
    use sas_core_rs::validate_type;
    use serde_json::json;

    #[test]
    fn string_validation() {
        assert!(validate_type(&json!("hello"), "string"));
        assert!(!validate_type(&json!(42), "string"));
        assert!(!validate_type(&json!(true), "string"));
    }

    #[test]
    fn integer_validation() {
        assert!(validate_type(&json!(42), "integer"));
        assert!(validate_type(&json!(0), "integer"));
        assert!(validate_type(&json!(-5), "integer"));
        assert!(!validate_type(&json!(3.14), "integer"));
        assert!(!validate_type(&json!("42"), "integer"));
    }

    #[test]
    fn number_validation() {
        assert!(validate_type(&json!(3.14), "number"));
        assert!(validate_type(&json!(42), "number"));
        assert!(!validate_type(&json!("3.14"), "number"));
    }

    #[test]
    fn boolean_validation() {
        assert!(validate_type(&json!(true), "boolean"));
        assert!(validate_type(&json!(false), "boolean"));
        assert!(!validate_type(&json!(1), "boolean"));
    }

    #[test]
    fn array_validation() {
        assert!(validate_type(&json!([1, 2, 3]), "array"));
        assert!(validate_type(&json!([]), "array"));
        assert!(!validate_type(&json!("[1,2]"), "array"));
    }

    #[test]
    fn object_validation() {
        assert!(validate_type(&json!({"key": "value"}), "object"));
        assert!(!validate_type(&json!("{}"), "object"));
    }

    #[test]
    fn unknown_type_always_valid() {
        assert!(validate_type(&json!(42), "unknown"));
        assert!(validate_type(&json!("anything"), "custom"));
    }
}

#[cfg(test)]
mod schema_tests {
    use sas_core_rs::{schema_to_json, JsonSchema, SchemaProperty};
    use std::collections::HashMap;

    #[test]
    fn schema_to_json_produces_valid_json() {
        let schema = JsonSchema {
            name: "test_tool".to_string(),
            description: Some("A test tool".to_string()),
            required: Some(vec!["query".to_string()]),
            properties: HashMap::from([(
                "query".to_string(),
                SchemaProperty {
                    ty: "string".to_string(),
                    description: Some("The query".to_string()),
                    default: None,
                },
            )]),
        };

        let json = schema_to_json(&schema);
        assert_eq!(json["type"], "object");
        assert_eq!(json["title"], "test_tool");
        assert_eq!(json["description"], "A test tool");
        assert_eq!(json["required"][0], "query");
        assert_eq!(json["properties"]["query"]["type"], "string");
        assert_eq!(json["properties"]["query"]["description"], "The query");
    }

    #[test]
    fn schema_without_required_or_description() {
        let schema = JsonSchema {
            name: "minimal".to_string(),
            description: None,
            required: None,
            properties: HashMap::new(),
        };

        let json = schema_to_json(&schema);
        assert!(json.get("required").is_none());
        assert!(json.get("description").is_none());
        assert!(json
            .get("properties")
            .unwrap()
            .as_object()
            .unwrap()
            .is_empty());
    }

    #[test]
    fn schema_with_defaults() {
        let schema = JsonSchema {
            name: "with_defaults".to_string(),
            description: None,
            required: None,
            properties: HashMap::from([(
                "limit".to_string(),
                SchemaProperty {
                    ty: "integer".to_string(),
                    description: None,
                    default: Some(serde_json::json!(10)),
                },
            )]),
        };

        let json = schema_to_json(&schema);
        assert_eq!(json["properties"]["limit"]["default"], 10);
    }
}

#[cfg(test)]
mod capability_token_tests {
    use sas_core_rs::{
        CanDispatchNetwork, CanExecuteCommands, CanProcessPayments, CanReadFilesystem,
        CanWriteFilesystem, Capability,
    };

    #[test]
    fn capabilities_are_send_sync() {
        fn assert_send<T: Send>() {}
        fn assert_sync<T: Sync>() {}

        assert_send::<CanReadFilesystem>();
        assert_sync::<CanReadFilesystem>();
        assert_send::<CanWriteFilesystem>();
        assert_sync::<CanWriteFilesystem>();
        assert_send::<CanDispatchNetwork>();
        assert_sync::<CanDispatchNetwork>();
        assert_send::<CanExecuteCommands>();
        assert_sync::<CanExecuteCommands>();
        assert_send::<CanProcessPayments>();
        assert_sync::<CanProcessPayments>();
    }
}
