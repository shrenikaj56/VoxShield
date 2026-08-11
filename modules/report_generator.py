from datetime import datetime
from pathlib import Path
import html

from utils.config import REPORTS_DIR


def generate_html_report(incident_record):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"{incident_record['incident_id']}.html"
    content = f"""
<!doctype html>
<html>
<head>
<title>VoxShield Evidence Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 32px; color: #07111c; background: #eef5f4; }}
h1 {{ color: #062a2e; }}
.card {{ background: white; padding: 20px; margin-bottom: 14px; border-radius: 12px; border: 1px solid #d0e6e8; }}
.badge {{ display: inline-block; padding: 6px 12px; border-radius: 16px; color: white; background: #198754; }}
</style>
</head>
<body>
<h1>VoxShield Prototype Fraud Incident Report</h1>
<div class="card">
<h2>Incident Overview</h2>
<p><b>Incident ID:</b> {incident_record['incident_id']}</p>
<p><b>Timestamp:</b> {incident_record['timestamp']}</p>
<p><b>Decision:</b> {incident_record['decision']}</p>
<p><b>Risk Score:</b> {incident_record['final_risk']}/100</p>
<p><b>Risk Level:</b> {incident_record['risk_level']}</p>
</div>
<div class="card">
<h2>Transaction</h2>
<p><b>Amount:</b> ₹{incident_record['amount']}</p>
<p><b>Beneficiary:</b> {incident_record['beneficiary']}</p>
<p><b>Features:</b> {html.escape(str(incident_record.get('transaction_features','')))}</p>
</div>
<div class="card">
<h2>Indicators</h2>
<p>{html.escape(str(incident_record.get('detected_reasons','')))}</p>
</div>
<div class="card">
<h2>Voice Transcript</h2>
<p>{html.escape(str(incident_record.get('voice_transcript','')))}</p>
</div>
<div class="card">
<h2>Behavioral Indicators</h2>
<p>{html.escape(str(incident_record.get('behavior_signals','')))}</p>
</div>
<div class="card">
<h2>Context Signals</h2>
<p>{html.escape(str(incident_record.get('context_signals','')))}</p>
<p><b>Context Risk:</b> {incident_record.get('context_risk', 0)}</p>
</div>
</body>
</html>
"""
    output_path.write_text(content, encoding='utf-8')
    return str(output_path)


def generate_pdf_report(incident_record):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception:
        return None

    output_path = REPORTS_DIR / f"{incident_record['incident_id']}.pdf"
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph('VoxShield Prototype Fraud Incident Report', styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Incident ID: {incident_record['incident_id']}", styles['Normal']))
    story.append(Paragraph(f"Timestamp: {incident_record['timestamp']}", styles['Normal']))
    story.append(Paragraph(f"Decision: {incident_record['decision']}", styles['Normal']))
    story.append(Paragraph(f"Risk Score: {incident_record['final_risk']}/100", styles['Normal']))
    story.append(Paragraph(f"Risk Level: {incident_record['risk_level']}", styles['Normal']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Beneficiary: {incident_record['beneficiary']}", styles['Normal']))
    story.append(Paragraph(f"Amount: ₹{incident_record['amount']}", styles['Normal']))
    story.append(Paragraph(f"Transaction Features: {incident_record.get('transaction_features')}", styles['Normal']))
    story.append(Paragraph(f"Indicators: {incident_record.get('detected_reasons')}", styles['Normal']))
    story.append(Paragraph(f"Voice Transcript: {incident_record.get('voice_transcript')}", styles['Normal']))
    story.append(Paragraph(f"Behavior Signals: {incident_record.get('behavior_signals')}", styles['Normal']))
    story.append(Paragraph(f"Context Signals: {incident_record.get('context_signals')}", styles['Normal']))
    doc.build(story)
    return str(output_path)
