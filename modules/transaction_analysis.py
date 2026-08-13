from utils.config import TRANSACTION_WEIGHTS
from modules.transaction_ml import predict_transaction_risk


def calculate_transaction_risk(transaction):
    """
    Calculate transaction risk using:
    1. PaySim-trained ML fraud model
    2. Existing VoxShield contextual transaction signals

    The ML model provides the primary transaction score.
    Existing contextual signals provide additional adaptive
    protection and explanation.
    """

    # ---------------------------------------------------------
    # Read existing VoxShield transaction inputs
    # ---------------------------------------------------------

    amount = float(
        transaction.get('amount', 0) or 0
    )

    beneficiary_new = bool(
        transaction.get('beneficiary_new', False)
    )

    frequency = transaction.get(
        'transaction_frequency',
        'regular'
    )

    transaction_time = transaction.get(
        'transaction_time',
        'normal'
    )

    device_known = bool(
        transaction.get('device_known', False)
    )

    location_anomaly = bool(
        transaction.get('location_anomaly', False)
    )

    previous_fraud_history = bool(
        transaction.get('previous_fraud_history', False)
    )

    # ---------------------------------------------------------
    # PaySim-compatible transaction information
    # ---------------------------------------------------------
    #
    # The current VoxShield payment UI does not expose actual
    # bank balance fields. Therefore, for this prototype,
    # consistent PaySim-style values are derived from the
    # transaction amount.
    #
    # UPI security payments are mapped internally to TRANSFER
    # because PaySim's fraud examples are concentrated in
    # TRANSFER and CASH_OUT transactions.
    # ---------------------------------------------------------

    transaction_type = transaction.get(
        'transaction_type',
        'TRANSFER'
    )

    old_balance_origin = float(
        transaction.get(
            'oldbalanceOrg',
            max(amount * 2, amount + 1000)
        )
    )

    new_balance_origin = float(
        transaction.get(
            'newbalanceOrig',
            max(
                0,
                old_balance_origin - amount
            )
        )
    )

    old_balance_destination = float(
        transaction.get(
            'oldbalanceDest',
            0
        )
    )

    new_balance_destination = float(
        transaction.get(
            'newbalanceDest',
            old_balance_destination + amount
        )
    )

    # ---------------------------------------------------------
    # MACHINE LEARNING TRANSACTION RISK
    # ---------------------------------------------------------

    try:
        ml_result = predict_transaction_risk(
            transaction_type=transaction_type,
            amount=amount,
            old_balance_origin=old_balance_origin,
            new_balance_origin=new_balance_origin,
            old_balance_destination=old_balance_destination,
            new_balance_destination=new_balance_destination
        )

        ml_score = int(
            ml_result['risk_score']
        )

        fraud_probability = float(
            ml_result['fraud_probability']
        )

        ml_risk_level = ml_result[
            'risk_level'
        ]

        ml_available = True

    except Exception:
        # Keep VoxShield operational if the ML model
        # is unavailable.

        ml_score = 0
        fraud_probability = 0.0
        ml_risk_level = 'LOW'
        ml_available = False

    # ---------------------------------------------------------
    # Existing contextual transaction signals
    # ---------------------------------------------------------

    context_score = 0
    reasons = []

    # ---------------------------------------------------------
    # Amount signal
    # ---------------------------------------------------------

    if amount > 25000:

        context_score += min(
            25,
            TRANSACTION_WEIGHTS['amount']
        )

        reasons.append(
            'High amount anomaly'
        )

    elif amount > 10000:

        context_score += 12

        reasons.append(
            'Large transfer amount'
        )

    elif amount <= 1000:

        context_score += 2

        reasons.append(
            'Low-value transaction remains low signal'
        )

    # ---------------------------------------------------------
    # New beneficiary
    # ---------------------------------------------------------

    if beneficiary_new:

        context_score += TRANSACTION_WEIGHTS[
            'beneficiary_new'
        ]

        reasons.append(
            'New beneficiary'
        )

    # ---------------------------------------------------------
    # Transaction frequency
    # ---------------------------------------------------------

    if frequency == 'rare':

        context_score += TRANSACTION_WEIGHTS[
            'transaction_frequency'
        ]

        reasons.append(
            'Infrequent beneficiary pattern'
        )

    # ---------------------------------------------------------
    # Transaction time
    # ---------------------------------------------------------

    if transaction_time in (
        'unusual',
        'after_hours'
    ):

        context_score += TRANSACTION_WEIGHTS[
            'transaction_time'
        ]

        reasons.append(
            'Unusual transaction time'
        )

    # ---------------------------------------------------------
    # Device
    # ---------------------------------------------------------

    if not device_known:

        context_score += TRANSACTION_WEIGHTS[
            'device_known'
        ]

        reasons.append(
            'Unknown device used'
        )

    # ---------------------------------------------------------
    # Location
    # ---------------------------------------------------------

    if location_anomaly:

        context_score += TRANSACTION_WEIGHTS[
            'location_anomaly'
        ]

        reasons.append(
            'Location anomaly detected'
        )

    # ---------------------------------------------------------
    # Previous fraud history
    # ---------------------------------------------------------

    if previous_fraud_history:

        context_score += TRANSACTION_WEIGHTS[
            'previous_fraud_history'
        ]

        reasons.append(
            'Prior fraud or suspicious activity history'
        )

    # ---------------------------------------------------------
    # Combine ML score + contextual transaction signals
    # ---------------------------------------------------------

    if ml_available:

        # Keep the contextual component capped.
        # The ML model remains the primary transaction signal.

        context_score = min(
            30,
            int(context_score)
        )

        # -----------------------------------------------------
        # Base transaction risk
        # -----------------------------------------------------

        transaction_score = int(
            round(
                (ml_score * 0.75)
                +
                (context_score * 0.25)
            )
        )

        # -----------------------------------------------------
        # Strong contextual escalation
        # -----------------------------------------------------
        #
        # VoxShield is a multi-signal fraud protection system.
        #
        # If several independent anomalies occur together,
        # the transaction should not remain LOW merely because
        # the synthetic PaySim-compatible input receives a low
        # ML probability.
        #
        # This does NOT modify or retrain the ML model.
        # It only affects the VoxShield transaction protection
        # decision.
        # -----------------------------------------------------

        strong_context_signals = sum([
            beneficiary_new,
            frequency == 'rare',
            transaction_time in (
                'unusual',
                'after_hours'
            ),
            not device_known,
            location_anomaly,
            previous_fraud_history
        ])

        # -----------------------------------------------------
        # 4 or more independent anomalies
        # -----------------------------------------------------

        if strong_context_signals >= 4:

            transaction_score = max(
                transaction_score,
                75
            )

            reasons.append(
                'Multiple independent security anomalies detected'
            )

        # -----------------------------------------------------
        # 3 independent anomalies
        # -----------------------------------------------------

        elif strong_context_signals >= 3:

            transaction_score = max(
                transaction_score,
                55
            )

            reasons.append(
                'Multiple transaction security anomalies detected'
            )

        # -----------------------------------------------------
        # High-value + new beneficiary
        # -----------------------------------------------------

        if amount >= 25000 and beneficiary_new:

            transaction_score = max(
                transaction_score,
                70
            )

            reasons.append(
                'High-value payment to a new beneficiary'
            )

        # -----------------------------------------------------
        # Final transaction score limits
        # -----------------------------------------------------

        transaction_score = max(
            0,
            min(
                100,
                int(transaction_score)
            )
        )

        # -----------------------------------------------------
        # ML explanation
        # -----------------------------------------------------

        reasons.insert(
            0,
            f'ML fraud probability: '
            f'{fraud_probability:.2%}'
        )

        reasons.insert(
            1,
            f'ML transaction risk: '
            f'{ml_score}/100 ({ml_risk_level})'
        )

    else:

        # -----------------------------------------------------
        # Fallback to rule-based transaction analysis
        # -----------------------------------------------------

        transaction_score = max(
            0,
            min(
                100,
                int(context_score)
            )
        )

        reasons.insert(
            0,
            'ML model unavailable; '
            'rule-based transaction analysis used'
        )

    # ---------------------------------------------------------
    # Return structure expected by VoxShield
    # ---------------------------------------------------------

    return {

        'score': int(
            transaction_score
        ),

        'reasons': reasons,

        'features': {

            'amount': amount,

            'transaction_type': transaction_type,

            'beneficiary_new': beneficiary_new,

            'transaction_frequency': frequency,

            'transaction_time': transaction_time,

            'device_known': device_known,

            'location_anomaly': location_anomaly,

            'previous_fraud_history': previous_fraud_history,

            # PaySim / ML information

            'ml_fraud_probability': fraud_probability,

            'ml_risk_score': ml_score,

            'ml_risk_level': ml_risk_level,

            'context_score': int(
                context_score
            ),

            'ml_model_used': ml_available
        }
    }