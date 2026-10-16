"""A-compatible triage with explicit mock/live modes and conservative fallback."""
import os
import re

from . import llm_client
from .models import CATEGORIES, normalise_input, parse_decision, timestamp
from .prompts import build_messages, PROMPT_VERSION
from .reply_styles import format_reply

INJECTION = r"ignore.{0,40}(instructions|rules)|system\s*prompt|you are now|<\|.*?\|>|忽略.{0,12}(指令|规则|規則)|泄露.{0,8}提示"
SENSITIVE = (r"\b(payment|transfer|bank|salary|payroll|legal|lawsuit|contract|hr|"
             r"dismissal|performance review|patient|password|credential|approve|approval)\b"
             r"|付款|转账|轉賬|薪資|薪资|合約|合同|法律|人事|病人|患者|密碼|密码|批准")
INCIDENT = (r"production is down|customers cannot log in|active.{0,20}(breach|leak)"
            r"|\bfire in\b|正在.{0,8}(洩漏|泄露)|系統故障|系统故障|服務中斷|服务中断")
NEGATION = r"\b(not|no|resolved|fixed|cancelled|canceled|yesterday|example|hypothetical)\b|已修復|已修复|不用|不需要|不急|昨天|演練|演练"
DEFERRED = (r"\bfyi\b|when you (are|get) back|no (action|reply|response).{0,12}(needed|required)"
            r"|not urgent|no rush|can wait|next month|meeting notes|team lunch"
            r"|明天.{0,6}(再|上班)|聽日.{0,6}(再|返工)|不急|僅供參考|仅供参考|下個月|下个月")
TONIGHT = r"\btonight\b|before.{0,12}(8\s*am|08:00).{0,12}tomorrow|今晚|今晩"


def _match(pattern, text):
    return bool(re.search(pattern, text, re.I))


def _guard(body):
    if _match(INJECTION, body):
        return "Possible instructions targeting the agent require human review."
    if _match(SENSITIVE, body):
        return "The message involves sensitive information, approval or a potential commitment."
    return None


def _decision(category, score, confidence, reason):
    style = {"urgent": "receipt", "wait_until_morning": "deferred",
             "needs_human_review": "none"}[category]
    return {"category": category, "urgency_score": score, "confidence": confidence,
            "reason": reason, "reply_style": style}


def _mock(message):
    """Transparent limited demo rules, not a substitute for semantic AI evaluation."""
    body = message["body"]
    incident = _match(INCIDENT, body)
    tonight = _match(TONIGHT, body)
    deferred = _match(DEFERRED, body)
    negated = _match(NEGATION, body)
    if (incident and negated) or (tonight and (deferred or negated)):
        return _decision("needs_human_review", .5, .5,
                         "Mixed timing or negated incident wording needs interpretation.")
    if incident:
        return _decision("urgent", .95, .90, "The message describes a current operational or safety incident.")
    deadline = timestamp(message.get("deadline_at"))
    start = timestamp(message.get("user_workday_starts_at"))
    if deadline:
        if not start:
            return _decision("needs_human_review", .6, .5, "A deadline is given but the next working period is unknown.")
        if deadline <= start:
            return _decision("urgent", .9, .9, "The deadline is at or before the next working period.")
        return _decision("wait_until_morning", .25, .85, "The stated deadline falls after the next working period begins.")
    if tonight:
        # Overnight shifts or explicit calendar context require semantic interpretation.
        if start:
            return _decision("needs_human_review", .7, .5, "Compare the textual deadline with the supplied working schedule.")
        return _decision("urgent", .85, .78, "The message explicitly requests action tonight or before tomorrow morning.")
    if deferred:
        return _decision("wait_until_morning", .15, .85, "The message is informational or explicitly allows later review.")
    return _decision("needs_human_review", .5, .4, "There is not enough clear context for a confident classification.")


