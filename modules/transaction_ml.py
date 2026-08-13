import os
import joblib
import pandas as pd


# ---------------------------------------------------------
# Model configuration
# ---------------------------------------------------------

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "models",
    "transaction_fraud_model.pkl"
)


# ---------------------------------------------------------
# Load trained model
# ---------------------------------------------------------

_model = None


def load_transaction_model():
    """
    Load the trained PaySim fraud detection model.
    The model is loaded only once.
    """
    global _model

    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Transaction model not found: {MODEL_PATH}"
            )

        _model = joblib.load(MODEL_PATH)

    return _model


# ---------------------------------------------------------
# Transaction risk prediction
# ---------------------------------------------------------

def predict_transaction_risk(
    transaction_type,
    amount,
    old_balance_origin,
    new_balance_origin,
    old_balance_destination,
    new_balance_destination
):
    """
    Predict fraud probability for a transaction.

    Returns:
        {
            'fraud_probability': float,
            'risk_score': int,
            'risk_level': str
        }
    """

    model = load_transaction_model()

    transaction = pd.DataFrame([
        {
            "type": transaction_type,
            "amount": float(amount),
            "oldbalanceOrg": float(old_balance_origin),
            "newbalanceOrig": float(new_balance_origin),
            "oldbalanceDest": float(old_balance_destination),
            "newbalanceDest": float(new_balance_destination)
        }
    ])

    # Probability of fraud
    probability = float(
        model.predict_proba(transaction)[0][1]
    )

    # Convert probability into 0-100 risk score
    risk_score = round(probability * 100)

    # Risk classification
    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "fraud_probability": round(probability, 4),
        "risk_score": risk_score,
        "risk_level": risk_level
    }