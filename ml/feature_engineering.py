
import re
import pandas as pd

from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer


# ==========================================
# 1. CONFIGURATION
# ==========================================

DATA_FILE = Path("data/cleaned_dataset.csv")


# ==========================================
# 2. LOAD DATASET
# ==========================================

print("\n===== LOADING DATASET =====")

df = pd.read_csv(DATA_FILE)

print("Dataset shape:", df.shape)

messages = df["instruction"].astype(str)


# ==========================================
# 3. TEXT PREPROCESSING
# ==========================================

def preprocess_text(text):

    # Convert to lowercase
    text = text.lower()

    # Remove leading and trailing spaces
    text = text.strip()

    # Replace multiple spaces with one space
    text = re.sub(r"\s+", " ", text)

    return text


print("\n===== TEXT PREPROCESSING =====")

processed_messages = messages.apply(preprocess_text)

print("\nOriginal message:")
print(messages.iloc[0])

print("\nProcessed message:")
print(processed_messages.iloc[0])


# ==========================================
# 4. TF-IDF VECTORIZATION
# ==========================================

print("\n===== TF-IDF FEATURE EXTRACTION =====")

vectorizer = TfidfVectorizer(

    # Individual words + two-word combinations
    ngram_range=(1, 2),

    # Ignore terms appearing in fewer than 2 messages
    min_df=2,

    # Limit vocabulary size
    max_features=50000,

    # Use lowercase text
    lowercase=True,

    # Apply sublinear term frequency scaling
    sublinear_tf=True
)


# Convert text into numerical features
X = vectorizer.fit_transform(processed_messages)


# ==========================================
# 5. DISPLAY FEATURE INFORMATION
# ==========================================

print("\n===== FEATURE INFORMATION =====")

print("Number of messages:", X.shape[0])

print("Number of extracted features:", X.shape[1])

print("Matrix shape:", X.shape)

print("Matrix type:", type(X))

print("\nFirst 20 vocabulary terms:")

feature_names = vectorizer.get_feature_names_out()

print(feature_names[:20])


# ==========================================
# 6. DISPLAY NUMERICAL FEATURE VECTOR
# ==========================================

print("\n===== NUMERICAL FEATURE VECTOR =====")

sample_vector = X[0]

print("Sparse vector:")
print(sample_vector)

print("\nNon-zero feature values:")

for index, value in zip(
    sample_vector.indices,
    sample_vector.data
):

    print(
        feature_names[index],
        ":", 
        round(float(value), 4)
    )



# ==========================================
# 7. DISPLAY UNIGRAMS AND BIGRAMS
# ==========================================

print("\n===== UNIGRAMS AND BIGRAMS =====")

for term in feature_names[:30]:

    if " " in term:
        print("BIGRAM:", term)

    else:
        print("UNIGRAM:", term)

print("\n===== FEATURE ENGINEERING COMPLETED =====")

