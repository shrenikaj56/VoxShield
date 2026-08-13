import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from utils.helpers import incident_id, now_iso
from modules.database import ensure_database, store_incident, fetch_recent_incidents
from modules.risk_engine import run_risk_engine
from modules.report_generator import generate_html_report, generate_pdf_report
from modules.voice_analyzer import analyze_voice

load_dotenv()

st.set_page_config(page_title='VoxShield', page_icon='🛡️', layout='wide')

st.markdown('''
<style>
.stApp { background: radial-gradient(circle at 10% 10%, #173b45, #071b22 80%, #020d10); color:#eefcfb; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#10292e,#061b21); }
.block-container { padding-top: 2rem; }
.vox-main-title { font-size:2.2rem; font-weight:800; color:#fff; }
.vc-card { border-radius:16px; padding:1rem; background:linear-gradient(160deg,rgba(18,54,57,.94),rgba(9,30,36,.94)); border:1px solid rgba(132,244,219,.38); }
.brand-header { padding:1rem 0 2rem; }
.brand-name { font-size:3.2rem; font-weight:800; color:#fff; }
.brand-tagline { color:#77ead2; font-size:.85rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
.brand-description { max-width:850px; color:#b9d8d4; font-size:1rem; line-height:1.65; margin-top:.8rem; }
.home-section-title { color:#fff; font-size:1.35rem; font-weight:800; margin:1.6rem 0 .7rem; }
.home-status-card,.pipeline-card,.flow-box { border-radius:15px; padding:1rem; background:rgba(9,32,38,.96); border:1px solid rgba(119,234,210,.24); min-height:110px; }
.home-status-label { color:#8fd7cd; font-size:.68rem; text-transform:uppercase; letter-spacing:.11em; }
.home-status-value { color:#fff; font-size:1.35rem; font-weight:800; margin-top:.35rem; }
.home-status-detail,.pipeline-text { color:#a9cbc7; font-size:.75rem; margin-top:.2rem; }
.pipeline-card { min-height:150px; text-align:center; }
.pipeline-number { width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto .5rem; color:#77ead2; border:1px solid rgba(119,234,210,.45); }
.pipeline-title { color:#fff; font-weight:800; }
.flow-box { min-height:auto; text-align:center; color:#fff; font-weight:700; }
.payment-result { border-radius:16px; padding:1.5rem; margin:1rem 0; background:rgba(18,54,57,.94); border:1px solid rgba(132,244,219,.38); }
.payment-result-title { font-size:1.6rem; font-weight:800; color:#fff; }
.pattern-swatch { height:34px; border-radius:10px; margin-bottom:.3rem; border:1px solid rgba(255,255,255,.25); }
.swatch-blue { background:#2f80ed; }.swatch-yellow { background:#f2c94c; }.swatch-red { background:#eb5757; }.swatch-green { background:#27ae60; }.swatch-purple { background:#9b51e0; }.swatch-orange { background:#f2994a; }
.home-disclaimer { margin-top:2rem; padding:1rem; border-top:1px solid rgba(119,234,210,.15); color:#789a96; font-size:.75rem; }
</style>
''', unsafe_allow_html=True)

# Session defaults
st.session_state.setdefault('last_result', None)
st.session_state.setdefault('operator_access', False)
st.session_state.setdefault('authenticated', False)
st.session_state.setdefault('last_incident_id', incident_id())
st.session_state.setdefault('nav', 'Home')
st.session_state.setdefault('payment_stage', 'idle')
st.session_state.setdefault('payment_result', None)
st.session_state.setdefault('payment_auth_pattern', [])
st.session_state.setdefault('voice_transcript', '')
st.session_state.setdefault('voice_upload_signature', None)

PAGES = ['Home', 'Secure Payment', 'Voice Analysis', 'Risk Analysis', 'Fraud Dashboard', 'Incident Report']
ensure_database()

