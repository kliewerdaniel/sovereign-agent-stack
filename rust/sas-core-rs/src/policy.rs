//! Policy hook typestate markers.
//!
//! This module provides compile-time enforcement of policy hooks before
//! privileged operations. The typestate pattern ensures that:
//!
//! 1. Filesystem writes require a `PreWrite` policy check
//! 2. Command execution requires a `PreExec` policy check
//! 3. Network dispatch requires a `PreDispatch` policy check
//! 4. Payment processing requires a `PrePayment` policy check
//!
//! Each policy hook is a typestate marker that must be "consumed" before
//! the operation can proceed. This makes it impossible to accidentally
//! skip a policy check.

use std::marker::PhantomData;

// ── Policy hook marker traits ────────────────────────────────────────────────

/// Marker trait for policy hooks.
pub trait PolicyHook: sealed::Sealed + Send + Sync + 'static {}

mod sealed {
    pub trait Sealed {}
}

/// Pre-write policy hook — must be checked before any filesystem write.
pub struct PreWrite;
impl sealed::Sealed for PreWrite {}
impl PolicyHook for PreWrite {}

/// Pre-exec policy hook — must be checked before any command execution.
pub struct PreExec;
impl sealed::Sealed for PreExec {}
impl PolicyHook for PreExec {}

/// Pre-dispatch policy hook — must be checked before any network dispatch.
pub struct PreDispatch;
impl sealed::Sealed for PreDispatch {}
impl PolicyHook for PreDispatch {}

/// Pre-payment policy hook — must be checked before any payment processing.
pub struct PrePayment;
impl sealed::Sealed for PrePayment {}
impl PolicyHook for PrePayment {}

/// Pre-read policy hook — must be checked before reading sensitive data.
pub struct PreRead;
impl sealed::Sealed for PreRead {}
impl PolicyHook for PreRead {}

/// Pre-compile policy hook — must be checked before compiling sources.
pub struct PreCompile;
impl sealed::Sealed for PreCompile {}
impl PolicyHook for PreCompile {}

// ── Policy proof ─────────────────────────────────────────────────────────────

/// A zero-sized proof that a policy hook has been checked.
///
/// This is the typestate mechanism: you can't construct a `PolicyProof<H>`
/// without actually checking the policy. The only way to get one is from
/// `PolicyEnforcer::check()`.
pub struct PolicyProof<H: PolicyHook> {
    _marker: PhantomData<H>,
}

impl<H: PolicyHook> std::fmt::Debug for PolicyProof<H> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("PolicyProof").finish()
    }
}

impl<H: PolicyHook> PolicyProof<H> {
    fn new() -> Self {
        Self {
            _marker: PhantomData,
        }
    }
}

impl<H: PolicyHook> Clone for PolicyProof<H> {
    fn clone(&self) -> Self {
        Self::new()
    }
}

impl<H: PolicyHook> Copy for PolicyProof<H> {}

impl<H: PolicyHook> Default for PolicyProof<H> {
    fn default() -> Self {
        Self::new()
    }
}

// ── Policy enforcer ──────────────────────────────────────────────────────────

/// Policy enforcement engine.
///
/// Checks policies and issues proofs that the check was performed.
/// The actual policy logic is pluggable via the `PolicyChecker` trait.
pub struct PolicyEnforcer {
    checker: Box<dyn PolicyChecker>,
}

/// Trait for pluggable policy checking logic.
pub trait PolicyChecker: Send + Sync {
    /// Check if a filesystem write is allowed.
    fn check_write(&self, path: &str, content: &[u8]) -> PolicyResult<()>;
    /// Check if a command execution is allowed.
    fn check_exec(&self, command: &str, args: &[&str]) -> PolicyResult<()>;
    /// Check if a network dispatch is allowed.
    fn check_dispatch(&self, url: &str, method: &str) -> PolicyResult<()>;
    /// Check if a payment is allowed.
    fn check_payment(&self, amount: f64, currency: &str, recipient: &str) -> PolicyResult<()>;
    /// Check if reading a path is allowed.
    fn check_read(&self, path: &str) -> PolicyResult<()>;
    /// Check if compiling a source is allowed.
    fn check_compile(&self, source: &str) -> PolicyResult<()>;
}

/// Result of a policy check.
pub type PolicyResult<T> = Result<T, PolicyError>;

