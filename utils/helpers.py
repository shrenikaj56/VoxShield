from datetime import datetime
import uuid


def now_iso():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def incident_id():
    return f"VS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def risk_level(score):
    if score < 40:
        return "LOW"
    if score < 70:
        return "MEDIUM"
    return "HIGH"


def decision_for_risk_level(risk_level_value):
    if risk_level_value == "LOW":
        return "ALLOW"
    if risk_level_value == "MEDIUM":
        return "WARN + VERIFY"
    return "BLOCK + REPORT"