# Login
if not st.session_state['authenticated']:
    st.title('VoxShield')
    st.caption('Fraud Intelligence Console')
    with st.form('voxshield_login'):
        operator_id = st.text_input('Operator ID', value='operator_demo')
        operator_pin = st.text_input('PIN', type='password', value='1234')
        color_pattern = st.selectbox('Color Pattern', ['Green', 'Blue', 'Amber'])
        submit = st.form_submit_button('Enter Secure Console')
        if submit:
            if operator_pin == '1234' and color_pattern == 'Green':
                st.session_state['authenticated'] = True
                st.session_state['operator_access'] = True
                st.session_state['operator_id'] = operator_id
                st.rerun()
            else:
                st.error('Authentication failed')
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown('<div style="font-size:48px;">🛡️</div>', unsafe_allow_html=True)
    st.title('VoxShield')
    st.caption('Real-Time UPI and Voice-Cloning Fraud Intervention')
    if st.button('Unlock Console'):
        st.session_state['operator_access'] = True
    nav = st.radio('Navigation', PAGES, index=PAGES.index(st.session_state['nav']) if st.session_state['nav'] in PAGES else 0)
    st.session_state['nav'] = nav


def save_last_result(result, amount=0, beneficiary='Astra Mart'):
    st.session_state['last_result'] = result
    st.session_state['last_amount'] = amount
    st.session_state['last_beneficiary'] = beneficiary
    st.session_state['last_incident_id'] = incident_id()


def run_payment_analysis(amount, beneficiary_new):
    if amount >= 20000:
        frequency, tx_time, device_known, location_anomaly = 'first_time', 'unusual', False, True
        voice_context = ('I am calling from your bank. Your account is under urgent review. '
                         'Complete this payment immediately. Share the OTP if asked.')
        behavior = {'typing_speed':'fast','interaction_pattern':'rapid_navigation','device_familiarity':'unknown',
                    'transaction_timing':'unusual','location_change':'significant','rapid_repeated_actions':True,
                    'screen_sharing':True}
    elif amount >= 5000 or beneficiary_new:
        frequency, tx_time, device_known, location_anomaly = 'rare', 'unusual', True, False
        voice_context = 'Please confirm this unusual payment. The beneficiary is new and additional verification is required.'
        behavior = {'typing_speed':'fast','interaction_pattern':'unusual','device_familiarity':'known',
                    'transaction_timing':tx_time,'location_change':'none','rapid_repeated_actions':False}
    else:
        frequency, tx_time, device_known, location_anomaly = 'regular', 'normal', True, False
        voice_context = ''
        behavior = {'typing_speed':'normal','interaction_pattern':'normal','device_familiarity':'known',
                    'transaction_timing':'normal','location_change':'none','rapid_repeated_actions':False}
    tx = {'amount':amount,'beneficiary_new':beneficiary_new,'transaction_frequency':frequency,
          'transaction_time':tx_time,'device_known':device_known,'location_anomaly':location_anomaly,
          'previous_fraud_history':False,'beneficiary_type':'new' if beneficiary_new else 'known',
          'transaction_channel':'upi'}
    return run_risk_engine(tx, voice_transcript=voice_context, behavior=behavior, api_key=os.getenv('GEMINI_API_KEY'))


def transcribe_audio_with_gemini(audio_path, mime_type=None):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY is not configured.')

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    upload_config = None
    if mime_type:
        upload_config = types.UploadFileConfig(mime_type=mime_type)

    if upload_config is not None:
        uploaded_file = client.files.upload(
            file=audio_path,
            config=upload_config
        )
    else:
        uploaded_file = client.files.upload(file=audio_path)

    response = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=[
            'Generate an accurate transcript of the speech in this audio. '
            'Return only the spoken words. Do not summarize, explain, translate, '
            'or add timestamps. Preserve the wording as closely as possible.',
            uploaded_file,
        ],
    )

    transcript_text = (response.text or '').strip()
    if not transcript_text:
        raise RuntimeError('Gemini returned an empty transcript.')

    return transcript_text


