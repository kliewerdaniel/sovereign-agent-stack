# Security Audit — Sovereign Agent Stack v0.1.0-alpha

**Date:** 2026-09-04  
**Scope:** All 8 layers, credential storage, inter-layer communication  
**Status:** Pre-release audit (alpha)

---

## 1. Threat Model

### Assets
- **Credentials** — API keys, OAuth tokens, refresh tokens stored in the auth vault
- **Knowledge graph** — Compiled facts about the user, their work, and their agent's behavior
- **Model outputs** — Responses from the LLM that may contain sensitive information
- **Payment instruments** — Virtual card numbers, MPP settlement credentials
- **Identity** — Email inboxes and phone numbers

### Threat Actors
1. **Remote attacker** — Gains access to the host machine via network
2. **Malicious dependency** — Compromised PyPI package or Docker image
3. **Insider** — Another user on the same machine (multi-user systems)
4. **Physical access** — Someone with direct access to the hardware

### Attack Vectors
- Network interception (MITM on API calls)
- Vault database file reading
- Memory scraping (reading decrypted credentials from RAM)
- Knowledge graph poisoning (adding false facts)
- Prompt injection via email/SMS
- Supply chain attacks on dependencies

---

## 2. Credential Vault Analysis

### Encryption at Rest

**Current implementation:** XOR-based obfuscation with SHA-256 key

```python
# Current (INSECURE — placeholder only)
encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
```

**Risk level:** HIGH  
XOR encryption is trivially reversible. An attacker with access to the vault file and the source code can extract credentials.

**Recommendation for production:**
- Use **libsodium** (via `pynacl`) for authenticated encryption
- Key derivation: Argon2id from a user-supplied passphrase
- Each credential encrypted with a unique nonce

```python
# Production target
from nacl.secret import SecretBox
from nacl.pwhash import argon2id

# Derive key from passphrase
key = argon2id.kdf(SecretBox.KEY_SIZE, passphrase, salt)
box = SecretBox(key)
encrypted = box.encrypt(credential_bytes)
```

### Encryption in Transit

All tool calls made by the auth broker inject credentials into HTTP headers. Ensure:
- HTTPS for all API calls (never HTTP)
- Certificate pinning for high-security tools
- No logging of Authorization headers

### Credential Rotation

The auth broker supports `refresh()` for token rotation. Implement:
- Cron-based refresh for OAuth tokens (every hour)
- Immediate revocation on suspected compromise
- Audit trail for all refresh operations

---

## 3. Knowledge Graph Security

### Poisoning Risk

An attacker who can write to the knowledge source directory can inject false facts that the agent will treat as trusted.

**Mitigation:**
- Restrict write access to the knowledge directory (`chmod 700`)
- Use Git for version control (track changes, enable rollback)
- Run `audit()` regularly to detect unexpected changes
- Consider cryptographic signing of knowledge files for high-security deployments

### Information Disclosure

The knowledge graph may contain sensitive facts. Ensure:
- Graph store file is not world-readable
- Backup files are encrypted
- Knowledge is not transmitted to third parties (verified: all queries are local)

---

## 4. Compute Substrate Security

### Container Isolation

The Docker desktop container should be:
- Run as non-root user
- Limited resource access (cgroups)
- No host mounts except where explicitly needed
- Network-isolated (only expose required ports)

### Computer-Use Operations

The substrate allows the agent to:
- Take screenshots (may capture sensitive info)
- Click and type (could trigger unintended actions)
- Execute commands (privilege escalation risk)

**Mitigation:**
- Run agent with minimal OS privileges
- Confirm high-risk actions via user prompt
- Audit all `execute()` calls

---

## 5. Identity Layer Security

### Email/SMS Attack Surface

The agent processes incoming email and SMS, which are common vectors for:
- Phishing attacks
- Prompt injection
- Malicious links/attachments

**Mitigation:**
- Scan URLs before clicking (via computer-use)
- Never auto-execute attachments
- Flag suspicious sender patterns
- Rate-limit outbound messages

### AgentMail/AgentPhone API Keys

