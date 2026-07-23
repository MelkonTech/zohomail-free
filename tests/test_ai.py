"""Tests for the LLM-integration helpers (no network required)."""

from zohomail.ai import (
    email_to_text,
    email_to_prompt,
    emails_to_messages,
    email_to_tool_result,
)

SAMPLE_EMAIL = {
    "from": "alice@example.com",
    "to": "bob@example.com",
    "date": "Mon, 24 Jul 2026 10:00:00 +0000",
    "subject": "Project update",
    "body": "The build is green.",
}


def test_email_to_text_includes_headers_and_body():
    text = email_to_text(SAMPLE_EMAIL)
    assert "From: alice@example.com" in text
    assert "Subject: Project update" in text
    assert "The build is green." in text


def test_email_to_text_falls_back_to_html_then_placeholder():
    assert "no body" in email_to_text({}).lower()
    assert "<b>hi</b>" in email_to_text({"body_html": "<b>hi</b>"})


def test_email_to_prompt_prepends_instruction():
    prompt = email_to_prompt(SAMPLE_EMAIL, instruction="Summarise:")
    assert prompt.startswith("Summarise:")
    assert "Project update" in prompt


def test_emails_to_messages_shape():
    msgs = emails_to_messages([SAMPLE_EMAIL], system="Do the thing.")
    assert len(msgs) == 2
    assert msgs[0] == {"role": "system", "content": "Do the thing."}
    assert msgs[1]["role"] == "user"
    assert "Project update" in msgs[1]["content"]


def test_email_to_tool_result_shape():
    result = email_to_tool_result(SAMPLE_EMAIL)
    assert result["type"] == "tool_result"
    assert "Project update" in result["content"]
