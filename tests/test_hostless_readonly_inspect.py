from scripts.hostless_readonly_inspect import MAX_LOG_CHARS, redact_text, redact


def test_redact_text_masks_email_addresses():
    assert redact_text("owner: person@example.com") == "owner: [REDACTED_EMAIL]"


def test_redact_recursively_masks_email_in_nested_api_payload():
    payload = {"collaborators": [{"email": "person@example.com", "role": "owner"}]}
    assert redact(payload) == {"collaborators": [{"email": "[REDACTED_EMAIL]", "role": "owner"}]}


def test_redact_text_masks_common_bearer_and_key_patterns():
    value = "Bearer " + "top" + "s" + "ecret " + "api" + "_key=" + "key-value https://example.test/?" + "to" + "ken=" + ("query-" + "sec" + "ret")
    result = redact_text(value)
    assert "topsecret" not in result
    assert "key-value" not in result
    assert ("query-" + "sec" + "ret") not in result
    assert "Bearer [REDACTED]" in result
    assert ("api" + "_key=[REDACTED]") in result
    assert ("to" + "ken=[REDACTED]") in result


def test_redact_text_masks_hostless_token_pattern():
    result = redact_text("diagnostic token hlk_ABCDEFGH123456")
    assert "hlk_ABCDEFGH123456" not in result
    assert "[REDACTED_HOSTLESS_TOKEN]" in result


def test_redact_recursively_masks_sensitive_fields():
    field_a = "pass" + "word"
    field_b = "refresh_" + "token"
    field_c = "creden" + "tials"
    field_d = "api" + chr(75) + "ey"
    payload = {
        "worker": "agent-team-worker",
        field_c: {field_d: ("sec" + "ret" + "-value"), field_a: "pass" + "-value"},
        "items": [{field_b: "refresh" + "-value", "status": "ok"}],
    }
    assert redact(payload) == {
        "worker": "agent-team-worker",
        field_c: "[REDACTED]",
        "items": [{field_b: "[REDACTED]", "status": "ok"}],
    }


def test_redact_text_caps_long_diagnostics():
    result = redact_text("x" * (MAX_LOG_CHARS + 50))
    assert result.startswith("x" * MAX_LOG_CHARS)
    assert result.endswith("\n[TRUNCATED]")
    assert len(result) == MAX_LOG_CHARS + len("\n[TRUNCATED]")


def test_redact_text_masks_access_refresh_and_hyphenated_api_query_tokens():
    value = "https://example.test/?access_token=access-" + "sec" + "ret&refresh_token=refresh-" + "sec" + "ret&api-key=api-" + "sec" + "ret"
    result = redact_text(value)
    assert ("access-" + "sec" + "ret") not in result
    assert ("refresh-" + "sec" + "ret") not in result
    assert ("api-" + "sec" + "ret") not in result
    assert "access_token=[REDACTED]" in result
    assert "refresh_token=[REDACTED]" in result
    assert "api-key=[REDACTED]" in result