These are stored in the vault. If compromised:
- Attacker can read agent's email
- Attacker can send messages as the agent
- Attacker can intercept 2FA codes

**Mitigation:**
- Use separate API keys per agent
- Restrict API key permissions (read-only where possible)
- Monitor for unusual API usage

---

## 6. Payments Security

### Spending Limits

Both `VirtualCardAdapter` and `MPPAdapter` enforce:
- Per-transaction limits
- Daily spending limits
- Receipt tracking

**Risk:** If an attacker compromises the agent, they can spend up to the daily limit.

**Mitigation:**
- Set conservative limits for the threat model
- Require user confirmation for transactions above a threshold
- Alert on unusual spending patterns

### MPP Settlement

Stablecoin settlement requires private key management. **This is not yet implemented in alpha** but for production:
- Use hardware security modules (HSM) or secure enclaves
- Never store private keys in plaintext
- Implement multi-sig for large settlements

---

## 7. Inter-Layer Communication

### Trust Boundaries

| Layer | Trust Level | Notes |
|-------|-------------|-------|
| Model | Low | Commodity, no secrets |
| Harness | High | Orchestration logic, audited |
| Compute | High | Runs agent code |
| Identity | Low | Third-party, rented |
| Memory | High | Local, sensitive |
| Knowledge | High | Local, versionable |
| Auth | Critical | Credential storage |
| Payments | Critical | Financial operations |

### Recommended Architecture

```
┌─────────────────────────────────────────┐
│  Untrusted Zone (Identity, Model API)   │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ AgentMail   │  │ Model Provider  │  │
│  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  Trusted Zone (Local Infrastructure)    │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ Auth Vault  │  │ Knowledge Graph │  │
│  └─────────────┘  └─────────────────┘  │
│  ┌─────────────┐  ┌─────────────────┐  │
│  │ Substrate   │  │ Memory          │  │
│  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 8. Supply Chain Security

### Dependencies

Current dependencies:
- `PyYAML` — YAML parsing (sas.yaml)
- `pynacl` — Production encryption (libsodium bindings)
- `pytest` — Testing only

**Recommendations:**
- Pin all dependencies with hashes
- Use `pip-audit` or `safety` to check for known vulnerabilities
- Vendor critical dependencies
- Sign all releases

### Docker Images

- Use specific tags, not `latest`
- Verify image signatures
- Build from source where possible

---

## 9. Audit Trail

The auth broker records all tool calls. Ensure:
- Audit logs are append-only (tamper-evident)
- Logs are rotated and backed up
- Logs do not contain credential values (only metadata)
- Logs are reviewed weekly

---

## 10. Known Limitations (Alpha)

| Issue | Severity | Target Fix |
|-------|----------|------------|
| XOR encryption instead of libsodium | HIGH | v0.1.0 |
| No HTTPS certificate pinning | MEDIUM | v0.2.0 |
| No rate limiting on tool calls | MEDIUM | v0.2.0 |
| No multi-user support (single-tenant) | LOW | v1.0.0 |
| No HSM for payment keys | HIGH | v0.2.0 |
| No knowledge graph signing | LOW | v1.0.0 |

---

## 11. Conclusion

The Sovereign Agent Stack provides a meaningful security improvement over fully-rented agent stacks by keeping credentials and knowledge local. However, the current alpha implementation uses placeholder encryption and lacks several production hardening features.

**Do not use with production credentials until:**
1. Encryption is upgraded to libsodium with Argon2id KDF
2. All dependencies are pinned and audited
3. The compute substrate runs containers with proper isolation

**For alpha testing:**
- Use test API keys only
- Run in an isolated environment
- Do not store real payment credentials

---

## Appendix: Security Checklist

- [ ] libsodium encryption implemented
- [ ] All dependencies pinned with hashes
- [ ] Vault file permissions set to 600
- [ ] Knowledge directory permissions set to 700
- [ ] Docker containers run as non-root
- [ ] Audit logging enabled and reviewed
- [ ] HTTPS enforced for all API calls
- [ ] Spending limits configured conservatively
- [ ] API keys restricted to minimum permissions
- [ ] Backup encryption verified
