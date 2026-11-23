
import pandas as pd
import re
from pathlib import Path

# Load original dataset and sampled pairs
df = pd.read_csv("data/dataset.csv")

very_high = pd.read_csv(
    "data/reports/very_high_review_sample.csv"
)

high = pd.read_csv(
    "data/reports/manual_review_sample.csv"
)

def normalize_text(text):
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

# Normalize original messages
df["normalized_message"] = df["instruction"].apply(
    normalize_text
)

# Create message-to-label lookup
lookup = (
    df.groupby("normalized_message")
    .agg(
        categories=("category", lambda x: "; ".join(sorted(set(x)))),
        intents=("intent", lambda x: "; ".join(sorted(set(x))))
    )
    .reset_index()
)

# Combine both samples
samples = pd.concat(
    [very_high, high],
    ignore_index=True
)

samples["message_1_normalized"] = samples["message_1"].apply(
    normalize_text
)

samples["message_2_normalized"] = samples["message_2"].apply(
    normalize_text
)

# Add labels for message 1
lookup_1 = lookup.rename(columns={
    "normalized_message": "message_1_normalized",
    "categories": "category_1",
    "intents": "intent_1"
})

samples = samples.merge(
    lookup_1,
    on="message_1_normalized",
    how="left"
)

# Add labels for message 2
lookup_2 = lookup.rename(columns={
    "normalized_message": "message_2_normalized",
    "categories": "category_2",
    "intents": "intent_2"
})

samples = samples.merge(
    lookup_2,
    on="message_2_normalized",
    how="left"
)

# Columns for manual review
samples["same_meaning"] = ""
samples["same_category"] = ""
samples["same_intent"] = ""
samples["review_decision"] = ""
samples["review_notes"] = ""

# Save final review file
output = Path(
    "data/reports/final_manual_review.csv"
)

samples.to_csv(output, index=False)

print("Manual review file created!")
print("Total sample pairs:", len(samples))
print("Missing category matches:", samples["category_1"].isna().sum())
print("Missing category matches:", samples["category_2"].isna().sum())
print("Saved:", output)
