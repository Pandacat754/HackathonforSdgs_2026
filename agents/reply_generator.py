"""Draft-only reply API, preserving A's generate_reply(message) call."""
from .classifier import classify_message
from .reply_styles import format_reply


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
    elif user_policy is not None and draft is not None:
        draft_category = {
            "receipt": "urgent",
            "deferred": "wait_until_morning",
        }.get(result.get("reply_style"), result["category"])
        draft = format_reply(
            message,
            draft_category,
            user_policy.get("response_style", "formal"),
            user_policy.get("reply_language", "auto"),
            preferred_tone=user_policy.get("preferred_tone", "Professional"),
        )
    return {"suggested_reply": draft, "requires_user_confirmation": True,
            "is_draft": True, "source": result.get("source", "fallback")}


def generate_suggested_reply(message, triage_result):
    """Handoff compatibility alias returning just the optional draft string."""
    return generate_reply(message, triage_result)["suggested_reply"]
