"""Tests for the identity adapters."""

import pytest

from sas.layers.identity import (
    AgentMailAdapter,
    AgentPhoneAdapter,
    MockEmailAdapter,
    MockPhoneAdapter,
    Inbox,
    Email,
    PhoneNumber,
    Call,
)


class TestAgentMailAdapter:
    """Tests for the AgentMail email adapter."""

    def test_provision_inbox(self) -> None:
        """Provisioning creates an inbox."""
        adapter = AgentMailAdapter(api_key="test-key")
        inbox = adapter.provision(username="hello", domain="agentmail.to")
        assert isinstance(inbox, Inbox)
        assert inbox.username == "hello"
        assert inbox.domain == "agentmail.to"
        assert inbox.id is not None

    def test_send_email(self) -> None:
        """Sending an email works."""
        adapter = AgentMailAdapter(api_key="test-key")
        inbox = adapter.provision(username="hello", domain="agentmail.to")
        message = Email(
            from_="hello@agentmail.to",
            to="world@example.com",
            subject="Test",
            body="Hello!",
        )
        adapter.send(inbox, message)
        # No exception = pass

    def test_watch_returns_emails(self) -> None:
        """Watch yields incoming emails."""
        adapter = AgentMailAdapter(api_key="test-key")
        inbox = adapter.provision(username="hello", domain="agentmail.to")
        emails = list(adapter.watch(inbox))
        assert isinstance(emails, list)


class TestAgentPhoneAdapter:
    """Tests for the AgentPhone telephony adapter."""

    def test_provision_number(self) -> None:
        """Provisioning creates a phone number."""
        adapter = AgentPhoneAdapter(api_key="test-key")
        number = adapter.provision(region="US")
        assert isinstance(number, PhoneNumber)
        assert number.region == "US"
        assert "voice" in number.capabilities

    def test_call(self) -> None:
        """Making a call works."""
        adapter = AgentPhoneAdapter(api_key="test-key")
        number = adapter.provision(region="US")
        call = adapter.call(number, "+15551234567")
        assert isinstance(call, Call)
        assert call.from_number == number.number
        assert call.to_number == "+15551234567"
        assert call.status == "completed"

    def test_sms(self) -> None:
        """Sending SMS works."""
        adapter = AgentPhoneAdapter(api_key="test-key")
        number = adapter.provision(region="US")
        adapter.sms(number, "Hello via SMS")
        # No exception = pass


class TestMockEmailAdapter:
    """Tests for the mock email adapter (local dev)."""

    def test_provision_inbox(self) -> None:
        """Mock provisioning creates an inbox."""
        adapter = MockEmailAdapter()
        inbox = adapter.provision(username="test", domain="localhost")
        assert isinstance(inbox, Inbox)
        assert inbox.username == "test"
        assert inbox.domain == "localhost"

    def test_send_and_receive(self) -> None:
        """Can send and receive emails."""
        adapter = MockEmailAdapter()
        inbox = adapter.provision(username="test", domain="localhost")

        # Send an email
        message = Email(
            from_="test@localhost",
            to="other@localhost",
            subject="Test",
            body="Hello!",
        )
        adapter.send(inbox, message)

        # Watch should return the sent email
        emails = list(adapter.watch(inbox))
        assert len(emails) == 1
        assert emails[0].subject == "Test"
        assert emails[0].body == "Hello!"

    def test_multiple_emails(self) -> None:
        """Multiple emails are queued."""
        adapter = MockEmailAdapter()
        inbox = adapter.provision(username="test", domain="localhost")

        for i in range(3):
            adapter.send(inbox, Email(
                from_="test@localhost",
                to=f"user{i}@localhost",
                subject=f"Email {i}",
                body=f"Body {i}",
            ))

        emails = list(adapter.watch(inbox))
        assert len(emails) == 3
        assert emails[0].subject == "Email 0"
        assert emails[2].subject == "Email 2"


class TestMockPhoneAdapter:
    """Tests for the mock phone adapter (local dev)."""

    def test_provision_number(self) -> None:
        """Mock provisioning creates a number."""
        adapter = MockPhoneAdapter()
        number = adapter.provision(region="US")
        assert isinstance(number, PhoneNumber)
        assert number.region == "US"

    def test_call_records_call(self) -> None:
        """Making a call records it."""
        adapter = MockPhoneAdapter()
        number = adapter.provision(region="US")
        call = adapter.call(number, "+15551234567")
        assert isinstance(call, Call)
        assert call.status == "completed"

    def test_sms_records_message(self) -> None:
        """Sending SMS records the message."""
        adapter = MockPhoneAdapter()
        number = adapter.provision(region="US")
        adapter.sms(number, "Test message")

        # Verify it was recorded
        messages = adapter.get_sent_messages(number)
        assert len(messages) == 1
        assert messages[0] == "Test message"

    def test_call_history(self) -> None:
        """Call history is tracked."""
        adapter = MockPhoneAdapter()
        number = adapter.provision(region="US")

        adapter.call(number, "+15551111111")
        adapter.call(number, "+15552222222")

        history = adapter.get_call_history(number)
        assert len(history) == 2
        assert history[0].to_number == "+15551111111"
        assert history[1].to_number == "+15552222222"
