"""Shared, dependency-free boundary validation for the B module."""
import json
import math
from datetime import datetime

CATEGORIES = {
    "urgent": ("Urgent", "notify_user_now"),
    "wait_until_morning": ("Non-Urgent", "queue_for_morning"),
    "needs_human_review": ("Needs Human Review", "ask_user_to_review"),
}
REPLY_STYLES = {"receipt", "deferred", "none"}


def unit_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Expected a numeric score")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Score outside [0, 1]")
    return float(value)


def timestamp(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Timestamp must be text")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp needs a timezone offset")
    return parsed


def normalise_input(message, policy=None):
    if not isinstance(message, dict):
        raise ValueError("Message must be an object")
    # A uses `message`; the handoff document uses `body`. Support both.
    body = message.get("message", message.get("body"))
    if not isinstance(body, str) or not body.strip() or len(body) > 8000:
        raise ValueError("Message must contain 1–8000 characters")
    if "message" in message and "body" in message and message["body"] != body:
        raise ValueError("Conflicting message and body fields")
    clean = {"body": body.strip()}
    for key in ("id", "sender", "sender_relationship", "channel",
                "received_at", "user_workday_starts_at", "deadline_at"):
        value = message.get(key)
        if value is not None:
            if not isinstance(value, str) or len(value) > 500:
                raise ValueError("Invalid metadata")
            clean[key] = value
    for key in ("received_at", "user_workday_starts_at", "deadline_at"):
        timestamp(clean.get(key))
    received = timestamp(clean.get("received_at"))
    start = timestamp(clean.get("user_workday_starts_at"))
    if received and start and start <= received:
        raise ValueError("Next working period must follow receipt")
    if policy is None:
        policy = {}
    if not isinstance(policy, dict):
        raise ValueError("Policy must be an object")
    # Only explicitly supported policy fields reach the model.
    threshold = unit_number(policy.get("confidence_threshold", 0.70))
    language = policy.get("reply_language", "auto")
    if language not in ("auto", "en", "zh"):
        raise ValueError("Unsupported reply language")
    return clean, {"confidence_threshold": threshold, "reply_language": language}


def parse_decision(raw):
    """Reject malformed, incomplete, non-finite and unexpected model data."""
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON field")
            result[key] = value
        return result

    if not isinstance(raw, str) or len(raw) > 16000:
        raise ValueError("Invalid model response")
    data = json.loads(raw, object_pairs_hook=unique_object)
    required = {"category", "urgency_score", "confidence", "reason", "reply_style"}
    if not isinstance(data, dict) or set(data) != required:
        raise ValueError("Unexpected model schema")
    if data["category"] not in CATEGORIES or data["reply_style"] not in REPLY_STYLES:
        raise ValueError("Invalid enum")
    data["urgency_score"] = unit_number(data["urgency_score"])
    data["confidence"] = unit_number(data["confidence"])
    if not isinstance(data["reason"], str) or not 1 <= len(data["reason"].strip()) <= 400:
        raise ValueError("Invalid reason")
    if data["category"] == "needs_human_review" and data["reply_style"] != "none":
        raise ValueError("Review case cannot contain a reply")
    if data["category"] == "urgent" and data["reply_style"] == "deferred":
        raise ValueError("Urgent case cannot promise deferral")
    return data