def _draft(style, message, policy):
    zh = policy.get("reply_language") == "zh" or (
        policy.get("reply_language", "auto") == "auto"
        and re.search(r"[\u4e00-\u9fff]", message.get("body", "")))
    if style == "none":
        return None
    if style == "deferred":
        return ("此消息可留待下一个工作时段查看；本人尚未阅读或接受此请求。"
                if zh else "This message can be held for the next working period. The recipient has not yet reviewed or accepted the request.")
    return ("此消息已由助手接收；本人尚未阅读或承诺采取行动。"
            if zh else "This message has reached the assistant. The recipient has not yet reviewed it or committed to any action.")


def _result(message, policy, decision, source, error_code=None):
    category = decision["category"]
    label, action = CATEGORIES[category]
    body = message.get("body", "")
    queued = category == "wait_until_morning"
    draft_category = {
        "receipt": "urgent",
        "deferred": "wait_until_morning",
    }.get(decision["reply_style"])
    return {
        "message_id": message.get("id"),
        "classification": label,  # Original A interface
        "category": category,    # Stable machine-readable value for C
        "urgency_score": decision["urgency_score"],
        "confidence": decision["confidence"],
        "reason": decision["reason"],
        "action": action,
        "suggested_reply": format_reply(
            message,
            draft_category,
            policy.get("response_style", "formal"),
            policy.get("reply_language", "auto"),
            preferred_tone=policy.get("preferred_tone", "Professional"),
        ),
        "reply_style": decision["reply_style"],
        "queue_title": " ".join(body.split())[:100] if queued else None,
        # No invented tomorrow date, weekend calendar or fixed timezone.
        "queue_for": message.get("user_workday_starts_at") if queued else None,
        "requires_user_confirmation": True,
        "source": source,
        "error_code": error_code,
        "prompt_version": PROMPT_VERSION,
    }


def _fallback(message, policy, reason, code):
    return _result(message, policy,
                   _decision("needs_human_review", .5, 0.0, reason), "fallback", code)


def classify_message(message, user_policy=None, *, mode=None):
    """Return a dict compatible with A; never send, notify or enqueue anything.

    mode='mock' (default): built-in classification rules.
    mode='llm': configured API; any failure -> human review, never silent mock.
    """
    try:
        clean, policy = normalise_input(message, user_policy)
    except (ValueError, TypeError, OverflowError):
        return _fallback({}, {}, "Input is missing, conflicting or invalid; please review it.", "invalid_input")
    selected = mode if mode is not None else os.environ.get("SILENCER_MODE", "mock")
    if selected not in ("mock", "llm"):
        return _fallback(clean, policy, "Agent mode is invalid; please check configuration.", "invalid_mode")
    guarded = _guard(clean["body"])
    if guarded:
        score = .9 if _match(TONIGHT, clean["body"]) or _match(INCIDENT, clean["body"]) else .5
        return _result(clean, policy, _decision("needs_human_review", score, 0.0, guarded), "guardrail")
    if selected == "mock":
        decision = _mock(clean)
        if not clean.get("received_at") or not clean.get("user_workday_starts_at"):
            decision["confidence"] = min(decision["confidence"], .80)
        source = "mock"
    else:
        try:
            decision = parse_decision(llm_client.complete(build_messages(clean, policy)))
        except (llm_client.LLMError, ValueError, TypeError, KeyError):
            return _fallback(clean, policy, "AI analysis was unavailable or invalid; human review is required.", "llm_unavailable_or_invalid")
        source = "llm"
    if decision["confidence"] < policy["confidence_threshold"] and decision["category"] != "needs_human_review":
        decision = {**decision, "category": "needs_human_review", "reply_style": "none",
                    "reason": "Confidence is below the selected threshold; human review is required."}
    # Derive actions locally: model output can never choose an executable action.
    if decision["category"] == "needs_human_review":
        decision["reply_style"] = "none"
    return _result(clean, policy, decision, source)


def triage_message(message, user_policy=None, *, mode=None):
    """Alias for the handoff document's suggested interface."""
    return classify_message(message, user_policy, mode=mode)
