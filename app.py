import os
import tempfile
import ast
from pathlib import Path
from textwrap import dedent


import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from utils.helpers import incident_id, now_iso
from modules.database import ensure_database, store_incident, fetch_recent_incidents
from modules.risk_engine import run_risk_engine
from modules.report_generator import generate_html_report, generate_pdf_report
from modules.voice_analyzer import analyze_voice

load_dotenv()

st.set_page_config(page_title="VoxShield", page_icon="🛡️", layout="wide")

st.markdown(
    """
<style>
.stApp { background: radial-gradient(circle at 10% 10%, #173b45, #071b22 80%, #020d10); color:#eefcfb; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#10292e,#061b21); }
.block-container { padding-top: 2rem; }

.vox-main-title { font-size:2.2rem; font-weight:800; color:#fff; }

.vc-card {
    border-radius:16px;
    padding:1rem;
    background:linear-gradient(160deg,rgba(18,54,57,.94),rgba(9,30,36,.94));
    border:1px solid rgba(132,244,219,.38);
}

.brand-header { padding:1rem 0 2rem; }

.brand-name {
    font-size:3.2rem;
    font-weight:800;
    color:#fff;
}

.brand-tagline {
    color:#77ead2;
    font-size:.85rem;
    font-weight:700;
    letter-spacing:.12em;
    text-transform:uppercase;
}

.brand-description {
    max-width:850px;
    color:#b9d8d4;
    font-size:1rem;
    line-height:1.65;
    margin-top:.8rem;
}

.home-section-title {
    color:#fff;
    font-size:1.35rem;
    font-weight:800;
    margin:1.6rem 0 .7rem;
}

.home-status-card,
.pipeline-card,
.flow-box {
    border-radius:15px;
    padding:1rem;
    background:rgba(9,32,38,.96);
    border:1px solid rgba(119,234,210,.24);
    min-height:110px;
}

.home-status-label {
    color:#8fd7cd;
    font-size:.68rem;
    text-transform:uppercase;
    letter-spacing:.11em;
}

.home-status-value {
    color:#fff;
    font-size:1.35rem;
    font-weight:800;
    margin-top:.35rem;
}

.home-status-detail,
.pipeline-text {
    color:#a9cbc7;
    font-size:.75rem;
    margin-top:.2rem;
}

.pipeline-card {
    min-height:150px;
    text-align:center;
}

.pipeline-number {
    width:34px;
    height:34px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    margin:0 auto .5rem;
    color:#77ead2;
    border:1px solid rgba(119,234,210,.45);
}

.pipeline-title {
    color:#fff;
    font-weight:800;
}

.flow-box {
    min-height:auto;
    text-align:center;
    color:#fff;
    font-weight:700;
}

.payment-result {
    border-radius:16px;
    padding:1.5rem;
    margin:1rem 0;
    background:rgba(18,54,57,.94);
    border:1px solid rgba(132,244,219,.38);
}

.payment-result-title {
    font-size:1.6rem;
    font-weight:800;
    color:#fff;
}
/* =========================================================
   PAYMENT RISK ALERT WINDOW
   ========================================================= */

.risk-alert-box {
    border-radius: 18px;
    padding: 2rem 2.2rem;
    margin: 1.5rem 0;
    border: 2px solid;
    text-align: center;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
}

.risk-alert-low {
    background: rgba(39, 174, 96, 0.14);
    border-color: #27ae60;
}

.risk-alert-medium {
    background: rgba(242, 201, 76, 0.14);
    border-color: #f2c94c;
}

.risk-alert-high {
    background: rgba(235, 87, 87, 0.14);
    border-color: #eb5757;
}

.risk-alert-icon {
    font-size: 2.8rem;
    margin-bottom: 0.5rem;
}

.risk-alert-title {
    color: #ffffff;
    font-size: 1.65rem;
    font-weight: 900;
    margin-bottom: 0.5rem;
}

.risk-alert-score {
    color: #b9d8d4;
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 1.2rem;
}

.risk-alert-message {
    color: #eefcfb;
    font-size: 1.05rem;
    line-height: 1.7;
    margin: 0 auto;
    max-width: 850px;
}

.risk-alert-submessage {
    color: #b9d8d4;
    font-size: 0.95rem;
    line-height: 1.6;
    margin: 1rem auto 0;
    max-width: 850px;
}

/* Combined security indicators section */

.risk-alert-indicators {
    margin-top: 1.5rem;
    padding-top: 1.2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.18);
    text-align: left;
}

.risk-indicators-title {
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 800;
    margin-bottom: 0.8rem;
}

.risk-indicator-item {
    color: #eefcfb;
    font-size: 0.92rem;
    line-height: 1.5;
    padding: 0.35rem 0;
}

.risk-indicators-safe {
    color: #9ee6b8;
    font-size: 0.92rem;
    font-weight: 700;
    padding: 0.3rem 0;
}

.pattern-swatch {
    height:34px;
    border-radius:10px;
    margin-bottom:.3rem;
    border:1px solid rgba(255,255,255,.25);
}

.swatch-blue { background:#2f80ed; }
.swatch-yellow { background:#f2c94c; }
.swatch-red { background:#eb5757; }
.swatch-green { background:#27ae60; }
.swatch-purple { background:#9b51e0; }
.swatch-orange { background:#f2994a; }

.home-disclaimer {
    margin-top:2rem;
    padding:1rem;
    border-top:1px solid rgba(119,234,210,.15);
    color:#789a96;
    font-size:.75rem;
}


/* =========================================================
   LOGIN BUTTON
   ========================================================= */

div.stButton > button,
div.stFormSubmitButton > button {
    background:#77ead2 !important;
    color:#062027 !important;
    border:1px solid #77ead2 !important;
    font-weight:800 !important;
    opacity:1 !important;
    visibility:visible !important;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    background:#9af5e3 !important;
    color:#062027 !important;
    border-color:#9af5e3 !important;
}

</style>
""",
    unsafe_allow_html=True,
)

# Session defaults
st.session_state.setdefault("last_result", None)
st.session_state.setdefault("operator_access", False)
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("last_incident_id", incident_id())
st.session_state.setdefault("nav", "Home")
st.session_state.setdefault("payment_stage", "idle")
st.session_state.setdefault("payment_result", None)
st.session_state.setdefault("payment_auth_pattern", [])
st.session_state.setdefault("voice_transcript", "")
st.session_state.setdefault("voice_upload_signature", None)
st.session_state.setdefault("selected_incident_id", None)
st.session_state.setdefault("risk_analysis_source", None)

PAGES = [
    "Home",
    "Secure Payment",
    "Voice Analysis",
    "Risk Analysis",
    "Fraud Dashboard",
    "Incident Report",
]
ensure_database()