# HOME
if nav == 'Home':
    st.markdown('''<div class="brand-header"><div class="brand-name">VoxShield</div>
    <div class="brand-tagline">Real-Time UPI &amp; Voice-Cloning Fraud Intervention</div>
    <div class="brand-description">A multi-layered fraud intelligence engine that analyzes transaction, voice, behavioral and contextual signals before authorization.</div></div>''', unsafe_allow_html=True)
    a1, a2, _ = st.columns([1.25,1.25,2.5])
    with a1:
        if st.button('Start Secure Payment', use_container_width=True, type='primary'):
            st.session_state['nav']='Secure Payment'; st.session_state['payment_stage']='idle'; st.rerun()
    with a2:
        if st.button('Analyze Voice Scam', use_container_width=True):
            st.session_state['nav']='Voice Analysis'; st.rerun()
    st.markdown('<div class="home-section-title">Protection Status</div>', unsafe_allow_html=True)
    cards=[('Protection Mode','PRE-AUTH','Before authorization'),('Risk Engine','ACTIVE','Multi-signal analysis'),('Signal Sources','4','Transaction · Voice · Behavior · Context'),('Protection Actions','3 LEVELS','Allow · Verify · Block')]
    for col, card in zip(st.columns(4), cards):
        with col:
            st.markdown(f'<div class="home-status-card"><div class="home-status-label">{card[0]}</div><div class="home-status-value">{card[1]}</div><div class="home-status-detail">{card[2]}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="home-section-title">How VoxShield Works</div>', unsafe_allow_html=True)
    pipeline=[('1','Transaction','Amount, beneficiary, device, timing and location'),('2','Voice','Urgency, threats, impersonation and scam intent'),('3','Behavior','Interaction, device familiarity and anomalies'),('4','Risk Decision','Explainable score → Allow, Verify or Block')]
    for col, item in zip(st.columns(4), pipeline):
        with col:
            st.markdown(f'<div class="pipeline-card"><div class="pipeline-number">{item[0]}</div><div class="pipeline-title">{item[1]}</div><div class="pipeline-text">{item[2]}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="home-section-title">Adaptive Protection</div>', unsafe_allow_html=True)
    for col, title, action in zip(st.columns(3),('LOW RISK','MEDIUM RISK','HIGH RISK'),('ALLOW','WARN + VERIFY','HOLD + REPORT')):
        with col: st.markdown(f'<div class="flow-box">{title}<br>{action}</div>', unsafe_allow_html=True)

