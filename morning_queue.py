"""Build the demo morning review list from this session's analysis results."""


def get_queue(messages, analyses, review_decisions):
    """Include non-urgent messages and human-review cases approved for morning."""
    queue = []
    for message in messages:
        analysis = analyses.get(message["id"])
        if not analysis:
            continue
        result = analysis["result"]
        category = result.get("category")
        if category != "wait_until_morning" and not (
            category == "needs_human_review"
            and review_decisions.get(message["id"]) is True
        ):
            continue
        queue.append({
            "id": message["id"],
            "sender": message["sender"],
            "message": message["message"],
            "received_at": message.get("received_at"),
            "category": result["category"],
            "classification": result["classification"],
        })
    return queue
