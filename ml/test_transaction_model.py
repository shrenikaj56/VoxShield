from modules.transaction_ml import predict_transaction_risk


tests = [
    {
        "name": "Normal Payment",
        "type": "PAYMENT",
        "amount": 500,
        "old_origin": 10000,
        "new_origin": 9500,
        "old_dest": 5000,
        "new_dest": 5500
    },
    {
        "name": "Large Transfer",
        "type": "TRANSFER",
        "amount": 35000,
        "old_origin": 50000,
        "new_origin": 15000,
        "old_dest": 10000,
        "new_dest": 45000
    },
    {
        "name": "High Value Transfer",
        "type": "TRANSFER",
        "amount": 200000,
        "old_origin": 250000,
        "new_origin": 50000,
        "old_dest": 10000,
        "new_dest": 210000
    }
]


print("\n================================")
print("VOXSHIELD TRANSACTION ML TEST")
print("================================")

for test in tests:

    result = predict_transaction_risk(
        transaction_type=test["type"],
        amount=test["amount"],
        old_balance_origin=test["old_origin"],
        new_balance_origin=test["new_origin"],
        old_balance_destination=test["old_dest"],
        new_balance_destination=test["new_dest"]
    )

    print(f"\n{test['name']}")
    print(f"Amount            : ₹{test['amount']:,}")
    print(f"Fraud Probability : {result['fraud_probability']}")
    print(f"Risk Score        : {result['risk_score']}/100")
    print(f"Risk Level        : {result['risk_level']}")