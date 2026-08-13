import re


URGENT_PHRASES = [
    "immediately",
    "right now",
    "urgent",
    "act now",
    "do it now",
    "hurry",
    "without delay",
    "quickly",
    "send it now",
]

OTP_PHRASES = [
    "otp",
    "one time password",
    "verification code",
    "verification number",
    "security code",
]

BANK_IMPERSONATION_PHRASES = [
    "from the bank",
    "calling from the bank",
    "bank representative",
    "bank officer",
    "bank employee",
    "from your bank",
    "bank security",
    "customer care",
]

PAYMENT_PHRASES = [
    "make the payment",
    "send the money",
    "transfer the money",
    "transfer funds",
    "send money",
    "payment",
    "upi",
    "transaction",
]

REMOTE_ACCESS_PHRASES = [
    "screen share",
    "screen sharing",
    "remote access",
    "anydesk",
    "teamviewer",
    "install the app",
    "download the app",
    "share your screen",
]

THREAT_PHRASES = [
    "account will be blocked",
    "account will be closed",
    "account will be suspended",
    "legal action",
    "police",
    "arrest",
    "your account is at risk",
    "account compromised",
]


def normalize_text(text: str) -> str:
    """
    Normalize transcript text before feature extraction.
    """
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_matches(text: str, phrases: list[str]) -> list[str]:
    """
    Return phrases detected in the transcript.
    """
    return [phrase for phrase in phrases if phrase in text]


def extract_voice_features(transcript: str) -> dict:
    """
    Convert a transcript into interpretable scam-related features.

    Gemini is NOT making the fraud decision.
    This function extracts signals from Gemini's transcript.
    """

    text = normalize_text(transcript)

    urgent = find_matches(text, URGENT_PHRASES)
    otp = find_matches(text, OTP_PHRASES)
    bank_impersonation = find_matches(text, BANK_IMPERSONATION_PHRASES)
    payment = find_matches(text, PAYMENT_PHRASES)
    remote_access = find_matches(text, REMOTE_ACCESS_PHRASES)
    threats = find_matches(text, THREAT_PHRASES)

    return {
        "urgent_language": urgent,
        "otp_request": otp,
        "bank_impersonation": bank_impersonation,
        "payment_request": payment,
        "remote_access": remote_access,
        "threat_language": threats,
        "transcript_length": len(text.split()),
    }