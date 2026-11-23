
import joblib
import pandas as pd

from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_FILE = BASE_DIR / "models" / "category_classifier.joblib"

REPORT_DIR = BASE_DIR / "ml" / "reports"

OUTPUT_FILE = REPORT_DIR / "custom_message_test_results.csv"


# ==========================================
# 2. LOAD TRAINED MODEL
# ==========================================

print("\n===== LOADING TRAINED MODEL =====")

if not MODEL_FILE.exists():
    raise FileNotFoundError(
        f"Trained model not found: {MODEL_FILE}"
    )

model = joblib.load(MODEL_FILE)

print("Model loaded successfully!")


# ==========================================
# 3. CREATE ORIGINAL TEST MESSAGES
# ==========================================

print("\n===== CUSTOM CUSTOMER MESSAGES =====")

test_data = [

    # ACCOUNT
    {
        "message": "hey i cant log into my acc",
        "expected_category": "ACCOUNT"
    },
    {
        "message": "forgot my passwrd how can i reset it",
        "expected_category": "ACCOUNT"
    },

    # CANCEL
    {
        "message": "pls cancel my order asap",
        "expected_category": "CANCEL"
    },
    {
        "message": "i dont want this order anymore cancel it",
        "expected_category": "CANCEL"
    },

    # PAYMENT
    {
        "message": "money got deducted twice from my card",
        "expected_category": "PAYMENT"
    },
    {
        "message": "payment failed but amount was taken",
        "expected_category": "PAYMENT"
    },

    # DELIVERY
    {
        "message": "my parcel still hasnt arrived",
        "expected_category": "DELIVERY"
    },
    {
        "message": "where is my package its very late",
        "expected_category": "DELIVERY"
    },

    # REFUND
    {
        "message": "can i get my money back pls",
        "expected_category": "REFUND"
    },
    {
        "message": "i returned the item but no refund yet",
        "expected_category": "REFUND"
    },

    # SHIPPING
    {
        "message": "can u update my delivery adress",
        "expected_category": "SHIPPING"
    },
    {
        "message": "need to change the shipping adress",
        "expected_category": "SHIPPING"
    },

    # ORDER
    {
        "message": "where can i see my order details",
        "expected_category": "ORDER"
    },
    {
        "message": "i placed an order but cant find it",
        "expected_category": "ORDER"
    },

    # INVOICE
    {
        "message": "can u send me the invoice again",
        "expected_category": "INVOICE"
    },
    {
        "message": "need a copy of my bill for last purchase",
        "expected_category": "INVOICE"
    },

    # CONTACT
    {
        "message": "how do i speak to a real support agent",
        "expected_category": "CONTACT"
    },
    {
        "message": "is there a phone number to contact u",
        "expected_category": "CONTACT"
    },

    # FEEDBACK
    {
        "message": "really happy with the service thank u",
        "expected_category": "FEEDBACK"
    },

    # SUBSCRIPTION
    {
        "message": "how can i stop my monthly subscription",
        "expected_category": "SUBSCRIPTION"
    }

]


# ==========================================
# 4. PREPARE TEST DATA
# ==========================================

df = pd.DataFrame(test_data)

messages = df["message"]
expected = df["expected_category"]

print("Total custom messages:", len(df))
print("Expected categories:", df["expected_category"].nunique())


# ==========================================
# 5. PREDICT CATEGORIES
# ==========================================

print("\n===== PREDICTING CATEGORIES =====")

predictions = model.predict(messages)

probabilities = model.predict_proba(messages)

confidence_scores = probabilities.max(axis=1)

df["predicted_category"] = predictions

df["confidence"] = confidence_scores.round(4)

df["result"] = (
    df["expected_category"] == df["predicted_category"]
).map({
    True: "Correct",
    False: "Incorrect"
})


# ==========================================
# 6. DISPLAY RESULTS
# ==========================================

print("\n===== CUSTOM MESSAGE TEST RESULTS =====")

for index, row in df.iterrows():

    print("\nMessage:", row["message"])

    print("Expected:", row["expected_category"])

    print("Predicted:", row["predicted_category"])

    print(
        "Confidence:",
        f"{row['confidence']:.2%}"
    )

    print("Result:", row["result"])


# ==========================================
# 7. CALCULATE ACCURACY
# ==========================================

print("\n===== CUSTOM TEST EVALUATION =====")

accuracy = accuracy_score(
    expected,
    predictions
)

correct = (expected == predictions).sum()

incorrect = len(df) - correct

print("Total messages:", len(df))

print("Correct predictions:", correct)

print("Incorrect predictions:", incorrect)

print(f"Custom test accuracy: {accuracy:.2%}")


# ==========================================
# 8. CLASSIFICATION REPORT
# ==========================================

print("\n===== CLASSIFICATION REPORT =====")

print(
    classification_report(
        expected,
        predictions,
        zero_division=0
    )
)


# ==========================================
# 9. WRONG PREDICTIONS
# ==========================================

print("\n===== INCORRECT PREDICTIONS =====")

wrong_predictions = df[
    df["result"] == "Incorrect"
]

if wrong_predictions.empty:

    print("No incorrect predictions!")

else:

    print(
        wrong_predictions[
            [
                "message",
                "expected_category",
                "predicted_category",
                "confidence"
            ]
        ].to_string(index=False)
    )


# ==========================================
# 10. SAVE RESULTS
# ==========================================

REPORT_DIR.mkdir(parents=True, exist_ok=True)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n===== RESULTS SAVED =====")

print("File:", OUTPUT_FILE)

print("\n===== CUSTOM MESSAGE TEST COMPLETED =====")
