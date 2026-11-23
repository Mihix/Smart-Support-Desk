from datasets import load_dataset
import pandas as pd

dataset = load_dataset(
    "bitext/Bitext-customer-support-llm-chatbot-training-dataset"
)

df = dataset["train"].to_pandas()

print("Dataset shape:", df.shape)
print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 10 rows:")
print(df.head(10))

print("\nMissing values:")
print(df.isnull().sum())

print("\nCategory distribution:")
print(df["category"].value_counts())

print("\nDuplicate instructions:")
print(df["instruction"].duplicated().sum())

df.to_csv("data/dataset.csv", index=False)