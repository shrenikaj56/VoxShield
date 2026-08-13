from modules.voice_features import extract_voice_features


def calculate_voice_risk(features: dict) -> int:
    """
    Calculate a prototype voice scam risk score from 0 to 100.

    This is an interpretable prototype scoring model.
    It is NOT a trained ML model yet.
    """

    score = 0

    if features["urgent_language"]:
        score += 20

    if features["otp_request"]:
        score += 30

    if features["bank_impersonation"]:
        score += 15

    if features["payment_request"]:
        score += 15

    if features["remote_access"]:
        score += 25

    if features["threat_language"]:
        score += 20

    return min(score, 100)


def get_risk_level(score: int) -> str:
    if score >= 70:
        return "HIGH"

    if score >= 40:
        return "MEDIUM"

    return "LOW"


def analyze_voice(transcript: str) -> dict:
    """
    Main Voice Analyzer.

    Input:
        transcript produced by Gemini

    Output:
        voice risk score, level and detected reasons
    """

    features = extract_voice_features(transcript)

    score = calculate_voice_risk(features)

    level = get_risk_level(score)

    reasons = []

    if features["urgent_language"]:
        reasons.append(
            "Urgent or pressure-based language detected."
        )

    if features["otp_request"]:
        reasons.append(
            "OTP or verification code request detected."
        )

    if features["bank_impersonation"]:
        reasons.append(
            "Possible bank impersonation detected."
        )

    if features["payment_request"]:
        reasons.append(
            "Payment or money-transfer request detected."
        )

    if features["remote_access"]:
        reasons.append(
            "Remote-access or screen-sharing request detected."
        )

    if features["threat_language"]:
        reasons.append(
            "Threat or account-blocking language detected."
        )

    return {
        "score": score,
        "level": level,
        "features": features,
        "reasons": reasons,
        "transcript": transcript,
    }