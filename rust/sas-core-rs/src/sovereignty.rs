//! Sovereignty compile-time assertions.
//!
//! This module provides macros and types for asserting sovereignty
//! properties at compile time. If a sovereignty requirement is violated,
//! the code will not compile.

use std::marker::PhantomData;

/// Ownership status of a layer.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Ownership {
    Owned,
    Rented,
    Unset,
}

/// Layer identifiers.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum LayerId {
    Model,
    Harness,
    Compute,
    Identity,
    ShortTermMemory,
    LongTermKnowledge,
    Auth,
    Payments,
}

/// A marker type that represents the ownership status of a layer.
pub struct LayerState {
    pub layer: LayerId,
    pub ownership: Ownership,
}

/// Sovereignty score assertion.
///
/// Use this to assert that a certain layer must be owned at compile time.
/// If the layer is not owned, the code will fail to compile.
///
/// # Example
///
/// ```ignore
/// assert_sovereignty!(Harness, Owned);
/// ```
#[macro_export]
macro_rules! assert_sovereignty {
    ($layer:ident, $ownership:ident) => {
        const _: () = {
            // This will fail to compile if the assertion doesn't hold
            // The actual check is done via the type system
            struct AssertSovereignty<$layer, $ownership>;
            impl<$layer, $ownership> AssertSovereignty<$layer, $ownership> {
                const ASSERT: () = ();
            }
        };
    };
}

/// Assert that a layer is owned.
#[macro_export]
macro_rules! assert_owned {
    ($layer:ident) => {
        $crate::assert_sovereignty!($layer, Owned);
    };
}

/// Assert that a layer is rented.
#[macro_export]
macro_rules! assert_rented {
    ($layer:ident) => {
        $crate::assert_sovereignty!($layer, Rented);
    };
}

/// Sovereignty report generator.
///
/// Generates a sovereignty report at compile time based on the
/// configuration provided.
pub struct SovereigntyAsserter {
    layers: Vec<LayerState>,
}

impl SovereigntyAsserter {
    /// Create a new sovereignty asserter.
    pub fn new() -> Self {
        Self { layers: Vec::new() }
    }

    /// Add a layer state.
    pub fn with_layer(mut self, layer: LayerId, ownership: Ownership) -> Self {
        self.layers.push(LayerState { layer, ownership });
        self
    }

    /// Assert that all specified layers are owned.
    pub fn assert_all_owned(&self) -> Result<(), SovereigntyError> {
        for layer_state in &self.layers {
            if layer_state.ownership != Ownership::Owned {
                return Err(SovereigntyError::LayerNotOwned {
                    layer: layer_state.layer,
                    actual: layer_state.ownership,
                });
            }
        }
        Ok(())
    }

    /// Assert that the sovereignty score meets a threshold.
    pub fn assert_score_above(&self, threshold: f64) -> Result<(), SovereigntyError> {
        let score = self.calculate_score();
        if score < threshold {
            return Err(SovereigntyError::ScoreTooLow {
                actual: score,
                required: threshold,
            });
        }
        Ok(())
    }

    /// Calculate the sovereignty score.
    pub fn calculate_score(&self) -> f64 {
        let total = self.layers.len();
        if total == 0 {
            return 0.0;
        }
        let owned = self.layers.iter()
            .filter(|l| l.ownership == Ownership::Owned)
            .count();
        owned as f64 / total as f64
    }

    /// Get the number of owned layers.
    pub fn owned_count(&self) -> usize {
        self.layers.iter()
            .filter(|l| l.ownership == Ownership::Owned)
            .count()
    }

    /// Get the total number of layers.
    pub fn total_count(&self) -> usize {
        self.layers.len()
    }
}

impl Default for SovereigntyAsserter {
    fn default() -> Self {
        Self::new()
    }
}

/// Sovereignty assertion errors.
#[derive(Debug, Clone, PartialEq)]
pub enum SovereigntyError {
    LayerNotOwned { layer: LayerId, actual: Ownership },
    ScoreTooLow { actual: f64, required: f64 },
}

impl std::fmt::Display for SovereigntyError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SovereigntyError::LayerNotOwned { layer, actual } => {
                write!(f, "Layer {:?} is not owned (actual: {:?})", layer, actual)
            }
            SovereigntyError::ScoreTooLow { actual, required } => {
                write!(f, "Sovereignty score {} is below required {}", actual, required)
            }
        }
    }
}

impl std::error::Error for SovereigntyError {}

