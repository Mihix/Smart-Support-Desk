
import re
import warnings
import joblib
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support
)


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = BASE_DIR / "data" / "cleaned_dataset.csv"
DUPLICATE_FILE = BASE_DIR / "data" / "reports" / "near_duplicates.csv"

MODEL_DIR = BASE_DIR / "models"
REPORT_DIR = BASE_DIR / "ml" / "reports"

MODEL_FILE = MODEL_DIR / "category_classifier.joblib"

RANDOM_STATE = 42
SIMILARITY_THRESHOLD = 0.90


# ==========================================
# 2. TEXT NORMALIZATION
# ==========================================

def normalize_text(text):
    """Normalize text consistently for grouping and training."""

    text = str(text).lower().strip()
    text = re.sub(r"\s+", " ", text)

    return text


# ==========================================
# 3. UNION-FIND FOR MESSAGE GROUPING
# ==========================================

class UnionFind:

    def __init__(self, items):
        self.parent = {item: item for item in items}
        self.rank = {item: 0 for item in items}

    def find(self, item):

        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])

        return self.parent[item]

    def union(self, item1, item2):

        root1 = self.find(item1)
        root2 = self.find(item2)

        if root1 == root2:
            return

        if self.rank[root1] < self.rank[root2]:
            root1, root2 = root2, root1

        self.parent[root2] = root1

        if self.rank[root1] == self.rank[root2]:
            self.rank[root1] += 1


# ==========================================
# 4. LOAD DATASET
# ==========================================

print("\n===== LOADING DATASET =====")

df = pd.read_csv(DATA_FILE)

required_columns = {"instruction", "category"}

if not required_columns.issubset(df.columns):
    raise ValueError(
        f"Dataset must contain columns: {required_columns}"
    )

df = df.dropna(subset=["instruction", "category"]).copy()

df["instruction"] = df["instruction"].astype(str)
df["category"] = df["category"].astype(str).str.strip().str.upper()

df["normalized_message"] = df["instruction"].apply(normalize_text)

# Remove empty messages
df = df[df["normalized_message"] != ""].copy()

# Reset index
df = df.reset_index(drop=True)

print("Dataset shape:", df.shape)
print("Number of categories:", df["category"].nunique())

print("\nCategory distribution:")
print(df["category"].value_counts())


# ==========================================
# 5. GROUP EXACT AND NEAR-DUPLICATE MESSAGES
# ==========================================

print("\n===== GROUPING SIMILAR MESSAGES =====")

unique_messages = df["normalized_message"].unique()

uf = UnionFind(unique_messages)

message_set = set(unique_messages)

# Exact duplicates are already connected because identical messages
# have the same normalized text.

near_duplicate_pairs = 0

if DUPLICATE_FILE.exists():

    duplicate_df = pd.read_csv(DUPLICATE_FILE)

    required_pair_columns = {
        "message_1",
        "message_2",
        "similarity"
    }

    if required_pair_columns.issubset(duplicate_df.columns):

        duplicate_df["similarity"] = pd.to_numeric(
            duplicate_df["similarity"],
            errors="coerce"
        )

        duplicate_df = duplicate_df[
            duplicate_df["similarity"] >= SIMILARITY_THRESHOLD
        ]

        for _, row in duplicate_df.iterrows():

            message1 = normalize_text(row["message_1"])
            message2 = normalize_text(row["message_2"])

            if message1 in message_set and message2 in message_set:

                uf.union(message1, message2)
                near_duplicate_pairs += 1

        print("Near-duplicate pairs used:", near_duplicate_pairs)

    else:

        print(
            "WARNING: Near-duplicate report has unexpected columns."
        )
        print("Available columns:", list(duplicate_df.columns))
        print("Using exact-message grouping only.")

else:

    print("WARNING: Near-duplicate report not found.")
    print("Using exact-message grouping only.")


# Give every message a group ID
df["group_id"] = df["normalized_message"].apply(uf.find)

print("Unique messages:", len(unique_messages))
print("Total groups:", df["group_id"].nunique())


# ==========================================
# 6. TRAIN / TEST SPLIT
# ==========================================

print("\n===== TRAIN / TEST SPLIT =====")

X = df["normalized_message"]
y = df["category"]
groups = df["group_id"]

splitter = StratifiedGroupKFold(
    n_splits=5,
    shuffle=True,
    random_state=RANDOM_STATE
)

train_indices, test_indices = next(
    splitter.split(X, y, groups)
)

X_train = X.iloc[train_indices]
X_test = X.iloc[test_indices]

y_train = y.iloc[train_indices]
y_test = y.iloc[test_indices]

train_groups = set(groups.iloc[train_indices])
test_groups = set(groups.iloc[test_indices])

if train_groups.intersection(test_groups):
    raise RuntimeError("Data leakage detected: groups overlap!")

missing_train = set(y.unique()) - set(y_train.unique())

if missing_train:
    raise RuntimeError(
        f"Some categories are missing from training: {missing_train}"
    )

print("Training messages:", len(X_train))
print("Testing messages:", len(X_test))

