def calculate_context_risk(context):
    """Prototype simulated context assessment.
    This is not actual device or call interception; it mirrors UI-driven
    simulated call/screen-sharing signals.
    """
    signals = context or {}
    risk = 0
    reasons = []

    suspicious_call = bool(signals.get('suspicious_call', False))
    screen_sharing = bool(signals.get('screen_sharing', False))
    remote_control = bool(signals.get('remote_control', False))
    unknown_caller = bool(signals.get('unknown_caller', False))

    if suspicious_call:
        risk += 24
        reasons.append('Suspicious active call')
    if screen_sharing:
        risk += 20
        reasons.append('Screen sharing active')
    if remote_control:
        risk += 26
        reasons.append('Remote-control session detected')
    if unknown_caller:
        risk += 14
        reasons.append('Unknown caller / caller not recognized')

    # Normalization to 0-100 for context signals.
    score = max(0, min(100, int(risk)))
    return {
        'score': score,
        'reasons': reasons,
        'signals': {
            'suspicious_call': suspicious_call,
            'screen_sharing': screen_sharing,
            'remote_control': remote_control,
            'unknown_caller': unknown_caller,
        }
    }
