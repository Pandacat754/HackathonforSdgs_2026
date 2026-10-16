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
RELATIONSHIP_MAP_FILE = APP_DIR / "data" / "relationship_map.json"
CATEGORY_DISPLAY_FILE = APP_DIR / "data" / "category_display.json"
REPLY_FEEDBACK_FILE = APP_DIR / "data" / "reply_feedback.json"
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
    .popup-category-review {
        flex-direction: column;
        gap: 0.25rem;
    }
    .popup-category-review strong { margin-right: 0; }
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
    .feedback-actions {
        display: flex;
        gap: 0.4rem;
        margin-top: 0.5rem;
    }
    .st-key-feedback-up-msg001 [data-testid="stButton"] button,
    [class*="st-key-feedback-up-"] [data-testid="stButton"] button,
    [class*="st-key-feedback-down-"] [data-testid="stButton"] button {
        width: 2.7rem;
        min-width: 2.7rem;
        max-width: 2.7rem;
        height: 2.7rem;
        min-height: 2.7rem;
        max-height: 2.7rem;
        padding: 0.25rem;
        border-radius: 50%;
        background: #f1f5f9;
        border-color: #cbd5e1;
        color: #64748b;
        box-shadow: none;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    [class*="st-key-feedback-up-"] [data-testid="stButton"] button > div,
    [class*="st-key-feedback-down-"] [data-testid="stButton"] button > div {
        display: flex !important;
        position: relative;
        width: 100%;
        height: 100%;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    [class*="st-key-feedback-up-"] [data-testid="stIconMaterial"],
    [class*="st-key-feedback-down-"] [data-testid="stIconMaterial"] {
        flex: 0 0 auto;
        position: absolute;
        top: 50%;
        left: 50%;
        margin: 0 !important;
        font-size: 1.25rem !important;
        line-height: 1;
        transform: translate(-50%, -50%);
    }
    .st-key-layout_toggle_button [data-testid="stButton"] button {
        min-width: 3.25rem;
        min-height: 3rem;
        padding: 0.25rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .st-key-layout_toggle_button [data-testid="stIconMaterial"] {
        margin: 0 !important;
        font-size: 1.75rem !important;
    }
    [class*="st-key-feedback-up-"] button[kind="primary"] {
        background: #16a34a !important;
        border-color: #16a34a !important;
        color: #fff !important;
    }
    [class*="st-key-feedback-down-"] button[kind="primary"] {
        background: #dc2626 !important;
        border-color: #dc2626 !important;
        color: #fff !important;
    }
    .stApp:has(.st-key-mobile-layout) .stMainBlockContainer {
        max-width: 100%;
        padding: 0.65rem 0.7rem 1.5rem;
    }
    .stApp:has(.st-key-mobile-layout) .st-key-main-header {
        padding: 0.25rem 0;
        margin-bottom: 0.6rem;
    }
    .stApp:has(.st-key-mobile-layout) .st-key-main-header [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 0.2rem !important;
    }
    .stApp:has(.st-key-mobile-layout) .st-key-app-icon {
        width: 2.8rem;
        height: 2.8rem;
    }
    .stApp:has(.st-key-mobile-layout) .st-key-app-icon [data-testid="stImage"] img {
        width: 44px;
        height: 44px;
    }
    .stApp:has(.st-key-mobile-layout) .brand-title { font-size: 1.35rem; }
    .stApp:has(.st-key-mobile-layout) .brand-subtitle { font-size: 0.62rem; }
    .stApp:has(.st-key-mobile-layout) .st-key-main-header [data-testid="stButton"] button {
        min-width: 2rem;
        padding: 0.25rem;
        font-size: 0.72rem;
        white-space: nowrap;
    }
    .stApp:has(.st-key-mobile-layout) .st-key-layout_toggle_button [data-testid="stButton"] button {
        min-width: 2.75rem;
        min-height: 2.75rem;
    }
    .stApp:has(.st-key-mobile-layout) .st-key-layout_toggle_button [data-testid="stIconMaterial"] {
        font-size: 1.5rem !important;
    }
    .stApp:has(.st-key-mobile-layout) [data-testid="stHorizontalBlock"] {
        gap: 0.55rem;
    }
    .stApp:has(.st-key-mobile-layout) .st-key-search-strip [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
    }
    .stApp:has(.st-key-mobile-layout) .st-key-search-strip [data-testid="stColumn"] {
        flex: 1 1 100% !important;
        min-width: 0;
    }
    .stApp:has(.st-key-mobile-layout) .kpi-card {
        padding: 0.8rem;
    }
    .stApp:has(.st-key-mobile-layout) .kpi-label,
    .stApp:has(.st-key-mobile-layout) .kpi-value {
        font-size: 1.25rem;
        min-height: 0;
    }
    .stApp:has(.st-key-mobile-layout) .greeting-title { font-size: 1.45rem; }
    .stApp:has(.st-key-mobile-layout) .st-key-urgent-hero-read,
    .stApp:has(.st-key-mobile-layout) .st-key-urgent-hero-unread {
        padding: 0.8rem;
        margin: 0.8rem 0;
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
if "show_relationship_map" not in st.session_state:
    st.session_state["show_relationship_map"] = False
if "layout_mode" not in st.session_state:
    st.session_state["layout_mode"] = "desktop"
if "settings_notice" not in st.session_state:
    st.session_state["settings_notice"] = ""
if "human_review_decisions" not in st.session_state:
    st.session_state["human_review_decisions"] = {}
if "read_message_ids" not in st.session_state:
    st.session_state["read_message_ids"] = set()
if "queue_confirmed_ids" not in st.session_state:
    st.session_state["queue_confirmed_ids"] = set()
if "resolved_message_ids" not in st.session_state:
    st.session_state["resolved_message_ids"] = set()

FONT_SIZES = {"Regular": 16, "Large": 19, "Extra large": 22}
MOBILE_FONT_SIZES = {"Regular": 14, "Large": 16, "Extra large": 18}
RELATIONSHIPS = (
    "Family", "Friend", "Lecturer", "Classmate", "Teammate",
    "Client", "Manager", "Colleague", "Other",
)
PREFERRED_TONES = (
    "Casual", "Friendly", "Professional", "Formal",
    "Respectful", "Empathetic", "Direct",
)
CATEGORY_DISPLAY_MODES = ("Standard labels", "Priority labels")
PRIORITY_CODES = ("P0", "P1", "P2")
RESPONSE_STYLE_CYCLE = ("formal", "concise", "warm")
TONE_RESPONSE_STYLES = {
    "Casual": "warm",
    "Friendly": "warm",
    "Professional": "formal",
    "Formal": "formal",
    "Respectful": "formal",
    "Empathetic": "warm",
    "Direct": "concise",
}


def strip_reply_label(reply):
    if not isinstance(reply, str):
        return reply
    for prefix in ("Automated assistant draft:", "自动助手回复草稿："):
        if reply.startswith(prefix):
            return reply[len(prefix):].lstrip()
    return reply


def infer_relationship(sender, message_history=()):
    sender_name = sender.casefold()
    context = " ".join(
        f'{item.get("sender", "")} {item.get("message", "")}'
        for item in message_history
        if str(item.get("sender", "")).casefold() == sender_name
    ).casefold()
    clues = f"{sender_name} {context}"
    if any(title in clues for title in ("lecturer", "professor", "teacher")):
        return "Lecturer"
    if any(title in clues for title in ("friend", "bestie")):
        return "Friend"
    if any(title in clues for title in ("family", "mum", "mom", "dad", "sister", "brother")):
        return "Family"
    if any(title in clues for title in ("classmate", "student")):
        return "Classmate"
    if any(title in clues for title in ("teammate", "team mate")):
        return "Teammate"
    if any(title in clues for title in ("client", "customer")):
        return "Client"
    if "manager" in clues or sender_name in ("boss", "pm"):
        return "Manager"
    if "colleague" in clues or "coworker" in clues:
        return "Colleague"
    return "Other"


def default_sender_profile(sender, message_history=()):
    relationship = infer_relationship(sender, message_history)
    suggested_tone = {
        "Lecturer": "Respectful",
        "Friend": "Casual",
        "Client": "Formal",
        "Family": "Friendly",
        "Classmate": "Friendly",
        "Teammate": "Friendly",
        "Manager": "Professional",
        "Colleague": "Professional",
        "Other": "Professional",
    }[relationship]
    return {
        "name": sender,
        "relationship_type": relationship,
        "preferred_tone": suggested_tone,
    }


def validate_sender_profiles(rows):
    profiles = []
    seen_senders = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each relationship and tone map row must be an object.")

        # Migrate the original profile schema without discarding saved preferences.
        sender = row.get("name", row.get("sender"))
        relationship = row.get("relationship_type", row.get("relationship"))
        tone = row.get("preferred_tone")
        if tone is None:
            tone = {
                "Formal": "Formal",
                "Warm": "Friendly",
                "Concise": "Direct",
            }.get(row.get("response_style"))
        relationship = {
            "Executive": "Manager",
            "Human resources": "Other",
            "Direct report": "Teammate",
            "Unknown": "Other",
        }.get(relationship, relationship)
        if sender is None and relationship is None and tone is None:
            continue
        if not isinstance(sender, str) or not sender.strip() or len(sender.strip()) > 200:
            raise ValueError("Each contact needs a name of 1–200 characters.")
        sender = sender.strip()
        if sender.casefold() in seen_senders:
            raise ValueError(f"Contact “{sender}” appears more than once.")
        if relationship not in RELATIONSHIPS:
            raise ValueError(f"Choose a valid relationship for {sender}.")
        if tone not in PREFERRED_TONES:
            raise ValueError(f"Choose a valid preferred tone for {sender}.")
        seen_senders.add(sender.casefold())
        profiles.append({
            "name": sender,
            "relationship_type": relationship,
            "preferred_tone": tone,
        })
    return profiles


def load_sender_profiles(messages):
    senders = dict.fromkeys(str(message["sender"]) for message in messages)
    if RELATIONSHIP_MAP_FILE.exists():
        try:
            saved_profiles = validate_sender_profiles(
                json.loads(RELATIONSHIP_MAP_FILE.read_text(encoding="utf-8"))
            )
        except (OSError, json.JSONDecodeError, ValueError) as error:
            st.error(f"Could not load the saved relationship and tone map: {error}")
            st.stop()
        known_senders = {profile["name"].casefold() for profile in saved_profiles}
        saved_profiles.extend(
            default_sender_profile(sender, messages)
            for sender in senders
            if sender.casefold() not in known_senders
        )
        return saved_profiles
    return [default_sender_profile(sender, messages) for sender in senders]


def get_sender_profile(message, profiles):
    sender = str(message.get("sender", ""))
    return next(
        (profile for profile in profiles if profile["name"].casefold() == sender.casefold()),
        default_sender_profile(sender, [message]),
    )


def with_sender_profile(message, profile):
    return {**message, "sender_relationship": profile["relationship_type"]}


def sender_policy(profile):
    sender_key = profile["name"].casefold()
    preferred_style = TONE_RESPONSE_STYLES[profile["preferred_tone"]]
    style = st.session_state["reply_feedback"]["style_overrides"].get(
        sender_key, preferred_style
    )
    return {
        "response_style": style,
        "preferred_tone": profile["preferred_tone"],
    }


def default_category_display():
    return {
        "mode": "Standard labels",
        "urgent": "P0",
        "wait_until_morning": "P2",
    }


def load_category_display():
    if not CATEGORY_DISPLAY_FILE.exists():
        return default_category_display()
    try:
        settings = json.loads(CATEGORY_DISPLAY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        st.error(f"Could not load category display settings: {error}")
        st.stop()
    defaults = default_category_display()
    if isinstance(settings, dict) and settings.get("mode") == "Priority codes":
        settings["mode"] = "Priority labels"
    if (
        not isinstance(settings, dict)
        or settings.get("mode") not in CATEGORY_DISPLAY_MODES
        or settings.get("urgent") not in PRIORITY_CODES
        or settings.get("wait_until_morning") not in PRIORITY_CODES
    ):
        st.error("Saved category display settings contain invalid values.")
        st.stop()
    return {key: settings.get(key, value) for key, value in defaults.items()}


def category_display_label(result):
    if result is None:
        return "Not analyzed"
    if st.session_state["category_display"]["mode"] == "Priority labels":
        category = result.get("category")
        if category in ("urgent", "wait_until_morning"):
            return st.session_state["category_display"][category]
        if category == "needs_human_review":
            return "P-1"
    return result.get("classification", "Not analyzed")


def apply_category_display(edited_settings):
    settings = {
        "mode": edited_settings["mode"],
        "urgent": edited_settings["urgent"],
        "wait_until_morning": edited_settings["wait_until_morning"],
    }
    if (
        settings["mode"] not in CATEGORY_DISPLAY_MODES
        or settings["urgent"] not in PRIORITY_CODES
        or settings["wait_until_morning"] not in PRIORITY_CODES
    ):
        st.error("Choose valid category display settings.")
        return False
    try:
        CATEGORY_DISPLAY_FILE.write_text(
            json.dumps(settings, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        st.error(f"Could not save category display settings: {error}")
        return False
    st.session_state["category_display"] = settings
    return True


def load_reply_feedback():
    if not REPLY_FEEDBACK_FILE.exists():
        return {"ratings": {}, "style_overrides": {}}
    try:
        saved = json.loads(REPLY_FEEDBACK_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        st.error(f"Could not load reply feedback: {error}")
        st.stop()
    if not isinstance(saved, dict):
        st.error("Saved reply feedback has an invalid format.")
        st.stop()
    ratings = saved.get("ratings", {})
    overrides = saved.get("style_overrides", {})
    if (
        not isinstance(ratings, dict)
        or not isinstance(overrides, dict)
        or any(
            not isinstance(entry, dict)
            or entry.get("rating") not in ("up", "down")
            or not isinstance(entry.get("sender"), str)
            or entry.get("style") not in RESPONSE_STYLE_CYCLE
            for entry in ratings.values()
        )
        or any(style not in RESPONSE_STYLE_CYCLE for style in overrides.values())
    ):
        st.error("Saved reply feedback has invalid entries.")
        st.stop()
    return {"ratings": ratings, "style_overrides": overrides}


def record_reply_feedback(message_id, rating):
    analysis = st.session_state["message_analyses"].get(message_id)
    message = next(
        (item for item in messages if str(item["id"]) == str(message_id)),
        None,
    )
    if (
        analysis is None
        or message is None
        or rating not in ("up", "down")
        or not analysis["reply"].get("suggested_reply")
    ):
        st.session_state["feedback_notice"] = "This reply is no longer available to rate."
        return

    current = st.session_state["reply_feedback"]
    ratings = dict(current["ratings"])
    previous_rating = ratings.get(str(message_id), {}).get("rating")
    if previous_rating == rating:
        ratings.pop(str(message_id))
    else:
        profile = get_sender_profile(message, st.session_state["sender_profiles"])
        ratings[str(message_id)] = {
            "sender": profile["name"],
            "rating": rating,
            "style": sender_policy(profile)["response_style"],
        }

    sender_key = message["sender"].casefold()
    sender_ratings = [
        entry for entry in ratings.values()
        if entry["sender"].casefold() == sender_key
    ]
    up_count = sum(entry["rating"] == "up" for entry in sender_ratings)
    down_count = sum(entry["rating"] == "down" for entry in sender_ratings)
    overrides = dict(current["style_overrides"])
    if down_count > up_count:
        latest_down_style = next(
            entry["style"] for entry in reversed(list(ratings.values()))
            if entry["sender"].casefold() == sender_key and entry["rating"] == "down"
        )
        style_index = RESPONSE_STYLE_CYCLE.index(latest_down_style)
        overrides[sender_key] = RESPONSE_STYLE_CYCLE[
            (style_index + 1) % len(RESPONSE_STYLE_CYCLE)
        ]
    elif up_count > down_count:
        latest_up_style = next(
            entry["style"] for entry in reversed(list(ratings.values()))
            if entry["sender"].casefold() == sender_key and entry["rating"] == "up"
        )
        overrides[sender_key] = latest_up_style
    else:
        overrides.pop(sender_key, None)

    updated = {"ratings": ratings, "style_overrides": overrides}
    try:
        REPLY_FEEDBACK_FILE.write_text(
            json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        st.session_state["feedback_notice"] = f"Could not save reply feedback: {error}"
        return
    st.session_state["reply_feedback"] = updated
    for existing_message in messages:
        existing_analysis = st.session_state["message_analyses"].get(
            existing_message["id"]
        )
        if (
            not existing_analysis
            or existing_message["sender"].casefold() != sender_key
        ):
            continue
        existing_profile = get_sender_profile(
            existing_message, st.session_state["sender_profiles"]
        )
        agent_message = with_sender_profile(existing_message, existing_profile)
        policy = sender_policy(existing_profile)
        reply = generate_reply(agent_message, existing_analysis["result"], policy)
        existing_analysis["result"]["suggested_reply"] = reply["suggested_reply"]
        existing_analysis["reply"] = reply
    st.session_state["feedback_notice"] = (
        "Reply preference updated from your feedback."
        if rating == "down" and previous_rating != "down"
        else "Reply feedback saved."
    )


def tone_explanation(profile):
    relationship = profile["relationship_type"]
    tone = profile["preferred_tone"]
    explanations = {
        "Lecturer": "Respectful, professional wording is prioritized for a lecturer.",
        "Friend": "A casual, friendly register suits a personal conversation with a friend.",
        "Client": "Formal, professional wording supports clear client communication.",
    }
    explanation = explanations.get(
        relationship,
        f"{tone} wording follows your preference for a {relationship.lower()}.",
    )
    return explanation


def visible_contact_tone(profile):
    relationship = profile["relationship_type"]
    tone = profile["preferred_tone"]
    combined_tones = {
        ("Lecturer", "Respectful"): "Respectful + Professional",
        ("Friend", "Casual"): "Casual + Friendly",
        ("Friend", "Friendly"): "Casual + Friendly",
        ("Client", "Formal"): "Formal + Professional",
    }
    return combined_tones.get((relationship, tone), tone)


def relationship_map_dot(profiles):
    quote = lambda label: json.dumps(str(label), ensure_ascii=False)
    category_styles = {
        "Family": ("♥", "#fce7f3", "#be185d"),
        "Friend": ("★", "#fef3c7", "#b45309"),
        "Lecturer": ("▣", "#ede9fe", "#6d28d9"),
        "Classmate": ("◉", "#dbeafe", "#1d4ed8"),
        "Teammate": ("◆", "#dcfce7", "#15803d"),
        "Client": ("⬟", "#ffedd5", "#c2410c"),
        "Manager": ("▲", "#fee2e2", "#b91c1c"),
        "Colleague": ("●", "#e0f2fe", "#0369a1"),
        "Other": ("○", "#f1f5f9", "#475569"),
    }
    lines = [
        "digraph relationship_tone_map {",
        'graph [rankdir=TB, bgcolor="transparent", nodesep=0.35, ranksep=0.55];',
        'node [shape=box, style="rounded,filled", fontname="Arial", fontsize=11, '
        'color="#bfdbfe", fillcolor="#eff6ff", fontcolor="#1e3a8a", margin="0.18,0.1"];',
        'edge [color="#94a3b8", penwidth=1.4, arrowhead=none];',
        f'map_root [label={quote("Relationship & Tone Map")}, fillcolor="#2563eb", '
        'color="#2563eb", fontcolor="white", fontsize=14];',
    ]
    if not profiles:
        lines.append(f'empty [label={quote("No contacts mapped yet")}];')
        lines.append("map_root -> empty;")
    grouped_profiles = {}
    for profile in profiles:
        grouped_profiles.setdefault(profile["relationship_type"], []).append(profile)
    for relationship_index, (relationship, contacts) in enumerate(grouped_profiles.items()):
        icon, fill, color = category_styles[relationship]
        relationship_id = f"relationship_{relationship_index}"
        lines.append(
            f'{relationship_id} [label={quote(f"{icon}  {relationship}")}, '
            f'fillcolor={quote(fill)}, color={quote(color)}, '
            f'fontcolor={quote(color)}];'
        )
        lines.append(f"map_root -> {relationship_id};")
        for contact_index, profile in enumerate(contacts):
            contact_id = f"contact_{relationship_index}_{contact_index}"
            contact_label = (
                f'{profile["name"]}\nTone: {visible_contact_tone(profile)}'
            )
            lines.append(
                f'{contact_id} [label={quote(contact_label)}, '
                f'tooltip={quote(tone_explanation(profile))}, '
                f'fillcolor={quote(fill)}, color={quote(color)}, '
                f'fontcolor="#1e293b"];'
            )
            lines.append(f"{relationship_id} -> {contact_id};")
    lines.append("}")
    return "\n".join(lines)


for saved_analysis in st.session_state["message_analyses"].values():
    saved_reply = saved_analysis.get("reply")
    if isinstance(saved_reply, dict):
        saved_reply["suggested_reply"] = strip_reply_label(
            saved_reply.get("suggested_reply")
        )


def is_valid_login(username, password):
    return username == "User" and password == "1234"


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

if "sender_profiles" not in st.session_state:
    st.session_state["sender_profiles"] = load_sender_profiles(messages)
if "category_display" not in st.session_state:
    st.session_state["category_display"] = load_category_display()
if "reply_feedback" not in st.session_state:
    st.session_state["reply_feedback"] = load_reply_feedback()

st.session_state["read_message_ids"].intersection_update(
    str(message["id"]) for message in messages
)
st.session_state["resolved_message_ids"].intersection_update(
    str(message["id"]) for message in messages
)
if st.session_state.get("feedback_notice"):
    st.info(st.session_state.pop("feedback_notice"))

st.markdown(
    f"<style>:root {{ --app-font-size: "
    f"{MOBILE_FONT_SIZES[st.session_state['font_size']] if st.session_state['layout_mode'] == 'mobile' else FONT_SIZES[st.session_state['font_size']]}px; "
    "}</style>",
    unsafe_allow_html=True,
)
if st.session_state["layout_mode"] == "mobile":
    with st.container(key="mobile-layout"):
        st.empty()


@st.dialog("Urgent message", width="medium")
def show_urgent_message(message, analysis):
    show_message_details_content(message, analysis)


@st.dialog("Message details", width="medium")
def show_message_details(message, analysis):
    show_message_details_content(message, analysis)
    if not analysis and st.button("Analyze message", key=f"dialog-analyze-{message['id']}"):
        profile = get_sender_profile(message, st.session_state["sender_profiles"])
        agent_message = with_sender_profile(message, profile)
        policy = sender_policy(profile)
        result = classify_message(agent_message, policy)
        reply = generate_reply(agent_message, result, policy)
        st.session_state["message_analyses"][message["id"]] = {
            "result": result,
            "reply": reply,
        }
        st.session_state["human_review_decisions"].pop(message["id"], None)
        st.rerun()


def show_message_details_content(message, analysis):
    message_id = html.escape(str(message["id"]))
    sender = html.escape(str(message["sender"]))
    app_name = html.escape(str(message.get("app") or "Not provided"))
    received_at = html.escape(str(message.get("received_at") or "Not provided"))
    full_message = html.escape(str(message["message"]))
    urgency_badge = '<span class="urgency-badge" style="background-color:#6c757d">Not assessed</span>'
    category = "Awaiting analysis"
    extra_content = ""

    if analysis:
        result = analysis["result"]
        reply = analysis["reply"]
        category = category_display_label(result)
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
    if category_key == "needs_human_review":
        category_markup = (
            '<div class="popup-category-review">'
            '<strong>Category:</strong>'
            f'<span>{html.escape(str(category))}</span>'
            '</div>'
        )
    else:
        category_markup = (
            f'<div><strong>Category:</strong> {html.escape(str(category))}</div>'
        )
    st.markdown(
        '<div class="popup-header">'
        f'<div><strong>Case ID:</strong> {message_id}</div>'
        f'{category_markup}'
        f'<div class="popup-urgency"><strong>Urgency level:</strong> '
        f'{urgency_badge}</div>'
        '</div>'
        '<div class="popup-body">'
        f'<p><strong>Sender: </strong>{sender}</p>'
        f'<p><strong>From: </strong>{app_name}</p>'
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
    category_label = category_display_label(result)
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
    from_label = html.escape(str(message.get("app") or "Not provided"))

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
                        profile = get_sender_profile(
                            message, st.session_state["sender_profiles"]
                        )
                        agent_message = with_sender_profile(message, profile)
                        policy = sender_policy(profile)
                        result = classify_message(agent_message, policy)
                        st.session_state["message_analyses"][message["id"]] = {
                            "result": result,
                            "reply": generate_reply(agent_message, result, policy),
                        }
                        st.session_state["human_review_decisions"].pop(message["id"], None)
                        st.session_state["queue_confirmed_ids"].discard(message_id)
                    st.rerun()

            if suggested_reply:
                current_rating = st.session_state["reply_feedback"]["ratings"].get(
                    message_id, {}
                ).get("rating")
                feedback_columns = st.columns([1, 1, 8])
                with feedback_columns[0]:
                    st.button(
                        " ",
                        key=f"feedback-up-{section}-{message_id}",
                        icon=":material/thumb_up:",
                        help="This reply was helpful",
                        type="primary" if current_rating == "up" else "secondary",
                        on_click=record_reply_feedback,
                        args=(message_id, "up"),
                    )
                with feedback_columns[1]:
                    st.button(
                        " ",
                        key=f"feedback-down-{section}-{message_id}",
                        icon=":material/thumb_down:",
                        help="This reply needs improvement",
                        type="primary" if current_rating == "down" else "secondary",
                        on_click=record_reply_feedback,
                        args=(message_id, "down"),
                    )

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
            profile = get_sender_profile(message, st.session_state["sender_profiles"])
            agent_message = with_sender_profile(message, profile)
            policy = sender_policy(profile)
            result = classify_message(agent_message, policy)
            analyses[message["id"]] = {
                "result": result,
                "reply": generate_reply(agent_message, result, policy),
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
    logo_col, brand_col, layout_col, settings_col, logout_col = st.columns(
        [0.14, 0.40, 0.10, 0.18, 0.16], vertical_alignment="center"
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
    with layout_col:
        layout_icon = (
            ":material/desktop_windows:"
            if st.session_state["layout_mode"] == "desktop"
            else ":material/smartphone:"
        )
        if st.button(
            " ",
            key="layout_toggle_button",
            icon=layout_icon,
            help="Switch between desktop and mobile layout",
            width="stretch",
        ):
            st.session_state["layout_mode"] = (
                "mobile"
                if st.session_state["layout_mode"] == "desktop"
                else "desktop"
            )
            st.rerun()
    with settings_col:
        settings_label = " " if st.session_state["layout_mode"] == "mobile" else "Settings"
        if st.button(
            settings_label,
            key="settings_button",
            icon=":material/settings:",
            help="Settings",
            width="stretch",
        ):
            st.session_state["show_settings"] = not st.session_state["show_settings"]
    with logout_col:
        logout_label = " " if st.session_state["layout_mode"] == "mobile" else "Log out"
        if st.button(
            logout_label,
            key="logout_button",
            icon=":material/logout:",
            help="Log out",
            width="stretch",
        ):
            st.session_state["is_authenticated"] = False
            st.session_state["user_name"] = ""
            st.session_state["read_message_ids"] = set()
            st.session_state["queue_confirmed_ids"] = set()
            st.session_state["resolved_message_ids"] = set()
            st.rerun()

if st.session_state["show_settings"]:
    with st.container(border=True):
        if st.session_state["settings_notice"]:
            st.success(st.session_state.pop("settings_notice"))
        mode = os.environ.get("SILENCER_MODE", "mock")
        st.write(f"Analysis mode: **{mode}**")
        st.selectbox(
            "Font size",
            tuple(FONT_SIZES),
            key="font_size",
            help="Choose Regular, Large, or Extra large text for the app.",
        )
        category_display_mode = st.selectbox(
            "Message category label",
            CATEGORY_DISPLAY_MODES,
            key="category_display_mode",
            index=CATEGORY_DISPLAY_MODES.index(
                st.session_state["category_display"]["mode"]
            ),
        )
        if category_display_mode == "Priority labels":
            urgent_priority = st.selectbox(
                "Urgent category",
                PRIORITY_CODES,
                key="urgent_priority",
                index=PRIORITY_CODES.index(
                    st.session_state["category_display"]["urgent"]
                ),
            )
            non_urgent_priority = st.selectbox(
                "Not urgent category",
                PRIORITY_CODES,
                key="non_urgent_priority",
                index=PRIORITY_CODES.index(
                    st.session_state["category_display"]["wait_until_morning"]
                ),
            )
            st.caption("P-1 always means Needs Human Review.")
        else:
            urgent_priority = st.session_state["category_display"]["urgent"]
            non_urgent_priority = st.session_state["category_display"]["wait_until_morning"]
        if st.button(
            "Apply category labels",
            key="apply_category_labels",
            type="primary",
        ):
            if apply_category_display({
                "mode": category_display_mode,
                "urgent": urgent_priority,
                "wait_until_morning": non_urgent_priority,
            }):
                st.session_state["settings_notice"] = "Category label settings applied."
                st.rerun()
        st.toggle(
            "Show Relationship & Tone Map",
            key="show_relationship_map",
            help="Show or hide contact relationships and preferred tones.",
        )
        if st.session_state["show_relationship_map"]:
            st.subheader("Relationship & Tone Map")
            st.caption(
                "Personalize draft replies with each contact's relationship and preferred "
                "tone. New profiles are preliminary suggestions for you to review; "
                "these settings never change message urgency."
            )
            st.graphviz_chart(
                relationship_map_dot(st.session_state["sender_profiles"]),
                width="stretch",
                alt="Contact profiles grouped by relationship, with preferred tone shown on each contact",
            )
            profiles = st.session_state["sender_profiles"]
            contact_options = ["Add contact"] + [
                profile["name"] for profile in profiles
            ]
            selected_contact = st.selectbox(
                "Contact profile",
                contact_options,
                key="relationship_profile_selection",
            )
            selected_profile = next(
                (
                    profile for profile in profiles
                    if profile["name"] == selected_contact
                ),
                None,
            )
            profile_key = (
                selected_profile["name"].casefold().replace(" ", "_")
                if selected_profile else "new"
            )
            relationship_default = (
                selected_profile["relationship_type"]
                if selected_profile else RELATIONSHIPS[-1]
            )
            tone_default = (
                selected_profile["preferred_tone"]
                if selected_profile else "Professional"
            )
            with st.form("relationship_profile_form"):
                input_columns = st.columns([1.3, 1, 1, 0.7])
                with input_columns[0]:
                    contact_name = st.text_input(
                        "Name",
                        value=selected_profile["name"] if selected_profile else "",
                        max_chars=200,
                        key=f"relationship_name_{profile_key}",
                    )
                with input_columns[1]:
                    relationship_type = st.selectbox(
                        "Relationship Type",
                        RELATIONSHIPS,
                        index=RELATIONSHIPS.index(relationship_default),
                        key=f"relationship_type_{profile_key}",
                    )
                with input_columns[2]:
                    preferred_tone = st.selectbox(
                        "Preferred Tone",
                        PREFERRED_TONES,
                        index=PREFERRED_TONES.index(tone_default),
                        key=f"preferred_tone_{profile_key}",
                    )
                with input_columns[3]:
                    save_relationship_map = st.form_submit_button(
                        "Save profile",
                        key="save_relationship_profile",
                        type="primary",
                        width="stretch",
                    )
            if save_relationship_map:
                try:
                    if not contact_name.strip():
                        raise ValueError("Enter a contact name before saving.")
                    updated_profile = validate_sender_profiles([{
                        "name": contact_name,
                        "relationship_type": relationship_type,
                        "preferred_tone": preferred_tone,
                    }])[0]
                    next_profiles = list(profiles)
                    existing_index = next(
                        (
                            index for index, profile in enumerate(next_profiles)
                            if profile["name"].casefold()
                            == selected_contact.casefold()
                        ),
                        None,
                    )
                    duplicate_index = next(
                        (
                            index for index, profile in enumerate(next_profiles)
                            if profile["name"].casefold()
                            == updated_profile["name"].casefold()
                        ),
                        None,
                    )
                    if (
                        duplicate_index is not None
                        and duplicate_index != existing_index
                    ):
                        raise ValueError(
                            f'Contact “{updated_profile["name"]}” already exists.'
                        )
                    if existing_index is None:
                        next_profiles.append(updated_profile)
                    else:
                        next_profiles[existing_index] = updated_profile
                    next_profiles = validate_sender_profiles(next_profiles)
                except (OSError, ValueError) as error:
                    st.error(f"Could not save the Relationship & Tone Map: {error}")
                else:
                    try:
                        RELATIONSHIP_MAP_FILE.write_text(
                            json.dumps(next_profiles, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8",
                        )
                    except OSError as error:
                        st.error(f"Could not save the Relationship & Tone Map: {error}")
                    else:
                        st.session_state["sender_profiles"] = next_profiles
                        for message in messages:
                            analysis = st.session_state["message_analyses"].get(
                                message["id"]
                            )
                            if not analysis:
                                continue
                            profile = get_sender_profile(message, next_profiles)
                            agent_message = with_sender_profile(message, profile)
                            policy = sender_policy(profile)
                            reply = generate_reply(
                                agent_message, analysis["result"], policy
                            )
                            analysis["result"]["suggested_reply"] = (
                                reply["suggested_reply"]
                            )
                            analysis["reply"] = reply
                        st.session_state["settings_notice"] = (
                            "Relationship & Tone Map saved."
                        )
                        st.rerun()
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
