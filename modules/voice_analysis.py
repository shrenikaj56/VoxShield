import os
import re

VOICE_RULES = {
    'urgency': ['urgent', 'immediately', 'asap', 'today', 'now', 'right away'],
    'threat': ['blocked', 'penalty', 'account will be closed', 'will be suspended', 'won’t allow', 'threat'],
    'impersonation': ['i am from', 'bank representative', 'customer care', 'branch manager', 'police', 'official'],
    'otp_request': ['otp', 'one time password', 'pin', 'sms code', 'authorization code'],
    'financial_pressure': ['payment', 'transfer', 'send money', 'upi', 'credit', 'debit'],
    'account_suspension': ['account will be suspended', 'suspended', 'freeze', 'locked'],
    'digital_arrest': ['digital arrest', 'under investigation', 'police complaint', 'investigation', 'cyber crime'],
    'payment_instruction': ['send money', 'make payment', 'upi id', 'qr code', 'scan this'],
    'coercive_language': ['or else', 'do it now', 'otherwise', 'send it', 'urgent'],
}


def analyze_voice(transcript, api_key=None):
    normalized = (transcript or '').strip().lower()
    if not normalized:
        return {
            'score': 0,
            'reasons': [],
            'method': 'fallback',
            'transcript': ''
        }

    matched = []
    features = {}
    for label, phrases in VOICE_RULES.items():
        label_hits = [p for p in phrases if p in normalized]
        if label_hits:
            matched.append(label)
            features[label] = True
        else:
            features[label] = False

    score = 0
    reasons = []
    if 'urgency' in matched:
        score += 5
        reasons.append('Urgency detected')
    if 'threat' in matched:
        score += 11
        reasons.append('Threat or suspension language')
    if 'impersonation' in matched:
        score += 12
        reasons.append('Impersonation or authority claim detected')
    if 'otp_request' in matched:
        score += 16
        reasons.append('OTP/PIN request detected')
    if 'financial_pressure' in matched:
        score += 12
        reasons.append('Financial pressure/payment instruction detected')
    if 'account_suspension' in matched:
        score += 12
        reasons.append('Account suspension claim detected')
    if 'digital_arrest' in matched:
        score += 13
        reasons.append('Digital arrest pattern detected')
    if 'payment_instruction' in matched:
        score += 15
        reasons.append('Suspicious payment instruction')
    if 'coercive_language' in matched:
        score += 7
        reasons.append('Coercive language')

    if matched:
        score = min(100, score)
        method = 'rule-based fallback' if not api_key else 'api-assisted'
    else:
        method = 'fallback' if not api_key else 'api-assisted'

    return {
        'score': int(score),
        'reasons': reasons,
        'method': method,
        'transcript': transcript,
        'matched': matched,
    }


def audio_to_transcript(audio_path=None, transcript_text=None):
    if transcript_text:
        return transcript_text

    if not audio_path:
        return ''

    # Graceful fallback: no Whisper/OpenAI package assumptions.
    try:
        import whisper
        model = whisper.load_model('base')
        result = model.transcribe(audio_path)
        return result.get('text', '')
    except Exception:
        return ''