# SECURE PAYMENT
elif nav == 'Secure Payment':
    stage=st.session_state['payment_stage']
    if stage == 'idle':
        st.markdown('<div class="vox-main-title">VoxShield</div>', unsafe_allow_html=True); st.caption('Secure Payment')
        left,right=st.columns([1.15,.85])
        with left:
            st.markdown('<div class="vc-card">',unsafe_allow_html=True); st.subheader('Pay to')
            recipient=st.text_input('Recipient',value='Astra Mart'); upi_id=st.text_input('UPI ID',value='@astramart'); amount=st.number_input('Amount',min_value=1,value=500,step=100)
            st.markdown('</div>',unsafe_allow_html=True)
        with right:
            st.markdown('<div class="vc-card">',unsafe_allow_html=True); st.subheader('Payment Method'); st.radio('Method',['UPI'],label_visibility='collapsed'); st.markdown('---'); st.subheader('From'); st.write("Anshu's Bank Account"); st.write('•••• 4821'); beneficiary_new=st.checkbox('New beneficiary'); st.caption('Simulation only — no real money or UPI API is used.'); st.markdown('</div>',unsafe_allow_html=True)
        if st.button('PAY',use_container_width=True,type='primary',key='pay_button'):
            st.session_state['payment_data']={'recipient':recipient,'upi_id':upi_id,'amount':amount,'beneficiary_new':beneficiary_new}; st.session_state['payment_stage']='analyzing'; st.rerun()
    elif stage == 'analyzing':
        data=st.session_state['payment_data']; st.info('Analyzing payment security...')
        with st.spinner('Collecting transaction, voice, behavior and context signals...'):
            result=run_payment_analysis(data['amount'],data['beneficiary_new'])
        st.session_state['payment_result']=result; save_last_result(result,data['amount'],data['recipient']); st.session_state['payment_stage']='result'; st.rerun()
    elif stage == 'result':
        data=st.session_state['payment_data']; final=st.session_state['payment_result']['final']; level=final['level']; score=final['score']
        if level=='LOW':
            st.success('PAYMENT APPROVED'); st.metric('Risk Score',f'{score}/100'); st.markdown(f'### ₹{data["amount"]:,.0f} — {data["recipient"]}'); st.write('VoxShield security check passed.')
            if st.button('CONTINUE TO PAY',use_container_width=True,type='primary'): st.session_state['payment_stage']='success'; st.rerun()
        elif level=='MEDIUM':
            st.warning('SECURITY ALERT'); st.metric('Risk Score',f'{score}/100'); st.write('Suspicious activity detected. Additional verification required.')
            c1,c2=st.columns(2)
            with c1:
                if st.button('VERIFY & CONTINUE',use_container_width=True,type='primary'): st.session_state['payment_stage']='auth'; st.session_state['payment_auth_pattern']=[]; st.rerun()
            with c2:
                if st.button('CANCEL PAYMENT',use_container_width=True): st.session_state['payment_stage']='cancelled'; st.rerun()
        else:
            st.error('HIGH RISK PAYMENT'); st.metric('Risk Score',f'{score}/100'); st.markdown(f'### ₹{data["amount"]:,.0f} → {data["recipient"]}'); st.write('VoxShield has temporarily held this payment before authorization.'); st.markdown('**Why was this flagged?**')
            reasons=final.get('reasons',[])
            if isinstance(reasons,dict): reasons=[x for vals in reasons.values() for x in (vals if isinstance(vals,list) else [vals])]
            if not reasons: reasons=['High-value transaction','Potential social-engineering indicators','Behavioral anomaly']
            for r in reasons: st.markdown(f'- {r}')
            c1,c2=st.columns(2)
            with c1:
                if st.button('VERIFY PAYMENT',use_container_width=True,type='primary'): st.session_state['payment_stage']='auth'; st.session_state['payment_auth_pattern']=[]; st.rerun()
            with c2:
                if st.button('CANCEL PAYMENT',use_container_width=True): st.session_state['payment_stage']='cancelled'; st.rerun()
    elif stage=='auth':
        selected=st.session_state['payment_auth_pattern']; matrix=[['BLUE','YELLOW','RED'],['GREEN','PURPLE','ORANGE'],['ORANGE','BLUE','GREEN']]; correct=[(1,2),(2,2),(3,2)]
        st.markdown('<div class="payment-result"><div class="payment-result-title">Verify it\'s really you</div><p>Select your registered colour pattern in the correct order.</p></div>',unsafe_allow_html=True)
        colors=[matrix[r-1][c-1] for r,c in selected]; st.info('Selected: '+(' → '.join(colors) if colors else 'No colours selected'))
        for r in range(1,4):
            cols=st.columns(3)
            for c in range(1,4):
                color=matrix[r-1][c-1]; cell=(r,c)
                with cols[c-1]:
                    st.markdown(f'<div class="pattern-swatch swatch-{color.lower()}"></div>',unsafe_allow_html=True)
                    if st.button(color,key=f'pattern_{r}_{c}',use_container_width=True,disabled=len(selected)>=3 or cell in selected): st.session_state['payment_auth_pattern'].append(cell); st.rerun()
        st.caption('Registered pattern: [1,2] → [2,2] → [3,2]  (YELLOW → PURPLE → BLUE)')
        c1,c2=st.columns(2)
        with c1:
            if st.button('VERIFY',use_container_width=True,type='primary',key='verify_pattern'): st.session_state['payment_stage']='success' if selected==correct else 'auth_failed'; st.session_state['payment_auth_pattern']=[]; st.rerun()
        with c2:
            if st.button('RESET PATTERN',use_container_width=True,key='reset_pattern'): st.session_state['payment_auth_pattern']=[]; st.rerun()
    elif stage=='auth_failed':
        st.error('Incorrect authentication pattern.'); st.warning('This transaction remains protected and has not been authorized.')
        if st.button('TRY AGAIN',use_container_width=True,type='primary'): st.session_state['payment_stage']='auth'; st.session_state['payment_auth_pattern']=[]; st.rerun()
    elif stage=='success':
        data=st.session_state['payment_data']; tid=f"VSX{str(st.session_state.get('last_incident_id',incident_id()))[-8:]}"; st.success('Payment Successful'); st.metric('Amount',f'₹{data["amount"]:,.0f}'); st.write(f'Paid to **{data["recipient"]}**'); st.write(f'Transaction ID: `{tid}`'); st.caption('Simulated transaction — no real money moved.')
        if st.button('MAKE ANOTHER PAYMENT',use_container_width=True): st.session_state['payment_stage']='idle'; st.session_state['payment_result']=None; st.session_state['payment_auth_pattern']=[]; st.rerun()
    elif stage=='cancelled':
        st.warning('Payment cancelled. No authorization was attempted.')
        if st.button('BACK TO PAYMENT',use_container_width=True): st.session_state['payment_stage']='idle'; st.rerun()