print(
    "Training percentage:",
    round(len(X_train) / len(df) * 100, 2),
    "%"
)

print(
    "Testing percentage:",
    round(len(X_test) / len(df) * 100, 2),
    "%"
)

print("Group overlap:", len(train_groups.intersection(test_groups)))


# ==========================================
# 7. BUILD ML PIPELINE
# ==========================================

print("\n===== BUILDING ML PIPELINE =====")

model = Pipeline([

    (
        "tfidf",
        TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            max_features=50000,
            sublinear_tf=True
        )
    ),

    (
        "classifier",
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE
        )
    )

])

print(model)


# ==========================================
# 8. TRAIN MODEL
# ==========================================

print("\n===== TRAINING MODEL =====")

model.fit(X_train, y_train)

print("Model training completed!")


# ==========================================
# 9. PREDICTIONS
# ==========================================

print("\n===== MAKING PREDICTIONS =====")

y_pred = model.predict(X_test)

probabilities = model.predict_proba(X_test)

confidence_scores = probabilities.max(axis=1)

print("Predictions completed!")


# ==========================================
# 10. MODEL EVALUATION
# ==========================================

print("\n===== MODEL EVALUATION =====")

accuracy = accuracy_score(y_test, y_pred)

precision, recall, f1, _ = precision_recall_fscore_support(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-score:  {f1:.4f}")

report = classification_report(
    y_test,
    y_pred,
    zero_division=0
)

print("\nClassification Report:")
print(report)


# ==========================================
# 11. CONFUSION MATRIX
# ==========================================

print("\n===== CONFUSION MATRIX =====")

classes = sorted(y.unique())

cm = confusion_matrix(
    y_test,
    y_pred,
    labels=classes
)

confusion_df = pd.DataFrame(
    cm,
    index=classes,
    columns=classes
)

REPORT_DIR.mkdir(parents=True, exist_ok=True)

confusion_path = REPORT_DIR / "confusion_matrix.csv"

confusion_df.to_csv(confusion_path)

print(confusion_df)
print("Saved:", confusion_path)


# Save confusion matrix image
plt.figure(figsize=(12, 10))

plt.imshow(cm, interpolation="nearest")
plt.title("Category Classification Confusion Matrix")
plt.colorbar()

plt.xticks(
    range(len(classes)),
    classes,
    rotation=45,
    ha="right"
)

plt.yticks(range(len(classes)), classes)

plt.xlabel("Predicted Category")
plt.ylabel("Actual Category")

plt.tight_layout()

matrix_image = REPORT_DIR / "confusion_matrix.png"

plt.savefig(matrix_image, dpi=200)
plt.close()

print("Saved:", matrix_image)


# ==========================================
# 12. IDENTIFY WRONG PREDICTIONS
# ==========================================

print("\n===== WRONG PREDICTIONS =====")

results_df = pd.DataFrame({

    "message": df.loc[X_test.index, "instruction"].values,

    "actual_category": y_test.values,

    "predicted_category": y_pred,

    "confidence": confidence_scores

})

wrong_predictions = results_df[
    results_df["actual_category"] != results_df["predicted_category"]
].copy()

wrong_predictions = wrong_predictions.sort_values(
    by="confidence",
    ascending=False
)

wrong_path = REPORT_DIR / "wrong_predictions.csv"

wrong_predictions.to_csv(wrong_path, index=False)

print("Total test messages:", len(y_test))
print("Incorrect predictions:", len(wrong_predictions))

print(
    "Error rate:",
    round(len(wrong_predictions) / len(y_test) * 100, 2),
    "%"
)

print("Saved:", wrong_path)


# ==========================================
# 13. SAVE EVALUATION REPORT
# ==========================================

evaluation_path = REPORT_DIR / "classification_report.txt"

with open(evaluation_path, "w", encoding="utf-8") as file:

    file.write("SMART SUPPORT DESK - MODEL EVALUATION\n")
    file.write("=" * 50 + "\n\n")

    file.write(f"Dataset size: {len(df)}\n")
    file.write(f"Training size: {len(X_train)}\n")
    file.write(f"Testing size: {len(X_test)}\n")
    file.write(f"Number of categories: {len(classes)}\n")

    file.write(
        f"Near-duplicate pairs used: {near_duplicate_pairs}\n\n"
    )

    file.write(f"Accuracy: {accuracy:.4f}\n")
    file.write(f"Precision: {precision:.4f}\n")
    file.write(f"Recall: {recall:.4f}\n")
    file.write(f"F1-score: {f1:.4f}\n\n")

    file.write("CLASSIFICATION REPORT\n")
    file.write(report)

print("Saved:", evaluation_path)


# ==========================================
# 14. SAVE TRAINED MODEL
# ==========================================

print("\n===== SAVING MODEL =====")

MODEL_DIR.mkdir(parents=True, exist_ok=True)

joblib.dump(model, MODEL_FILE)

print("Model saved successfully!")
print("Model location:", MODEL_FILE)


# ==========================================
# 15. COMPLETION
# ==========================================

print("\n========================================")
print("MODEL TRAINING COMPLETED")
print("========================================")
