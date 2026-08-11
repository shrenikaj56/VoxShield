def calculate_behavior_risk(behavior):
    signal = behavior or {}
    risk = 0
    reasons = []

    typing_speed = signal.get('typing_speed', 'normal')
    interaction_pattern = signal.get('interaction_pattern', 'normal')
    device_familiarity = signal.get('device_familiarity', 'known')
    transaction_timing = signal.get('transaction_timing', 'normal')
    location_change = signal.get('location_change', 'none')
    rapid_actions = signal.get('rapid_repeated_actions', False)

    if typing_speed == 'fast':
        risk += 6
        reasons.append('Unusually rapid typing speed')
    elif typing_speed == 'slow':
        risk += 4
        reasons.append('Unusually slow typing speed')

    if interaction_pattern == 'unusual':
        risk += 12
        reasons.append('Unusual interaction pattern')
    elif interaction_pattern == 'rapid_navigation':
        risk += 8
        reasons.append('Rapid navigation pattern')

    if device_familiarity == 'unknown':
        risk += 10
        reasons.append('Unknown device familiarity')

    if transaction_timing == 'unusual':
        risk += 8
        reasons.append('Unusual transaction timing')

    if location_change == 'significant':
        risk += 12
        reasons.append('Location mismatch or new geography')

    if rapid_actions:
        risk += 14
        reasons.append('Rapid repeated actions')

    # Not real biometrics; this is a simulated behavioral profile.
    score = max(0, min(100, int(risk)))
    return {
        'score': score,
        'reasons': reasons,
        'signals': {
            'typing_speed': typing_speed,
            'interaction_pattern': interaction_pattern,
            'device_familiarity': device_familiarity,
            'transaction_timing': transaction_timing,
            'location_change': location_change,
            'rapid_repeated_actions': rapid_actions,
        }
    }
