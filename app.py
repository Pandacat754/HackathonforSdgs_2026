import json
from pathlib import Path

import streamlit as st

from agents.classifier import classify_message
from agents.reply_generator import generate_reply

DATA_FILE = Path(__file__).resolve().parent / "data" / "sample_messages.json"

with DATA_FILE.open("r", encoding="utf-8") as f:
    messages = json.load(f)

st.title("Weekend Message Agent")
st.write("Analyze sample messages and review draft-only suggestions. Nothing is sent or queued automatically.")

if "message_analyses" not in st.session_state:
    st.session_state["message_analyses"] = {}

for msg in messages:
    st.subheader(msg["sender"])
    st.write(msg["message"])

    if st.button(f"Analyze {msg['id']}"):
        result = classify_message(msg)
        reply = generate_reply(msg, result)
        st.session_state["message_analyses"][msg["id"]] = {
            "result": result,
            "reply": reply,
        }

    analysis = st.session_state["message_analyses"].get(msg["id"])
    if analysis:
        result = analysis["result"]
        reply = analysis["reply"]

        if result["source"] == "mock":
            st.info("Offline rule demo — no AI model was called.")
        elif result["source"] == "fallback":
            st.error("Analysis was unavailable or invalid. Human review is required.")
        elif result["source"] == "guardrail":
            st.warning("A local safety check routed this message for human review.")

        st.write("### Classification")
        st.write(result["classification"])

        st.write("### Urgency Score")
        st.write(result["urgency_score"])

        st.write("### Demo Confidence (not calibrated)")
        st.write(result["confidence"])

        st.write("### Reason")
        st.write(result["reason"])

        st.write("### Suggested Reply")
        if reply["suggested_reply"] is None:
            st.write("No safe reply draft is available; please handle this message manually.")
        else:
            st.write(reply["suggested_reply"])

        st.write("User confirmation is required. This page does not send replies or add messages to a queue.")