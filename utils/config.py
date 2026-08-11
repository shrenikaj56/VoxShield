from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "voxshield.db"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
MODELS_DIR = BASE_DIR / "models"

RISK_WEIGHTS = {
    "transaction": 0.40,
    "voice": 0.30,
    "behavior": 0.20,
    "context": 0.10,
}

LOW_THRESHOLD = 40
MEDIUM_THRESHOLD = 70
RISK_LEVELS = {
    "LOW": (0, LOW_THRESHOLD - 1),
    "MEDIUM": (LOW_THRESHOLD, MEDIUM_THRESHOLD - 1),
    "HIGH": (MEDIUM_THRESHOLD, 100),
}

LANGUAGES = {
    'en': {
        'LOW_RISK': 'LOW RISK',
        'MEDIUM_RISK': 'MEDIUM RISK',
        'HIGH_RISK': 'HIGH RISK',
        'TRANSACTION_BLOCKED': 'TRANSACTION BLOCKED',
        'VERIFY_TRANSACTION': 'VERIFY TRANSACTION',
        'SUSPICIOUS_ACTIVITY': 'SUSPICIOUS ACTIVITY DETECTED',
        'DO_NOT_SHARE_OTP': 'DO NOT SHARE OTP/PIN'
    },
    'hi': {
        'LOW_RISK': 'कम जोखिम',
        'MEDIUM_RISK': 'मध्यम जोखिम',
        'HIGH_RISK': 'उच्च जोखिम',
        'TRANSACTION_BLOCKED': 'लेनदेन अवरुद्ध',
        'VERIFY_TRANSACTION': 'लेनदेन सत्यापित करें',
        'SUSPICIOUS_ACTIVITY': 'संदिग्ध गतिविधि पाई गई',
        'DO_NOT_SHARE_OTP': 'OTP/PIN साझा न करें'
    },
    'ta': {
        'LOW_RISK': 'குறைந்த ஆபத்து',
        'MEDIUM_RISK': 'மிதமான ஆபத்து',
        'HIGH_RISK': 'உயர் ஆபத்து',
        'TRANSACTION_BLOCKED': 'பரிவர்த்தனைத் தடுக்கப்பட்டது',
        'VERIFY_TRANSACTION': 'பரிவர்த்தனையை உறுதிப்படுத்தவும்',
        'SUSPICIOUS_ACTIVITY': 'சந்தேகமான செயல்பாடு கண்டறியப்பட்டது',
        'DO_NOT_SHARE_OTP': 'OTP/PIN-ஐப் பகிர வேண்டாம்'
    }
}

TRANSACTION_WEIGHTS = {
    "amount": 24,
    "beneficiary_new": 18,
    "transaction_frequency": 10,
    "transaction_time": 10,
    "device_known": 12,
    "location_anomaly": 12,
    "previous_fraud_history": 14,
}

VOICE_WEIGHTS = {
    "urgency": 7,
    "threat": 11,
    "impersonation": 11,
    "otp_request": 15,
    "financial_pressure": 12,
    "account_suspension": 10,
    "digital_arrest": 12,
    "payment_instruction": 11,
    "coercive_language": 10,
}

DEFAULT_SCENARIOS = {
    "SAFE": {
        "amount": 500,
        "beneficiary_type": "known",
        "device_known": True,
        "transaction_time": "normal",
        "location_anomaly": False,
        "transaction_frequency": "regular",
        "beneficiary_new": False,
        "transaction_channel": "upi",
        "previous_fraud_history": False,
        "normal_behavior": True,
        "voice_transcript": "I’m calling to confirm a normal monthly payment."
    },
    "SUSPICIOUS": {
        "amount": 15000,
        "beneficiary_type": "new",
        "device_known": False,
        "transaction_time": "unusual",
        "location_anomaly": True,
        "transaction_frequency": "rare",
        "beneficiary_new": True,
        "transaction_channel": "upi",
        "previous_fraud_history": False,
        "normal_behavior": False,
        "voice_transcript": "Please complete this urgently before the system refreshes.",
        "context": {
            "suspicious_call": True,
            "screen_sharing": False,
            "remote_control": False,
            "unknown_caller": True
        }
    },
    "HIGH_RISK": {
        "amount": 35000,
        "beneficiary_type": "new",
        "device_known": False,
        "transaction_time": "unusual",
        "location_anomaly": True,
        "transaction_frequency": "rare",
        "beneficiary_new": True,
        "transaction_channel": "upi",
        "previous_fraud_history": True,
        "normal_behavior": False,
        "voice_transcript": "Your bank account has been flagged for suspicious activity. Your account will be blocked unless you complete verification immediately. Transfer the money to the secure account now. Do not disconnect the call and do not contact anyone else. Legal action may be taken if you fail to comply.",
        "context": {
            "suspicious_call": True,
            "screen_sharing": True,
            "remote_control": True,
            "unknown_caller": True
        }
    }
}