# Login
if not st.session_state["authenticated"]:
    st.title("VoxShield")
    st.caption("Fraud Intelligence Console")

    with st.form("voxshield_login"):
        operator_id = st.text_input("Operator ID", value="operator_demo")

        operator_pin = st.text_input("PIN", type="password", value="1234")

        submit = st.form_submit_button("LOGIN", use_container_width=True)

        if submit:
            if operator_pin == "1234":
                st.session_state["authenticated"] = True
                st.session_state["operator_access"] = True
                st.session_state["operator_id"] = operator_id
                st.rerun()
            else:
                st.error("Authentication failed")

    st.stop()

# Sidebar
with st.sidebar:
    st.markdown('<div style="font-size:48px;">🛡️</div>', unsafe_allow_html=True)
    st.title("VoxShield")
    st.caption("Real-Time UPI and Voice-Cloning Fraud Intervention")
    if st.button("Unlock Console"):
        st.session_state["operator_access"] = True
    nav = st.radio(
        "Navigation",
        PAGES,
        index=(
            PAGES.index(st.session_state["nav"])
            if st.session_state["nav"] in PAGES
            else 0
        ),
    )
    st.session_state["nav"] = nav


def save_last_result(result, amount=0, beneficiary="Astra Mart"):
    st.session_state["last_result"] = result
    st.session_state["last_amount"] = amount
    st.session_state["last_beneficiary"] = beneficiary
    st.session_state["last_incident_id"] = incident_id()


def run_payment_analysis(amount, beneficiary_new):
    if amount >= 20000:
        frequency, tx_time, device_known, location_anomaly = (
            "first_time",
            "unusual",
            False,
            True,
        )
        voice_context = (
            "I am calling from your bank. Your account is under urgent review. "
            "Complete this payment immediately. Share the OTP if asked."
        )
        behavior = {
            "typing_speed": "fast",
            "interaction_pattern": "rapid_navigation",
            "device_familiarity": "unknown",
            "transaction_timing": "unusual",
            "location_change": "significant",
            "rapid_repeated_actions": True,
            "screen_sharing": True,
        }
    elif amount >= 5000 or beneficiary_new:
        frequency, tx_time, device_known, location_anomaly = (
            "rare",
            "unusual",
            True,
            False,
        )
        voice_context = "Please confirm this unusual payment. The beneficiary is new and additional verification is required."
        behavior = {
            "typing_speed": "fast",
            "interaction_pattern": "unusual",
            "device_familiarity": "known",
            "transaction_timing": tx_time,
            "location_change": "none",
            "rapid_repeated_actions": False,
        }
    else:
        frequency, tx_time, device_known, location_anomaly = (
            "regular",
            "normal",
            True,
            False,
        )
        voice_context = ""
        behavior = {
            "typing_speed": "normal",
            "interaction_pattern": "normal",
            "device_familiarity": "known",
            "transaction_timing": "normal",
            "location_change": "none",
            "rapid_repeated_actions": False,
        }
    tx = {
        "amount": amount,
        "beneficiary_new": beneficiary_new,
        "transaction_frequency": frequency,
        "transaction_time": tx_time,
        "device_known": device_known,
        "location_anomaly": location_anomaly,
        "previous_fraud_history": False,
        "beneficiary_type": "new" if beneficiary_new else "known",
        "transaction_channel": "upi",
    }
    return run_risk_engine(
        tx,
        voice_transcript=voice_context,
        behavior=behavior,
        api_key=os.getenv("GEMINI_API_KEY"),
    )


def transcribe_audio_with_gemini(audio_path, mime_type=None):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    upload_config = None
    if mime_type:
        upload_config = types.UploadFileConfig(mime_type=mime_type)

    if upload_config is not None:
        uploaded_file = client.files.upload(file=audio_path, config=upload_config)
    else:
        uploaded_file = client.files.upload(file=audio_path)

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=[
            "Generate an accurate transcript of the speech in this audio. "
            "Return only the spoken words. Do not summarize, explain, translate, "
            "or add timestamps. Preserve the wording as closely as possible.",
            uploaded_file,
        ],
    )

    transcript_text = (response.text or "").strip()
    if not transcript_text:
        raise RuntimeError("Gemini returned an empty transcript.")

    return transcript_text


def parse_stored_value(value, default=None):
    """
    Convert values stored in SQLite as strings back into Python objects.
    """
    if value is None:
        return default

    if isinstance(value, (dict, list)):
        return value

    if not isinstance(value, str):
        return value

    value = value.strip()

    if not value:
        return default

    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def get_incident_by_id(incident_id_value):
    """
    Find one incident from the stored SQLite incidents.
    """
    incidents = fetch_recent_incidents(limit=500)

    for incident in incidents:
        if str(incident.get("incident_id")) == str(incident_id_value):
            return incident

    return None


def split_timestamp(timestamp):
    """
    Split ISO timestamp into separate date and time values.
    """
    if not timestamp:
        return "-", "-"

    timestamp = str(timestamp)

    if "T" in timestamp:
        date_part, time_part = timestamp.split("T", 1)
        time_part = time_part.replace("Z", "")

        return date_part, time_part

    return timestamp, "-"


# HOME
if nav == "Home":
    st.markdown(
        """<div class="brand-header"><div class="brand-name">VoxShield</div>
    <div class="brand-tagline">Real-Time UPI &amp; Voice-Cloning Fraud Intervention</div>
    <div class="brand-description">A multi-layered fraud intelligence engine that analyzes transaction, voice, behavioral and contextual signals before authorization.</div></div>""",
        unsafe_allow_html=True,
    )
    a1, a2, _ = st.columns([1.25, 1.25, 2.5])
    with a1:
        if st.button("Start Secure Payment", use_container_width=True, type="primary"):
            st.session_state["nav"] = "Secure Payment"
            st.session_state["payment_stage"] = "idle"
            st.rerun()
    with a2:
        if st.button("Analyze Voice Scam", use_container_width=True):
            st.session_state["nav"] = "Voice Analysis"
            st.rerun()
    st.markdown(
        '<div class="home-section-title">Protection Status</div>',
        unsafe_allow_html=True,
    )
    cards = [
        ("Protection Mode", "PRE-AUTH", "Before authorization"),
        ("Risk Engine", "ACTIVE", "Multi-signal analysis"),
        ("Signal Sources", "4", "Transaction · Voice · Behavior · Context"),
        ("Protection Actions", "3 LEVELS", "Allow · Verify · Block"),
    ]
    for col, card in zip(st.columns(4), cards):
        with col:
            st.markdown(
                f'<div class="home-status-card"><div class="home-status-label">{card[0]}</div><div class="home-status-value">{card[1]}</div><div class="home-status-detail">{card[2]}</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown(
        '<div class="home-section-title">How VoxShield Works</div>',
        unsafe_allow_html=True,
    )
    pipeline = [
        ("1", "Transaction", "Amount, beneficiary, device, timing and location"),
        ("2", "Voice", "Urgency, threats, impersonation and scam intent"),
        ("3", "Behavior", "Interaction, device familiarity and anomalies"),
        ("4", "Risk Decision", "Explainable score → Allow, Verify or Block"),
    ]
    for col, item in zip(st.columns(4), pipeline):
        with col:
            st.markdown(
                f'<div class="pipeline-card"><div class="pipeline-number">{item[0]}</div><div class="pipeline-title">{item[1]}</div><div class="pipeline-text">{item[2]}</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown(
        '<div class="home-section-title">Adaptive Protection</div>',
        unsafe_allow_html=True,
    )
    for col, title, action in zip(
        st.columns(3),
        ("LOW RISK", "MEDIUM RISK", "HIGH RISK"),
        ("ALLOW", "WARN + VERIFY", "HOLD + REPORT"),
    ):
        with col:
            st.markdown(
                f'<div class="flow-box">{title}<br>{action}</div>',
                unsafe_allow_html=True,
            )

