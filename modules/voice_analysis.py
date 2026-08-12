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


def audio_to_transcript(audio_path=None, transcript_text=None, api_key=None):
    """
    Convert uploaded audio into text using Gemini.
    If transcript text is already provided, use it directly.
    """

    if transcript_text and transcript_text.strip():
        return transcript_text.strip()

    if not audio_path:
        return ''

    api_key = api_key or os.getenv('GEMINI_API_KEY')

    if not api_key:
        return ''

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        uploaded_file = client.files.upload(file=audio_path)

        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[
                'Generate an accurate transcript of this audio. '
                'Return only the spoken words. '
                'Do not summarize or explain.',
                uploaded_file
            ]
        )

        return (response.text or '').strip()

    except Exception as e:
        print(f'Gemini audio transcription error: {e}')
        return ''