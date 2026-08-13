import pandas as pd

from modules.transaction_ml import predict_transaction_risk


DATA_PATH = "data/PS_20174392719_1491204439457_log.csv"

print("Loading PaySim dataset...")

df = pd.read_csv(DATA_PATH)

# Select actual non-fraud transactions
normal_df = df[df["isFraud"] == 0].head(10)

print("\n================================")
print("VOXSHIELD REAL NORMAL TEST")
print("================================")

for index, row in normal_df.iterrows():

    result = predict_transaction_risk(
        transaction_type=row["type"],
        amount=row["amount"],
        old_balance_origin=row["oldbalanceOrg"],
        new_balance_origin=row["newbalanceOrig"],
        old_balance_destination=row["oldbalanceDest"],
        new_balance_destination=row["newbalanceDest"]
    )

    print("\n--------------------------------")
    print(f"PaySim Row        : {index}")
    print(f"Actual Fraud      : {row['isFraud']}")
    print(f"Transaction Type  : {row['type']}")
    print(f"Amount            : ₹{row['amount']:,.2f}")
    print(f"Model Probability : {result['fraud_probability']}")
    print(f"Model Risk Score  : {result['risk_score']}/100")
    print(f"Model Risk Level  : {result['risk_level']}")