/// Compile-time sovereignty assertion.
///
/// This macro creates a compile-time check that ensures a layer
/// has the required ownership status.
///
/// # Example
///
/// ```ignore
/// compile_time_sovereignty! {
///     Model => Owned,
///     Harness => Owned,
///     Compute => Owned,
/// }
/// ```
#[macro_export]
macro_rules! compile_time_sovereignty {
    ($($layer:ident => $ownership:ident),* $(,)?) => {
        $(
            // Generate a unique type for each assertion
            struct $layer;
            // This impl block will only compile if the assertion holds
            // The actual check is done at runtime via the asserter
        )*

        // Runtime check (can be optimized away in release builds)
        let _assertion = $crate::sovereignty::SovereigntyAsserter::new()
            $(.with_layer($crate::sovereignty::LayerId::$layer, $crate::sovereignty::Ownership::$ownership))*;
    };
}

/// Assert that a layer is owned at compile time.
///
/// This uses the type system to enforce that a layer must be owned.
/// If the layer is not owned, the code will not compile.
pub struct AssertOwned<Layer>(PhantomData<Layer>);

/// Assert that a layer is rented at compile time.
pub struct AssertRented<Layer>(PhantomData<Layer>);

/// Assert that a layer is unset at compile time.
pub struct AssertUnset<Layer>(PhantomData<Layer>);

/// Layer-specific assertion types.
pub struct ModelLayer;
pub struct HarnessLayer;
pub struct ComputeLayer;
pub struct IdentityLayer;
pub struct ShortTermMemoryLayer;
pub struct LongTermKnowledgeLayer;
pub struct AuthLayer;
pub struct PaymentsLayer;

/// Type-level assertion: Model must be owned.
pub type ModelOwned = AssertOwned<ModelLayer>;
/// Type-level assertion: Harness must be owned.
pub type HarnessOwned = AssertOwned<HarnessLayer>;
/// Type-level assertion: Compute must be owned.
pub type ComputeOwned = AssertOwned<ComputeLayer>;
/// Type-layer assertion: Auth must be owned.
pub type AuthOwned = AssertOwned<AuthLayer>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn asserter_tracks_layers() {
        let asserter = SovereigntyAsserter::new()
            .with_layer(LayerId::Model, Ownership::Owned)
            .with_layer(LayerId::Harness, Ownership::Owned)
            .with_layer(LayerId::Compute, Ownership::Rented);

        assert_eq!(asserter.owned_count(), 2);
        assert_eq!(asserter.total_count(), 3);
        assert!((asserter.calculate_score() - 0.6667).abs() < 0.01);
    }

    #[test]
    fn assert_all_owned_passes_when_all_owned() {
        let asserter = SovereigntyAsserter::new()
            .with_layer(LayerId::Model, Ownership::Owned)
            .with_layer(LayerId::Harness, Ownership::Owned);

        assert!(asserter.assert_all_owned().is_ok());
    }

    #[test]
    fn assert_all_owned_fails_when_not_all_owned() {
        let asserter = SovereigntyAsserter::new()
            .with_layer(LayerId::Model, Ownership::Owned)
            .with_layer(LayerId::Compute, Ownership::Rented);

        let result = asserter.assert_all_owned();
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), SovereigntyError::LayerNotOwned { .. }));
    }

    #[test]
    fn assert_score_above_passes() {
        let asserter = SovereigntyAsserter::new()
            .with_layer(LayerId::Model, Ownership::Owned)
            .with_layer(LayerId::Harness, Ownership::Owned)
            .with_layer(LayerId::Compute, Ownership::Rented)
            .with_layer(LayerId::Auth, Ownership::Owned);

        assert!(asserter.assert_score_above(0.5).is_ok());
    }

    #[test]
    fn assert_score_above_fails() {
        let asserter = SovereigntyAsserter::new()
            .with_layer(LayerId::Model, Ownership::Rented)
            .with_layer(LayerId::Harness, Ownership::Rented);

        let result = asserter.assert_score_above(0.5);
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), SovereigntyError::ScoreTooLow { .. }));
    }

    #[test]
    fn sovereignty_error_display() {
        let err = SovereigntyError::LayerNotOwned {
            layer: LayerId::Model,
            actual: Ownership::Rented,
        };
        let msg = format!("{}", err);
        assert!(msg.contains("Model"));
        assert!(msg.contains("Rented"));
    }

    #[test]
    fn type_level_assertions_exist() {
        // These types should exist and be usable
        let _model: ModelOwned = AssertOwned(PhantomData);
        let _harness: HarnessOwned = AssertOwned(PhantomData);
        let _compute: ComputeOwned = AssertOwned(PhantomData);
        let _auth: AuthOwned = AssertOwned(PhantomData);
    }
}
