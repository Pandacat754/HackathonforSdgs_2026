import streamlit as st
import json

from agents.classifier import classify_message
from agents.reply_generator import generate_reply

with open("data/sample_messages.json", "r") as f:
    messages = json.load(f)

st.title("Weekend Message Agent")

for msg in messages:

    st.subheader(msg["sender"])
    st.write(msg["message"])

    if st.button(f"Analyze {msg['id']}"):

        result = classify_message(msg)
        reply = generate_reply(msg)

        st.write("### Classification")
        st.write(result["classification"])

        st.write("### Urgency Score")
        st.write(result["urgency_score"])

        st.write("### Reason")
        st.write(result["reason"])

        st.write("### Suggested Reply")
        st.write(reply["suggested_reply"])