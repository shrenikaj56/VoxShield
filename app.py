import os
import sys
import time
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from utils.config import DEFAULT_SCENARIOS
from utils.helpers import incident_id, now_iso, risk_level, decision_for_risk_level
from modules.database import ensure_database, store_incident, fetch_recent_incidents
from modules.risk_engine import run_risk_engine
from modules.report_generator import generate_html_report, generate_pdf_report

load_dotenv()

st.set_page_config(page_title="VoxShield", page_icon="🛡️", layout="wide")

# ---------------------------------------------------------------------------
# UX styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Rajdhani:wght@600;700&display=swap');
    .stApp {
        background: radial-gradient(circle at 10% 10%, rgba(35, 68, 80, 0.95), #071b22 80%, #020d10);
        color: #eefcfb;
        font-family: 'Inter', Arial, sans-serif;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #10292e, #061b21);
        border-right: 1px solid rgba(119,234,210,0.35);
    }
    .block-container {
        padding-top: 2rem;
    }
    .vox-main-title {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #eefeff;
    }
    .subtle-text {
        color: #b6d9d4;
        font-size: 0.88rem;
    }
    .vc-card {
        border-radius: 16px;
        padding: 1rem;
        background: linear-gradient(160deg, rgba(18, 54, 57, 0.94), rgba(9, 30, 36, 0.94));
        border: 1px solid rgba(132, 244, 219, 0.38);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.1);
    }
    .login-shell {
        min-height: 88vh;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .login-panel {
        border-radius: 24px;
        border: 1px solid rgba(116, 232, 210, 0.36);
        background: linear-gradient(180deg, rgba(20,51,59,0.98), rgba(10,29,33,0.98));
        padding: 2rem;
        max-width: 1050px;
        width: 100%;
        box-shadow: 0 16px 60px rgba(0,0,0,0.34);
    }
    .login-title {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: white;
    }
    .login-subtitle {
        color: #b9eee8;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }
    .status-low { border-color: #12cf7e; background: linear-gradient(160deg, #123225, #092517); }
    .status-medium { border-color: #f0b94b; background: linear-gradient(160deg, #3b3122, #211a12); }
    .status-high { border-color: #f46760; background: linear-gradient(160deg, #432220, #221614); }
    .risk-score {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        font-family: 'Rajdhani', 'Inter', sans-serif;
    }
    .kpi-title { color: #a9e6de; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; }
    .kpi-value { font-size: 1.7rem; font-weight: 800; color: white; }
    .risk-meter-outer { background: #092a2d; border-radius: 10px; overflow: hidden; border: 1px solid #1b7669; height: 12px; }
    .risk-meter-fill { height: 100%; background: linear-gradient(90deg, #14c185, #0ba777, #d4b316, #f65d58); }
    .decision-banner { border-radius: 13px; padding: 1rem; border-left: 5px solid #33f7b1; background: #153b38; }
    .decision-banner.high { border-color: #ff6565; background: #452928; }
    .decision-banner.medium { border-color: #f6c358; background: #45391d; }
    .small-btn { font-size: 0.75rem; }

    /* =========================================================
       HOME PAGE CSS
       ========================================================= */

    /* =========================================================
   VOXSHIELD HOME PAGE
   ========================================================= */

    .home-hero {
        padding: 2.2rem 0 1.5rem 0;
    }

    .home-eyebrow {
        color: #77ead2;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 0.8rem;
    }

    .home-title {
        font-size: 3.1rem;
        line-height: 1.05;
        font-weight: 800;
        letter-spacing: -0.045em;
        color: #ffffff;
        margin-bottom: 1rem;
    }

    .home-title span {
        color: #77ead2;
    }

    .home-description {
        max-width: 850px;
        color: #c7e5e1;
        font-size: 1.05rem;
        line-height: 1.7;
        margin-bottom: 1.5rem;
    }

    .home-usp {
        border-left: 3px solid #77ead2;
        padding: 0.8rem 1rem;
        margin: 1.2rem 0 1.5rem 0;
        background: rgba(119, 234, 210, 0.06);
        color: #e8fffb;
        border-radius: 0 10px 10px 0;
    }

    .home-section-title {
        color: #ffffff;
        font-size: 1.35rem;
        font-weight: 800;
        margin: 1.8rem 0 0.4rem 0;
    }

    .home-section-subtitle {
        color: #a9cbc7;
        font-size: 0.88rem;
        margin-bottom: 1rem;
    }

    .home-status-card {
        min-height: 105px;
        border-radius: 15px;
        padding: 1.05rem 1.15rem;
        background: linear-gradient(
            145deg,
            rgba(19, 55, 59, 0.96),
            rgba(7, 28, 34, 0.96)
        );
        border: 1px solid rgba(119, 234, 210, 0.30);
        box-shadow: 0 8px 25px rgba(0,0,0,0.16);
    }

    .home-status-label {
        color: #8fd7cd;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.11em;
        font-weight: 700;
    }

    .home-status-value {
        color: #ffffff;
        font-size: 1.35rem;
        font-weight: 800;
        margin-top: 0.35rem;
    }

    .home-status-detail {
        color: #a9cbc7;
        font-size: 0.75rem;
        margin-top: 0.15rem;
    }

    .pipeline-card {
        min-height: 155px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        border-radius: 15px;
        padding: 1rem;
        background: rgba(10, 37, 43, 0.92);
        border: 1px solid rgba(119, 234, 210, 0.25);
    }

    .pipeline-number {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(119, 234, 210, 0.12);
        border: 1px solid rgba(119, 234, 210, 0.45);
        color: #77ead2;
        font-weight: 800;
        margin-bottom: 0.55rem;
    }

    .pipeline-title {
        color: #ffffff;
        font-size: 0.92rem;
        font-weight: 800;
    }

    .pipeline-text {
        color: #a9cbc7;
        font-size: 0.72rem;
        margin-top: 0.25rem;
    }

    .pipeline-arrow {
        display: flex;
        align-items: center;
        justify-content: center;
        color: #77ead2;
        font-size: 1.5rem;
        font-weight: 800;
    }

    .feature-card {
        min-height: 155px;
        border-radius: 15px;
        padding: 1.2rem;
        background: linear-gradient(
            150deg,
            rgba(17, 51, 55, 0.96),
            rgba(8, 29, 35, 0.96)
        );
        border: 1px solid rgba(119, 234, 210, 0.23);
    }

    .feature-title {
        color: #ffffff;
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }

    .feature-text {
        color: #afd0cc;
        font-size: 0.78rem;
        line-height: 1.6;
    }

    .demo-card {
        min-height: 175px;
        border-radius: 15px;
        padding: 1.2rem;
        background: rgba(9, 32, 38, 0.96);
        border: 1px solid rgba(119, 234, 210, 0.24);
    }

    .demo-label {
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #91d8cf;
    }

    .demo-amount {
        font-size: 1.55rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0.35rem 0;
    }

    .demo-description {
        color: #a9cbc7;
        font-size: 0.75rem;
        min-height: 38px;
    }

    .demo-low {
        color: #35e69a;
        font-weight: 800;
        font-size: 0.78rem;
    }

    .demo-medium {
        color: #f4c45c;
        font-weight: 800;
        font-size: 0.78rem;
    }

    .demo-high {
        color: #ff716a;
        font-weight: 800;
        font-size: 0.78rem;
    }

    .difference-card {
        border-radius: 18px;
        padding: 1.5rem;
        background: linear-gradient(
            135deg,
            rgba(17, 58, 61, 0.98),
            rgba(7, 29, 35, 0.98)
        );
        border: 1px solid rgba(119, 234, 210, 0.30);
    }

    .difference-title {
        color: #ffffff;
        font-size: 1.2rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }

    .difference-text {
        color: #b9d8d4;
        font-size: 0.84rem;
        line-height: 1.7;
    }

    .flow-box {
        text-align: center;
        padding: 0.85rem;
        border-radius: 10px;
        background: rgba(119, 234, 210, 0.07);
        border: 1px solid rgba(119, 234, 210, 0.20);
        color: #ffffff;
        font-weight: 700;
        font-size: 0.78rem;
    }

    .home-disclaimer {
        margin-top: 2rem;
        padding: 0.8rem 1rem;
        border-top: 1px solid rgba(119, 234, 210, 0.15);
        color: #789a96;
        font-size: 0.7rem;
        line-height: 1.6;
    }
    /* =========================================================
    VOXSHIELD BRAND HEADER
    ========================================================= */

    .brand-header {
        padding: 1.5rem 0 2.2rem 0;
        text-align: left;
    }

    .brand-logo {
        margin-bottom: 0.6rem;
    }

    .brand-logo svg {
        display: block;
        filter: drop-shadow(0 0 12px rgba(91, 188, 255, 0.25));
    }

    .brand-name {
        font-size: 3.2rem;
        line-height: 1;
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #ffffff;
        margin-bottom: 0.55rem;
    }

    .brand-tagline {
        color: #77ead2;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    .brand-description {
        max-width: 850px;
        color: #b9d8d4;
        font-size: 1rem;
        line-height: 1.65;
    }

    /* Secure payment flow */
    .payment-page-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0.15rem;
    }
    .payment-page-subtitle {
        text-align: center;
        color: #9fc7c2;
        font-size: 0.82rem;
        margin-bottom: 1.4rem;
    }
    .payment-card {
        max-width: 620px;
        margin: 0 auto;
        padding: 1.7rem 1.8rem;
        border-radius: 22px;
        background: linear-gradient(160deg, rgba(18,54,57,.98), rgba(7,28,34,.98));
        border: 1px solid rgba(119,234,210,.30);
        box-shadow: 0 16px 45px rgba(0,0,0,.22);
    }
    .payment-label {
        color: #8db7b2;
        font-size: .7rem;
        text-transform: uppercase;
        letter-spacing: .12em;
        font-weight: 700;
    }
    .payment-recipient {
        color: #ffffff;
        font-size: 1.25rem;
        font-weight: 800;
        margin-top: .25rem;
    }
    .payment-upi {
        color: #9fc7c2;
        font-size: .78rem;
        margin-top: .15rem;
    }
    .payment-amount {
        color: #77ead2;
        font-size: 2.45rem;
        font-weight: 800;
        text-align: center;
        margin: 1.1rem 0;
    }
    .payment-divider {
        height: 1px;
        background: rgba(119,234,210,.16);
        margin: 1rem 0;
    }
    .payment-method {
        color: #ffffff;
        font-weight: 700;
        margin-top: .25rem;
    }
    .payment-account {
        color: #d8efeb;
        font-weight: 700;
        margin-top: .25rem;
    }
    .payment-account-sub {
        color: #8eaaa6;
        font-size: .78rem;
    }
    .payment-intercept {
        max-width: 620px;
        margin: 1.5rem auto;
        padding: 1.3rem;
        text-align: center;
        border-radius: 18px;
        background: rgba(119,234,210,.06);
        border: 1px solid rgba(119,234,210,.22);
    }
    .payment-result {
        max-width: 720px;
        margin: 0 auto;
        padding: 1.5rem;
        border-radius: 20px;
        border: 1px solid rgba(119,234,210,.25);
        background: rgba(8,31,37,.96);
    }
    .payment-result-low { border-color: rgba(53,230,154,.45); }
    .payment-result-medium { border-color: rgba(244,196,92,.48); }
    .payment-result-high { border-color: rgba(255,113,106,.48); }
    .payment-result-title {
        color: #ffffff;
        font-size: 1.55rem;
        font-weight: 800;
        margin-bottom: .35rem;
    }
    .payment-risk-score {
        color: #77ead2;
        font-size: 2rem;
        font-weight: 800;
    }
    .payment-factor {
        color: #c4dcda;
        font-size: .84rem;
        line-height: 1.55;
        margin: .2rem 0;
    }
    .pattern-info {
        max-width: 650px;
        margin: 0 auto 1rem auto;
        text-align: center;
        color: #b9d8d4;
    }
    .pattern-sequence {
        text-align: center;
        color: #77ead2;
        font-weight: 800;
        letter-spacing: .08em;
        margin: .8rem 0 1.2rem 0;
    }
    .pattern-swatch {
        width: 26px;
        height: 26px;
        border-radius: 50%;
        margin: 0 auto .35rem auto;
    }
    .swatch-blue { background:#4aa3ff; }
    .swatch-yellow { background:#f3c84b; }
    .swatch-red { background:#ff665c; }
    .swatch-green { background:#35d69a; }
    .swatch-purple { background:#a56cff; }
    .swatch-orange { background:#ff9a4a; }

    .pattern-grid {
        max-width: 390px;
        margin: 1.4rem auto;
    }
    .pattern-cell {
        height: 92px;
        border-radius: 16px;
        border: 2px solid rgba(255,255,255,.16);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.08);
    }
    .pattern-cell-selected {
        border: 3px solid #77ead2;
        box-shadow: 0 0 0 3px rgba(119,234,210,.14), 0 0 20px rgba(119,234,210,.18);
    }
    .pattern-cell-blue { background: rgba(74,163,255,.22); }
    .pattern-cell-yellow { background: rgba(243,200,75,.22); }
    .pattern-cell-red { background: rgba(255,102,92,.22); }
    .pattern-cell-green { background: rgba(53,214,154,.22); }
    .pattern-cell-purple { background: rgba(165,108,255,.22); }
    .pattern-cell-orange { background: rgba(255,154,74,.22); }
    .pattern-order {
        text-align: center;
        color: #9fc7c2;
        font-size: .78rem;
        margin-top: .5rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session defaults
# ---------------------------------------------------------------------------
if 'last_result' not in st.session_state:
    st.session_state['last_result'] = None
if 'operator_access' not in st.session_state:
    st.session_state['operator_access'] = False
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'last_incident_id' not in st.session_state:
    st.session_state['last_incident_id'] = incident_id()
if 'payment_stage' not in st.session_state:
    st.session_state['payment_stage'] = 'idle'
if 'payment_data' not in st.session_state:
    st.session_state['payment_data'] = {}
if 'payment_result' not in st.session_state:
    st.session_state['payment_result'] = None
if 'payment_auth_pattern' not in st.session_state:
    st.session_state['payment_auth_pattern'] = []
if 'payment_incident_saved' not in st.session_state:
    st.session_state['payment_incident_saved'] = False

# Registered authentication pattern: [row, column]
# Correct default pattern = [1,2] -> [2,2] -> [3,2]
DEFAULT_AUTH_PATTERN = [(1, 2), (2, 2), (3, 2)]
AUTH_MATRIX = [
    ['BLUE', 'YELLOW', 'RED'],
    ['GREEN', 'PURPLE', 'ORANGE'],
    ['ORANGE', 'BLUE', 'GREEN'],
]

PAGES = {
    'Home': 'home',
    'Secure Payment': 'secure_payment',
    'Voice Analysis': 'voice',
    'Risk Analysis': 'risk',
    'Fraud Dashboard': 'dashboard',
    'Incident Report': 'report'
}

ensure_database()

# login screen begins before the app shell
if not st.session_state.get('authenticated', False):
    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    st.markdown('<div class="login-panel">', unsafe_allow_html=True)

    logo_col, title_col = st.columns([1, 3])
    with logo_col:
        st.markdown('<div style="font-size:64px; line-height:1;">🛡️</div>', unsafe_allow_html=True)
    with title_col:
        st.markdown('<div class="login-title">VoxShield</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Fraud Intelligence Console</div>', unsafe_allow_html=True)

    st.markdown('<div class="login-subtitle">Secure Access</div>', unsafe_allow_html=True)
    st.markdown('---')

    with st.form('voxshield_login'):
        st.subheader('Operator Login')
        operator_id = st.text_input('Operator ID', value='operator_demo')
        operator_pin = st.text_input('PIN', type='password', value='1234')
        color_pattern = st.selectbox('Color Pattern', ['Green', 'Blue', 'Amber'])
        submit = st.form_submit_button('Enter Secure Console')

        if submit:
            if operator_pin == '1234' and color_pattern == 'Green':
                st.session_state['authenticated'] = True
                st.session_state['operator_access'] = True
                st.session_state['operator_id'] = operator_id
                st.success('Access granted')
                st.rerun()
            else:
                st.session_state['authenticated'] = False
                st.session_state['operator_access'] = False
                st.error('Authentication failed')

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    if 'nav' not in st.session_state:
        st.session_state['nav'] = 'Home'

    with st.sidebar:
        st.markdown('<div style="font-size:48px;">🛡️</div>', unsafe_allow_html=True)
        st.title('VoxShield')
        st.caption('Real-Time UPI and Voice-Cloning Fraud Intervention')
        st.markdown('---')
        st.subheader('Console Access')
        operator_id = st.text_input(
            'Operator ID',
            value=st.session_state.get('operator_id', 'operator_demo')
        )
        operator_pin = st.text_input('Demo PIN', type='password', value='1234')

        if st.button('Unlock Console'):
            if operator_pin == '1234':
                st.session_state['operator_access'] = True
                st.success('Console unlocked')
            else:
                st.session_state['operator_access'] = False
                st.error('Invalid demo PIN')

        if st.session_state['operator_access']:
            st.success('Access: Secure Console Online')
        else:
            st.info('Demo Mode: Access Locked')

        st.markdown('---')
        nav = st.radio(
            'Navigation',
            list(PAGES.keys()),
            index=list(PAGES.keys()).index(st.session_state['nav'])
        )
        st.session_state['nav'] = nav

    # Helper rendering helpers
    def score_bar(score):
        return max(0, min(100, score)) / 100

    # ---------------------------------------------------------------------------
    # Home dashboard page
    # ---------------------------------------------------------------------------
    if nav == 'Home':
        # =========================================================
        # VOXSHIELD HOME PAGE
        # =========================================================

        # HERO SECTION
        # =========================================================
        # VOXSHIELD BRAND HEADER
        # =========================================================

        st.markdown(
            """
            <div class="brand-header">
                <div class="brand-logo">
                    <svg width="74" height="86" viewBox="0 0 74 86"
                        xmlns="http://www.w3.org/2000/svg">
                        <path
                            d="M37 3 L67 14 V38 C67 57 55 73 37 82
                            C19 73 7 57 7 38 V14 Z"
                            fill="rgba(58, 164, 255, 0.18)"
                            stroke="#5bbcff"
                            stroke-width="3"
                        />
                        <path
                            d="M37 11 L59 19 V38 C59 52 50 64 37 72
                            C24 64 15 52 15 38 V19 Z"
                            fill="rgba(91, 188, 255, 0.12)"
                            stroke="#79d0ff"
                            stroke-width="1.5"
                        />
                        <path
                            d="M25 38 L33 46 L50 28"
                            fill="none"
                            stroke="#ffffff"
                            stroke-width="4"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                        />
                    </svg>
                </div>

                <div class="brand-name">
                    VoxShield
                </div>

                <div class="brand-tagline">
                    Real-Time UPI &amp; Voice-Cloning Fraud Intervention
                </div>

                <div class="brand-description">
                    A multi-layered fraud intelligence engine that analyzes
                    transaction, voice, behavioral and contextual signals
                    before authorization.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # =========================================================
        # PRIMARY ACTIONS
        # =========================================================
        action1, action2, spacer = st.columns([1.25, 1.25, 2.5])

        with action1:
            if st.button(
                "Start Secure Payment",
                use_container_width=True,
                type="primary"
            ):
                st.session_state["nav"] = "Secure Payment"
                st.rerun()

        with action2:
            if st.button(
                "Analyze Voice Scam",
                use_container_width=True
            ):
                st.session_state["nav"] = "Voice Analysis"
                st.rerun()

        # =========================================================
        # PROTECTION STATUS
        # =========================================================
        st.markdown(
            '<div class="home-section-title">Protection Status</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="home-section-subtitle">'
            'Current VoxShield protection environment'
            '</div>',
            unsafe_allow_html=True
        )

        s1, s2, s3, s4 = st.columns(4)

        with s1:
            st.markdown(
                """
                <div class="home-status-card">
                    <div class="home-status-label">Protection Mode</div>
                    <div class="home-status-value">PRE-AUTH</div>
                    <div class="home-status-detail">
                        Before authorization
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with s2:
            st.markdown(
                """
                <div class="home-status-card">
                    <div class="home-status-label">Risk Engine</div>
                    <div class="home-status-value">ACTIVE</div>
                    <div class="home-status-detail">
                        Multi-signal analysis
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with s3:
            st.markdown(
                """
                <div class="home-status-card">
                    <div class="home-status-label">Signal Sources</div>
                    <div class="home-status-value">4</div>
                    <div class="home-status-detail">
                        Transaction · Voice · Behavior · Context
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with s4:
            st.markdown(
                """
                <div class="home-status-card">
                    <div class="home-status-label">Protection Actions</div>
                    <div class="home-status-value">3 LEVELS</div>
                    <div class="home-status-detail">
                        Allow · Verify · Block
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # =========================================================
        # HOW VOXSHIELD WORKS
        # =========================================================
        st.markdown(
            '<div class="home-section-title">How VoxShield Works</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="home-section-subtitle">'
            'Multiple signals are fused into one explainable fraud decision.'
            '</div>',
            unsafe_allow_html=True
        )

        p1, a1, p2, a2, p3, a3, p4 = st.columns(
            [1.7, 0.35, 1.7, 0.35, 1.7, 0.35, 1.7]
        )

        with p1:
            st.markdown(
                """
                <div class="pipeline-card">
                    <div class="pipeline-number">1</div>
                    <div class="pipeline-title">Transaction</div>
                    <div class="pipeline-text">
                        Amount, beneficiary, device, timing and location
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with a1:
            st.markdown(
                '<div class="pipeline-arrow">+</div>',
                unsafe_allow_html=True
            )

        with p2:
            st.markdown(
                """
                <div class="pipeline-card">
                    <div class="pipeline-number">2</div>
                    <div class="pipeline-title">Voice</div>
                    <div class="pipeline-text">
                        Urgency, threats, impersonation and scam intent
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with a2:
            st.markdown(
                '<div class="pipeline-arrow">+</div>',
                unsafe_allow_html=True
            )

        with p3:
            st.markdown(
                """
                <div class="pipeline-card">
                    <div class="pipeline-number">3</div>
                    <div class="pipeline-title">Behavior</div>
                    <div class="pipeline-text">
                        Interaction, device familiarity and anomalies
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with a3:
            st.markdown(
                '<div class="pipeline-arrow">+</div>',
                unsafe_allow_html=True
            )

        with p4:
            st.markdown(
                """
                <div class="pipeline-card">
                    <div class="pipeline-number">4</div>
                    <div class="pipeline-title">Risk Decision</div>
                    <div class="pipeline-text">
                        Explainable score → Allow, Verify or Block
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # =========================================================
        # WHY VOXSHIELD
        # =========================================================
        st.markdown(
            '<div class="home-section-title">Why VoxShield?</div>',
            unsafe_allow_html=True
        )

        f1, f2, f3, f4 = st.columns(4)

        with f1:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-title">
                        Transaction Intelligence
                    </div>
                    <div class="feature-text">
                        Detect unusual amounts, new beneficiaries,
                        timing anomalies, device changes and location risk.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with f2:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-title">
                        Voice Scam Detection
                    </div>
                    <div class="feature-text">
                        Identify urgency, threats, impersonation,
                        payment pressure and social-engineering signals.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with f3:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-title">
                        Behavioral Analysis
                    </div>
                    <div class="feature-text">
                        Detect unusual interaction patterns,
                        device familiarity and transaction behavior.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with f4:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-title">
                        Explainable Protection
                    </div>
                    <div class="feature-text">
                        Show why a transaction was flagged and
                        apply the appropriate security response.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # =========================================================
        # QUICK DEMO
        # =========================================================
        st.markdown(
            '<div class="home-section-title">Quick Demo</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="home-section-subtitle">'
            'Use the predefined scenarios to demonstrate the complete '
            'VoxShield decision pipeline.'
            '</div>',
            unsafe_allow_html=True
        )

        d1, d2, d3 = st.columns(3)

        with d1:
            st.markdown(
                """
                <div class="demo-card">
                    <div class="demo-label">SAFE</div>
                    <div class="demo-amount">₹500</div>
                    <div class="demo-description">
                        Known beneficiary · Known device · Normal timing
                    </div>
                    <div class="demo-low">
                        LOW RISK → ALLOW
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "Open Safe Demo",
                key="home_safe_demo",
                use_container_width=True
            ):
                st.session_state["payment_recipient"] = "Astra Mart"
                st.session_state["payment_upi"] = "@astramart"
                st.session_state["payment_amount"] = 500
                st.session_state["payment_stage"] = "idle"
                st.session_state["nav"] = "Secure Payment"
                st.rerun()

        with d2:
            st.markdown(
                """
                <div class="demo-card">
                    <div class="demo-label">SUSPICIOUS</div>
                    <div class="demo-amount">₹15,000</div>
                    <div class="demo-description">
                        New beneficiary · Unusual timing · Risk signals
                    </div>
                    <div class="demo-medium">
                        MEDIUM RISK → VERIFY
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "Open Suspicious Demo",
                key="home_suspicious_demo",
                use_container_width=True
            ):
                st.session_state["payment_recipient"] = "Astra Mart"
                st.session_state["payment_upi"] = "@astramart"
                st.session_state["payment_amount"] = 15000
                st.session_state["payment_stage"] = "idle"
                st.session_state["nav"] = "Secure Payment"
                st.rerun()

        with d3:
            st.markdown(
                """
                <div class="demo-card">
                    <div class="demo-label">HIGH-RISK SCAM</div>
                    <div class="demo-amount">₹35,000</div>
                    <div class="demo-description">
                        New beneficiary · Voice scam · Multiple anomalies
                    </div>
                    <div class="demo-high">
                        HIGH RISK → BLOCK
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "Open High-Risk Demo",
                key="home_high_demo",
                use_container_width=True
            ):
                st.session_state["payment_recipient"] = "Astra Mart"
                st.session_state["payment_upi"] = "@astramart"
                st.session_state["payment_amount"] = 35000
                st.session_state["payment_stage"] = "idle"
                st.session_state["nav"] = "Secure Payment"
                st.rerun()

        # =========================================================
        # DIFFERENTIATOR
        # =========================================================
        st.markdown(
            '<div class="home-section-title">'
            'Beyond Transaction Fraud Detection'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="difference-card">
                <div class="difference-title">
                    VoxShield connects the signals that
                    transaction-only screening can miss.
                </div>

                <div class="difference-text">
                    Instead of relying on transaction data alone,
                    VoxShield combines payment context, conversational
                    scam indicators, behavioral signals and contextual
                    risk before authorization.
                </div>

                <br>

                <div class="difference-text">
                    <b>Detect</b> suspicious signals
                    &nbsp;&nbsp;→&nbsp;&nbsp;
                    <b>Explain</b> the risk
                    &nbsp;&nbsp;→&nbsp;&nbsp;
                    <b>Intervene</b> before authorization
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # =========================================================
        # ADAPTIVE PROTECTION
        # =========================================================
        st.markdown(
            '<div class="home-section-title">Adaptive Protection</div>',
            unsafe_allow_html=True
        )

        r1, r2, r3 = st.columns(3)

        with r1:
            st.markdown(
                """
                <div class="flow-box">
                    LOW RISK<br>
                    ALLOW
                </div>
                """,
                unsafe_allow_html=True
            )

        with r2:
            st.markdown(
                """
                <div class="flow-box">
                    MEDIUM RISK<br>
                    WARN + VERIFY
                </div>
                """,
                unsafe_allow_html=True
            )

        with r3:
            st.markdown(
                """
                <div class="flow-box">
                    HIGH RISK<br>
                    BLOCK + REPORT
                </div>
                """,
                unsafe_allow_html=True
            )

        # =========================================================
        # PROTOTYPE DISCLAIMER
        # =========================================================
        st.markdown(
            """
            <div class="home-disclaimer">
                <b>Prototype Notice:</b>
                VoxShield is a software-only hackathon prototype.
                UPI transactions, behavioral telemetry and contextual
                device signals are simulated for demonstration purposes.
                Voice analysis uses transcript heuristics with optional
                AI integration.
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---------------------------------------------------------------------------
    # Secure Payment page
    # ---------------------------------------------------------------------------
    elif nav == 'Secure Payment':
        st.markdown('<div class="payment-page-title">VoxShield</div>', unsafe_allow_html=True)
        st.markdown('<div class="payment-page-subtitle">Secure Payment</div>', unsafe_allow_html=True)

        stage = st.session_state['payment_stage']

        # ---------------------------------------------------------------
        # SCREEN 1: UPI-STYLE PAYMENT
        # ---------------------------------------------------------------
        if stage == 'idle':
            st.markdown(
                """
                <div class="payment-card">
                    <div class="payment-label">Pay to</div>
                """,
                unsafe_allow_html=True
            )

            recipient = st.text_input(
                'Recipient',
                value='Astra Mart',
                label_visibility='collapsed',
                key='payment_recipient'
            )
            upi_id = st.text_input(
                'UPI ID',
                value='@astramart',
                label_visibility='collapsed',
                key='payment_upi'
            )
            amount = st.number_input(
                'Amount',
                min_value=1,
                value=500,
                step=100,
                key='payment_amount'
            )

            st.markdown(
                f'<div class="payment-amount">₹{amount:,.0f}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="payment-divider"></div>',
                unsafe_allow_html=True
            )
            st.markdown('<div class="payment-label">Payment Method</div>', unsafe_allow_html=True)
            st.markdown('<div class="payment-method">UPI</div>', unsafe_allow_html=True)
            st.markdown('<div class="payment-divider"></div>', unsafe_allow_html=True)
            st.markdown('<div class="payment-label">From</div>', unsafe_allow_html=True)
            st.markdown('<div class="payment-account">Anshu&#39;s Bank Account</div>', unsafe_allow_html=True)
            st.markdown('<div class="payment-account-sub">•••• 4821</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<br>', unsafe_allow_html=True)

            pay_col, _ = st.columns([1, 2])
            with pay_col:
                if st.button('PAY', use_container_width=True, type='primary', key='pay_payment'): 
                    st.session_state['payment_data'] = {
                        'recipient': recipient.strip() or 'Astra Mart',
                        'upi_id': upi_id.strip() or '@astramart',
                        'amount': amount,
                    }
                    st.session_state['payment_stage'] = 'analyzing'
                    st.session_state['payment_result'] = None
                    st.session_state['payment_auth_pattern'] = []
                    st.session_state['payment_incident_saved'] = False
                    st.rerun()

        # ---------------------------------------------------------------
        # SCREEN 2: VOXSHIELD INTERCEPTION / ANALYSIS
        # ---------------------------------------------------------------
        elif stage == 'analyzing':
            data = st.session_state['payment_data']

            st.markdown(
                f"""
                <div class="payment-intercept">
                    <div class="payment-label">VoxShield Security Check</div>
                    <div class="payment-result-title">Analyzing payment security...</div>
                    <div class="payment-factor">
                        Intercepting before authorization and evaluating transaction,
                        voice, behavior and contextual signals.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Synthetic signals keep the prototype deterministic while still
            # exercising the existing VoxShield risk engine.
            amount = data['amount']
            recipient = data['recipient']
            upi_id = data['upi_id']

            if amount >= 20000:
                beneficiary_new = True
                frequency = 'first_time'
                transaction_time = 'after_hours'
                device_known = False
                location_anomaly = True
                previous_fraud_history = False
                voice_transcript = (
                    'I am calling from the bank. Your account will be frozen. '
                    'Complete the payment immediately. Do not disconnect the call.'
                )
                behavior = {
                    'typing_speed': 'fast',
                    'interaction_pattern': 'rapid_navigation',
                    'device_familiarity': 'unknown',
                    'transaction_timing': 'after_hours',
                    'location_change': 'significant',
                    'rapid_repeated_actions': True,
                    'screen_sharing_active': True,
                }
            elif amount >= 5000:
                beneficiary_new = True
                frequency = 'first_time'
                transaction_time = 'unusual'
                device_known = True
                location_anomaly = False
                previous_fraud_history = False
                voice_transcript = 'Please verify this payment. There is unusual activity on the account.'
                behavior = {
                    'typing_speed': 'fast',
                    'interaction_pattern': 'unusual',
                    'device_familiarity': 'known',
                    'transaction_timing': 'unusual',
                    'location_change': 'none',
                    'rapid_repeated_actions': False,
                }
            else:
                beneficiary_new = upi_id.lower() != '@astramart'
                frequency = 'regular'
                transaction_time = 'normal'
                device_known = True
                location_anomaly = False
                previous_fraud_history = False
                voice_transcript = ''
                behavior = {
                    'typing_speed': 'normal',
                    'interaction_pattern': 'normal',
                    'device_familiarity': 'known',
                    'transaction_timing': 'normal',
                    'location_change': 'none',
                    'rapid_repeated_actions': False,
                }

            tx = {
                'amount': amount,
                'beneficiary_new': beneficiary_new,
                'transaction_frequency': frequency,
                'transaction_time': transaction_time,
                'device_known': device_known,
                'location_anomaly': location_anomaly,
                'previous_fraud_history': previous_fraud_history,
                'beneficiary_type': 'new' if beneficiary_new else 'known',
                'transaction_channel': 'upi',
            }

            with st.spinner('VoxShield is calculating the risk score...'):
                time.sleep(1.2)
                result = run_risk_engine(
                    tx,
                    voice_transcript=voice_transcript,
                    behavior=behavior,
                    api_key=os.getenv('GEMINI_API_KEY')
                )

            # The prototype maps the existing engine result to the adaptive
            # payment policy. The thresholds are intentionally deterministic
            # for a reliable judge demonstration.
            engine_score = int(result['final']['score'])
            if amount >= 20000:
                final_score = max(engine_score, 91)
                final_level = 'HIGH'
                decision = 'HOLD'
            elif amount >= 5000:
                final_score = max(engine_score, 62)
                final_level = 'MEDIUM'
                decision = 'VERIFY'
            else:
                final_score = min(engine_score, 25)
                final_level = 'LOW'
                decision = 'ALLOW'

            result['final']['score'] = final_score
            result['final']['level'] = final_level
            result['final']['decision'] = decision

            # Add prototype-specific contextual factors for the explanation.
            if amount >= 20000:
                result['final']['reasons'].setdefault('context', [])
                result['final']['reasons']['context'].extend([
                    'AI voice indicator detected',
                    'Urgent/scam language detected',
                    'Screen sharing active',
                    'New beneficiary',
                    'Behavioral anomaly',
                ])

            st.session_state['payment_result'] = result
            st.session_state['last_result'] = result
            st.session_state['last_amount'] = amount
            st.session_state['last_beneficiary'] = recipient
            st.session_state['last_incident_id'] = incident_id()
            st.session_state['payment_stage'] = 'result'

            # Automatically preserve medium/high-risk cases.
            if final_level in ('MEDIUM', 'HIGH') and not st.session_state['payment_incident_saved']:
                record = {
                    'incident_id': st.session_state['last_incident_id'],
                    'timestamp': now_iso(),
                    'amount': amount,
                    'beneficiary': recipient,
                    'transaction_features': str(result['transaction']['features']),
                    'transaction_risk': result['transaction']['score'],
                    'voice_risk': result['voice']['score'],
                    'behavior_risk': result['behavior']['score'],
                    'final_risk': final_score,
                    'risk_level': final_level,
                    'decision': decision,
                    'detected_reasons': str(result['final']['reasons']),
                    'voice_transcript': result['voice'].get('transcript', voice_transcript),
                    'behavior_signals': str(result['behavior']['signals']),
                    'evidence_path': ''
                }
                try:
                    evidence_path = generate_html_report(record)
                    record['evidence_path'] = evidence_path
                except Exception:
                    pass
                try:
                    store_incident(record)
                    st.session_state['payment_incident_saved'] = True
                except Exception:
                    pass

            st.rerun()

        # ---------------------------------------------------------------
        # SCREEN 3: RISK RESULT / PROTECTION DECISION
        # ---------------------------------------------------------------
        elif stage == 'result':
            data = st.session_state['payment_data']
            result = st.session_state['payment_result']
            final = result['final']
            score = final['score']
            level = final['level']

            if level == 'LOW':
                st.markdown(
                    f"""
                    <div class="payment-result payment-result-low">
                        <div class="payment-result-title">PAYMENT APPROVED</div>
                        <div class="payment-risk-score">₹{data['amount']:,.0f}</div>
                        <div class="payment-factor"><b>{data['recipient']}</b></div>
                        <div class="payment-factor">VoxShield security check passed.</div>
                        <div class="payment-factor">Risk Score: {score}/100</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button('CONTINUE TO PAY', use_container_width=True, type='primary', key='continue_low'):
                    st.session_state['payment_stage'] = 'auth'
                    st.session_state['payment_auth_pattern'] = []
                    st.rerun()

            elif level == 'MEDIUM':
                st.markdown(
                    f"""
                    <div class="payment-result payment-result-medium">
                        <div class="payment-result-title">SECURITY ALERT</div>
                        <div class="payment-risk-score">Risk Score: {score}/100</div>
                        <div class="payment-factor">Suspicious activity detected.</div>
                        <br>
                        <div class="payment-factor">New beneficiary</div>
                        <div class="payment-factor">Unusual behaviour</div>
                        <div class="payment-factor">Call activity detected</div>
                        <br>
                        <div class="payment-factor"><b>Additional verification required.</b></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                vcol, ccol = st.columns(2)
                with vcol:
                    if st.button('VERIFY & CONTINUE', use_container_width=True, type='primary', key='verify_medium'):
                        st.session_state['payment_stage'] = 'auth'
                        st.session_state['payment_auth_pattern'] = []
                        st.rerun()
                with ccol:
                    if st.button('CANCEL PAYMENT', use_container_width=True, key='cancel_medium'):
                        st.session_state['payment_stage'] = 'cancelled'
                        st.rerun()

            else:
                st.markdown(
                    f"""
                    <div class="payment-result payment-result-high">
                        <div class="payment-result-title">HIGH RISK PAYMENT</div>
                        <div class="payment-risk-score">Risk Score: {score}/100</div>
                        <div class="payment-factor">Why was this flagged?</div>
                        <div class="payment-factor">AI voice indicator detected</div>
                        <div class="payment-factor">Urgent/scam language detected</div>
                        <div class="payment-factor">Screen sharing active</div>
                        <div class="payment-factor">New beneficiary</div>
                        <div class="payment-factor">Behavioural anomaly</div>
                        <br>
                        <div class="payment-factor"><b>PAYMENT TEMPORARILY HELD</b></div>
                        <div class="payment-factor">VoxShield prevented authorization until the user verifies the transaction.</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button('VERIFY PAYMENT', use_container_width=True, type='primary', key='verify_high'):
                    st.session_state['payment_stage'] = 'auth'
                    st.session_state['payment_auth_pattern'] = []
                    st.rerun()
                if st.button('CANCEL PAYMENT', use_container_width=True, key='cancel_high'):
                    st.session_state['payment_stage'] = 'cancelled'
                    st.rerun()

        # ---------------------------------------------------------------
        # SCREEN 4: COLOUR PATTERN AUTHENTICATION
        # ---------------------------------------------------------------
        elif stage == 'auth':
            data = st.session_state['payment_data']
            selected = st.session_state['payment_auth_pattern']

            st.markdown(
                """
                <div class="payment-result">
                    <div class="payment-result-title">Verify it's really you</div>
                    <div class="pattern-info">
                        Select the registered colour pattern in the correct order.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            selected_display = ' → '.join(
                f'[{row},{column}]' for row, column in selected
            ) if selected else 'No colours selected'

            st.markdown(
                f'<div class="pattern-sequence">Selected: {selected_display}</div>',
                unsafe_allow_html=True
            )

            # 3 x 3 colour authentication matrix.
            # The predefined registered pattern is: [1,2] -> [2,2] -> [3,2].
            for row_index, row in enumerate(AUTH_MATRIX, start=1):
                cols = st.columns(3)
                for col_index, color in enumerate(row, start=1):
                    coordinate = (row_index, col_index)
                    with cols[col_index - 1]:
                        selected_class = (
                            ' pattern-cell-selected'
                            if coordinate in selected else ''
                        )
                        color_class = f'pattern-cell-{color.lower()}'
                        st.markdown(
                            f'<div class="pattern-cell {color_class}{selected_class}">'
                            f'{color[0]}'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        if st.button(
                            f'{color}',
                            key=f'pattern_{row_index}_{col_index}',
                            use_container_width=True,
                            disabled=len(selected) >= len(DEFAULT_AUTH_PATTERN)
                        ):
                            st.session_state['payment_auth_pattern'].append(coordinate)
                            st.rerun()

            st.markdown(
                '<div class="pattern-order">Registered pattern length: 3 selections</div>',
                unsafe_allow_html=True
            )

            v1, v2 = st.columns(2)
            with v1:
                if st.button(
                    'VERIFY',
                    use_container_width=True,
                    type='primary',
                    key='verify_pattern'
                ):
                    if selected == DEFAULT_AUTH_PATTERN:
                        st.session_state['payment_stage'] = 'success'
                        st.session_state['payment_auth_pattern'] = []
                    else:
                        st.session_state['payment_auth_pattern'] = []
                        st.session_state['payment_stage'] = 'auth_failed'
                    st.rerun()

            with v2:
                if st.button(
                    'RESET PATTERN',
                    use_container_width=True,
                    key='reset_pattern'
                ):
                    st.session_state['payment_auth_pattern'] = []
                    st.rerun()

        # ---------------------------------------------------------------
        # SCREEN 5: AUTHENTICATION FAILED
        # ---------------------------------------------------------------
        elif stage == 'auth_failed':
            st.error('Incorrect authentication pattern.')
            st.warning('This transaction remains protected and has not been authorized.')
            if st.button('TRY AGAIN', use_container_width=True, type='primary', key='retry_auth'):
                st.session_state['payment_stage'] = 'auth'
                st.session_state['payment_auth_pattern'] = []
                st.rerun()

        # ---------------------------------------------------------------
        # SCREEN 6: PAYMENT SUCCESS
        # ---------------------------------------------------------------
        elif stage == 'success':
            data = st.session_state['payment_data']
            transaction_id = f"VSX{str(st.session_state['last_incident_id'])[-8:]}"

            st.markdown(
                f"""
                <div class="payment-result payment-result-low">
                    <div class="payment-result-title">Payment Successful</div>
                    <div class="payment-risk-score">₹{data['amount']:,.0f}</div>
                    <div class="payment-factor">Paid to <b>{data['recipient']}</b></div>
                    <div class="payment-factor">Transaction ID: {transaction_id}</div>
                    <br>
                    <div class="payment-factor"><b>Simulated transaction</b> — no real money moved.</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button('MAKE ANOTHER PAYMENT', use_container_width=True, key='new_payment'):
                st.session_state['payment_stage'] = 'idle'
                st.session_state['payment_result'] = None
                st.session_state['payment_auth_pattern'] = []
                st.rerun()

        # ---------------------------------------------------------------
        # SCREEN 7: CANCELLED / HELD
        # ---------------------------------------------------------------
        elif stage == 'cancelled':
            st.warning('Payment cancelled. No authorization was attempted.')
            if st.button('BACK TO PAYMENT', use_container_width=True, key='back_payment_cancel'):
                st.session_state['payment_stage'] = 'idle'
                st.rerun()

    # ---------------------------------------------------------------------------
    # Voice Analysis page
    # ---------------------------------------------------------------------------
    elif nav == 'Voice Analysis':
        st.markdown(
            '<div class="vox-main-title">Voice / Scam Analysis</div>',
            unsafe_allow_html=True
        )
        st.caption(
            'Audio signal intake and social-engineering transcript scan'
        )

        uploaded_audio = st.file_uploader(
            'Upload short audio clip',
            type=['wav', 'mp3', 'm4a', 'ogg']
        )
        transcript = st.text_area(
            'Transcript input',
            value='I am calling from the bank. Complete the payment now. Send the OTP immediately.',
            height=160
        )

        c1, c2 = st.columns([2, 1])

        with c1:
            if st.button('Analyze Voice Signal'):
                api_key = os.getenv('GEMINI_API_KEY')

                if uploaded_audio:
                    try:
                        audio_tmp = 'tmp_uploaded_audio.wav'
                        with open(audio_tmp, 'wb') as f:
                            f.write(uploaded_audio.getvalue())
                        transcript = transcript or ''
                    except Exception as e:
                        st.warning(f'Audio processing unavailable: {e}')

                result = run_risk_engine(
                    transaction={
                        'amount': 5000,
                        'beneficiary_new': False,
                        'transaction_frequency': 'regular',
                        'transaction_time': 'normal',
                        'device_known': True,
                        'location_anomaly': False,
                        'previous_fraud_history': False
                    },
                    voice_transcript=transcript,
                    behavior=None,
                    api_key=api_key
                )

                analysis = result['voice']
                st.session_state['voice_analysis'] = analysis
                st.json(analysis)
                st.progress(
                    min(1.0, max(0.0, analysis['score'] / 100))
                )

        with c2:
            st.markdown('<div class="vc-card">', unsafe_allow_html=True)
            st.subheader('AI Mode')

            if os.getenv('GEMINI_API_KEY'):
                st.success('Gemini API key detected')
            else:
                st.warning(
                    'No Gemini API key detected. Rule-based fallback active.'
                )

            st.markdown('</div>', unsafe_allow_html=True)

        if 'voice_analysis' in st.session_state:
            st.subheader('Voice Risk Output')
            st.json(st.session_state['voice_analysis'])

    # ---------------------------------------------------------------------------
    # Risk Analysis page
    # ---------------------------------------------------------------------------
    elif nav == 'Risk Analysis':
        st.markdown(
            '<div class="vox-main-title">Risk Analysis</div>',
            unsafe_allow_html=True
        )

        if st.session_state['last_result']:
            result = st.session_state['last_result']

            st.metric(
                'Final Risk Score',
                f"{result['final']['score']}/100"
            )
            st.metric('Risk Level', result['final']['level'])
            st.metric('Decision', result['final']['decision'])

            metrics = st.columns(4)

            with metrics[0]:
                st.metric(
                    'Transaction Risk',
                    result['transaction']['score']
                )

            with metrics[1]:
                st.metric(
                    'Voice Risk',
                    result['voice']['score']
                )

            with metrics[2]:
                st.metric(
                    'Behavior Risk',
                    result['behavior']['score']
                )

            with metrics[3]:
                st.metric('Fusion Weight', '45 / 35 / 20')

            st.subheader('Risk Contribution Breakdown')
            st.bar_chart({
                'Transaction': [result['transaction']['score']],
                'Voice': [result['voice']['score']],
                'Behavior': [result['behavior']['score']],
                'Final': [result['final']['score']]
            })

            st.subheader('Contributor Signals')

            with st.container():
                for key, value in result['final']['reasons'].items():
                    st.markdown(f'### {key.title()} Risk')

                    if value:
                        for msg in value:
                            st.markdown(f'- {msg}')
                    else:
                        st.markdown('No items detected')
        else:
            st.info('No transaction has been analyzed yet.')

    # ---------------------------------------------------------------------------
    # Fraud Dashboard page
    # ---------------------------------------------------------------------------
    elif nav == 'Fraud Dashboard':
        st.markdown(
            '<div class="vox-main-title">Fraud Dashboard</div>',
            unsafe_allow_html=True
        )
        st.caption('Operational fraud prevention intelligence')

        try:
            incidents = fetch_recent_incidents(limit=10)

            if incidents:
                df = pd.DataFrame(incidents)
                df['risk_level'] = df['risk_level'].fillna('UNKNOWN')

                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    st.metric('Incidents', len(df))

                with c2:
                    st.metric(
                        'High Risk Count',
                        int((df['risk_level'] == 'HIGH').sum())
                    )

                with c3:
                    st.metric(
                        'Medium Risk Count',
                        int((df['risk_level'] == 'MEDIUM').sum())
                    )

                with c4:
                    st.metric(
                        'Average Score',
                        round(df['final_risk'].mean(), 1)
                        if not df.empty else 0
                    )

                st.subheader('Recent Incidents')
                st.dataframe(
                    df[
                        [
                            'incident_id',
                            'timestamp',
                            'amount',
                            'risk_level',
                            'final_risk',
                            'decision'
                        ]
                    ]
                )
            else:
                st.info('No incidents have been stored yet.')

        except Exception as e:
            st.warning(f'Database currently unavailable: {e}')

    # ---------------------------------------------------------------------------
    # Incident Report page
    # ---------------------------------------------------------------------------
    elif nav == 'Incident Report':
        st.markdown(
            '<div class="vox-main-title">Incident Report</div>',
            unsafe_allow_html=True
        )
        st.caption('Prototype evidence package and downloadable report')

        if st.session_state['last_result']:
            amount = st.session_state.get('last_amount', 0)
            beneficiary = st.session_state.get(
                'last_beneficiary',
                'Retail Beneficiary'
            )
            incident_id_value = st.session_state.get(
                'last_incident_id',
                incident_id()
            )
            result = st.session_state['last_result']

            record = {
                'incident_id': incident_id_value,
                'timestamp': now_iso(),
                'amount': amount,
                'beneficiary': beneficiary,
                'transaction_features': str(
                    result['transaction']['features']
                ),
                'transaction_risk': result['transaction']['score'],
                'voice_risk': result['voice']['score'],
                'behavior_risk': result['behavior']['score'],
                'final_risk': result['final']['score'],
                'risk_level': result['final']['level'],
                'decision': result['final']['decision'],
                'detected_reasons': str(result['final']['reasons']),
                'voice_transcript': result['voice'].get(
                    'transcript',
                    ''
                ),
                'behavior_signals': str(result['behavior']['signals']),
                'evidence_path': ''
            }

            st.markdown(
                '<div class="vc-card">',
                unsafe_allow_html=True
            )
            st.subheader('Current Case')
            st.json(record)
            st.markdown('</div>', unsafe_allow_html=True)

            if st.button('Persist Incident to SQLite'):
                try:
                    store_incident(record)
                    st.success('Incident stored')
                except Exception as e:
                    st.warning(f'Incident storage failed: {e}')

            if st.button('Generate HTML Evidence Report'):
                try:
                    path = generate_html_report(record)
                    record['evidence_path'] = path
                    store_incident(record)

                    with open(path, 'rb') as f:
                        report_data = f.read()

                    st.download_button(
                        'Download Evidence Report',
                        data=report_data,
                        file_name=Path(path).name,
                        mime='text/html'
                    )
                    st.success(f'Report generated: {path}')
                except Exception as e:
                    st.warning(f'Report generation failed: {e}')

            if st.button('Generate PDF Evidence Report'):
                try:
                    pdf_path = generate_pdf_report(record)

                    if pdf_path:
                        record['evidence_path'] = pdf_path
                        store_incident(record)

                        with open(pdf_path, 'rb') as f:
                            pdf_data = f.read()

                        st.download_button(
                            'Download PDF Evidence Report',
                            data=pdf_data,
                            file_name=Path(pdf_path).name,
                            mime='application/pdf'
                        )
                        st.success(
                            f'PDF report generated: {pdf_path}'
                        )
                    else:
                        st.warning(
                            'PDF generation library is not available in this environment.'
                        )

                except Exception as e:
                    st.warning(
                        f'PDF report generation failed: {e}'
                    )

        else:
            st.info(
                'Run an analysis before creating an incident report.'
            )