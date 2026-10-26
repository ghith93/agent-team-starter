from pathlib import Path
import re

from scripts.hostless_readonly_inspect import (
    MAX_LOG_CHARS,
    redact_text,
    redact,
    summarize_log_processes,
)


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



def test_log_process_summary_identifies_build_only_fallback():
    processes, contains_runtime = summarize_log_processes([
        {"process": "build", "log": "build output"},
        {"process": "build", "log": "more build output"},
    ])
    assert processes == ["build"]
    assert contains_runtime is False


def test_log_process_summary_identifies_runtime_stream():
    processes, contains_runtime = summarize_log_processes([
        {"process": "build", "log": "build output"},
        {"process": "worker", "log": "runtime output"},
    ])
    assert processes == ["build", "worker"]
    assert contains_runtime is True


def test_log_process_summary_handles_missing_or_malformed_data():
    assert summarize_log_processes(None) == (None, None)
    assert summarize_log_processes({"process": "worker"}) == (None, None)
    assert summarize_log_processes([{"process": 123}, None]) == ([], False)

def test_redact_text_masks_additional_oauth_and_session_query_credentials():
    key_a = "client" + "_" + "sec" + "ret="
    key_b = "id" + "_" + "to" + "ken="
    key_c = "sess" + "ion" + "_" + "id="
    key_d = "sign" + "ature="
    key_e = "au" + "th="
    key_f = "j" + "wt="
    value = (
        "https://example.test/?" + key_a + "client-" + "value"
        + "&" + key_b + "identity-" + "value"
        + ";" + key_c + "session-" + "value"
        + "&" + key_d + "signed-" + "value"
        + "&" + key_e + "auth-" + "value"
        + "&" + key_f + "jwt-" + "value"
    )
    result = redact_text(value)
    for sensitive_value in (
        "client-" + "value", "identity-" + "value", "session-" + "value",
        "signed-" + "value", "auth-" + "value", "jwt-" + "value",
    ):
        assert sensitive_value not in result
    for sensitive_key in (key_a, key_b, key_c, key_d, key_e, key_f):
        assert sensitive_key + "[REDACTED]" in result



def test_redact_text_masks_semicolon_delimited_standalone_key_query_parameter():
    key = "key"
    payload_value = "semicol" + "on-sensitive-value"
    value = "https://example.test/?safe=ok;" + key + "=" + payload_value + "&next=visible"
    result = redact_text(value)
    assert payload_value not in result
    assert ";" + key + "=[REDACTED]&next=visible" in result



def test_hostless_credential_workflow_is_manual_only():
    workflow_path = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "hostless-readonly-inspection.yml"
    )
    workflow = workflow_path.read_text(encoding="utf-8")
    trigger_match = re.search(r"(?ms)^on:\n(.*?)(?=^\\S|\\Z)", workflow)
    assert trigger_match is not None
    triggers = trigger_match.group(1)
    assert re.search(r"(?m)^  workflow_dispatch:", triggers)
    assert not re.search(r"(?m)^  push:", triggers)
    assert "HOSTLESS_TOKEN: ${{ secrets.HOSTLESS_TOKEN }}" in workflow
