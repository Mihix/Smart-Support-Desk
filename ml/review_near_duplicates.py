
import pandas as pd

# Load near duplicate results
df = pd.read_csv("data/reports/near_duplicates.csv")

# Sort by highest similarity
df = df.sort_values(
    by="similarity",
    ascending=False
)

# Separate into groups
very_high = df[df["similarity"] >= 0.95]

high = df[
    (df["similarity"] >= 0.90) &
    (df["similarity"] < 0.95)
]

# Select 50 examples from the 0.90-0.95 group
sample = high.sample(
    n=min(50, len(high)),
    random_state=42
)

# Save separate reports
very_high.to_csv(
    "data/reports/very_high_similarity.csv",
    index=False
)

sample.to_csv(
    "data/reports/manual_review_sample.csv",
    index=False
)

# Randomly select 50 pairs from very high similarity
very_high_sample = very_high.sample(
    n=min(50, len(very_high)),
    random_state=42
)

very_high_sample.to_csv(
    "data/reports/very_high_review_sample.csv",
    index=False
)

print(
    "Very high similarity samples:",
    len(very_high_sample)
)

# Print summary
print("Total candidate pairs:", len(df))

print("Similarity >= 0.95:", len(very_high))

print("Similarity 0.90-0.95:", len(high))

print("Selected manual samples:", len(sample))

print("\nReports generated successfully!")
