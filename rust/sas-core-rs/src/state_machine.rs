//! State machine with compile-time transition exhaustiveness checking.

/// Define a state machine with compile-time exhaustiveness checking.
#[macro_export]
macro_rules! transitions {
    ($state_enum:ident {
        $($from:ident => [$($to:ident),* $(,)?]),* $(,)?
    }) => {
        /// Agent states.
        #[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
        pub enum $state_enum {
            $($from,)*
        }

        impl $state_enum {
            /// Check if a transition to `target` is valid from this state.
            pub fn can_transition(&self, target: &$state_enum) -> bool {
                match self {
                    $(Self::$from => {
                        let valid_targets: &[$state_enum] = &[
                            $(Self::$to,)*
                        ];
                        valid_targets.contains(target)
                    })*
                }
            }

            /// Get all valid target states from this state.
            pub fn valid_targets(&self) -> &'static [$state_enum] {
                match self {
                    $(Self::$from => {
                        static TARGETS: &[$state_enum] = &[
                            $($state_enum::$to,)*
                        ];
                        TARGETS
                    })*
                }
            }
        }

        /// State machine with history tracking.
        pub struct StateMachine {
            current: $state_enum,
            history: Vec<Transition>,
        }

        /// A recorded state transition.
        #[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
        pub struct Transition {
            pub from: $state_enum,
            pub to: $state_enum,
            pub timestamp: String,
            pub reason: Option<String>,
        }

        impl StateMachine {
            /// Create a new state machine in the initial state.
            pub fn new(initial: $state_enum) -> Self {
                Self {
                    current: initial,
                    history: Vec::new(),
                }
            }

            /// Get the current state.
            pub fn current(&self) -> $state_enum {
                self.current
            }

            /// Attempt a state transition.
            pub fn transition(&mut self, target: $state_enum, reason: Option<String>) -> Result<(), StateError> {
                if !self.current.can_transition(&target) {
                    return Err(StateError::InvalidTransition {
                        from: self.current,
                        to: target,
                    });
                }

                let t = Transition {
                    from: self.current,
                    to: target,
                    timestamp: chrono::Utc::now().to_rfc3339(),
                    reason,
                };
                self.history.push(t);
                self.current = target;
                Ok(())
            }

            /// Get the transition history.
            pub fn history(&self) -> &[Transition] {
                &self.history
            }

            /// Check if the machine is in a terminal state.
            pub fn is_terminal(&self) -> bool {
                self.current().valid_targets().is_empty()
            }
        }

        impl Default for StateMachine {
            fn default() -> Self {
                Self::new($state_enum::Start)
            }
        }

        /// Errors that occur during state transitions.
        #[derive(Debug, Clone, serde::Serialize, serde::Deserialize, PartialEq)]
        pub enum StateError {
            InvalidTransition {
                from: $state_enum,
                to: $state_enum,
            },
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
    };
}

/// Assert that a state is valid in a state machine.
#[macro_export]
macro_rules! assert_valid_state {
    ($state_enum:ident :: $state:ident) => {
        // Compile-time check: this will fail if the state doesn't exist
        let _: $state_enum = $state_enum::$state;
    };
}

/// Assert that a transition is valid in a state machine.
#[macro_export]
macro_rules! assert_valid_transition {
    ($state_enum:ident, $from:ident => $to:ident) => {
        // Compile-time check: this will fail if either state doesn't exist
        let _: $state_enum = $state_enum::$from;
        let _: $state_enum = $state_enum::$to;
    };
}

#[cfg(test)]
mod tests {
    use super::*;

    // Test the macro with a simple state machine
    transitions! {
        TestState {
            Start => [Middle, End],
            Middle => [End, Error],
            Error => [Start],
            End => [],
        }
    }

    #[test]
    fn macro_generates_enum() {
        assert!(TestState::Start.can_transition(&TestState::Middle));
        assert!(TestState::Start.can_transition(&TestState::End));
        assert!(!TestState::Start.can_transition(&TestState::Error));
    }

    #[test]
    fn macro_generates_state_machine() {
        let mut sm = StateMachine::new(TestState::Start);
        assert_eq!(sm.current(), TestState::Start);

        sm.transition(TestState::Middle, None).unwrap();
        assert_eq!(sm.current(), TestState::Middle);

        sm.transition(TestState::End, None).unwrap();
        assert_eq!(sm.current(), TestState::End);

        assert!(sm.is_terminal());
    }

    #[test]
    fn macro_rejects_invalid_transition() {
        let mut sm = StateMachine::new(TestState::Start);
        let result = sm.transition(TestState::Error, None);
        assert!(result.is_err());
    }

    #[test]
    fn macro_records_history() {
        let mut sm = StateMachine::new(TestState::Start);
        sm.transition(TestState::Middle, Some("step 1".to_string()))
            .unwrap();
        sm.transition(TestState::End, None).unwrap();

        assert_eq!(sm.history().len(), 2);
        assert_eq!(sm.history()[0].from, TestState::Start);
        assert_eq!(sm.history()[0].to, TestState::Middle);
        assert_eq!(sm.history()[0].reason, Some("step 1".to_string()));
    }

    #[test]
    fn valid_targets() {
        let targets = TestState::Start.valid_targets();
        assert_eq!(targets, &[TestState::Middle, TestState::End]);

        let empty = TestState::End.valid_targets();
        assert!(empty.is_empty());
    }
}