# SECURE PAYMENT
elif nav == "Secure Payment":
    stage = st.session_state["payment_stage"]
    if stage == "idle":
        st.markdown(
            '<div class="vox-main-title">VoxShield</div>', unsafe_allow_html=True
        )
        st.caption("Secure Payment")
        left, right = st.columns([1.15, 0.85])
        with left:
            st.markdown('<div class="vc-card">', unsafe_allow_html=True)
            st.subheader("Pay to")
            recipient = st.text_input("Recipient", value="Astra Mart")
            upi_id = st.text_input("UPI ID", value="@astramart")
            amount = st.number_input("Amount", min_value=1, value=500, step=100)
            st.markdown("</div>", unsafe_allow_html=True)
        with right:
            st.markdown('<div class="vc-card">', unsafe_allow_html=True)
            st.subheader("Payment Method")
            st.radio("Method", ["UPI"], label_visibility="collapsed")
            st.markdown("---")
            st.subheader("From")
            st.write("Anshu's Bank Account")
            st.write("•••• 4821")
            beneficiary_new = st.checkbox("New beneficiary")
            st.caption("Simulation only — no real money or UPI API is used.")
            st.markdown("</div>", unsafe_allow_html=True)
        if st.button("PAY", use_container_width=True, type="primary", key="pay_button"):
            st.session_state["payment_data"] = {
                "recipient": recipient,
                "upi_id": upi_id,
                "amount": amount,
                "beneficiary_new": beneficiary_new,
            }
            st.session_state["payment_stage"] = "analyzing"
            st.rerun()
    elif stage == "analyzing":
        data = st.session_state["payment_data"]
        st.info("Analyzing payment security...")
        with st.spinner(
            "Collecting transaction, voice, behavior and context signals..."
        ):
            result = run_payment_analysis(data["amount"], data["beneficiary_new"])
        st.session_state["payment_result"] = result
        save_last_result(result, data["amount"], data["recipient"])
        st.session_state["payment_stage"] = "result"
        st.rerun()
    elif stage == "result":
        data = st.session_state["payment_data"]
        final = st.session_state["payment_result"]["final"]
        level = final["level"]
        score = final["score"]
        if level == "LOW":
            st.success("PAYMENT APPROVED")
            st.metric("Risk Score", f"{score}/100")
            st.markdown(f'### ₹{data["amount"]:,.0f} — {data["recipient"]}')
            st.write("VoxShield security check passed.")
            if st.button(
                "CONTINUE TO PAY",
                use_container_width=True,
                type="primary",
                key="continue_low_payment",
            ):
                st.session_state["payment_stage"] = "risk_alert"
                st.rerun()
        elif level == "MEDIUM":
            st.warning("SECURITY ALERT")
            st.metric("Risk Score", f"{score}/100")
            st.write("Suspicious activity detected. Additional verification required.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button(
                    "CONTINUE TO PAY",
                    use_container_width=True,
                    type="primary",
                    key="continue_medium_payment",
                    
                ):
                    st.session_state["payment_stage"] = "risk_alert"
                    st.session_state["payment_auth_pattern"] = []
                    st.rerun()
            with c2:
                if st.button("CANCEL PAYMENT", use_container_width=True):
                    st.session_state["payment_stage"] = "cancelled"
                    st.rerun()
        else:
            st.error("HIGH RISK PAYMENT")
            st.metric("Risk Score", f"{score}/100")
            st.markdown(f'### ₹{data["amount"]:,.0f} → {data["recipient"]}')
            st.write(
                "VoxShield has temporarily held this payment before authorization."
            )
            st.markdown("**Why was this flagged?**")
            reasons = final.get("reasons", [])
            if isinstance(reasons, dict):
                reasons = [
                    x
                    for vals in reasons.values()
                    for x in (vals if isinstance(vals, list) else [vals])
                ]
            if not reasons:
                reasons = [
                    "High-value transaction",
                    "Potential social-engineering indicators",
                    "Behavioral anomaly",
                ]
            for r in reasons:
                st.markdown(f"- {r}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button(
                    "CONTINUE TO PAY",
                    use_container_width=True,
                    type="primary",
                    key="continue_high_payment",
                ):
                    st.session_state["payment_stage"] = "risk_alert"
                    st.session_state["payment_auth_pattern"] = []
                    st.rerun()
            with c2:
                if st.button("CANCEL PAYMENT", use_container_width=True):
                    st.session_state["payment_stage"] = "cancelled"
                    st.rerun()
    # ---------------------------------------------------------------
    # SCREEN 4: RISK ALERT BEFORE AUTHENTICATION
    # ---------------------------------------------------------------
    elif stage == "risk_alert":

        data = st.session_state["payment_data"]
        final = st.session_state["payment_result"]["final"]

        level = final["level"]
        score = final["score"]

        # ---------------------------------------------------------------
        # PREPARE RISK REASONS
        # ---------------------------------------------------------------

        reasons = final.get("reasons", [])

        if isinstance(reasons, dict):
            reasons = [
                item
                for values in reasons.values()
                for item in (
                    values if isinstance(values, list) else [values]
                )
            ]

        reasons = [str(reason) for reason in reasons if reason]

        # ---------------------------------------------------------------
        # RISK LEVEL CONTENT
        # ---------------------------------------------------------------

        if level == "LOW":

            alert_class = "risk-alert-low"
            alert_icon = "🟢"
            alert_title = "PAYMENT SECURITY CHECK PASSED"

            alert_message = (
                "VoxShield has completed its security assessment of this "
                "payment. No significant indicators of fraudulent or "
                "suspicious activity were detected across the available "
                "security signals."
            )

            alert_submessage = (
                "The payment appears consistent with normal activity. "
                "You may continue to the identity verification step before "
                "the payment is authorized."
            )

            indicator_title = "Security Status"
            indicator_icon = "✓"

        elif level == "MEDIUM":

            alert_class = "risk-alert-medium"
            alert_icon = "🟡"
            alert_title = "PAYMENT REQUIRES ADDITIONAL VERIFICATION"

            alert_message = (
                "VoxShield has detected unusual characteristics associated "
                "with this payment. The transaction is not classified as "
                "high risk, but additional verification is required before "
                "authorization."
            )

            alert_submessage = (
                "Please carefully review the recipient, amount and payment "
                "details. Continue only if you personally initiated this "
                "transaction and everything appears correct."
            )

            indicator_title = "Security Signals Detected"
            indicator_icon = "🔎"

        else:

            alert_class = "risk-alert-high"
            alert_icon = "🔴"
            alert_title = "HIGH-RISK PAYMENT DETECTED"

            alert_message = (
                "VoxShield has identified multiple indicators associated "
                "with potentially fraudulent activity. This transaction "
                "presents a significant security risk and should be treated "
                "with extreme caution."
            )

            alert_submessage = (
                "The payment is under protection until your identity is "
                "verified. Do not proceed if you did not personally initiate "
                "this transaction or if someone is pressuring you to complete it."
            )

            indicator_title = "Why VoxShield Flagged This Payment"
            indicator_icon = "⚠️"

        # ---------------------------------------------------------------
        # BUILD ONE COMBINED ALERT BOX
        # ---------------------------------------------------------------

        if reasons:

            displayed_reasons = reasons[:5]

            indicators_html = "".join(
                f'<div class="risk-indicator-item">{indicator_icon} {reason}</div>'
                for reason in displayed_reasons
            )

        else:

            if level == "LOW":
                indicators_html = """
                <div class="risk-indicators-safe">
                    ✓ No significant security indicators detected.
                </div>
                """
            elif level == "MEDIUM":
                indicators_html = """
                <div class="risk-indicators-safe">
                    🔎 Minor security anomalies require additional verification.
                </div>
                """
            else:
                indicators_html = """
                <div class="risk-indicators-safe">
                    ⚠️ Multiple security indicators require immediate attention.
                </div>
                """

        

        # ---------------------------------------------------------------
        # DISPLAY RISK ALERT
        # ---------------------------------------------------------------

        if level == "LOW":

            alert_text = (
                f"🟢 **PAYMENT SECURITY CHECK PASSED**\n\n"
                f"**Risk Score: {score}/100 • LOW**\n\n"
                f"VoxShield has completed its security assessment of this "
                f"payment. No significant indicators of fraudulent or "
                f"suspicious activity were detected.\n\n"
                f"Your payment appears consistent with normal activity. "
                f"You may continue to the identity verification step "
                f"before the payment is authorized."
            )

            st.success(alert_text)

            if reasons:
                st.write("**Security Status**")
                for reason in reasons[:3]:
                    st.write(f"✓ {reason}")
            else:
                st.write("✓ No significant security indicators detected.")

        elif level == "MEDIUM":

            alert_text = (
                f"🟡 **PAYMENT REQUIRES ADDITIONAL VERIFICATION**\n\n"
                f"**Risk Score: {score}/100 • MEDIUM**\n\n"
                f"VoxShield has detected unusual characteristics "
                f"associated with this payment. The transaction is not "
                f"classified as high risk, but additional verification "
                f"is required before authorization.\n\n"
                f"Please carefully review the recipient, amount and "
                f"payment details. Continue only if you personally "
                f"initiated this transaction."
            )

            st.warning(alert_text)

            if reasons:
                st.write("**Security Signals Detected**")
                for reason in reasons[:5]:
                    st.write(f"🔎 {reason}")
            else:
                st.write("🔎 Minor security anomalies require verification.")

        else:

            alert_text = (
                f"🔴 **HIGH-RISK PAYMENT DETECTED**\n\n"
                f"**Risk Score: {score}/100 • HIGH**\n\n"
                f"VoxShield has identified multiple indicators associated "
                f"with potentially fraudulent activity. This transaction "
                f"presents a significant security risk and should be "
                f"treated with extreme caution.\n\n"
                f"The payment is under protection until your identity is "
                f"verified. Do not proceed if you did not personally "
                f"initiate this transaction or if someone is pressuring "
                f"you to complete it."
            )

            st.error(alert_text)

            if reasons:
                st.write("**Why VoxShield Flagged This Payment**")
                for reason in reasons[:5]:
                    st.write(f"⚠️ {reason}")
            else:
                st.write(
                    "⚠️ Multiple security indicators require immediate attention."
                )

        # ---------------------------------------------------------------
        # PAYMENT DETAILS
        # ---------------------------------------------------------------

        st.divider()

        st.markdown(
            f"""
            <div class="vc-card">
                <strong>Payment Details</strong><br><br>
                Recipient: {data["recipient"]}<br>
                Amount: ₹{data["amount"]:,.2f}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "CONTINUE TO AUTHENTICATION",
                use_container_width=True,
                type="primary",
                key="continue_risk_alert",
            ):
                st.session_state["payment_stage"] = "auth"
                st.session_state["payment_auth_pattern"] = []
                st.rerun()

        with c2:

            if st.button(
                "CANCEL PAYMENT",
                use_container_width=True,
                key="cancel_risk_alert",
            ):
                st.session_state["payment_stage"] = "cancelled"
                st.session_state["payment_auth_pattern"] = []
                st.rerun()


    # ---------------------------------------------------------------
    # SCREEN 5: COLOUR PATTERN AUTHENTICATION
    # ---------------------------------------------------------------
    elif stage == "auth":
    

        data = st.session_state["payment_data"]

        selected = st.session_state["payment_auth_pattern"]

        st.markdown(
            """
            <div class="payment-result">
                <div class="payment-result-title">
                    Verify it's really you
                </div>

                
            </div>
            """,
            unsafe_allow_html=True,
        )
        matrix = [
            ["BLUE", "YELLOW", "RED"],
            ["GREEN", "PURPLE", "ORANGE"],
            ["ORANGE", "BLUE", "GREEN"],
        ]

        correct = [(1, 2), (2, 2), (3, 2)]

        selected_colors = []

        for row, col in selected:
            selected_colors.append(matrix[row - 1][col - 1])

        sequence_text = (
            " → ".join(selected_colors) if selected_colors else "No colours selected"
        )

        st.markdown(
            f'<div class="pattern-sequence">' f"Selected: {sequence_text}" f"</div>",
            unsafe_allow_html=True,
        )

        # -----------------------------------------------------------
        # COLOUR MATRIX
        # -----------------------------------------------------------

        cols = st.columns(3)

        for row in range(3):

            for col in range(3):

                cell = (row + 1, col + 1)

                color = matrix[row][col]

                with cols[col]:

                    swatch_class = f"swatch-{color.lower()}"

                    st.markdown(
                        f"""
                        <div class="pattern-swatch {swatch_class}">
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        color,
                        key=f"pattern_{row}_{col}",
                        use_container_width=True,
                        disabled=len(selected) >= 3 or cell in selected,
                    ):

                        st.session_state["payment_auth_pattern"].append(cell)

                        st.rerun()

        st.caption(
            "Prototype authentication: " "registered pattern is YELLOW → PURPLE → BLUE."
        )

        if selected_colors:

            st.info("Selected pattern: " + " → ".join(selected_colors))

        # -----------------------------------------------------------
        # VERIFY / RESET
        # -----------------------------------------------------------

        v1, v2 = st.columns(2)

        with v1:

            if st.button(
                "VERIFY", use_container_width=True, type="primary", key="verify_pattern"
            ):

                if selected == correct:

                    st.session_state["payment_stage"] = "success"

                    st.session_state["payment_auth_pattern"] = []

                else:

                    st.session_state["payment_stage"] = "auth_failed"

                    st.session_state["payment_auth_pattern"] = []

                st.rerun()

        with v2:

            if st.button(
                "RESET PATTERN", use_container_width=True, key="reset_pattern"
            ):

                st.session_state["payment_auth_pattern"] = []

                st.rerun()

            # ---------------------------------------------------------------
    # SCREEN 5: AUTHENTICATION FAILED
    # ---------------------------------------------------------------
    elif stage == "auth_failed":

        st.error("Incorrect authentication pattern.")

        st.warning("This transaction remains protected and has not been authorized.")

        if st.button(
            "TRY AGAIN", use_container_width=True, type="primary", key="retry_auth"
        ):
            st.session_state["payment_stage"] = "auth"
            st.session_state["payment_auth_pattern"] = []
            st.rerun()

    # ---------------------------------------------------------------
    # SCREEN 6: PAYMENT SUCCESS
    # ---------------------------------------------------------------
    elif stage == "success":

        data = st.session_state["payment_data"]

        transaction_id = (
            f"VSX{str(st.session_state.get('last_incident_id', incident_id()))[-8:]}"
        )

        st.divider()

        # Payment details
        c1, c2 = st.columns(2)

        with c1:
            st.metric("Amount Paid", f"₹{data['amount']:,.2f}")

        with c2:
            st.metric("Payment Status", "SUCCESSFUL")

        st.markdown("### Transaction Details")

        d1, d2 = st.columns(2)

        with d1:
            st.write("**Paid To :**")
            st.write(data["recipient"])

            st.write("**Transaction ID :**")
            st.code(transaction_id)

        with d2:
            st.write("**Payment Method :**")
            st.write("UPI")

            st.write("**Security Verification**")
            st.write("Colour pattern verified")

        st.success(
            "VoxShield security verification completed. "
            "The transaction was authorized successfully."
        )

        st.caption("Prototype transaction — no real money was transferred.")

        st.divider()

        if st.button(
            "MAKE ANOTHER PAYMENT",
            use_container_width=True,
            type="primary",
            key="new_payment",
        ):
            st.session_state["payment_stage"] = "idle"
            st.session_state["payment_result"] = None
            st.session_state["payment_auth_pattern"] = []
            st.rerun()

    # ---------------------------------------------------------------
    # SCREEN 7: PAYMENT CANCELLED
    # ---------------------------------------------------------------
    elif stage == "cancelled":

        st.warning("Payment cancelled. No authorization was attempted.")

        if st.button(
            "BACK TO PAYMENT",
            use_container_width=True,
            type="primary",
            key="back_payment_cancel",
        ):
            st.session_state["payment_stage"] = "idle"
            st.session_state["payment_result"] = None
            st.session_state["payment_auth_pattern"] = []
            st.rerun()