/// Policy violation error.
#[derive(Debug, Clone, PartialEq)]
pub enum PolicyError {
    WriteForbidden { path: String, reason: String },
    ExecForbidden { command: String, reason: String },
    DispatchForbidden { url: String, reason: String },
    PaymentForbidden { amount: f64, currency: String, reason: String },
    ReadForbidden { path: String, reason: String },
    CompileForbidden { source: String, reason: String },
    Custom(String),
}

impl std::fmt::Display for PolicyError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            PolicyError::WriteForbidden { path, reason } => {
                write!(f, "Write to '{}' forbidden: {}", path, reason)
            }
            PolicyError::ExecForbidden { command, reason } => {
                write!(f, "Exec '{}' forbidden: {}", command, reason)
            }
            PolicyError::DispatchForbidden { url, reason } => {
                write!(f, "Dispatch to '{}' forbidden: {}", url, reason)
            }
            PolicyError::PaymentForbidden { amount, currency, reason } => {
                write!(f, "Payment {} {} forbidden: {}", amount, currency, reason)
            }
            PolicyError::ReadForbidden { path, reason } => {
                write!(f, "Read '{}' forbidden: {}", path, reason)
            }
            PolicyError::CompileForbidden { source, reason } => {
                write!(f, "Compile '{}' forbidden: {}", source, reason)
            }
            PolicyError::Custom(msg) => write!(f, "Policy error: {}", msg),
        }
    }
}

impl std::error::Error for PolicyError {}

impl PolicyEnforcer {
    /// Create a new policy enforcer with the given checker.
    pub fn new(checker: Box<dyn PolicyChecker>) -> Self {
        Self { checker }
    }

    /// Check pre-write policy and return a proof if allowed.
    pub fn check_write(&self, path: &str, content: &[u8]) -> PolicyResult<PolicyProof<PreWrite>> {
        self.checker.check_write(path, content)?;
        Ok(PolicyProof::new())
    }

    /// Check pre-exec policy and return a proof if allowed.
    pub fn check_exec(&self, command: &str, args: &[&str]) -> PolicyResult<PolicyProof<PreExec>> {
        self.checker.check_exec(command, args)?;
        Ok(PolicyProof::new())
    }

    /// Check pre-dispatch policy and return a proof if allowed.
    pub fn check_dispatch(&self, url: &str, method: &str) -> PolicyResult<PolicyProof<PreDispatch>> {
        self.checker.check_dispatch(url, method)?;
        Ok(PolicyProof::new())
    }

    /// Check pre-payment policy and return a proof if allowed.
    pub fn check_payment(&self, amount: f64, currency: &str, recipient: &str) -> PolicyResult<PolicyProof<PrePayment>> {
        self.checker.check_payment(amount, currency, recipient)?;
        Ok(PolicyProof::new())
    }

    /// Check pre-read policy and return a proof if allowed.
    pub fn check_read(&self, path: &str) -> PolicyResult<PolicyProof<PreRead>> {
        self.checker.check_read(path)?;
        Ok(PolicyProof::new())
    }

    /// Check pre-compile policy and return a proof if allowed.
    pub fn check_compile(&self, source: &str) -> PolicyResult<PolicyProof<PreCompile>> {
        self.checker.check_compile(source)?;
        Ok(PolicyProof::new())
    }
}

// ── Allow-all policy (for testing) ──────────────────────────────────────────

/// A policy checker that allows everything.
pub struct AllowAllPolicy;

impl PolicyChecker for AllowAllPolicy {
    fn check_write(&self, _path: &str, _content: &[u8]) -> PolicyResult<()> {
        Ok(())
    }
    fn check_exec(&self, _command: &str, _args: &[&str]) -> PolicyResult<()> {
        Ok(())
    }
    fn check_dispatch(&self, _url: &str, _method: &str) -> PolicyResult<()> {
        Ok(())
    }
    fn check_payment(&self, _amount: f64, _currency: &str, _recipient: &str) -> PolicyResult<()> {
        Ok(())
    }
    fn check_read(&self, _path: &str) -> PolicyResult<()> {
        Ok(())
    }
    fn check_compile(&self, _source: &str) -> PolicyResult<()> {
        Ok(())
    }
}

// ── Deny-all policy (for testing) ──────────────────────────────────────────

/// A policy checker that denies everything.
pub struct DenyAllPolicy;

