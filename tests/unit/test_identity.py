# — Unit tests for the Identity Adapters (Phase 6) —

import pytest

from sas.layers.identity import (
    AgentMailAdapter,
    AgentPhoneAdapter,
    Call,
    Email,
    EmailIdentity,
    Inbox,
    MockEmailAdapter,
    MockPhoneAdapter,
    PhoneIdentity,
    PhoneNumber,
)


# ── Inbox / Email / PhoneNumber / Call dataclasses ─────────────────────────────

class TestInbox:
    def test_create_inbox(self):
        inbox = Inbox(id="i1", username="agent", domain="agentmail.to", created_at="2024-01-01T00:00:00Z")
        assert inbox.username == "agent"
        assert inbox.domain == "agentmail.to"


class TestEmail:
    def test_create_email(self):
        email = Email(
            from_="alice@example.com",
            to="agent@agentmail.to",
            subject="Hello",
            body="Hi there",
        )
        email.thread_id is None
        assert email.subject == "Hello"


class TestPhoneNumber:
    def test_create_phone(self):
        phone = PhoneNumber(id="p1", number="+15551234567", region="US", capabilities=["voice", "sms"])
        assert phone.region == "US"
        assert "sms" in phone.capabilities


class TestCall:
    def test_create_call(self):
        call = Call(id="c1", from_number="+15551234567", to_number="+15559876543", status="completed")
        assert call.status == "completed"
        assert call.to_number == "+15559876543"


# ── MockEmailAdapter ────────────────────────────────────────────────────────────

class TestMockEmailAdapter:
    def test_provision(self):
        adapter = MockEmailAdapter()
        inbox = adapter.provision("myagent", "agentmail.to")
        assert inbox.id.startswith("mock_inbox_")
        assert inbox.username == "myagent"
        assert inbox.domain == "agentmail.to"

    def test_provision_stores_inbox(self):
        adapter = MockEmailAdapter()
        inbox = adapter.provision("agent", "agentmail.to")
        assert inbox.id in adapter._inboxes

    def test_send(self):
        adapter = MockEmailAdapter()
        inbox = adapter.provision("agent", "agentmail.to")
        email = Email(
            from_="agent@agentmail.to",
            to="client@example.com",
            subject="Proposal",
            body="Here is my proposal.",
        )
        adapter.send(inbox, email)
        sent = adapter.watch(inbox)
        assert len(sent) == 1
        assert sent[0].subject == "Proposal"

    def test_watch_returns_sent(self):
        adapter = MockEmailAdapter()
        inbox = adapter.provision("agent", "agentmail.to")
        assert adapter.watch(inbox) == []
        adapter.send(inbox, Email("a@b.com", "c@d.com", "Hi", "Body"))
        assert len(adapter.watch(inbox)) == 1

    def test_send_multiple(self):
        adapter = MockEmailAdapter()
        inbox = adapter.provision("agent", "agentmail.to")
        for i in range(3):
            adapter.send(inbox, Email("a@b.com", "c@d.com", f"Subject {i}", "Body"))
        assert len(adapter.watch(inbox)) == 3


# ── MockPhoneAdapter ────────────────────────────────────────────────────────────

class TestMockPhoneAdapter:
    def test_provision(self):
        adapter = MockPhoneAdapter()
        phone = adapter.provision("US")
        assert phone.id.startswith("mock_phone_")
        assert phone.region == "US"
        assert "+1555" in phone.number

    def test_provision_stores_number(self):
        adapter = MockPhoneAdapter()
        phone = adapter.provision("US")
        assert phone.id in adapter._numbers

    def test_call(self):
        adapter = MockPhoneAdapter()
        phone = adapter.provision("US")
        call = adapter.call(phone, "+15559876543")
        assert call.id.startswith("mock_call_")
        assert call.to_number == "+15559876543"
        assert call.status == "completed"

    def test_call_history(self):
        adapter = MockPhoneAdapter()
        phone = adapter.provision("US")
        adapter.call(phone, "+15559876543")
        adapter.call(phone, "+15551234567")
        history = adapter.get_call_history(phone)
        assert len(history) == 2

    def test_sms(self):
        adapter = MockPhoneAdapter()
        phone = adapter.provision("US")
        adapter.sms(phone, "Hello world")
        messages = adapter.get_sent_messages(phone)
        assert len(messages) == 1
        assert messages[0] == "Hello world"

    def test_sms_multiple(self):
        adapter = MockPhoneAdapter()
        phone = adapter.provision("US")
        for msg in ["Hi", "Hello", "Hey"]:
            adapter.sms(phone, msg)
        assert len(adapter.get_sent_messages(phone)) == 3


# ── AgentMailAdapter (stub) ─────────────────────────────────────────────────────

class TestAgentMailAdapter:
    def test_provision(self):
        adapter = AgentMailAdapter(api_key="test-key")
        inbox = adapter.provision("myagent", "agentmail.to")
        assert inbox.id.startswith("inbox_")
        assert inbox.username == "myagent"
        assert inbox.domain == "agentmail.to"

    def test_send_does_not_raise(self):
        adapter = AgentMailAdapter(api_key="test-key")
        inbox = adapter.provision("agent", "agentmail.to")
        email = Email("a@b.com", "c@d.com", "Subject", "Body")
        adapter.send(inbox, email)  # Stub, should not raise

    def test_watch_returns_empty(self):
        adapter = AgentMailAdapter(api_key="test-key")
        inbox = adapter.provision("agent", "agentmail.to")
        assert adapter.watch(inbox) == []


# ── AgentPhoneAdapter (stub) ────────────────────────────────────────────────────

class TestAgentPhoneAdapter:
    def test_provision(self):
        adapter = AgentPhoneAdapter(api_key="test-key")
        phone = adapter.provision("US")
        assert phone.id.startswith("phone_")
        assert phone.region == "US"

    def test_call(self):
        adapter = AgentPhoneAdapter(api_key="test-key")
        phone = adapter.provision("US")
        call = adapter.call(phone, "+15559876543")
        assert call.id.startswith("call_")
        assert call.to_number == "+15559876543"

    def test_sms_does_not_raise(self):
        adapter = AgentPhoneAdapter(api_key="test-key")
        phone = adapter.provision("US")
        adapter.sms(phone, "Test message")


# ── Protocol conformance ────────────────────────────────────────────────────────

class TestProtocolConformance:
    def test_mock_email_implements_email_identity(self):
        from typing import runtime_checkable
        # MockEmailAdapter structurally satisfies EmailIdentity
        adapter = MockEmailAdapter()
        assert hasattr(adapter, "provision")
        assert hasattr(adapter, "send")
        assert hasattr(adapter, "watch")

    def test_mock_phone_implements_phone_identity(self):
        adapter = MockPhoneAdapter()
        assert hasattr(adapter, "provision")
        assert hasattr(adapter, "call")
        assert hasattr(adapter, "sms")