# VOICE ANALYSIS
elif nav == 'Voice Analysis':
    st.markdown(
        '<div class="vox-main-title">Voice / Scam Analysis</div>',
        unsafe_allow_html=True
    )
    st.caption(
        'Upload a call recording and VoxShield will automatically transcribe it before scam-risk analysis.'
    )

    uploaded_audio = st.file_uploader(
        'Upload short audio clip',
        type=[
            'wav', 'mp3', 'mpeg', 'mpga', 'm4a', 'aac',
            'ogg', 'flac', 'aiff', 'opus', 'webm'
        ],
        key='voice_audio_upload'
    )

    if uploaded_audio is not None:
        upload_signature = (
            uploaded_audio.name,
            uploaded_audio.size,
            uploaded_audio.type
        )

        if upload_signature != st.session_state.get('voice_upload_signature'):
            st.session_state['voice_upload_signature'] = upload_signature

            api_key = os.getenv('GEMINI_API_KEY')

            if not api_key:
                st.warning(
                    'Gemini API key is not configured. '
                    'You can still type or paste a transcript manually below.'
                )
            else:
                temp_path = None
                try:
                    suffix = Path(uploaded_audio.name).suffix.lower() or '.audio'

                    mime_map = {
                        '.wav': 'audio/wav',
                        '.mp3': 'audio/mpeg',
                        '.mpeg': 'audio/mpeg',
                        '.mpga': 'audio/mpeg',
                        '.m4a': 'audio/mp4',
                        '.aac': 'audio/aac',
                        '.ogg': 'audio/ogg',
                        '.flac': 'audio/flac',
                        '.aiff': 'audio/aiff',
                        '.opus': 'audio/opus',
                        '.webm': 'audio/webm',
                    }

                    mime_type = (
                        uploaded_audio.type
                        if uploaded_audio.type and uploaded_audio.type.startswith('audio/')
                        else mime_map.get(suffix, 'audio/mpeg')
                    )

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=suffix
                    ) as tmp:
                        tmp.write(uploaded_audio.getbuffer())
                        temp_path = tmp.name

                    with st.spinner('Transcribing audio with Gemini...'):
                        generated_transcript = transcribe_audio_with_gemini(
                            temp_path,
                            mime_type=mime_type
                        )

                    st.session_state['voice_transcript_input'] = generated_transcript
                    st.success('Audio transcribed successfully.')

                except Exception as exc:
                    st.error(
                        'Audio transcription failed. '
                        f'You can still enter the transcript manually. Details: {exc}'
                    )

                finally:
                    if temp_path:
                        try:
                            os.remove(temp_path)
                        except OSError:
                            pass

    transcript = st.text_area(
        'Transcript input',
        value=st.session_state.get('voice_transcript_input', ''),
        height=180,
        key='voice_transcript_input',
        placeholder=(
            'The generated transcript will appear here automatically. '
            'You can also type or paste a transcript manually.'
        )
    )

    st.caption(
        'Manual mode is always available: type or paste text here if automatic transcription is unavailable.'
    )

    c1, c2 = st.columns([2, 1])

    with c1:
        if st.button(
            'Analyze Voice Signal',
            use_container_width=True,
            type='primary',
            key='analyze_voice_signal'
        ):
            transcript_for_analysis = transcript.strip()

            if not transcript_for_analysis:
                st.warning(
                    'Please upload an audio recording with Gemini configured, '
                    'or type/paste a transcript in the Transcript input box.'
                )
            else:
                try:
                    result = run_risk_engine(
                        transaction={
                            'amount': 5000,
                            'beneficiary_new': False,
                            'transaction_frequency': 'regular',
                            'transaction_time': 'normal',
                            'device_known': True,
                            'location_anomaly': False,
                            'previous_fraud_history': False,
                        },
                        voice_transcript=transcript_for_analysis,
                        behavior=None,
                        api_key=os.getenv('GEMINI_API_KEY')
                    )

                    st.session_state['voice_analysis'] = result['voice']
                    st.success('Voice analysis completed.')

                except Exception as exc:
                    st.error(f'Voice analysis failed: {exc}')

    with c2:
        st.markdown('<div class="vc-card">', unsafe_allow_html=True)
        st.subheader('AI Mode')

        if os.getenv('GEMINI_API_KEY'):
            st.success(
                'Gemini connected — automatic audio transcription enabled.'
            )
        else:
            st.warning(
                'No Gemini API key detected. '
                'Manual transcript / rule-based analysis is available.'
            )

        st.markdown('</div>', unsafe_allow_html=True)

    if 'voice_analysis' in st.session_state:
        analysis = st.session_state['voice_analysis']
        st.subheader('Voice Risk Output')
        st.metric(
            'Voice Risk Score',
            f"{analysis.get('score', 0)}/100"
        )
        st.json(analysis)

