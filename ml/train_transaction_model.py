import os
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score
)
import joblib


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DATA_PATH = "data/PS_20174392719_1491204439457_log.csv"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "transaction_fraud_model.pkl")


# ---------------------------------------------------------
# Load dataset
# ---------------------------------------------------------

print("Loading PaySim dataset...")

df = pd.read_csv(DATA_PATH)

print(f"Dataset loaded: {df.shape}")


# ---------------------------------------------------------
# Select relevant features
# ---------------------------------------------------------

FEATURES = [
    "type",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest"
]

TARGET = "isFraud"

X = df[FEATURES]
y = df[TARGET]


# ---------------------------------------------------------
# Train/Test split
# ---------------------------------------------------------

print("Splitting dataset...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print(f"Training samples: {len(X_train)}")
print(f"Testing samples: {len(X_test)}")


# ---------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------

categorical_features = ["type"]

numeric_features = [
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest"
]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features
        ),
        (
            "numeric",
            "passthrough",
            numeric_features
        )
    ]
)


# ---------------------------------------------------------
# Random Forest model
# ---------------------------------------------------------

print("Building Random Forest model...")

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=12,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)


# ---------------------------------------------------------
# Complete ML pipeline
# ---------------------------------------------------------

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("classifier", model)
    ]
)


# ---------------------------------------------------------
# Train
# ---------------------------------------------------------

print("Training model...")
print("This may take some time because the dataset contains over 6 million rows.")

pipeline.fit(X_train, y_train)

print("Training completed.")


# ---------------------------------------------------------
# Predictions
# ---------------------------------------------------------

print("Evaluating model...")

y_pred = pipeline.predict(X_test)
y_probability = pipeline.predict_proba(X_test)[:, 1]


# ---------------------------------------------------------
# Evaluation
# ---------------------------------------------------------

print("\n==============================")
print("MODEL EVALUATION")
print("==============================")

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nROC-AUC Score:")
print(round(roc_auc_score(y_test, y_probability), 4))


# ---------------------------------------------------------
# Save model
# ---------------------------------------------------------

os.makedirs(MODEL_DIR, exist_ok=True)

joblib.dump(pipeline, MODEL_PATH)

print("\n==============================")
print("MODEL SAVED")
print("==============================")
print(f"Model path: {MODEL_PATH}")