# VOICE ANALYSIS
elif nav == "Voice Analysis":
    st.markdown(
        '<div class="vox-main-title">Voice / Scam Analysis</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Upload a call recording and VoxShield will automatically transcribe it before scam-risk analysis."
    )

    uploaded_audio = st.file_uploader(
        "Upload short audio clip",
        type=[
            "wav",
            "mp3",
            "mpeg",
            "mpga",
            "m4a",
            "aac",
            "ogg",
            "flac",
            "aiff",
            "opus",
            "webm",
        ],
        key="voice_audio_upload",
    )

    if uploaded_audio is not None:
        upload_signature = (
            uploaded_audio.name,
            uploaded_audio.size,
            uploaded_audio.type,
        )

        if upload_signature != st.session_state.get("voice_upload_signature"):
            st.session_state["voice_upload_signature"] = upload_signature

            api_key = os.getenv("GEMINI_API_KEY")

            if not api_key:
                st.warning(
                    "Gemini API key is not configured. "
                    "You can still type or paste a transcript manually below."
                )
            else:
                temp_path = None
                try:
                    suffix = Path(uploaded_audio.name).suffix.lower() or ".audio"

                    mime_map = {
                        ".wav": "audio/wav",
                        ".mp3": "audio/mpeg",
                        ".mpeg": "audio/mpeg",
                        ".mpga": "audio/mpeg",
                        ".m4a": "audio/mp4",
                        ".aac": "audio/aac",
                        ".ogg": "audio/ogg",
                        ".flac": "audio/flac",
                        ".aiff": "audio/aiff",
                        ".opus": "audio/opus",
                        ".webm": "audio/webm",
                    }

                    mime_type = (
                        uploaded_audio.type
                        if uploaded_audio.type
                        and uploaded_audio.type.startswith("audio/")
                        else mime_map.get(suffix, "audio/mpeg")
                    )

                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=suffix
                    ) as tmp:
                        tmp.write(uploaded_audio.getbuffer())
                        temp_path = tmp.name

                    with st.spinner("Transcribing audio with Gemini..."):
                        generated_transcript = transcribe_audio_with_gemini(
                            temp_path, mime_type=mime_type
                        )

                    st.session_state["voice_transcript_input"] = generated_transcript
                    st.success("Audio transcribed successfully.")

                except Exception as exc:
                    st.error(
                        "Audio transcription failed. "
                        f"You can still enter the transcript manually. Details: {exc}"
                    )

                finally:
                    if temp_path:
                        try:
                            os.remove(temp_path)
                        except OSError:
                            pass

    transcript = st.text_area(
        "Transcript input",
        value=st.session_state.get("voice_transcript_input", ""),
        height=180,
        key="voice_transcript_input",
        placeholder=(
            "The generated transcript will appear here automatically. "
            "You can also type or paste a transcript manually."
        ),
    )

    st.caption(
        "Manual mode is always available: type or paste text here if automatic transcription is unavailable."
    )

    c1, c2 = st.columns([2, 1])

    with c1:
        if st.button(
            "Analyze Voice Signal",
            use_container_width=True,
            type="primary",
            key="analyze_voice_signal",
        ):
            transcript_for_analysis = transcript.strip()

            if not transcript_for_analysis:
                st.warning(
                    "Please upload an audio recording with Gemini configured, "
                    "or type/paste a transcript in the Transcript input box."
                )
            else:
                try:
                    voice_result = analyze_voice(transcript_for_analysis)

                    # NEW CODE STARTS HERE
                    st.session_state["voice_analysis"] = voice_result
                    st.session_state["voice_transcript"] = transcript_for_analysis

                    voice_score = int(voice_result.get("score", 0))
                    voice_level = voice_result.get("level", "LOW")
                    voice_reasons = voice_result.get("reasons", [])

                    # ---------------------------------------------------------
                    # STORE VOICE ANALYSIS AS AN INCIDENT
                    # ---------------------------------------------------------

                    voice_incident_id = incident_id()

                    voice_record = {
                        "incident_id": voice_incident_id,
                        "timestamp": now_iso(),
                        # Voice-only analysis
                        "amount": 0,
                        "beneficiary": "Voice Analysis",
                        "transaction_features": "{}",
                        "transaction_risk": 0,
                        "voice_risk": voice_score,
                        "behavior_risk": 0,
                        "final_risk": voice_score,
                        "risk_level": voice_level,
                        "decision": (
                            "ALLOW"
                            if voice_level == "LOW"
                            else (
                                "WARN + VERIFY"
                                if voice_level == "MEDIUM"
                                else "BLOCK + REPORT"
                            )
                        ),
                        "detected_reasons": str({"voice": voice_reasons}),
                        "voice_transcript": voice_result.get(
                            "transcript", transcript_for_analysis
                        ),
                        "behavior_signals": "{}",
                        "evidence_path": "",
                    }

                    try:
                        store_incident(voice_record)

                        st.session_state["last_incident_id"] = voice_incident_id

                        st.success(
                            f"Voice analysis completed and stored as incident "
                            f"{voice_incident_id}."
                        )

                    except Exception as exc:
                        st.warning(
                            f"Voice analysis completed, but incident could not be stored: {exc}"
                        )

                    # ---------------------------------------------------------
                    # SAVE RESULT FOR RISK ANALYSIS SCREEN
                    # ---------------------------------------------------------

                    st.session_state["last_result"] = {
                        "transaction": {"score": 0, "reasons": []},
                        "voice": {
                            "score": voice_score,
                            "reasons": voice_reasons,
                            "transcript": voice_result.get(
                                "transcript", transcript_for_analysis
                            ),
                            "features": voice_result.get("features", {}),
                        },
                        "behavior": {"score": 0, "reasons": []},
                        "context": {"score": 0, "reasons": []},
                        "final": {
                            "score": voice_score,
                            "level": voice_level,
                            "decision": (
                                "ALLOW"
                                if voice_level == "LOW"
                                else (
                                    "WARN + VERIFY"
                                    if voice_level == "MEDIUM"
                                    else "BLOCK + REPORT"
                                )
                            ),
                            "reasons": {"voice": voice_reasons},
                        },
                    }

                    st.session_state["risk_analysis_source"] = "voice"

                except Exception as exc:
                    st.error(f"Voice analysis failed: {exc}")

                    st.session_state["last_result"] = {
                        "transaction": {"score": 0, "reasons": []},
                        "voice": {
                            "score": voice_score,
                            "reasons": voice_reasons,
                            "transcript": voice_result.get(
                                "transcript", transcript_for_analysis
                            ),
                            "features": voice_result.get("features", {}),
                        },
                        "behavior": {"score": 0, "reasons": []},
                        "context": {"score": 0, "reasons": []},
                        "final": {
                            "score": voice_score,
                            "level": voice_level,
                            "decision": (
                                "ALLOW"
                                if voice_level == "LOW"
                                else (
                                    "WARN + VERIFY"
                                    if voice_level == "MEDIUM"
                                    else "BLOCK + REPORT"
                                )
                            ),
                            "reasons": {"voice": voice_reasons},
                        },
                    }

                    st.session_state["risk_analysis_source"] = "voice"

                    st.success("Voice analysis completed.")

                except Exception as exc:
                    st.error(f"Voice analysis failed: {exc}")

    with c2:
        st.markdown('<div class="vc-card">', unsafe_allow_html=True)
        st.subheader("AI Mode")

        if os.getenv("GEMINI_API_KEY"):
            st.success("Gemini connected — automatic audio transcription enabled.")
        else:
            st.warning(
                "No Gemini API key detected. "
                "Manual transcript / rule-based analysis is available."
            )

        st.markdown("</div>", unsafe_allow_html=True)

    if "voice_analysis" in st.session_state:
        analysis = st.session_state["voice_analysis"]

        st.subheader("Voice Risk Output")

        score = analysis.get("score", 0)
        level = analysis.get("level", "LOW")

        c1, c2 = st.columns(2)

        with c1:
            st.metric("Voice Risk Score", f"{score}/100")

        with c2:
            st.metric("Voice Risk Level", level)

        st.subheader("Detected Signals")

        features = analysis.get("features", {})

        for feature_name, values in features.items():

            if feature_name == "transcript_length":
                continue

            if values:
                st.markdown(f'**{feature_name.replace("_", " ").title()}**')

                for value in values:
                    st.markdown(f"- `{value}`")

        st.subheader("Risk Reasons")

        reasons = analysis.get("reasons", [])

        if reasons:
            for reason in reasons:
                st.markdown(f"- {reason}")
        else:
            st.success("No scam indicators detected.")

        st.subheader("Transcript Used for Analysis")

        st.text_area(
            "Generated transcript",
            value=analysis.get("transcript", ""),
            height=180,
            disabled=True,
            key="voice_analysis_transcript_display",
        )
        st.divider()

        if st.button(
            "VIEW DETAILED RISK ANALYSIS",
            use_container_width=True,
            type="primary",
            key="view_voice_risk_analysis",
        ):
            st.session_state["risk_analysis_source"] = "voice"
            st.session_state["nav"] = "Risk Analysis"
            st.rerun()

