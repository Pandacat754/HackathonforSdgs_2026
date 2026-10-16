"""Locally rendered reply drafts with no commitments or autonomous actions."""


def format_reply(
    message,
    category,
    response_style="formal",
    reply_language="auto",
    *,
    preferred_tone="Professional",
):
    """Render a safe receipt or deferral in the requested register."""
    if category == "needs_human_review":
        return None
    if category not in ("urgent", "wait_until_morning"):
        return None

    body = message.get("body", message.get("message", ""))
    chinese = reply_language == "zh" or (
        reply_language == "auto"
        and any("\u4e00" <= character <= "\u9fff" for character in body)
    )
    style = response_style if response_style in ("formal", "warm", "concise") else "formal"
    relationship = message.get("sender_relationship", "Other")
    preferred_tone = preferred_tone if isinstance(preferred_tone, str) else "Professional"
    casual_tones = {"Casual", "Friendly", "Empathetic"}
    formal_tones = {"Formal", "Professional", "Respectful"}
    if relationship in ("Lecturer", "Client") and preferred_tone in casual_tones:
        style = "formal"
    elif relationship == "Friend" and preferred_tone in formal_tones:
        style = "warm"
    templates = {
        "formal": {
            "urgent": (
                "此消息已由助手接收。本人尚未审阅请求或承诺采取任何行动。"
                if chinese else
                "This message has been received by the assistant. The recipient has not yet reviewed the request or committed to any action."
            ),
            "wait_until_morning": (
                "此消息可留待下一个工作时段查看；本人尚未审阅或接受此请求。"
                if chinese else
                "This message can be held for the next working period. The recipient has not yet reviewed or accepted the request."
            ),
        },
        "warm": {
            "urgent": (
                "助手已收到此消息。本人尚未审阅或接受此请求。"
                if chinese else
                "This message has reached the assistant. The recipient has not yet reviewed or accepted the request."
            ),
            "wait_until_morning": (
                "这条消息可以留到下一个工作时段再看；本人尚未查看或答应此请求。"
                if chinese else
                "This message can wait for the next working period. The recipient has not yet reviewed or accepted the request."
            ),
        },
        "concise": {
            "urgent": (
                "助手已收到消息，待本人审阅；尚未同意采取行动。"
                if chinese else
                "Received by the assistant; awaiting the recipient's review. No action has been agreed to."
            ),
            "wait_until_morning": (
                "可留待下个工作时段查看；尚未审阅或接受请求。"
                if chinese else
                "Can wait until the next working period; not yet reviewed or accepted."
            ),
        },
    }
    prefix = ""
    if relationship == "Lecturer":
        prefix = "謝謝您的消息。" if chinese else "Thank you for your message. "
    elif relationship == "Client":
        prefix = "感謝您的聯絡。" if chinese else "Thank you for contacting us. "
    elif relationship == "Friend":
        prefix = "謝謝你發消息！" if chinese else "Thanks for the message! "
    return f"{prefix}{templates[style][category]}"
