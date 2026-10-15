import base64
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
    :root {
        --ink: #0f172a;
        --muted: #64748b;
        --accent: #3b82f6;
        --urgent: #ef4444;
        --success: #10b981;
        --surface: #ffffff;
        --canvas: #f8fafc;
        --line: #e2e8f0;
        --app-font-size: 16px;
    }
    [data-testid="stAppViewContainer"] { background: var(--canvas); }
    [data-testid="stHeader"] { background: transparent; }
    .stMainBlockContainer {
        max-width: 1380px;
        padding: 1.25rem 2rem 3rem;
        font-size: var(--app-font-size);
    }
    .stApp:has(.st-key-login-shell) [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
    }
    .stApp:has(.st-key-login-shell) .stMainBlockContainer {
        box-sizing: border-box;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        max-width: 100%;
        min-height: 100vh;
        padding: 1.5rem;
    }
    .st-key-login-shell { width: min(100%, 560px); margin: auto; }
    .st-key-login-card {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.11);
        padding: 2rem;
        transition: transform 180ms ease, box-shadow 180ms ease;
    }
    .st-key-login-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 22px 52px rgba(15, 23, 42, 0.14);
    }
    .login-brand {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.7rem;
        margin-bottom: 0.3rem;
    }
    .login-brand img { width: 46px; height: 46px; object-fit: contain; }
    .login-brand-title {
        color: var(--ink);
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.05em;
    }
    .login-tagline {
        color: #334155;
        font-size: 1rem;
        font-weight: 650;
        margin: 0 0 0.45rem;
        text-align: center;
    }
    .st-key-login-card p.login-description {
        width: 100%;
        max-width: 420px;
        margin: 0 auto 0.7rem !important;
        text-align: center !important;
    }
    .st-key-login-card .login-form-title {
        font-size: 1.45rem;
        line-height: 1.3;
        margin: 0.2rem 0 0;
    }
    .st-key-login-card .login-form-subtitle { margin: 0.25rem 0 0.85rem; }
    .st-key-login-card [data-testid="stForm"] { margin-top: 0; padding: 0; }
    .login-description {
        color: var(--muted);
        font-size: 0.91rem;
        line-height: 1.55;
        margin: 0 auto 1.5rem;
        max-width: 360px;
        text-align: center;
    }
    .login-form-title {
        color: var(--ink);
        font-size: 1.45rem;
        font-weight: 750;
        letter-spacing: -0.03em;
        margin: 0;
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
    .login-form-subtitle { color: var(--muted); margin: 0.25rem 0 1rem; }
    .st-key-login-card [data-testid="stTextInput"] input {
        border-radius: 10px;
        border-color: #cbd5e1;
        transition: border-color 150ms ease, box-shadow 150ms ease;
    }
    .st-key-login-card [data-testid="stTextInput"] input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.16);
    }
    .st-key-login-card [data-testid="stButton"] button[kind="primary"],
    .st-key-login-card [data-testid="stFormSubmitButton"] button[kind="primary"] {
        background: #3b82f6 !important;
        border-color: #3b82f6 !important;
        color: #fff !important;
        min-height: 2.8rem;
        border-radius: 10px;
        font-weight: 700;
        transition: transform 150ms ease, box-shadow 150ms ease;
    }
    .st-key-login-card [data-testid="stButton"] button[kind="primary"]:hover,
    .st-key-login-card [data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
        background: #2563eb !important;
        border-color: #2563eb !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(59, 130, 246, 0.22);
    }
    .stApp:has(.st-key-login-shell) [data-testid="stHeader"] { display: none; }
    [data-testid="stImage"] img { object-fit: contain; }
    .st-key-main-header {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 0.5rem 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.05);
    }
    .brand-title {
        color: var(--ink);
        font-size: 3rem;
        font-weight: 750;
        letter-spacing: -0.04em;
        line-height: 1.2;
    }
    .brand-subtitle { color: var(--muted); font-size: 1rem; }
    .greeting-title {
        color: var(--ink);
        font-size: clamp(1.7rem, 3vw, 2.15rem);
        font-weight: 750;
        letter-spacing: -0.045em;
        margin: 0;
    }
    .greeting-copy { color: var(--muted); margin: 0.35rem 0 1.5rem; }
    .kpi-card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 16px;
        height: 10.5rem;
        box-sizing: border-box;
        padding: 1.15rem 1.2rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.045);
        transition: transform 160ms ease, box-shadow 160ms ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.09);
    }
    .kpi-label {
        color: var(--muted);
        font-size: 1.8rem;
        font-weight: 600;
        min-height: 2.3rem;
        flex-shrink: 0;
    }
    .kpi-value {
        color: var(--ink);
        font-size: 1.8rem;
        font-weight: 750;
        line-height: 1.35;
        flex-shrink: 0;
    }
    .kpi-note { color: #94a3b8; font-size: 0.77rem; flex-shrink: 0; }
    .st-key-urgent-hero {
        background: linear-gradient(120deg, #fff1f2 0%, #fff7ed 100%);
        border: 1px solid #fecaca;
        border-left: 6px solid var(--urgent);
        border-radius: 18px;
        padding: 1.35rem 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.09);
    }
    .hero-eyebrow {
        color: #b91c1c;
        font-size: 0.82rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .hero-sender { color: var(--ink); font-size: 1.18rem; font-weight: 700; margin-top: 0.6rem; }
    .hero-message { color: #334155; font-size: 1.05rem; margin: 0.6rem 0 0.85rem; }
    .hero-score { color: #991b1b; font-size: 0.9rem; font-weight: 700; }
    .st-key-search-strip {
        background: transparent;
        border: 0;
        border-radius: 0;
        padding: 0;
        margin: 0.5rem 0 1.5rem;
    }
    .section-title { color: var(--ink); font-size: 1.25rem; font-weight: 750; margin: 0.3rem 0 0.9rem; }
    [class*="st-key-message-card-"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1rem 1.15rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04);
        transition: transform 160ms ease, box-shadow 160ms ease;
    }
    [class*="st-key-message-card-unread-"] {
        background: var(--surface);
        border-color: var(--line);
        border-left: 4px solid var(--accent);
    }
    [class*="st-key-message-card-"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 9px 20px rgba(15, 23, 42, 0.08);
    }
    .message-topline { display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }
    .category-badge {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 0.27rem 0.7rem;
        font-size: 0.8rem;
        font-weight: 750;
    }
    .badge-urgent { color: #991b1b; background: #fee2e2; }
    .badge-high { color: #9a3412; background: #ffedd5; }
    .badge-medium { color: #854d0e; background: #fef9c3; }
    .badge-low { color: #166534; background: #dcfce7; }
    .badge-spam { color: #334155; background: #e2e8f0; }
    .badge-review { color: #5b21b6; background: #ede9fe; }
    .badge-pending { color: #475569; background: #f1f5f9; }
    .message-sender { color: var(--ink); font-size: 1.05rem; font-weight: 600; }
    [class*="st-key-message-card-unread-"] .message-sender,
    [class*="st-key-message-card-unread-"] .message-body { font-weight: 750; }
    .unread-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        color: #1d4ed8;
        font-size: 0.78rem;
        font-weight: 750;
    }
    .unread-dot {
        display: inline-block;
        width: 0.5rem;
        height: 0.5rem;
        border-radius: 50%;
        background: #3b82f6;
    }
    .message-time { color: var(--muted); font-size: 0.85rem; }
    .message-body { color: #334155; line-height: 1.55; margin: 0.7rem 0; overflow-wrap: anywhere; }
    .reply-preview {
        background: #f8fafc;
        border-left: 3px solid #93c5fd;
        border-radius: 0 10px 10px 0;
        color: #334155;
        line-height: 1.5;
        margin: 0.85rem 0;
        padding: 0.75rem 0.9rem;
        overflow-wrap: anywhere;
    }
    .message-meta { color: var(--muted); font-size: 0.82rem; margin: 0.5rem 0; }
    [data-testid="stButton"] button {
        border-radius: 10px;
        font-weight: 650;
        transition: transform 150ms ease, box-shadow 150ms ease, background 150ms ease;
    }
    [data-testid="stButton"] button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.12);
    }
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        border-radius: 10px;
        border-color: #cbd5e1;
    }
    .popup-header {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        background: #f8fafc;
        border: 1px solid var(--line);
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 1rem;
    }
    [data-testid="stDialog"] [role="dialog"] {
        height: auto;
        max-height: calc(100vh - 2rem);
        overflow-y: auto;
        border-radius: 18px;
    }
    .popup-header > div {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 3.25rem;
        padding: 0.6rem;
        border-right: 1px solid var(--line);
        text-align: center;
        overflow-wrap: anywhere;
    }
    .popup-header > div:last-child { border-right: 0; }
    .popup-header strong { margin-right: 0.35rem; }
    .popup-body {
        display: flex;
        flex-direction: column;
        gap: 0.9rem;
        padding: 0.5rem;
        color: #334155;
        overflow-wrap: anywhere;
    }
    .popup-body p { margin: 0; line-height: 1.55; }
    .popup-message { white-space: pre-wrap; }
    .popup-reason, .popup-reply { padding-top: 0.75rem; border-top: 1px solid var(--line); }
    .urgency-badge {
        display: inline-block;
        border-radius: 999px;
        padding: 0.15rem 0.55rem;
        color: #fff;
        font-weight: 700;
        text-align: center;
        white-space: nowrap;
    }
    @media (max-width: 900px) {
        .stMainBlockContainer { padding: 1rem 1.1rem 2rem; }
        .st-key-main-header { padding: 0.4rem 0.6rem; }
    }
    @media (max-width: 640px) {
        .stMainBlockContainer { padding: 0.75rem 0.7rem 1.5rem; }
        .st-key-main-header [data-testid="stImage"] img { max-width: 64px; }
        .brand-title { font-size: 2.5rem; }
        .brand-subtitle { font-size: 0.75rem; }
        .st-key-urgent-hero { padding: 1rem; }
        .popup-header { grid-template-columns: 1fr; }
        .popup-header > div { border-right: 0; border-bottom: 1px solid var(--line); }
        .popup-header > div:last-child { border-bottom: 0; }
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { transition-duration: 0.01ms !important; }
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
if "read_message_ids" not in st.session_state:
    st.session_state["read_message_ids"] = set()

FONT_SIZES = {"Regular": 16, "Large": 19, "Extra large": 22}


def is_valid_login(username, password):
    return username == "test" and password == "1234"


if not st.session_state["is_authenticated"]:
    with st.container(key="login-shell"):
        with st.container(key="login-card"):
            icon_data = base64.b64encode(ICON_FILE.read_bytes()).decode("ascii")
            st.markdown(
                '<div class="login-brand">'
                f'<img src="data:image/png;base64,{icon_data}" alt="Silencer logo">'
                '<span class="login-brand-title">Silencer</span></div>'
                '<p class="login-tagline">Silence the noise. Surface what matters.</p>'
                '<p class="login-description">AI-powered message analysis that helps you '
                'identify urgent communications and focus on what matters most.</p>'
                '<h2 class="login-form-title">Welcome Back</h2>'
                '<p class="login-form-subtitle">Sign in to review your messages.</p>',
                unsafe_allow_html=True,
            )
            with st.form("login_form", enter_to_submit=False, border=False):
                username = st.text_input("Username", key="login_username")
                password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password",
                )
                submitted = st.form_submit_button(
                    "Sign In",
                    type="primary",
                    width="stretch",
                )
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

st.session_state["read_message_ids"].intersection_update(
    str(message["id"]) for message in messages
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
        f'<div class="popup-urgency"><strong>Urgency level:</strong> '
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
        return "#ef4444"
    score = max(0.0, min(1.0, float(result.get("urgency_score", 0.0))))
    green = (16, 185, 129)
    red = (239, 68, 68)
    rgb = tuple(round(low + (high - low) * score) for low, high in zip(green, red))
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def urgency_badge(result):
    if result is None:
        return "Awaiting analysis", "badge-pending"
    category = result.get("category")
    if category == "urgent":
        return "Urgent", "badge-urgent"
    if category == "spam":
        return "Spam", "badge-spam"
    if category == "needs_human_review":
        return "Needs review", "badge-review"
    score = float(result.get("urgency_score", 0.0))
    if score >= 0.7:
        return "High", "badge-high"
    if score >= 0.4:
        return "Medium", "badge-medium"
    return "Low", "badge-low"


def mark_message_as_read(message_id):
    st.session_state["read_message_ids"].add(str(message_id))


analyses = st.session_state["message_analyses"]
unanalyzed_messages = [
    message for message in messages if message["id"] not in analyses
]
if unanalyzed_messages:
    if os.environ.get("SILENCER_MODE", "mock") == "llm":
        st.caption(
            "Automatic analysis makes one model request per message and may incur API charges."
        )
    with st.spinner(f"Analyzing {len(unanalyzed_messages)} messages..."):
        for message in unanalyzed_messages:
            result = classify_message(message)
            analyses[message["id"]] = {
                "result": result,
                "reply": generate_reply(message, result),
            }

analyzed_count = sum(message["id"] in analyses for message in messages)
urgent_items = [
    (message, analyses[message["id"]]["result"])
    for message in messages
    if message["id"] in analyses
    and analyses[message["id"]]["result"].get("category") == "urgent"
]
urgent_count = len(urgent_items)
with st.container(key="main-header"):
    logo_col, brand_col, settings_col, logout_col = st.columns(
        [0.12, 0.52, 0.19, 0.17], vertical_alignment="center"
    )
    with logo_col:
        st.image(str(ICON_FILE), width=92)
    with brand_col:
        st.markdown(
            '<div class="brand-title">Silencer</div>'
            '<div class="brand-subtitle">Silence the noise. Surface what matters.</div>',
            unsafe_allow_html=True,
        )
    with settings_col:
        if st.button("Settings", key="settings_button", icon=":material/settings:", width="stretch"):
            st.session_state["show_settings"] = not st.session_state["show_settings"]
    with logout_col:
        if st.button("Log out", key="logout_button", icon=":material/logout:", width="stretch"):
            st.session_state["is_authenticated"] = False
            st.session_state["user_name"] = ""
            st.session_state["read_message_ids"] = set()
            st.rerun()

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
        st.write(
            "API credentials are not displayed here. Replies are drafts only; "
            "nothing is sent or queued."
        )

name = html.escape(st.session_state["user_name"].strip().title() or "there")
unread_count = sum(
    str(message["id"]) not in st.session_state["read_message_ids"]
    for message in messages
)
urgent_summary = (
    f"{urgent_count} message requires immediate attention."
    if urgent_count == 1
    else f"{urgent_count} messages require immediate attention."
    if urgent_count
    else "No messages currently require immediate attention."
)
st.markdown(
    f'<h1 class="greeting-title">Welcome back, {name} 👋</h1>'
    f'<p class="greeting-copy">You have {len(messages)} messages today, '
    f'{unread_count} unread. '
    f'{urgent_summary}</p>',
    unsafe_allow_html=True,
)

kpi_data = [
    ("Messages received", str(len(messages)), "In your inbox"),
    ("Urgent messages", str(urgent_count), "Immediate attention"),
    ("Analyzed", f"{analyzed_count}/{len(messages)}", "Messages reviewed"),
]
kpi_columns = st.columns(3, gap="medium")
for column, (label, value, note) in zip(kpi_columns, kpi_data):
    with column:
        st.markdown(
            '<div class="kpi-card">'
            f'<div class="kpi-label">{html.escape(label)}</div>'
            f'<div class="kpi-value">{html.escape(value)}</div>'
            f'<div class="kpi-note">{html.escape(note)}</div>'
            '</div>',
            unsafe_allow_html=True,
        )

if urgent_items:
    urgent_message, urgent_result = max(
        urgent_items, key=lambda item: item[1].get("urgency_score", 0)
    )
    urgent_analysis = analyses[urgent_message["id"]]
    urgent_reply = urgent_analysis["reply"]
    badge_label, badge_class = urgency_badge(urgent_result)
    with st.container(key="urgent-hero"):
        st.markdown(
            '<div class="hero-eyebrow">Action needed '
            f'<span class="category-badge {badge_class}">{html.escape(badge_label)}</span>'
            '</div>'
            f'<div class="hero-sender">From {html.escape(str(urgent_message["sender"]))}</div>'
            f'<p class="hero-message">{html.escape(str(urgent_message["message"]))}</p>'
            f'<div class="hero-score">Urgency score · '
            f'{urgent_result["urgency_score"]:.2f}</div>',
            unsafe_allow_html=True,
        )
        suggested_reply = urgent_reply["suggested_reply"]
        if suggested_reply:
            st.markdown(
                '<div class="reply-preview"><strong>Suggested reply</strong><br>'
                f'{html.escape(str(suggested_reply))}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="reply-preview"><strong>Suggested reply</strong><br>'
                'No safe reply draft is available; please handle this message manually.'
                '</div>',
                unsafe_allow_html=True,
            )
        with st.container():
            if st.button(
                "View details",
                key="urgent-hero-details",
                icon=":material/visibility:",
                width="stretch",
                on_click=mark_message_as_read,
                args=(urgent_message["id"],),
            ):
                show_urgent_message(urgent_message, urgent_result, urgent_reply)
else:
    with st.container(border=True):
        st.markdown("### ✅ You’re all caught up")
        st.write("No messages currently need immediate attention.")

with st.container(key="search-strip"):
    search_col, filter_col = st.columns([0.68, 0.32], gap="medium", vertical_alignment="center")
    with search_col:
        search_text = st.text_input(
            "Search messages",
            placeholder="Search messages or senders",
            label_visibility="collapsed",
            icon=":material/search:",
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

st.markdown('<div class="section-title">Your messages</div>', unsafe_allow_html=True)
if not visible_messages:
    st.info("No messages match the current search and filter.")

for message in visible_messages:
    analysis = analyses.get(message["id"])
    result = analysis["result"] if analysis else None
    reply = analysis["reply"] if analysis else None
    message_id = str(message["id"])
    is_unread = message_id not in st.session_state["read_message_ids"]
    badge_label, badge_class = urgency_badge(result)
    suggested_reply = reply["suggested_reply"] if reply else None
    received_at = message.get("received_at") or "Time not provided"
    urgency_value = f'{result["urgency_score"]:.2f}' if result else "Not assessed"
    card_state = "unread" if is_unread else "read"
    with st.container(key=f"message-card-{card_state}-{message_id}", border=True):
        unread_marker = (
            '<span class="unread-indicator"><span class="unread-dot"></span>'
            'Unread</span>'
            if is_unread
            else ""
        )
        st.markdown(
            '<div class="message-topline">'
            f'<span class="category-badge {badge_class}">{html.escape(badge_label)}</span>'
            f'<span class="message-meta">Case {html.escape(message_id)}</span>'
            f'{unread_marker}</div>'
            f'<div class="message-sender">{html.escape(str(message["sender"]))}</div>'
            f'<div class="message-time">Received · {html.escape(str(received_at))}</div>'
            f'<p class="message-body">{html.escape(str(message["message"]))}</p>',
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
        if suggested_reply:
            st.markdown(
                '<div class="reply-preview"><strong>Suggested reply</strong><br>'
                f'{html.escape(str(suggested_reply))}</div>',
                unsafe_allow_html=True,
            )
        elif reply:
            st.markdown(
                '<div class="reply-preview"><strong>Suggested reply</strong><br>'
                'No safe reply draft is available; please handle this message manually.'
                '</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="message-meta">Urgency score · {html.escape(urgency_value)}</div>',
            unsafe_allow_html=True,
        )
        details_col, copy_col, _ = st.columns([0.2, 0.2, 0.6])
        with details_col:
            if st.button(
                "View details",
                key=f"view-details-{message_id}",
                icon=":material/visibility:",
                width="stretch",
                on_click=mark_message_as_read,
                args=(message_id,),
            ):
                show_message_details(message, analysis)
        with copy_col:
            if st.button(
                "Copy reply",
                key=f"copy-reply-{message_id}",
                icon=":material/content_copy:",
                disabled=not suggested_reply,
                width="stretch",
            ):
                st.session_state["copy_reply_visible"] = message_id
        if (
            suggested_reply
            and st.session_state.get("copy_reply_visible") == message_id
        ):
            st.caption("Use the copy control on the draft below to copy it.")
            st.code(suggested_reply)
