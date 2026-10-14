import html
import json
import os
from pathlib import Path

import streamlit as st

from agents.classifier import classify_message
from agents.reply_generator import generate_reply
from morning_queue import get_queue

APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "data" / "sample_messages.json"
ICON_FILE = APP_DIR / "assets" / "icon.png"

st.set_page_config(page_title="Silencer", page_icon=str(ICON_FILE), layout="wide")
st.markdown(
    """
    <style>
    .stMainBlockContainer {
        max-width: 1120px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        font-size: var(--app-font-size, 16px);
    }
    .st-key-search-strip {
        background: #ffffff;
        border-radius: 4px;
        padding: 0.25rem 0.75rem 0;
        margin: 0.75rem 0 1.5rem;
    }
    .message-count-table {
        position: relative;
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        border: 1px solid #555;
        border-radius: 12px;
        text-align: center;
        margin: 0.75rem 0 1.5rem;
        overflow: hidden;
    }
    .message-count-table > div {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 3.5rem;
        padding: 0.65rem 0.4rem;
        font-size: 1.1em;
    }
    .message-count-table > div {
        justify-content: center;
        text-align: center;
    }
    .message-count-table::before {
        position: absolute;
        inset: 0;
        content: "";
        pointer-events: none;
        background: linear-gradient(
            to right,
            transparent calc(33.333% - 0.5px),
            #555 calc(33.333% - 0.5px),
            #555 calc(33.333% + 0.5px),
            transparent calc(33.333% + 0.5px),
            transparent calc(66.666% - 0.5px),
            #555 calc(66.666% - 0.5px),
            #555 calc(66.666% + 0.5px),
            transparent calc(66.666% + 0.5px)
        );
    }
    .message-count-label {
        border-bottom: 1px solid #555;
    }
    .st-key-analyze-all-messages [data-testid="stButton"] {
        display: flex;
        justify-content: flex-end;
        padding-left: 1.5rem;
    }
    .st-key-analyze-all-messages button {
        min-height: 5.75rem;
        border: 1px solid #555;
        border-radius: 18px;
        white-space: normal;
        width: 100%;
        max-width: none;
        font-size: 1.15rem !important;
        font-weight: 600;
    }
    [data-testid="stImage"] img {
        object-fit: contain;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #303030;
        border-radius: 22px;
    }
    @keyframes urgent-summary-appear {
        from {
            opacity: 0;
            transform: translateY(0.75rem);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .st-key-tonight-summary {
        border: 2px solid #303030;
        border-radius: 24px;
        padding: 1.3rem 1.5rem;
        margin: 1.5rem 0 1rem;
        text-align: center;
        animation: urgent-summary-appear 500ms ease-out both;
    }
    .st-key-tonight-summary h3 {
        margin: 0 0 0.4rem;
        color: #b02a37;
    }
    @media (prefers-reduced-motion: reduce) {
        .st-key-tonight-summary {
            animation: none;
        }
    }
    [class*="st-key-tonight-message-"] button {
        width: 100%;
        min-height: 3rem;
        border: 0;
        background: transparent;
        color: inherit;
        white-space: normal;
        overflow-wrap: anywhere;
    }
    [class*="st-key-tonight-message-"] button:hover {
        border: 0;
        color: #b02a37;
        background: #f7f7f7;
    }
    [class*="st-key-message-card-"] {
        border: 1px solid #555;
        border-radius: 20px;
        padding: 0.75rem 1rem;
        margin-bottom: 1.25rem;
    }
    .message-card-header {
        display: grid;
        grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr) minmax(12rem, 1.4fr);
        border-bottom: 1px solid #555;
        margin: -0.75rem -1rem 0.5rem;
    }
    .message-card-header > div {
        padding: 0.35rem 0.5rem;
        border-right: 1px solid #888;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .message-card-header > div:first-child {
        justify-content: center;
        text-align: center;
    }
    .message-card-header strong,
    .popup-header strong,
    .popup-body strong {
        margin-right: 0.35rem;
    }
    .message-card-header > div:last-child {
        border-right: 0;
    }
    .message-urgency {
        flex-direction: row;
        gap: 0.5rem;
        white-space: nowrap;
    }
    .message-urgency strong {
        margin-right: 0;
        white-space: nowrap;
    }
    .popup-header {
        display: grid;
        grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr) minmax(12rem, 1.4fr);
        border: 1px solid #555;
        border-radius: 0;
        overflow: hidden;
        margin-bottom: 1rem;
    }
    [data-testid="stDialog"] [role="dialog"] {
        height: auto;
        max-height: calc(100vh - 2rem);
        overflow-y: auto;
    }
    .popup-header > div {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 3.25rem;
        padding: 0.6rem 0.75rem;
        border-right: 1px solid #888;
        text-align: center;
        overflow-wrap: anywhere;
    }
    .popup-header > div:last-child {
        border-right: 0;
    }
    .popup-urgency {
        flex-direction: row;
        gap: 0.5rem;
        white-space: nowrap;
    }
    .popup-urgency strong {
        margin-right: 0;
        white-space: nowrap;
    }
    .popup-body {
        display: flex;
        flex-direction: column;
        gap: 0.85rem;
        padding: 0.25rem 0.25rem 0.5rem;
        overflow-wrap: anywhere;
    }
    .popup-body p {
        margin: 0;
        line-height: 1.5;
    }
    .popup-message {
        white-space: pre-wrap;
    }
    .popup-reason,
    .popup-reply {
        padding-top: 0.5rem;
        border-top: 1px solid #e5e5e5;
    }
    .message-card-message {
        display: -webkit-box;
        -webkit-box-orient: vertical;
        -webkit-line-clamp: 2;
        overflow: hidden;
        overflow-wrap: anywhere;
        min-height: 3rem;
        margin: 0.5rem 0;
    }
    .urgency-badge {
        display: inline-block;
        border-radius: 999px;
        padding: 0.15rem 0.55rem;
        color: #fff;
        font-weight: 700;
        text-align: center;
        white-space: nowrap;
    }
    .app-brand {
        color: #146b37;
        font-weight: 700;
        font-size: 1.5rem;
    }
    [data-testid="stMarkdownContainer"],
    [data-testid="stWidgetLabel"],
    [data-testid="stButton"] button,
    input,
    textarea,
    select {
        font-size: var(--app-font-size, 16px) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "message_analyses" not in st.session_state:
    st.session_state["message_analyses"] = {}
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "is_authenticated" not in st.session_state:
    st.session_state["is_authenticated"] = False
if "show_settings" not in st.session_state:
    st.session_state["show_settings"] = False
if "font_size" not in st.session_state:
    st.session_state["font_size"] = "Regular"
if "human_review_decisions" not in st.session_state:
    st.session_state["human_review_decisions"] = {}

FONT_SIZES = {"Regular": 16, "Large": 19, "Extra large": 22}


def is_valid_login(username, password):
    return username == "test" and password == "1234"


if not st.session_state["is_authenticated"]:
    st.title("Silencer")
    st.subheader("Log in")
    st.caption("Sign in to review your messages.")
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Log in")
    st.info("Demo account: username `test`, password `1234`.")
    if submitted:
        if is_valid_login(username, password):
            st.session_state["is_authenticated"] = True
            st.session_state["user_name"] = username
            st.rerun()
        else:
            st.error("Incorrect username or password.")
    st.stop()

with DATA_FILE.open("r", encoding="utf-8") as f:
    messages = json.load(f)
queued_messages = get_queue(
    messages,
    st.session_state["message_analyses"],
    st.session_state["human_review_decisions"],
)

st.markdown(
    f"<style>:root {{ --app-font-size: {FONT_SIZES[st.session_state['font_size']]}px; }}</style>",
    unsafe_allow_html=True,
)


@st.dialog("Message details", width="medium")
def show_message_details(message, analysis):
    show_message_details_content(message, analysis)
    if not analysis and st.button("Analyze message", key=f"dialog-analyze-{message['id']}"):
        result = classify_message(message)
        reply = generate_reply(message, result)
        st.session_state["message_analyses"][message["id"]] = {
            "result": result,
            "reply": reply,
        }
        st.session_state["human_review_decisions"].pop(message["id"], None)
        st.rerun()


def show_message_details_content(message, analysis):
    message_id = html.escape(str(message["id"]))
    sender = html.escape(str(message["sender"]))
    received_at = html.escape(str(message.get("received_at") or "Not provided"))
    full_message = html.escape(str(message["message"]))
    urgency_value = "Not assessed"
    urgency_style = "background-color:#6c757d"
    category = "Awaiting analysis"
    extra_content = ""

    if analysis:
        result = analysis["result"]
        reply = analysis["reply"]
        category = result["classification"]
        urgency_value = f"{result['urgency_score']:.2f}"
        urgency_style = f"background-color:{urgency_color(result)}"
        extra_content = (
            '<p><strong>Demo confidence (not calibrated):</strong> '
            f'{result["confidence"]:.2f}</p>'
            f'<p class="popup-reason"><strong>Reason:</strong> '
            f'{html.escape(str(result["reason"]))}</p>'
        )
        if result["source"] == "mock":
            extra_content += '<p><strong>Status:</strong> Offline rule demo — no AI model was called.</p>'
        elif result["source"] == "fallback":
            extra_content += '<p><strong>Status:</strong> Analysis was unavailable or invalid. Human review is required.</p>'
        elif result["source"] == "guardrail":
            extra_content += '<p><strong>Status:</strong> A local safety check routed this message for human review.</p>'
        if reply["suggested_reply"] is None:
            extra_content += '<p class="popup-reply"><strong>Suggested reply:</strong> No safe reply draft is available; please handle this message manually.</p>'
        else:
            extra_content += (
                '<p class="popup-reply"><strong>Suggested reply:</strong> '
                f'{html.escape(str(reply["suggested_reply"]))}</p>'
            )

    category_key = analysis["result"].get("category") if analysis else None
    if category_key == "urgent":
        queue_footer = "Urgent: handle this tonight. It is not in the morning review queue."
    elif category_key == "wait_until_morning":
        queue_footer = "This non-urgent message appears in morning review automatically. No reply has been sent."
    elif category_key == "needs_human_review":
        decision = st.session_state["human_review_decisions"].get(message["id"])
        if decision is True:
            queue_footer = "You chose morning review for this message. No reply has been sent."
        elif decision is False:
            queue_footer = "You chose to handle this tonight. It appears in Tonight's attention, not morning review. No reply has been sent."
        else:
            queue_footer = "Needs your decision before it can enter morning review. No reply has been sent."
    else:
        queue_footer = "Analyze this message to decide whether it belongs in morning review."
    st.markdown(
        '<div class="popup-header">'
        f'<div><strong>Case ID:</strong> {message_id}</div>'
        f'<div><strong>Category:</strong> {html.escape(str(category))}</div>'
        f'<div class="popup-urgency"><strong>Urgent level:</strong> '
        f'<span class="urgency-badge" style="{urgency_style}">{urgency_value}</span></div>'
        '</div>'
        '<div class="popup-body">'
        f'<p><strong>Sender: </strong>{sender}</p>'
        f'<p><strong>Received at: </strong>{received_at}</p>'
        f'<p class="popup-message"><strong>Message: </strong>{full_message}</p>'
        f'{extra_content}'
        f'<p>{queue_footer}</p>'
        '</div>',
        unsafe_allow_html=True,
    )


def urgency_color(result):
    if result.get("category") == "urgent":
        return "#dc3545"
    score = max(0.0, min(1.0, float(result.get("urgency_score", 0.0))))
    green = (25, 135, 84)
    red = (220, 53, 69)
    rgb = tuple(round(low + (high - low) * score) for low, high in zip(green, red))
    return "#{:02x}{:02x}{:02x}".format(*rgb)


icon_col, name_col, settings_col = st.columns(
    [0.16, 0.70, 0.14], vertical_alignment="center"
)
with icon_col:
    st.image(str(ICON_FILE), width=80)
with name_col:
    st.markdown(
        f'<div class="app-brand">Welcome, {html.escape(st.session_state["user_name"])}</div>',
        unsafe_allow_html=True,
    )
with settings_col:
    if st.button("Settings", key="settings_button", use_container_width=True):
        st.session_state["show_settings"] = not st.session_state["show_settings"]

if st.session_state["show_settings"]:
    with st.container(border=True):
        mode = os.environ.get("SILENCER_MODE", "mock")
        st.write(f"Analysis mode: **{mode}**")
        st.selectbox(
            "Font size",
            tuple(FONT_SIZES),
            key="font_size",
            help="Choose Regular, Large, or Extra large text for the app.",
        )
        st.write("API credentials are not displayed here. Replies are drafts only and are never sent.")

analyses = st.session_state["message_analyses"]
review_decisions = st.session_state["human_review_decisions"]
tonight_items = [
    message
    for message in messages
    if message["id"] in analyses
    and (
        analyses[message["id"]]["result"].get("category") == "urgent"
        or (
            analyses[message["id"]]["result"].get("category") == "needs_human_review"
            and review_decisions.get(message["id"]) is False
        )
    )
]
if tonight_items:
    tonight_items.sort(
        key=lambda message: analyses[message["id"]]["result"].get("urgency_score", 0),
        reverse=True,
    )
    with st.container(key="tonight-summary"):
        st.markdown(
            f"<h3>Tonight's attention ({len(tonight_items)})</h3>",
            unsafe_allow_html=True,
        )
        for tonight_message in tonight_items:
            result = analyses[tonight_message["id"]]["result"]
            source = (
                "Analysis: Urgent" if result.get("category") == "urgent"
                else "Your decision: handle tonight"
            )
            if st.button(
                f"{source} · {tonight_message['sender']}: {tonight_message['message']}",
                key=f"tonight-message-{tonight_message['id']}",
                use_container_width=True,
            ):
                show_message_details(tonight_message, analyses[tonight_message["id"]])

with st.container(key="search-strip"):
    search_col, filter_col = st.columns([0.7, 0.3], vertical_alignment="center")
    with search_col:
        search_text = st.text_input(
            "Search messages",
            placeholder="Search messages or senders",
            label_visibility="collapsed",
            key="message_search",
        )
    with filter_col:
        selected_filter = st.selectbox(
            "Filter messages",
            ("All messages", "Urgent", "Non-Urgent", "Needs Human Review", "Not analyzed"),
            label_visibility="collapsed",
            key="message_filter",
        )

analyzed_count = sum(message["id"] in analyses for message in messages)
unanalyzed_messages = [
    message for message in messages if message["id"] not in analyses
]
with st.container(key="message-count-grid"):
    counter_col, batch_col = st.columns(
        [2.3, 1], gap="large", vertical_alignment="center"
    )
    with counter_col:
        st.markdown(
            '<div class="message-count-table">'
            '<div class="message-count-label">Messages received</div>'
            '<div class="message-count-label">Analyzed</div>'
            '<div class="message-count-label">Not analyzed</div>'
            f'<div>{len(messages)}</div>'
            f'<div>{analyzed_count}</div>'
            f'<div>{len(unanalyzed_messages)}</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with batch_col:
        if st.button(
            "Analyze all messages",
            key="analyze-all-messages",
            disabled=not unanalyzed_messages,
        ):
            with st.spinner(f"Analyzing {len(unanalyzed_messages)} messages..."):
                for message in unanalyzed_messages:
                    result = classify_message(message)
                    reply = generate_reply(message, result)
                    analyses[message["id"]] = {"result": result, "reply": reply}
                    st.session_state["human_review_decisions"].pop(message["id"], None)
            st.rerun()
if os.environ.get("SILENCER_MODE", "mock") == "llm" and unanalyzed_messages:
    st.caption(
        "Analyze all makes one model request per unanalyzed message and may incur API charges."
    )

review_items = [
    message for message in messages
    if message["id"] in analyses
    and analyses[message["id"]]["result"].get("category") == "needs_human_review"
]
if review_items:
    st.subheader(f"Needs human review ({len(review_items)})")
    st.caption("Choose whether each message can wait until morning. No reply is sent.")
    for review_message in review_items:
        review_id = review_message["id"]
        decision = st.session_state["human_review_decisions"].get(review_id)
        with st.container(border=True):
            st.write(f"{review_message['sender']}: {review_message['message']}")
            st.caption(analyses[review_id]["result"]["reason"])
            if decision is True:
                st.success("Your choice: review in the morning")
            elif decision is False:
                st.warning("Your choice: handle tonight")
            morning_col, tonight_col = st.columns(2)
            with morning_col:
                if st.button("Yes, review in morning", key=f"review-morning-{review_id}"):
                    st.session_state["human_review_decisions"][review_id] = True
                    st.rerun()
            with tonight_col:
                if st.button("No, handle tonight", key=f"review-tonight-{review_id}"):
                    st.session_state["human_review_decisions"][review_id] = False
                    st.rerun()

st.subheader(f"Morning review queue ({len(queued_messages)})")
st.caption("Non-urgent messages appear automatically; human-review messages appear only if you choose morning. No replies are sent.")
if not queued_messages:
    st.info("No messages in morning review yet. Analyze messages to build the list.")
else:
    for queued_message in queued_messages:
        with st.container(border=True):
            st.markdown(f"**{html.escape(queued_message['sender'])}**")
            st.write(queued_message["message"])
            st.caption(f"Category: {queued_message['classification']}")
            if queued_message["category"] == "needs_human_review":
                st.caption("Added after your decision; AI classification remains Needs Human Review.")
            st.caption(
                f"Received: {queued_message.get('received_at') or 'Not provided'}"
            )

filter_categories = {
    "Urgent": "urgent",
    "Non-Urgent": "wait_until_morning",
    "Needs Human Review": "needs_human_review",
}
visible_messages = []
for message in messages:
    analysis = analyses.get(message["id"])
    haystack = f"{message['sender']} {message['message']}".casefold()
    if search_text and search_text.casefold() not in haystack:
        continue
    if selected_filter == "Not analyzed" and analysis:
        continue
    if selected_filter in filter_categories:
        if not analysis or analysis["result"].get("category") != filter_categories[selected_filter]:
            continue
    visible_messages.append(message)

if not visible_messages:
    st.info("No messages match the current search and filter.")

for message in visible_messages:
    analysis = analyses.get(message["id"])
    message_id = html.escape(str(message["id"]))
    category = analysis["result"]["classification"] if analysis else "Awaiting analysis"
    urgency = analysis["result"]["urgency_score"] if analysis else None
    received_at = message.get("received_at") or "Not provided"
    if analysis:
        color = urgency_color(analysis["result"])
        urgency_label = f"{urgency:.2f}"
    else:
        color = "#6c757d"
        urgency_label = "Not assessed"

    with st.container(key=f"message-card-{message_id}"):
        st.markdown(
            '<div class="message-card-header">'
            f'<div><strong>Case ID:</strong> {message_id}</div>'
            f'<div><strong>Category:</strong> {html.escape(str(category))}</div>'
            f'<div class="message-urgency"><strong>Urgency level:</strong> '
            f'<span class="urgency-badge" style="background-color:{color}">'
            f'{urgency_label}</span></div>'
            '</div>'
            f'<p><strong>Sender:</strong> {html.escape(str(message["sender"]))}</p>'
            f'<p><strong>Received at:</strong> {html.escape(str(received_at))}</p>'
            f'<div class="message-card-message"><strong>Message:</strong> '
            f'{html.escape(str(message["message"]))}</div>',
            unsafe_allow_html=True,
        )
        action_col, details_col = st.columns([0.78, 0.22])
        with action_col:
            action_label = "Re-analyze message" if analysis else "Analyze message"
            if st.button(action_label, key=f"analyze-{message_id}"):
                result = classify_message(message)
                reply = generate_reply(message, result)
                analyses[message["id"]] = {"result": result, "reply": reply}
                st.session_state["human_review_decisions"].pop(message["id"], None)
                st.rerun()
        with details_col:
            if st.button("View details", key=f"view-details-{message_id}"):
                show_message_details(message, analysis)
