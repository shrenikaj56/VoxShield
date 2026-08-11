from utils.config import TRANSACTION_WEIGHTS


def calculate_transaction_risk(transaction):
    amount = float(transaction.get('amount', 0) or 0)
    beneficiary_new = bool(transaction.get('beneficiary_new', False))
    frequency = transaction.get('transaction_frequency', 'regular')
    transaction_time = transaction.get('transaction_time', 'normal')
    device_known = bool(transaction.get('device_known', False))
    location_anomaly = bool(transaction.get('location_anomaly', False))
    previous_fraud_history = bool(transaction.get('previous_fraud_history', False))

    score = 0
    reasons = []

    if amount > 25000:
        score += min(25, TRANSACTION_WEIGHTS['amount'])
        reasons.append('High amount anomaly')
    elif amount > 10000:
        score += 12
        reasons.append('Large transfer amount')
    elif amount <= 1000:
        score += 2
        reasons.append('Low-value transaction remains low signal')

    if beneficiary_new:
        score += TRANSACTION_WEIGHTS['beneficiary_new']
        reasons.append('New beneficiary')

    if frequency == 'rare':
        score += TRANSACTION_WEIGHTS['transaction_frequency']
        reasons.append('Infrequent beneficiary pattern')

    if transaction_time in ('unusual', 'after_hours'):
        score += TRANSACTION_WEIGHTS['transaction_time']
        reasons.append('Unusual transaction time')

    if not device_known:
        score += TRANSACTION_WEIGHTS['device_known']
        reasons.append('Unknown device used')

    if location_anomaly:
        score += TRANSACTION_WEIGHTS['location_anomaly']
        reasons.append('Location anomaly detected')

    if previous_fraud_history:
        score += TRANSACTION_WEIGHTS['previous_fraud_history']
        reasons.append('Prior fraud or suspicious activity history')

    # clamp between 0 and 100
    score = max(0, min(100, int(score)))
    return {
        'score': score,
        'reasons': reasons,
        'features': {
            'amount': amount,
            'beneficiary_new': beneficiary_new,
            'transaction_frequency': frequency,
            'transaction_time': transaction_time,
            'device_known': device_known,
            'location_anomaly': location_anomaly,
            'previous_fraud_history': previous_fraud_history,
        }
    }