# RISK ANALYSIS
elif nav == "Risk Analysis":

    st.markdown(
        '<div class="vox-main-title">Risk Analysis</div>', unsafe_allow_html=True
    )

    result = st.session_state.get("last_result")
    source = st.session_state.get("risk_analysis_source")

    if result:

        final = result["final"]

        # ---------------------------------------------------------
        # FINAL RISK SUMMARY
        # ---------------------------------------------------------

        st.metric("Final Risk Score", f"{final['score']}/100")

        st.metric("Risk Level", final["level"])

        st.metric("Decision", final["decision"])

        # ---------------------------------------------------------
        # ANALYSIS SOURCE
        # ---------------------------------------------------------

        if source == "voice":

            st.info("This risk analysis is based on the selected voice recording.")

        else:

            st.info("This risk analysis is based on the selected payment.")

        # ---------------------------------------------------------
        # RISK BREAKDOWN
        # ---------------------------------------------------------

        cols = st.columns(4)

        with cols[0]:
            st.metric("Transaction Risk", result["transaction"]["score"])

        with cols[1]:
            st.metric("Voice Risk", result["voice"]["score"])

        with cols[2]:
            st.metric("Behavior Risk", result["behavior"]["score"])

        with cols[3]:

            if source == "voice":
                st.metric("Analysis Source", "VOICE")
            else:
                st.metric("Fusion Weight", "45 / 35 / 20")

        # ---------------------------------------------------------
        # RISK CONTRIBUTION BREAKDOWN
        # ---------------------------------------------------------

        st.subheader("Risk Contribution Breakdown")

        st.bar_chart(
            {
                "Transaction": [result["transaction"]["score"]],
                "Voice": [result["voice"]["score"]],
                "Behavior": [result["behavior"]["score"]],
                "Final": [final["score"]],
            }
        )

        # ---------------------------------------------------------
        # CONTRIBUTOR SIGNALS
        # ---------------------------------------------------------

        st.subheader("Contributor Signals")

        reasons = final.get("reasons", {})

        if isinstance(reasons, dict):

            for key, values in reasons.items():

                if not values:
                    continue

                st.markdown(f"### {key.title()} Risk")

                if isinstance(values, list):

                    for msg in values:
                        st.markdown(f"- {msg}")

                else:

                    st.markdown(f"- {values}")

        else:

            for msg in reasons or []:
                st.markdown(f"- {msg}")

        # ---------------------------------------------------------
        # VOICE TRANSCRIPT
        # ---------------------------------------------------------

        if source == "voice":

            transcript = result.get("voice", {}).get("transcript", "")

            if transcript:

                st.subheader("Transcript Used for Analysis")

                st.text_area(
                    "Voice transcript",
                    value=transcript,
                    height=180,
                    disabled=True,
                    key="risk_analysis_voice_transcript",
                )

    else:

        st.info("Run a payment or voice analysis before opening Risk Analysis.")