# RISK ANALYSIS
elif nav == 'Risk Analysis':
    st.markdown('<div class="vox-main-title">Risk Analysis</div>',unsafe_allow_html=True)
    result=st.session_state.get('last_result')
    if result:
        final=result['final']; st.metric('Final Risk Score',f"{final['score']}/100"); st.metric('Risk Level',final['level']); st.metric('Decision',final['decision'])
        cols=st.columns(4)
        with cols[0]: st.metric('Transaction Risk',result['transaction']['score'])
        with cols[1]: st.metric('Voice Risk',result['voice']['score'])
        with cols[2]: st.metric('Behavior Risk',result['behavior']['score'])
        with cols[3]: st.metric('Fusion Weight','45 / 35 / 20')
        st.subheader('Risk Contribution Breakdown'); st.bar_chart({'Transaction':[result['transaction']['score']],'Voice':[result['voice']['score']],'Behavior':[result['behavior']['score']],'Final':[final['score']]})
        st.subheader('Contributor Signals'); reasons=final.get('reasons',{})
        if isinstance(reasons,dict):
            for key,values in reasons.items():
                st.markdown(f'### {key.title()} Risk')
                for msg in values if isinstance(values,list) else [values]: st.markdown(f'- {msg}')
        else:
            for msg in reasons or []: st.markdown(f'- {msg}')
    else: st.info('No transaction has been analyzed yet.')

# FRAUD DASHBOARD
elif nav == 'Fraud Dashboard':
    st.markdown('<div class="vox-main-title">Fraud Dashboard</div>',unsafe_allow_html=True); st.caption('Operational fraud prevention intelligence')
    try:
        incidents=fetch_recent_incidents(limit=10)
        if incidents:
            df=pd.DataFrame(incidents); df['risk_level']=df['risk_level'].fillna('UNKNOWN'); cols=st.columns(4)
            with cols[0]: st.metric('Incidents',len(df))
            with cols[1]: st.metric('High Risk Count',int((df['risk_level']=='HIGH').sum()))
            with cols[2]: st.metric('Medium Risk Count',int((df['risk_level']=='MEDIUM').sum()))
            with cols[3]: st.metric('Average Score',round(df['final_risk'].mean(),1) if not df.empty else 0)
            st.subheader('Recent Incidents'); st.dataframe(df[['incident_id','timestamp','amount','risk_level','final_risk','decision']])
        else: st.info('No incidents have been stored yet.')
    except Exception as e: st.warning(f'Database currently unavailable: {e}')

# INCIDENT REPORT
elif nav == 'Incident Report':
    st.markdown('<div class="vox-main-title">Incident Report</div>',unsafe_allow_html=True); st.caption('Prototype evidence package and downloadable report')
    result=st.session_state.get('last_result')
    if result:
        record={'incident_id':st.session_state.get('last_incident_id',incident_id()),'timestamp':now_iso(),'amount':st.session_state.get('last_amount',0),'beneficiary':st.session_state.get('last_beneficiary','Retail Beneficiary'),'transaction_features':str(result['transaction'].get('features',{})),'transaction_risk':result['transaction']['score'],'voice_risk':result['voice']['score'],'behavior_risk':result['behavior']['score'],'final_risk':result['final']['score'],'risk_level':result['final']['level'],'decision':result['final']['decision'],'detected_reasons':str(result['final'].get('reasons',{})),'voice_transcript':result['voice'].get('transcript',''),'behavior_signals':str(result['behavior'].get('signals',{})),'evidence_path':''}
        st.json(record)
        if st.button('Persist Incident to SQLite'):
            try: store_incident(record); st.success('Incident stored')
            except Exception as e: st.warning(f'Incident storage failed: {e}')
        if st.button('Generate HTML Evidence Report'):
            try:
                path=generate_html_report(record); record['evidence_path']=path; store_incident(record)
                with open(path,'rb') as f: st.download_button('Download Evidence Report',data=f.read(),file_name=Path(path).name,mime='text/html')
            except Exception as e: st.warning(f'Report generation failed: {e}')
        if st.button('Generate PDF Evidence Report'):
            try:
                path=generate_pdf_report(record)
                if path:
                    record['evidence_path']=path; store_incident(record)
                    with open(path,'rb') as f: st.download_button('Download PDF Evidence Report',data=f.read(),file_name=Path(path).name,mime='application/pdf')
                else: st.warning('PDF generation library is not available in this environment.')
            except Exception as e: st.warning(f'PDF report generation failed: {e}')
    else: st.info('Run an analysis before creating an incident report.')