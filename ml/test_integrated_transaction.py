from modules.transaction_analysis import calculate_transaction_risk


tests = [

    {
        'name': 'Normal Payment',
        'amount': 500,
        'beneficiary_new': False,
        'transaction_frequency': 'regular',
        'transaction_time': 'normal',
        'device_known': True,
        'location_anomaly': False,
        'previous_fraud_history': False
    },

    {
        'name': 'New Beneficiary Payment',
        'amount': 5000,
        'beneficiary_new': True,
        'transaction_frequency': 'rare',
        'transaction_time': 'normal',
        'device_known': True,
        'location_anomaly': False,
        'previous_fraud_history': False
    },

    {
        'name': 'High Risk Payment',
        'amount': 35000,
        'beneficiary_new': True,
        'transaction_frequency': 'rare',
        'transaction_time': 'after_hours',
        'device_known': False,
        'location_anomaly': True,
        'previous_fraud_history': False
    }
]


print()
print('======================================')
print('VOXSHIELD INTEGRATED TRANSACTION TEST')
print('======================================')


for test in tests:

    result = calculate_transaction_risk(test)

    print()
    print('--------------------------------------')
    print(test['name'])
    print('--------------------------------------')

    print(
        f"Amount              : "
        f"₹{test['amount']:,}"
    )

    print(
        f"ML Probability      : "
        f"{result['features']['ml_fraud_probability']}"
    )

    print(
        f"ML Risk             : "
        f"{result['features']['ml_risk_score']}/100"
    )

    print(
        f"Context Risk        : "
        f"{result['features']['context_score']}/100"
    )

    print(
        f"Final Transaction   : "
        f"{result['score']}/100"
    )

    print(
        f"ML Model Used       : "
        f"{result['features']['ml_model_used']}"
    )

    print('Reasons:')

    for reason in result['reasons']:
        print(f' - {reason}')