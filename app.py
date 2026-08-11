import os
import sys
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
        operator_id = st.text_input('Operator ID', value=st.session_state.get('operator_id', 'operator_demo'))
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
        nav = st.radio('Navigation', list(PAGES.keys()), index=list(PAGES.keys()).index(st.session_state['nav']))
        st.session_state['nav'] = nav

    # Helper rendering helpers

    def score_bar(score):
        return max(0, min(100, score)) / 100

    # ---------------------------------------------------------------------------
    # Home dashboard page
    # ---------------------------------------------------------------------------
    if nav == 'Home':
        st.markdown('<div class="vox-main-title">VoxShield Command Center</div>', unsafe_allow_html=True)
        st.caption('Fraud Intervention Intelligence Layer')
        st.markdown('VoxShield combines UPI payment context, voice/social-engineering indicators, and simulated behavioral telemetry to intervene before authorization.')

        st.markdown('---')

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown('<div class="vc-card"><div class="kpi-title">Live Risk State</div><div class="kpi-value">STABLE</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="vc-card"><div class="kpi-title">Active Mode</div><div class="kpi-value">SIMULATED</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="vc-card"><div class="kpi-title">Protection Layer</div><div class="kpi-value">PRE-AUTH</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown('<div class="vc-card"><div class="kpi-title">Threat Feed</div><div class="kpi-value">ONLINE</div></div>', unsafe_allow_html=True)

        st.markdown('---')

        sc = st.selectbox('Quick Scenario Loader', ['SAFE', 'SUSPICIOUS', 'HIGH_RISK'])
        scenario = DEFAULT_SCENARIOS[sc]
        scenario_col, scenario_details = st.columns([2, 3])
        with scenario_col:
            st.markdown('<div class="vc-card">', unsafe_allow_html=True)
            st.subheader('Scenario Profile')
            st.metric('Scenario', sc)
            st.metric('Amount', f"₹{scenario['amount']:,}")
            st.metric('Beneficiary', 'Known' if scenario['beneficiary_new'] == False else 'New')
            st.markdown('</div>', unsafe_allow_html=True)
        with scenario_details:
            st.subheader('Simulation Signal Stack')
            st.json(scenario)

        # quick action row
        qa1, qa2, qa3 = st.columns(3)
        with qa1:
            if st.button('Open Secure Payment'):
                st.session_state['nav'] = 'Secure Payment'
                st.rerun()
        with qa2:
            if st.button('Analyze Voice'):
                st.session_state['nav'] = 'Voice Analysis'
                st.rerun()
        with qa3:
            if st.button('Generate Report'):
                st.session_state['nav'] = 'Incident Report'
                st.rerun()

    # ---------------------------------------------------------------------------
    # Secure Payment page
    # ---------------------------------------------------------------------------
    elif nav == 'Secure Payment':
        st.markdown('<div class="vox-main-title">Secure Payment</div>', unsafe_allow_html=True)
        st.caption('UPI transaction simulation and protection pre-screen')

        scenario = st.selectbox('Scenario', ['SAFE', 'SUSPICIOUS', 'HIGH_RISK'], index=0)
        scenario_data = DEFAULT_SCENARIOS[scenario]

        st.markdown('---')

        col_left, col_right = st.columns([1.2, 1.05])
        with col_left:
            st.markdown('<div class="vc-card">', unsafe_allow_html=True)
            st.subheader('Payment Initiation')
            st.markdown('---')
            amount = st.number_input('Amount', min_value=1, value=scenario_data['amount'])
            beneficiary = st.text_input('Beneficiary', value='Astra Mart' if amount <= 1000 else 'New Merchant')
            beneficiary_new = st.checkbox('New beneficiary', value=scenario_data['beneficiary_new'])
            frequency = st.selectbox('Transaction frequency', ['regular', 'rare', 'first_time'], index=0 if scenario_data['transaction_frequency'] == 'regular' else 1)
            location_anomaly = st.checkbox('Location anomaly', value=scenario_data['location_anomaly'])
            device_known = st.checkbox('Known device', value=scenario_data['device_known'])
            transaction_time = st.selectbox('Transaction time', ['normal', 'unusual', 'after_hours'], index=0 if scenario_data['transaction_time'] == 'normal' else 1)
            previous_fraud_history = st.checkbox('Previous fraud/suspicious activity', value=scenario_data['previous_fraud_history'])
            channel = st.selectbox('Channel', ['upi', 'wallet', 'merchant'], index=0)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_right:
            st.markdown('<div class="vc-card">', unsafe_allow_html=True)
            st.subheader('Behavioral Signals')
            behavior = {
                'typing_speed': st.selectbox('Simulated typing speed', ['normal', 'fast', 'slow'], index=0),
                'interaction_pattern': st.selectbox('Interaction pattern', ['normal', 'unusual', 'rapid_navigation'], index=0),
                'device_familiarity': 'known' if device_known else 'unknown',
                'transaction_timing': transaction_time,
                'location_change': 'significant' if location_anomaly else 'none',
                'rapid_repeated_actions': st.checkbox('Rapid repeated actions', value=False)
            }
            voice_transcript = st.text_area('Voice transcript / scam context', value=scenario_data['voice_transcript'], height=150)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('---')
        run_cols = st.columns([1, 1, 1, 3])
        with run_cols[0]:
            run_analysis = st.button('Run VoxShield Analysis')
        with run_cols[1]:
            if st.button('Allow / Proceed'):
                st.success('Allow simulation approved')
        with run_cols[2]:
            if st.button('Verify'):
                st.warning('Verification prompt issued')

        if run_analysis:
            tx = {
                'amount': amount,
                'beneficiary_new': beneficiary_new,
                'transaction_frequency': frequency,
                'transaction_time': transaction_time,
                'device_known': device_known,
                'location_anomaly': location_anomaly,
                'previous_fraud_history': previous_fraud_history,
                'beneficiary_type': 'new' if beneficiary_new else 'known',
                'transaction_channel': channel,
            }
            result = run_risk_engine(tx, voice_transcript=voice_transcript, behavior=behavior, api_key=os.getenv('GEMINI_API_KEY'))
            final = result['final']
            final_score = final['score']
            final_level = final['level']
            st.session_state['last_result'] = result
            st.session_state['last_amount'] = amount
            st.session_state['last_beneficiary'] = beneficiary
            st.session_state['last_incident_id'] = incident_id()

            class_name = 'status-low' if final_level == 'LOW' else 'status-medium' if final_level == 'MEDIUM' else 'status-high'
            st.markdown(f'<div class="vc-card {class_name}">', unsafe_allow_html=True)
            st.header('Risk Decision')
            st.markdown(f'<div class="decision-banner">Final Risk Score <span class="risk-score">{final_score}/100</span> · <b>{final_level}</b> · {final["decision"]}</div>', unsafe_allow_html=True)
            if final_level == 'LOW':
                st.success('Payment appears safe. Allow / proceed simulation available.')
            elif final_level == 'MEDIUM':
                st.warning('Suspicious activity detected. Verification required to continue.')
            else:
                st.error('TRANSACTION BLOCKED. Evidence report required before processing. ')
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('---')
            st.subheader('Risk Contribution Stack')
            st.bar_chart({
                'Transaction Risk': [result['transaction']['score']],
                'Voice Risk': [result['voice']['score']],
                'Behavior Risk': [result['behavior']['score']],
                'Final Risk': [final_score]
            })

            st.subheader('Explainable Contributor List')
            reasons = []
            reasons.extend(result['transaction']['reasons'])
            reasons.extend(result['voice']['reasons'])
            reasons.extend(result['behavior']['reasons'])
            for item in reasons:
                st.markdown(f'- {item}')

    # ---------------------------------------------------------------------------
    # Voice Analysis page
    # ---------------------------------------------------------------------------
    elif nav == 'Voice Analysis':
        st.markdown('<div class="vox-main-title">Voice / Scam Analysis</div>', unsafe_allow_html=True)
        st.caption('Audio signal intake and social-engineering transcript scan')

        uploaded_audio = st.file_uploader('Upload short audio clip', type=['wav', 'mp3', 'm4a', 'ogg'])
        transcript = st.text_area('Transcript input', value='I am calling from the bank. Complete the payment now. Send the OTP immediately.', height=160)

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
                    transaction={'amount': 5000, 'beneficiary_new': False, 'transaction_frequency': 'regular', 'transaction_time': 'normal', 'device_known': True, 'location_anomaly': False, 'previous_fraud_history': False},
                    voice_transcript=transcript,
                    behavior=None,
                    api_key=api_key
                )
                analysis = result['voice']
                st.session_state['voice_analysis'] = analysis
                st.json(analysis)
                st.progress(min(1.0, max(0.0, analysis['score'] / 100)))
        with c2:
            st.markdown('<div class="vc-card">', unsafe_allow_html=True)
            st.subheader('AI Mode')
            if os.getenv('GEMINI_API_KEY'):
                st.success('Gemini API key detected')
            else:
                st.warning('No Gemini API key detected. Rule-based fallback active.')
            st.markdown('</div>', unsafe_allow_html=True)

        if 'voice_analysis' in st.session_state:
            st.subheader('Voice Risk Output')
            st.json(st.session_state['voice_analysis'])

    # ---------------------------------------------------------------------------
    # Risk Analysis page
    # ---------------------------------------------------------------------------
    elif nav == 'Risk Analysis':
        st.markdown('<div class="vox-main-title">Risk Analysis</div>', unsafe_allow_html=True)
        if st.session_state['last_result']:
            result = st.session_state['last_result']
            st.metric('Final Risk Score', f"{result['final']['score']}/100")
            st.metric('Risk Level', result['final']['level'])
            st.metric('Decision', result['final']['decision'])

            metrics = st.columns(4)
            with metrics[0]:
                st.metric('Transaction Risk', result['transaction']['score'])
            with metrics[1]:
                st.metric('Voice Risk', result['voice']['score'])
            with metrics[2]:
                st.metric('Behavior Risk', result['behavior']['score'])
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
        st.markdown('<div class="vox-main-title">Fraud Dashboard</div>', unsafe_allow_html=True)
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
                    st.metric('High Risk Count', int((df['risk_level'] == 'HIGH').sum()))
                with c3:
                    st.metric('Medium Risk Count', int((df['risk_level'] == 'MEDIUM').sum()))
                with c4:
                    st.metric('Average Score', round(df['final_risk'].mean(), 1) if not df.empty else 0)

                st.subheader('Recent Incidents')
                st.dataframe(df[['incident_id', 'timestamp', 'amount', 'risk_level', 'final_risk', 'decision']])
            else:
                st.info('No incidents have been stored yet.')
        except Exception as e:
            st.warning(f'Database currently unavailable: {e}')

    # ---------------------------------------------------------------------------
    # Incident Report page
    # ---------------------------------------------------------------------------
    elif nav == 'Incident Report':
        st.markdown('<div class="vox-main-title">Incident Report</div>', unsafe_allow_html=True)
        st.caption('Prototype evidence package and downloadable report')
        if st.session_state['last_result']:
            amount = st.session_state.get('last_amount', 0)
            beneficiary = st.session_state.get('last_beneficiary', 'Retail Beneficiary')
            incident_id_value = st.session_state.get('last_incident_id', incident_id())
            result = st.session_state['last_result']
            record = {
                'incident_id': incident_id_value,
                'timestamp': now_iso(),
                'amount': amount,
                'beneficiary': beneficiary,
                'transaction_features': str(result['transaction']['features']),
                'transaction_risk': result['transaction']['score'],
                'voice_risk': result['voice']['score'],
                'behavior_risk': result['behavior']['score'],
                'final_risk': result['final']['score'],
                'risk_level': result['final']['level'],
                'decision': result['final']['decision'],
                'detected_reasons': str(result['final']['reasons']),
                'voice_transcript': result['voice'].get('transcript', ''),
                'behavior_signals': str(result['behavior']['signals']),
                'evidence_path': ''
            }

            st.markdown('<div class="vc-card">', unsafe_allow_html=True)
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
                    st.download_button('Download Evidence Report', data=open(path, 'rb').read(), file_name=Path(path).name, mime='text/html')
                    st.success(f'Report generated: {path}')
                except Exception as e:
                    st.warning(f'Report generation failed: {e}')

            if st.button('Generate PDF Evidence Report'):
                try:
                    pdf_path = generate_pdf_report(record)
                    if pdf_path:
                        record['evidence_path'] = pdf_path
                        store_incident(record)
                        st.download_button('Download PDF Evidence Report', data=open(pdf_path, 'rb').read(), file_name=Path(pdf_path).name, mime='application/pdf')
                        st.success(f'PDF report generated: {pdf_path}')
                    else:
                        st.warning('PDF generation library is not available in this environment.')
                except Exception as e:
                    st.warning(f'PDF report generation failed: {e}')
        else:
            st.info('Run an analysis before creating an incident report.')


ensure_database()
