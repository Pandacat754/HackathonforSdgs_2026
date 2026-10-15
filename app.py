import base64
import html
import json
import os
from datetime import datetime, timezone
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
    }
    html { font-size: var(--app-font-size, 16px); }
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
    .login-brand img { width: 84px; height: 84px; object-fit: contain; }
    .login-brand-title {
        color: var(--ink);
        background: transparent;
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
        background: transparent;
        border: 0;
        border-radius: 0;
        padding: 0.5rem 1rem;
        margin-bottom: 1rem;
        box-shadow: none;
    }
    .st-key-app-icon {
        width: 6.5rem;
        height: 6.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        border: 0;
        background: transparent;
    }
    .st-key-app-icon [data-testid="stImage"] img {
        width: 104px;
        height: 104px;
        object-fit: contain;
    }
    .brand-title {
        color: var(--ink);
        background: transparent;
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
    .st-key-urgent-hero-read,
    .st-key-urgent-hero-unread {
        background: #fff5f5;
        border: 1px solid #ef4444;
        border-radius: 18px;
        padding: 1.35rem 1.5rem;
        margin: 1.5rem 0;
        box-shadow: 0 4px 14px rgba(239, 68, 68, 0.08);
    }
    .priority-title {
        color: #b91c1c;
        font-size: 1.35rem;
        font-weight: 750;
        margin-bottom: 0.7rem;
    }
    .hero-urgency {
        color: #7f1d1d;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.55rem;
    }
    .hero-urgency .urgency-badge {
        margin-left: 0.35rem;
        font-size: 1rem;
        padding: 0.2rem 0.65rem;
    }
    .st-key-urgent-hero-read [data-testid="stButton"] button,
    .st-key-urgent-hero-unread [data-testid="stButton"] button {
        min-height: 0;
        height: auto;
        justify-content: flex-start;
        padding: 0.25rem 0;
        border: 0;
        background: transparent;
        box-shadow: none;
        color: #334155;
        font-size: 1.05rem;
        line-height: 1.7;
        text-align: left;
        white-space: pre-wrap;
    }
    .st-key-urgent-hero-read [data-testid="stButton"] [data-testid="stMarkdownContainer"] p,
    .st-key-urgent-hero-unread [data-testid="stButton"] [data-testid="stMarkdownContainer"] p {
        font-size: 1.05rem !important;
        line-height: 1.7;
    }
    .st-key-urgent-hero-read [data-testid="stButton"] button > div,
    .st-key-urgent-hero-unread [data-testid="stButton"] button > div {
        width: 100%;
        justify-content: flex-start;
    }
    .st-key-urgent-hero-read [data-testid="stButton"] [data-testid="stMarkdownContainer"],
    .st-key-urgent-hero-unread [data-testid="stButton"] [data-testid="stMarkdownContainer"] {
        width: 100%;
        text-align: left;
    }
    .st-key-urgent-hero-read [data-testid="stButton"] button:hover,
    .st-key-urgent-hero-unread [data-testid="stButton"] button:hover {
        transform: none;
        box-shadow: none;
        background: transparent;
        color: var(--ink);
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
        padding: 0.75rem 0 0;
        margin: 0.5rem 0 1.5rem;
    }
    .section-title { color: var(--ink); font-size: 1.25rem; font-weight: 750; margin: 0.3rem 0 0.9rem; }
    [data-testid="stExpander"] summary {
        color: #000;
        cursor: pointer;
    }
    [data-testid="stExpander"] summary p {
        color: #0f172a;
        font-size: 1.5rem !important;
        font-weight: 800 !important;
    }
    [data-testid="stExpander"] summary svg {
        color: #000;
        fill: #000;
    }
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
    .message-fields {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.5rem;
        margin-bottom: 0.55rem;
        color: var(--ink);
    }
    .message-fields strong, .message-detail strong { font-weight: 750; }
    .message-detail { margin: 0.35rem 0; overflow-wrap: anywhere; }
    .message-actions { margin-top: 0.8rem; }
    .queue-actions [data-testid="stButton"] button { font-size: 0.88rem; }
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
    .st-key-search-strip [data-testid="stTextInputRootElement"],
    .st-key-search-strip [data-testid="stTextInput"] input,
    .st-key-search-strip [data-testid="stSelectbox"] [role="group"] {
        background: #e2e8f0;
        color: #1f2937;
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
        .st-key-main-header [data-testid="stImage"] img { max-width: 104px; }
        .st-key-app-icon { width: 6.5rem; height: 6.5rem; }
        .brand-title { font-size: 2.5rem; }
        .brand-subtitle { font-size: 0.75rem; }
        .st-key-urgent-hero-read,
        .st-key-urgent-hero-unread { padding: 1rem; }
        .popup-header { grid-template-columns: 1fr; }
        .popup-header > div { border-right: 0; border-bottom: 1px solid var(--line); }
        .popup-header > div:last-child { border-bottom: 0; }
        .message-fields { grid-template-columns: 1fr; }
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
if "queue_confirmed_ids" not in st.session_state:
    st.session_state["queue_confirmed_ids"] = set()
if "resolved_message_ids" not in st.session_state:
    st.session_state["resolved_message_ids"] = set()

FONT_SIZES = {"Regular": 16, "Large": 19, "Extra large": 22}


def strip_reply_label(reply):
    if not isinstance(reply, str):
        return reply
    for prefix in ("Automated assistant draft:", "自动助手回复草稿："):
        if reply.startswith(prefix):
            return reply[len(prefix):].lstrip()
    return reply


for saved_analysis in st.session_state["message_analyses"].values():
    saved_reply = saved_analysis.get("reply")
    if isinstance(saved_reply, dict):
        saved_reply["suggested_reply"] = strip_reply_label(
            saved_reply.get("suggested_reply")
        )


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
                '<h2 class="login-form-title">Welcome Back</h2>',
                unsafe_allow_html=True,
            )
            with st.form("login_form", enter_to_submit=True, border=False):
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

st.session_state["read_message_ids"].intersection_update(
    str(message["id"]) for message in messages
)
st.session_state["resolved_message_ids"].intersection_update(
    str(message["id"]) for message in messages
)

st.markdown(
    f"<style>:root {{ --app-font-size: {FONT_SIZES[st.session_state['font_size']]}px; }}</style>",
    unsafe_allow_html=True,
)


@st.dialog("Urgent message", width="medium")
def show_urgent_message(message, analysis):
    show_message_details_content(message, analysis)


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
    urgency_badge = '<span class="urgency-badge" style="background-color:#6c757d">Not assessed</span>'
    category = "Awaiting analysis"
    extra_content = ""

    if analysis:
        result = analysis["result"]
        reply = analysis["reply"]
        category = result["classification"]
        urgency_badge = urgency_badge_html(result)
        extra_content = (
            '<p><strong>Demo confidence (not calibrated):</strong> '
            f'{result["confidence"]:.2f}</p>'
            f'<p class="popup-reason"><strong>Reason:</strong> '
            f'{html.escape(str(result["reason"]))}</p>'
        )
        if result["source"] == "fallback":
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
        queue_footer = "This non-urgent message appears in morning review automatically."
    elif category_key == "needs_human_review":
        decision = st.session_state["human_review_decisions"].get(message["id"])
        if decision is True:
            queue_footer = "You chose morning review for this message."
        elif decision is False:
            queue_footer = "You chose to handle this tonight. It appears in Tonight's attention, not morning review."
        else:
            queue_footer = "Needs your decision before it can enter morning review."
    else:
        queue_footer = "Analyze this message to decide whether it belongs in morning review."
    st.markdown(
        '<div class="popup-header">'
        f'<div><strong>Case ID:</strong> {message_id}</div>'
        f'<div><strong>Category:</strong> {html.escape(str(category))}</div>'
        f'<div class="popup-urgency"><strong>Urgency level:</strong> '
        f'{urgency_badge}</div>'
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


def urgency_badge_html(result):
    score = f"{float(result['urgency_score']):.2f}"
    color = urgency_color(result)
    return (
        f'<span class="urgency-badge" style="background-color:{color}">'
        f'{score}</span>'
    )


def urgency_badge(result):
    if result is None:
        return "Awaiting analysis", "badge-pending"
    category = result.get("category")
    if category == "urgent":
        return "Urgent", "badge-urgent"
    if category == "wait_until_morning":
        return "Not urgent", "badge-low"
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


def resolve_human_review(message_id, review_in_morning):
    st.session_state["human_review_decisions"][message_id] = review_in_morning
    result = st.session_state["message_analyses"][message_id]["result"]
    if review_in_morning:
        result.update(
            category="wait_until_morning",
            classification="Non-Urgent",
            action="queue_for_morning",
            reason="You chose to review this message in the morning.",
        )
    else:
        result.update(
            category="urgent",
            classification="Urgent",
            action="notify_user_now",
            urgency_score=max(float(result.get("urgency_score", 0.0)), 0.85),
            reason="You chose to handle this message tonight.",
        )


def received_at_order(message):
    received_at = message.get("received_at")
    if not received_at:
        return 1, datetime.max.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(received_at).replace("Z", "+00:00"))
    except ValueError:
        return 1, datetime.max.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return 0, parsed.astimezone(timezone.utc)


def mark_message_as_read(message_id):
    st.session_state["read_message_ids"].add(str(message_id))


def confirm_queue_message(message_id):
    st.session_state["read_message_ids"].add(str(message_id))
    st.session_state["queue_confirmed_ids"].add(str(message_id))


def mark_message_as_replied(message_id):
    message_id = str(message_id)
    st.session_state["resolved_message_ids"].add(message_id)
    st.session_state["read_message_ids"].add(message_id)
    st.session_state["reply_notice"] = True


def mark_message_as_manually_replied(message_id):
    message_id = str(message_id)
    st.session_state["resolved_message_ids"].add(message_id)
    st.session_state["read_message_ids"].add(message_id)
    st.session_state["manual_reply_notice"] = True


def mark_queue_message_urgent(message_id):
    result = st.session_state["message_analyses"][message_id]["result"]
    result.update(
        category="urgent",
        classification="Urgent",
        action="notify_user_now",
        urgency_score=max(float(result.get("urgency_score", 0.0)), 0.85),
        reason="You chose to handle this message urgently.",
    )
    st.session_state["human_review_decisions"][message_id] = False
    st.session_state["queue_confirmed_ids"].discard(str(message_id))
    st.session_state["read_message_ids"].add(str(message_id))
    mark_message_as_replied(message_id)


def render_message_card(message, section, *, queued=False, history=False):
    message_id = str(message["id"])
    analysis = st.session_state["message_analyses"].get(message["id"])
    result = analysis["result"] if analysis else None
    reply = analysis["reply"] if analysis else None
    suggested_reply = reply["suggested_reply"] if reply else None
    is_unread = message_id not in st.session_state["read_message_ids"]
    card_state = "unread" if is_unread else "read"
    category_label = result["classification"] if result else "Not analyzed"
    urgency_html = (
        urgency_badge_html(result)
        if result
        else '<span class="urgency-badge" style="background-color:#6c757d">'
        'Not assessed</span>'
    )
    sender = html.escape(str(message["sender"]))
    body = html.escape(str(message["message"]))
    received_at = html.escape(str(message.get("received_at") or "Not provided"))
    reply_text = (
        html.escape(str(suggested_reply))
        if suggested_reply
        else "No safe reply draft is available."
    )
    from_label = "Silencer"

    with st.container(
        key=f"message-card-{card_state}-{section}-{message_id}",
        border=True,
    ):
        if queued:
            st.markdown(
                '<div class="message-detail">'
                f'<strong>Message ID:</strong> {html.escape(message_id)}</div>'
                f'<div class="message-detail"><strong>Sender:</strong> {sender}</div>'
                f'<div class="message-detail"><strong>Message:</strong> {body}</div>'
                '<div class="message-detail"><strong>Suggested reply:</strong> '
                f'{reply_text}</div>'
                f'<div class="message-detail"><strong>From:</strong> {from_label}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="message-fields">'
                f'<div><strong>Message ID:</strong> {html.escape(message_id)}</div>'
                f'<div><strong>Category:</strong> {html.escape(category_label)}</div>'
                f'<div><strong>Urgency level:</strong> {urgency_html}</div>'
                '</div>'
                f'<div class="message-detail"><strong>Sender:</strong> {sender}</div>'
                '<div class="message-detail"><strong>Received at:</strong> '
                f'{html.escape(str(message.get("received_at") or "Not provided"))}</div>'
                f'<div class="message-detail"><strong>Message:</strong> {body}</div>'
                '<div class="message-detail"><strong>Suggested reply:</strong> '
                f'{reply_text}</div>'
                f'<div class="message-detail"><strong>From:</strong> {from_label}</div>',
                unsafe_allow_html=True,
            )

        if queued:
            if message_id in st.session_state["queue_confirmed_ids"]:
                st.markdown(":material/check_circle: **Confirmed**")
            else:
                choice_columns = st.columns(2)
                with choice_columns[0]:
                    st.button(
                        "Not urgent",
                        key=f"queue-not-urgent-{message_id}",
                        icon=":material/check_circle:",
                        width="stretch",
                        on_click=confirm_queue_message,
                        args=(message_id,),
                    )
                with choice_columns[1]:
                    st.button(
                        "Urgent and send reply now",
                        key=f"queue-send-now-{message_id}",
                        icon=":material/priority_high:",
                        width="stretch",
                        on_click=mark_queue_message_urgent,
                        args=(message_id,),
                    )
        elif history:
            st.markdown(":material/check_circle: **Replied**")
        else:
            action_columns = st.columns(4)
            with action_columns[0]:
                if st.button(
                    "View details",
                    key=(
                        "urgent-hero-details"
                        if section == "priority"
                        else f"{section}-details-{message_id}"
                    ),
                    icon=":material/visibility:",
                    width="stretch",
                    on_click=mark_message_as_read,
                    args=(message_id,),
                ):
                    show_message_details(message, analysis)
            with action_columns[1]:
                manual_reply = section == "human-review"
                st.button(
                    "Manual reply" if manual_reply else "Send reply",
                    key=f"{section}-send-{message_id}",
                    icon=":material/check_circle:" if manual_reply else ":material/send:",
                    width="stretch",
                    disabled=not manual_reply and not suggested_reply,
                    on_click=(
                        mark_message_as_manually_replied
                        if manual_reply
                        else mark_message_as_replied
                    ),
                    args=(message_id,),
                )
            with action_columns[2]:
                if st.button(
                    "Copy reply",
                    key=f"{section}-copy-{message_id}",
                    icon=":material/content_copy:",
                    width="stretch",
                    disabled=not suggested_reply,
                ):
                    st.session_state["copy_reply_visible"] = message_id
            with action_columns[3]:
                if st.button(
                    "Re-analyze",
                    key=f"{section}-reanalyze-{message_id}",
                    icon=":material/refresh:",
                    width="stretch",
                ):
                    with st.spinner("Re-analyzing message..."):
                        result = classify_message(message)
                        st.session_state["message_analyses"][message["id"]] = {
                            "result": result,
                            "reply": generate_reply(message, result),
                        }
                        st.session_state["human_review_decisions"].pop(message["id"], None)
                        st.session_state["queue_confirmed_ids"].discard(message_id)
                    st.rerun()

            if suggested_reply and st.session_state.get("copy_reply_visible") == message_id:
                st.code(suggested_reply)


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

queued_messages = get_queue(
    messages,
    analyses,
    st.session_state["human_review_decisions"],
)
resolved_ids = st.session_state["resolved_message_ids"]
active_messages = [
    message for message in messages if str(message["id"]) not in resolved_ids
]
history_messages = [
    message for message in messages if str(message["id"]) in resolved_ids
]
queued_messages = [
    message for message in queued_messages
    if str(message["id"]) not in resolved_ids
]
certain_count = sum(
    message["id"] in analyses
    and analyses[message["id"]]["result"].get("category") != "needs_human_review"
    for message in active_messages
)
urgent_items = [
    (message, analyses[message["id"]]["result"])
    for message in active_messages
    if message["id"] in analyses
    and analyses[message["id"]]["result"].get("category") == "urgent"
]
urgent_count = len(urgent_items)
with st.container(key="main-header"):
    logo_col, brand_col, settings_col, logout_col = st.columns(
        [0.16, 0.48, 0.19, 0.17], vertical_alignment="center"
    )
    with logo_col:
        with st.container(key="app-icon"):
            st.image(ICON_FILE, width=96, alt="Silencer logo")
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
            st.session_state["queue_confirmed_ids"] = set()
            st.session_state["resolved_message_ids"] = set()
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
        st.write("API credentials are not displayed here.")

analyses = st.session_state["message_analyses"]
review_decisions = st.session_state["human_review_decisions"]
if urgent_items:
    urgent_message, urgent_result = min(
        urgent_items, key=lambda item: received_at_order(item[0])
    )
    urgent_id = str(urgent_message["id"])
    urgent_sender = html.escape(str(urgent_message["sender"]))
    urgent_body = html.escape(str(urgent_message["message"]))
    priority_state = (
        "unread" if urgent_id not in st.session_state["read_message_ids"] else "read"
    )
    with st.container(key=f"urgent-hero-{priority_state}"):
        st.markdown(
            '<div class="priority-title">Highest Priority Message</div>',
            unsafe_allow_html=True,
        )
        urgent_score = f"{float(urgent_result['urgency_score']):.2f}"
        st.markdown(
            '<div class="hero-urgency"><strong>Urgency level:</strong> '
            f'<span class="urgency-badge" '
            f'style="background-color:{urgency_color(urgent_result)}">'
            f'{urgent_score}</span></div>',
            unsafe_allow_html=True,
        )
        if st.button(
            f"**Sender:** {urgent_sender}\n\n**Message:** {urgent_body}",
            key="urgent-hero-open",
            type="tertiary",
            width="stretch",
            on_click=mark_message_as_read,
            args=(urgent_id,),
        ):
            show_urgent_message(urgent_message, analyses[urgent_message["id"]])

name = html.escape(st.session_state["user_name"].strip().title() or "there")
unread_count = sum(
    str(message["id"]) not in st.session_state["read_message_ids"]
    for message in active_messages
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
    f'<p class="greeting-copy">You have {len(active_messages)} messages today, '
    f'{unread_count} unread. '
    f'{urgent_summary}</p>',
    unsafe_allow_html=True,
)

kpi_data = [
    ("Messages received", str(len(active_messages)), "In your inbox"),
    ("Urgent messages", str(urgent_count), "Immediate attention"),
    ("Analyzed", f"{certain_count}/{len(active_messages)}", "Messages reviewed"),
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

review_items = [
    message for message in active_messages
    if message["id"] in analyses
    and analyses[message["id"]]["result"].get("category") == "needs_human_review"
]
with st.expander(f"Needs human review ({len(review_items)})", expanded=True):
    st.caption("Review uncertain messages and decide whether they can wait until morning.")
    for review_message in review_items:
        review_id = review_message["id"]
        decision = st.session_state["human_review_decisions"].get(review_id)
        render_message_card(review_message, "human-review")
        st.caption(analyses[review_id]["result"]["reason"])
        if decision is True:
            st.success("Your choice: review in the morning")
        elif decision is False:
            st.warning("Your choice: handle tonight")
        morning_col, tonight_col = st.columns(2)
        with morning_col:
            if st.button("Yes, review in morning", key=f"review-morning-{review_id}"):
                resolve_human_review(review_id, review_in_morning=True)
                st.rerun()
        with tonight_col:
            if st.button("No, handle tonight", key=f"review-tonight-{review_id}"):
                resolve_human_review(review_id, review_in_morning=False)
                st.rerun()

with st.expander(f"Morning review queue ({len(queued_messages)})", expanded=True):
    st.caption(
        "Non-urgent messages appear automatically. Human-review messages appear "
        "only when you choose morning review."
    )
    if not queued_messages:
        st.info("No messages in morning review yet. Analyze messages to build the list.")
    else:
        for queued_message in queued_messages:
            render_message_card(queued_message, "morning-queue", queued=True)
if st.session_state.pop("reply_notice", False):
    st.success("The message was marked as replied and moved to History.")
if st.session_state.pop("manual_reply_notice", False):
    st.success("The message was marked as replied and moved to History.")

filter_categories = {
    "Urgent": "urgent",
    "Non-Urgent": "wait_until_morning",
    "Needs Human Review": "needs_human_review",
}
visible_messages = []
for message in active_messages:
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

with st.expander(f"Messages List ({len(visible_messages)})", expanded=True):
    st.caption("All messages are displayed here for your review.")
    if not visible_messages:
        st.info("No messages match the current search and filter.")
    for message in visible_messages:
        render_message_card(message, "inbox")

with st.expander(f"History ({len(history_messages)})", expanded=False):
    st.caption("Review past messages here.")
    if not history_messages:
        st.info("No resolved messages yet.")
    for message in history_messages:
        render_message_card(message, "history", history=True)