# FRAUD DASHBOARD
elif nav == "Fraud Dashboard":

    st.markdown(
        '<div class="vox-main-title">Fraud Dashboard</div>', unsafe_allow_html=True
    )

    st.caption("Operational fraud prevention intelligence")

    try:
        incidents = fetch_recent_incidents(limit=100)

        if incidents:

            df = pd.DataFrame(incidents)

            df["risk_level"] = df["risk_level"].fillna("UNKNOWN")

            # ---------------------------------------------------------
            # Dashboard metrics
            # ---------------------------------------------------------

            cols = st.columns(4)

            with cols[0]:
                st.metric("Incidents", len(df))

            with cols[1]:
                st.metric("High Risk Count", int((df["risk_level"] == "HIGH").sum()))

            with cols[2]:
                st.metric(
                    "Medium Risk Count", int((df["risk_level"] == "MEDIUM").sum())
                )

            with cols[3]:
                st.metric(
                    "Average Score",
                    round(df["final_risk"].mean(), 1) if not df.empty else 0,
                )

            st.subheader("Recent Incidents")

            # ---------------------------------------------------------
            # Incident table
            # ---------------------------------------------------------

            for index, incident in enumerate(incidents):

                incident_value = incident.get("incident_id", "UNKNOWN")

                timestamp = incident.get("timestamp", "")

                date_value, time_value = split_timestamp(timestamp)

                amount = incident.get("amount", 0)

                risk_level = incident.get("risk_level", "UNKNOWN")

                final_risk = incident.get("final_risk", 0)

                decision = incident.get("decision", "UNKNOWN")

                # -----------------------------------------------------
                # Table header
                # -----------------------------------------------------

                if index == 0:

                    header_cols = st.columns([2.4, 1.4, 1.4, 1.2, 1.2, 1.2, 1.8])

                    header_cols[0].markdown("**Incident ID**")

                    header_cols[1].markdown("**Date**")

                    header_cols[2].markdown("**Time**")

                    header_cols[3].markdown("**Amount**")

                    header_cols[4].markdown("**Risk Level**")

                    header_cols[5].markdown("**Score**")

                    header_cols[6].markdown("**Decision**")

                # -----------------------------------------------------
                # Table row
                # -----------------------------------------------------

                row_cols = st.columns([2.4, 1.4, 1.4, 1.2, 1.2, 1.2, 1.8])

                with row_cols[0]:

                    if st.button(
                        incident_value,
                        key=f"incident_dashboard_{incident_value}",
                        use_container_width=True,
                    ):

                        st.session_state["selected_incident_id"] = incident_value

                        st.session_state["nav"] = "Incident Report"

                        st.rerun()

                with row_cols[1]:
                    st.write(date_value)

                with row_cols[2]:
                    st.write(time_value)

                with row_cols[3]:
                    try:
                        st.write(f"₹{float(amount):,.0f}")
                    except (ValueError, TypeError):
                        st.write(amount)

                with row_cols[4]:
                    st.write(risk_level)

                with row_cols[5]:
                    st.write(f"{final_risk}/100")

                with row_cols[6]:
                    st.write(decision)

        else:

            st.info("No incidents have been stored yet.")

    except Exception as e:

        st.warning(f"Database currently unavailable: {e}")

