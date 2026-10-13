"""Draft-only reply API, preserving A's generate_reply(message) call."""
from .classifier import classify_message


def generate_reply(message, triage_result=None, user_policy=None, *, mode=None):
    """Pass the previous result to avoid a second model call.

    triage_result must come from classify_message for THIS message. It is not an
    external/untrusted input interface. Nothing here sends or queues a message.
    """
    result = triage_result if triage_result is not None else classify_message(
        message, user_policy, mode=mode)
    draft = result.get("suggested_reply")
    if result.get("category") not in ("urgent", "wait_until_morning"):
        draft = None
    return {"suggested_reply": draft, "requires_user_confirmation": True,
            "is_draft": True, "source": result.get("source", "fallback")}


def generate_suggested_reply(message, triage_result):
    """Handoff compatibility alias returning just the optional draft string."""
    return generate_reply(message, triage_result)["suggested_reply"]
