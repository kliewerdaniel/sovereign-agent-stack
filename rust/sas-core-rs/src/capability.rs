//! Typestate-based capability enforcement.

use std::marker::PhantomData;

// ── Capability marker traits ────────────────────────────────────────────────-

/// Marker trait for all capabilities.
pub trait Capability: sealed::Sealed + Send + Sync + 'static {}

mod sealed {
    pub trait Sealed {}
}

// ── Individual capabilities ──────────────────────────────────────────────────

/// Capability: read from filesystem.
pub struct ReadFilesystem;
impl sealed::Sealed for ReadFilesystem {}
impl Capability for ReadFilesystem {}

/// Capability: write to filesystem.
pub struct WriteFilesystem;
impl sealed::Sealed for WriteFilesystem {}
impl Capability for WriteFilesystem {}

/// Capability: dispatch network requests.
pub struct DispatchNetwork;
impl sealed::Sealed for DispatchNetwork {}
impl Capability for DispatchNetwork {}

/// Capability: execute commands.
pub struct ExecuteCommands;
impl sealed::Sealed for ExecuteCommands {}
impl Capability for ExecuteCommands {}

/// Capability: process payments.
pub struct ProcessPayments;
impl sealed::Sealed for ProcessPayments {}
impl Capability for ProcessPayments {}

/// Capability: emit events.
pub struct EmitEvents;
impl sealed::Sealed for EmitEvents {}
impl Capability for EmitEvents {}

/// Capability: read from knowledge graph.
pub struct ReadKnowledge;
impl sealed::Sealed for ReadKnowledge {}
impl Capability for ReadKnowledge {}

/// Capability: write to knowledge graph.
pub struct WriteKnowledge;
impl sealed::Sealed for WriteKnowledge {}
impl Capability for WriteKnowledge {}

/// No capability required (unprivileged).
pub struct NoCapability;
impl sealed::Sealed for NoCapability {}
impl Capability for NoCapability {}

// ── Capability proof ─────────────────────────────────────────────────────────

/// A zero-sized proof that a capability has been granted.
pub struct Proof<C: Capability> {
    _marker: PhantomData<C>,
}

impl<C: Capability> Proof<C> {
    fn new() -> Self {
        Self {
            _marker: PhantomData,
        }
    }
}

impl<C: Capability> Clone for Proof<C> {
    fn clone(&self) -> Self {
        Self::new()
    }
}

impl<C: Capability> Copy for Proof<C> {}

impl<C: Capability> Default for Proof<C> {
    fn default() -> Self {
        Self::new()
    }
}

// ── Capability registry ──────────────────────────────────────────────────────

/// A registry that tracks which capabilities have been granted.
pub struct CapabilityRegistry {
    granted: std::collections::HashSet<std::any::TypeId>,
}

impl CapabilityRegistry {
    /// Create a new registry with no capabilities granted.
    pub fn new() -> Self {
        Self {
            granted: std::collections::HashSet::new(),
        }
    }

    /// Grant a capability.
    pub fn grant<C: Capability>(&mut self) {
        self.granted.insert(std::any::TypeId::of::<C>());
    }

    /// Check if a capability is granted.
    pub fn is_granted<C: Capability>(&self) -> bool {
        // NoCapability is always granted (it represents no requirement)
        if std::any::TypeId::of::<C>() == std::any::TypeId::of::<NoCapability>() {
            return true;
        }
        self.granted.contains(&std::any::TypeId::of::<C>())
    }

    /// Get a proof of a capability, or None if not granted.
    pub fn proof<C: Capability>(&self) -> Option<Proof<C>> {
        if self.is_granted::<C>() {
            Some(Proof::new())
        } else {
            Option::None
        }
    }

    /// Get a proof of a capability, panicking if not granted.
    pub fn require<C: Capability>(&self) -> Proof<C> {
        self.proof::<C>().expect("Required capability not granted")
    }
}

impl Default for CapabilityRegistry {
    fn default() -> Self {
        Self::new()
    }
}

// ── Tool with typestate capability ──────────────────────────────────────────

/// A tool that requires capability C to execute.
pub trait Tool<C: Capability>: Send + Sync + 'static {
    /// Execute the tool, given proof of capability.
    fn execute(
        _proof: Proof<C>,
        input: serde_json::Value,
    ) -> Result<serde_json::Value, crate::ToolError>;
}

// ── Helper types for common capability combinations ─────────────────────────

/// Tool that needs both read AND write filesystem access.
pub struct ReadWriteFilesystem;
impl sealed::Sealed for ReadWriteFilesystem {}
impl Capability for ReadWriteFilesystem {}

/// Tool that needs read access to filesystem OR network.
pub struct ReadFilesystemOrNetwork;
impl sealed::Sealed for ReadFilesystemOrNetwork {}
impl Capability for ReadFilesystemOrNetwork {}

/// Tool that needs full access (all capabilities).
pub struct FullAccess;
impl sealed::Sealed for FullAccess {}
impl Capability for FullAccess {}

/// Unprivileged tool.
pub type Unprivileged = NoCapability;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn registry_grants_and_checks() {
        let mut reg = CapabilityRegistry::new();
        assert!(!reg.is_granted::<ReadFilesystem>());

        reg.grant::<ReadFilesystem>();
        assert!(reg.is_granted::<ReadFilesystem>());
        assert!(!reg.is_granted::<WriteFilesystem>());
    }

    #[test]
    fn registry_provides_proof() {
        let mut reg = CapabilityRegistry::new();
        assert!(reg.proof::<ReadFilesystem>().is_none());

        reg.grant::<ReadFilesystem>();
        let _proof: Proof<ReadFilesystem> = reg.require::<ReadFilesystem>();
    }

    #[test]
    #[should_panic(expected = "Required capability not granted")]
    fn registry_require_panics_when_missing() {
        let reg = CapabilityRegistry::new();
        let _proof: Proof<ReadFilesystem> = reg.require::<ReadFilesystem>();
    }

    #[test]
    fn combined_capability() {
        let mut reg = CapabilityRegistry::new();
        reg.grant::<ReadWriteFilesystem>();
        assert!(reg.is_granted::<ReadWriteFilesystem>());
        assert!(!reg.is_granted::<ReadFilesystem>());
    }

    #[test]
    fn no_capability() {
        let reg = CapabilityRegistry::new();
        assert!(reg.is_granted::<NoCapability>());
        let _proof: Proof<NoCapability> = reg.require::<NoCapability>();
    }
}