# INCIDENT REPORT
elif nav == "Incident Report":

    ###st.markdown(
    ##'<div class="vox-main-title">Incident Report</div>',
    ##unsafe_allow_html=True
    # )

    st.caption("Incident history, detailed risk analysis and downloadable evidence")

    # ================================================================
    # Load stored incidents
    # ================================================================

    try:

        incidents = fetch_recent_incidents(limit=100)

    except Exception as e:

        st.error(f"Unable to load incidents: {e}")

        incidents = []

    # ================================================================
    # No incidents
    # ================================================================

    if not incidents:

        st.info("No incidents have been stored yet.")

    else:

        # ============================================================
        # Selected incident
        # ============================================================

        selected_id = st.session_state.get("selected_incident_id")

        # If nothing is selected, show the incident list.
        # ============================================================

        if not selected_id:

            st.subheader("Incident Reports")

            st.caption("Select an incident to open its complete risk analysis.")

            for index, incident in enumerate(incidents):

                current_id = incident.get("incident_id", "UNKNOWN")

                timestamp = incident.get("timestamp", "")

                date_value, time_value = split_timestamp(timestamp)

                # ---------------------------------------------------------
            # INCIDENT REPORT TABLE
            # ---------------------------------------------------------

            st.caption("Select an incident ID to open its complete risk analysis.")

            # Table header
            header_id, header_date, header_time = st.columns([4, 3, 2])

            with header_id:
                st.markdown("**INCIDENT ID**")

            with header_date:
                st.markdown("**DATE**")

            with header_time:
                st.markdown("**TIME**")

            st.divider()

            # Table rows
            for index, incident in enumerate(incidents):

                current_id = incident.get("incident_id", "UNKNOWN")

                timestamp = incident.get("timestamp", "")

                date_value, time_value = split_timestamp(timestamp)

                row_id, row_date, row_time = st.columns([4, 3, 2])

                # -----------------------------------------------------
                # CLICKABLE INCIDENT ID
                # -----------------------------------------------------
                with row_id:
                    if st.button(
                        current_id,
                        key=f"open_report_{current_id}_{index}",
                        use_container_width=True,
                    ):
                        st.session_state["selected_incident_id"] = current_id

                        st.rerun()

                # -----------------------------------------------------
                # DATE
                # -----------------------------------------------------
                with row_date:
                    st.write(date_value)

                # -----------------------------------------------------
                # TIME
                # -----------------------------------------------------
                with row_time:
                    st.write(time_value)

                st.divider()
        # ============================================================
        # Display selected incident
        # ============================================================

        else:

            record = get_incident_by_id(selected_id)

            if record is None:

                st.error("The selected incident could not be found.")

                if st.button("Back to Incident Reports"):
                    st.session_state["selected_incident_id"] = None

                    st.rerun()

            else:

                # ====================================================
                # Back button
                # ====================================================

                if st.button("← Back to Incident Reports", key="back_to_incident_list"):

                    st.session_state["selected_incident_id"] = None

                    st.rerun()

                # ====================================================
                # Basic incident information
                # ====================================================

                incident_id_value = record.get("incident_id", "UNKNOWN")

                timestamp = record.get("timestamp", "")

                date_value, time_value = split_timestamp(timestamp)

                amount = record.get("amount", 0)

                beneficiary = record.get("beneficiary", "Unknown")

                risk_level = record.get("risk_level", "UNKNOWN")

                final_risk = record.get("final_risk", 0)

                decision = record.get("decision", "UNKNOWN")

                # ====================================================
                # Header
                # ====================================================

                st.markdown(
                    f"""
                    <div class="vc-card"
                         style="margin:1rem 0;">
                        <div style="
                            color:#8fd7cd;
                            font-size:.7rem;
                            text-transform:uppercase;
                            letter-spacing:.1em;
                        ">
                            Incident Report
                        </div>

                        <div style="
                            color:#ffffff;
                            font-size:1.7rem;
                            font-weight:800;
                            margin-top:.3rem;
                        ">
                            {incident_id_value}
                        </div>

                        <div style="
                            color:#a9cbc7;
                            margin-top:.4rem;
                        ">
                            Date: {date_value}
                            &nbsp;&nbsp;|&nbsp;&nbsp;
                            Time: {time_value}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # ====================================================
                # Main risk metrics
                # ====================================================

                cols = st.columns(4)

                with cols[0]:
                    st.metric("Final Risk Score", f"{final_risk}/100")

                with cols[1]:
                    st.metric("Risk Level", risk_level)

                with cols[2]:
                    st.metric("Decision", decision)

                with cols[3]:
                    try:
                        st.metric("Amount", f"₹{float(amount):,.0f}")
                    except (ValueError, TypeError):
                        st.metric("Amount", str(amount))

                # ====================================================
                # Transaction information
                # ====================================================

                st.subheader("Transaction Details")

                transaction_cols = st.columns(2)

                with transaction_cols[0]:

                    st.write(f"**Beneficiary:** {beneficiary}")

                    st.write(
                        f"**Amount:** ₹{float(amount):,.0f}"
                        if isinstance(amount, (int, float))
                        else f"**Amount:** {amount}"
                    )

                with transaction_cols[1]:

                    st.write(f"**Date:** {date_value}")

                    st.write(f"**Time:** {time_value}")

                # ====================================================
                # Risk score breakdown
                # ====================================================

                st.subheader("Risk Analysis Breakdown")

                score_cols = st.columns(4)

                with score_cols[0]:
                    st.metric(
                        "Transaction Risk", f"{record.get('transaction_risk', 0)}/100"
                    )

                with score_cols[1]:
                    st.metric("Voice Risk", f"{record.get('voice_risk', 0)}/100")

                with score_cols[2]:
                    st.metric("Behavior Risk", f"{record.get('behavior_risk', 0)}/100")

                with score_cols[3]:
                    st.metric("Final Risk", f"{final_risk}/100")

                # ====================================================
                # Transaction signals
                # ====================================================

                transaction_features = parse_stored_value(
                    record.get("transaction_features"), {}
                )

                st.subheader("Transaction Risk Signals")

                if transaction_features:

                    if isinstance(transaction_features, dict):

                        for key, value in transaction_features.items():

                            st.markdown(f'**{key.replace("_", " ").title()}**')

                            st.write(value)

                    else:

                        st.write(transaction_features)

                else:

                    st.info("No transaction signals were stored.")

                # ====================================================
                # Voice analysis
                # ====================================================

                st.subheader("Voice / Scam Analysis")

                voice_transcript = record.get("voice_transcript", "")

                if voice_transcript:

                    st.markdown("**Transcript Used for Analysis**")

                    st.text_area(
                        "Voice Transcript",
                        value=voice_transcript,
                        height=180,
                        disabled=True,
                        key=f"voice_report_{incident_id_value}",
                    )

                else:

                    st.info("No voice transcript was stored for this incident.")

                # ====================================================
                # Behavior signals
                # ====================================================

                behavior_signals = parse_stored_value(
                    record.get("behavior_signals"), {}
                )

                st.subheader("Behavioral Analysis")

                if behavior_signals:

                    if isinstance(behavior_signals, dict):

                        for key, value in behavior_signals.items():

                            st.markdown(f'**{key.replace("_", " ").title()}**')

                            st.write(value)

                    else:

                        st.write(behavior_signals)

                else:

                    st.info("No behavioral signals were stored.")

                # ====================================================
                # Detection reasons
                # ====================================================

                reasons = parse_stored_value(record.get("detected_reasons"), {})

                st.subheader("Why Was This Incident Flagged?")

                if reasons:

                    if isinstance(reasons, dict):

                        for category, values in reasons.items():

                            st.markdown(f"### {str(category).title()} Risk")

                            if isinstance(values, list):

                                for value in values:
                                    st.markdown(f"- {value}")

                            else:

                                st.markdown(f"- {values}")

                    elif isinstance(reasons, list):

                        for reason in reasons:
                            st.markdown(f"- {reason}")

                    else:

                        st.write(reasons)

                else:

                    st.success("No additional risk reasons were stored.")

                # ====================================================
                # PDF report
                # ====================================================

                st.subheader("Incident Evidence")

                if st.button(
                    "Generate PDF Report",
                    use_container_width=True,
                    type="primary",
                    key=f"pdf_report_{incident_id_value}",
                ):

                    try:

                        pdf_path = generate_pdf_report(record)

                        if pdf_path:

                            with open(pdf_path, "rb") as pdf_file:

                                pdf_data = pdf_file.read()

                            st.download_button(
                                "Download PDF Report",
                                data=pdf_data,
                                file_name=(f"{incident_id_value}.pdf"),
                                mime="application/pdf",
                                use_container_width=True,
                                key=f"download_pdf_{incident_id_value}",
                            )

                        else:

                            st.warning("PDF generation library is not available.")

                    except Exception as e:

                        st.error(f"PDF report generation failed: {e}")