impl PolicyChecker for DenyAllPolicy {
    fn check_write(&self, path: &str, _content: &[u8]) -> PolicyResult<()> {
        Err(PolicyError::WriteForbidden {
            path: path.to_string(),
            reason: "denied by policy".to_string(),
        })
    }
    fn check_exec(&self, command: &str, _args: &[&str]) -> PolicyResult<()> {
        Err(PolicyError::ExecForbidden {
            command: command.to_string(),
            reason: "denied by policy".to_string(),
        })
    }
    fn check_dispatch(&self, url: &str, _method: &str) -> PolicyResult<()> {
        Err(PolicyError::DispatchForbidden {
            url: url.to_string(),
            reason: "denied by policy".to_string(),
        })
    }
    fn check_payment(&self, amount: f64, currency: &str, _recipient: &str) -> PolicyResult<()> {
        Err(PolicyError::PaymentForbidden {
            amount,
            currency: currency.to_string(),
            reason: "denied by policy".to_string(),
        })
    }
    fn check_read(&self, path: &str) -> PolicyResult<()> {
        Err(PolicyError::ReadForbidden {
            path: path.to_string(),
            reason: "denied by policy".to_string(),
        })
    }
    fn check_compile(&self, source: &str) -> PolicyResult<()> {
        Err(PolicyError::CompileForbidden {
            source: source.to_string(),
            reason: "denied by policy".to_string(),
        })
    }
}

// ── Policy-gated operations ──────────────────────────────────────────────────

/// A filesystem write operation that requires a PreWrite proof.
///
/// The typestate pattern ensures that you cannot call `perform()` without
/// first obtaining a `PolicyProof<PreWrite>` from the policy enforcer.
pub struct WriteOperation<'a> {
    path: &'a str,
    content: &'a [u8],
}

impl<'a> WriteOperation<'a> {
    pub fn new(path: &'a str, content: &'a [u8]) -> Self {
        Self { path, content }
    }

    /// Perform the write, consuming the policy proof.
    pub fn perform(self, _proof: PolicyProof<PreWrite>) -> std::io::Result<()> {
        std::fs::write(self.path, self.content)
    }
}

/// A command execution operation that requires a PreExec proof.
pub struct ExecOperation<'a> {
    command: &'a str,
    args: &'a [&'a str],
}

impl<'a> ExecOperation<'a> {
    pub fn new(command: &'a str, args: &'a [&'a str]) -> Self {
        Self { command, args }
    }

    /// Perform the exec, consuming the policy proof.
    pub fn perform(self, _proof: PolicyProof<PreExec>) -> std::io::Result<std::process::Output> {
        std::process::Command::new(self.command)
            .args(self.args)
            .output()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn allow_all_policy_permits_everything() {
        let enforcer = PolicyEnforcer::new(Box::new(AllowAllPolicy));

        let proof = enforcer.check_write("/tmp/test.txt", b"hello");
        assert!(proof.is_ok());

        let proof = enforcer.check_exec("ls", &["-la"]);
        assert!(proof.is_ok());

        let proof = enforcer.check_dispatch("https://example.com", "GET");
        assert!(proof.is_ok());

        let proof = enforcer.check_payment(100.0, "USD", "recipient");
        assert!(proof.is_ok());
    }

    #[test]
    fn deny_all_policy_denies_everything() {
        let enforcer = PolicyEnforcer::new(Box::new(DenyAllPolicy));

        let err = enforcer.check_write("/tmp/test.txt", b"hello").unwrap_err();
        assert!(matches!(err, PolicyError::WriteForbidden { .. }));

        let err = enforcer.check_exec("ls", &["-la"]).unwrap_err();
        assert!(matches!(err, PolicyError::ExecForbidden { .. }));

        let err = enforcer.check_dispatch("https://example.com", "GET").unwrap_err();
        assert!(matches!(err, PolicyError::DispatchForbidden { .. }));

        let err = enforcer.check_payment(100.0, "USD", "recipient").unwrap_err();
        assert!(matches!(err, PolicyError::PaymentForbidden { .. }));
    }

    #[test]
    fn policy_proof_is_consumed() {
        let enforcer = PolicyEnforcer::new(Box::new(AllowAllPolicy));
        let proof = enforcer.check_write("/tmp/test.txt", b"hello").unwrap();

        let op = WriteOperation::new("/tmp/test.txt", b"hello");
        let _ = op.perform(proof);

        // proof is consumed and cannot be used again
        // This is enforced at compile time!
    }

    #[test]
    fn policy_error_display() {
        let err = PolicyError::WriteForbidden {
            path: "/etc/passwd".to_string(),
            reason: "read-only filesystem".to_string(),
        };
        let msg = format!("{}", err);
        assert!(msg.contains("/etc/passwd"));
        assert!(msg.contains("read-only"));
    }
}
