from scripts.hostless_readonly_inspect import MAX_LOG_CHARS, redact_text, redact


def test_redact_text_masks_email_addresses():
    assert redact_text("owner: person@example.com") == "owner: [REDACTED_EMAIL]"


def test_redact_recursively_masks_email_in_nested_api_payload():
    payload = {"collaborators": [{"email": "person@example.com", "role": "owner"}]}
    assert redact(payload) == {"collaborators": [{"email": "[REDACTED_EMAIL]", "role": "owner"}]}


def test_redact_text_masks_common_bearer_and_key_patterns():
    value = "Bearer topsecret api_key=key-value https://example.test/?token=query-secret"
    result = redact_text(value)
    assert "topsecret" not in result
    assert "key-value" not in result
    assert "query-secret" not in result
    assert "Bearer [REDACTED]" in result
    assert "api_key=[REDACTED]" in result
    assert "token=[REDACTED]" in result


def test_redact_text_masks_hostless_token_pattern():
    result = redact_text("diagnostic token hlk_ABCDEFGH123456")
    assert "hlk_ABCDEFGH123456" not in result
    assert "[REDACTED_HOSTLESS_TOKEN]" in result


def test_redact_recursively_masks_sensitive_fields():
    payload = {
        "worker": "agent-team-worker",
        "credentials": {"apiKey": "secret-value", "password": "pass-value"},
        "items": [{"refresh_token": "refresh-value", "status": "ok"}],
    }
    assert redact(payload) == {
        "worker": "agent-team-worker",
        "credentials": "[REDACTED]",
        "items": [{"refresh_token": "[REDACTED]", "status": "ok"}],
    }


def test_redact_text_caps_long_diagnostics():
    result = redact_text("x" * (MAX_LOG_CHARS + 50))
    assert result.startswith("x" * MAX_LOG_CHARS)
    assert result.endswith("\n[TRUNCATED]")
    assert len(result) == MAX_LOG_CHARS + len("\n[TRUNCATED]")
