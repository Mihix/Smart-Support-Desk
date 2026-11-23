
import os
import json
import time
import random
import pandas as pd

from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


# ==================================================
# 1. CONFIGURATION
# ==================================================

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found. Check your .env file."
    )

client = OpenAI(api_key=API_KEY)

INPUT_FILE = Path("data/reports/final_manual_review.csv")
OUTPUT_FILE = Path("data/reports/ai_manual_review.csv")

MODEL = "gpt-4.1-mini"

MAX_RETRIES = 5
BASE_WAIT_SECONDS = 5

REVIEW_COLUMNS = [
    "same_meaning",
    "same_category",
    "same_intent",
    "review_decision",
    "review_notes"
]

VALID_MEANINGS = ["Yes", "No", "Unclear"]


# ==================================================
# 2. LOAD DATASET
# ==================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )

source_df = pd.read_csv(INPUT_FILE)

required_columns = [
    "message_1",
    "message_2",
    "category_1",
    "category_2",
    "intent_1",
    "intent_2"
]

missing_columns = [
    col for col in required_columns
    if col not in source_df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ==================================================
# 3. RESUME PREVIOUS PROGRESS
# ==================================================

if OUTPUT_FILE.exists():

    print("Existing progress found. Resuming review...")

    saved_df = pd.read_csv(OUTPUT_FILE)

    # Validate row count
    if len(saved_df) != len(source_df):
        raise ValueError(
            "Input and output row counts do not match. "
            "Please check your CSV files."
        )

    # Validate original pair data before resuming
    for column in required_columns:

        if not saved_df[column].equals(source_df[column]):
            raise ValueError(
                f"Input data mismatch in column: {column}. "
                "The output may belong to a different dataset."
            )

    df = saved_df.copy()

else:

    print("Starting a new AI review...")

    df = source_df.copy()

    for column in REVIEW_COLUMNS:
        df[column] = ""


# Ensure all review columns exist
for column in REVIEW_COLUMNS:

    if column not in df.columns:
        df[column] = ""


# ==================================================
# 4. HELPER FUNCTIONS
# ==================================================

def is_completed(value):

    if pd.isna(value):
        return False

    return str(value).strip().capitalize() in VALID_MEANINGS


def compare_labels(a, b):

    if pd.isna(a) or pd.isna(b):
        return "No"

    values_a = {
        x.strip().casefold()
        for x in str(a).split(";")
        if x.strip()
    }

    values_b = {
        x.strip().casefold()
        for x in str(b).split(";")
        if x.strip()
    }

    return "Yes" if values_a == values_b else "No"


# ==================================================
# 5. OPENAI SEMANTIC MEANING COMPARISON
# ==================================================

def check_meaning(message1, message2):

    prompt = f"""
You are an expert customer support dataset reviewer.

Your task is to compare two customer support messages
and determine whether they express the same meaning.

MESSAGE 1:
{json.dumps(str(message1), ensure_ascii=False)}

MESSAGE 2:
{json.dumps(str(message2), ensure_ascii=False)}

EVALUATION RULES:

1. Ignore minor grammar, spelling and wording differences.

2. Focus on the actual customer need and requested
   support action.

3. Similar words do not automatically mean the
   same customer intention.

4. Different actions must be treated as different.
   For example:
   - Tracking an order vs cancelling an order.
   - Requesting a refund vs checking payment status.
   - Updating an address vs changing a product.

5. Consider the context of both messages.

6. If the meaning is ambiguous, return Unclear.

7. Do not assume that two messages are equivalent
   without sufficient evidence.

Return a valid JSON object with exactly these fields:

{{
    "same_meaning": "Yes",
    "reason": "Short explanation"
}}

The same_meaning field must contain exactly one of:
Yes, No, Unclear.

The reason must briefly explain your decision.
"""

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = client.chat.completions.create(

                model=MODEL,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                response_format={
                    "type": "json_object"
                },

                temperature=0,

                max_tokens=200
            )

            response_text = (
                response.choices[0].message.content
            )

            if not response_text:
                raise ValueError(
                    "OpenAI returned an empty response."
                )

            result = json.loads(response_text)

            meaning = str(
                result.get("same_meaning", "")
            ).strip().capitalize()

            if meaning not in VALID_MEANINGS:
                raise ValueError(
                    f"Invalid meaning returned: {meaning}"
                )

            reason = str(
                result.get("reason", "")
            ).strip()

            return {
                "same_meaning": meaning,
                "reason": reason
            }

        except Exception as error:

            print(
                f"OpenAI attempt {attempt}/{MAX_RETRIES} failed: "
                f"{str(error)[:250]}"
            )

            if attempt == MAX_RETRIES:
                raise

            # Exponential backoff with random jitter
            wait_time = (
                BASE_WAIT_SECONDS * (2 ** (attempt - 1))
                + random.uniform(0, 2)
            )

            print(
                f"Retrying in {wait_time:.1f} seconds..."
            )

            time.sleep(wait_time)


# ==================================================
# 6. FINAL DECISION LOGIC
# ==================================================

def make_decision(
    meaning,
    same_category,
    same_intent
):

    if meaning == "No":
        return "Keep Separate"

    if meaning == "Unclear":
        return "Investigate"

    if (
        meaning == "Yes"
        and same_category == "Yes"
        and same_intent == "Yes"
    ):
        return "Group"

    return "Investigate"


# ==================================================
# 7. PROCESS DATASET
# ==================================================

total = len(df)

completed = sum(
    is_completed(value)
    for value in df["same_meaning"]
)

failed = 0

print("\n===================================")
print(" OPENAI AI MANUAL REVIEW STARTED")
print("===================================")

print("Total pairs:", total)
print("Previously completed:", completed)
print("Model:", MODEL)
print("Input:", INPUT_FILE)
print("Output:", OUTPUT_FILE)


for index, row in df.iterrows():

    # Skip previously completed rows
    if is_completed(row["same_meaning"]):
        continue

    try:

        print(
            f"\nProcessing pair {index + 1}/{total}"
        )

        # ------------------------------------------
        # A. Compare message meanings using OpenAI
        # ------------------------------------------

        result = check_meaning(
            row["message_1"],
            row["message_2"]
        )

        meaning = result["same_meaning"]

        # ------------------------------------------
        # B. Compare categories
        # ------------------------------------------

        same_category = compare_labels(
            row["category_1"],
            row["category_2"]
        )

        # ------------------------------------------
        # C. Compare intents
        # ------------------------------------------

        same_intent = compare_labels(
            row["intent_1"],
            row["intent_2"]
        )

        # ------------------------------------------
        # D. Generate final decision
        # ------------------------------------------

        decision = make_decision(
            meaning,
            same_category,
            same_intent
        )

        # ------------------------------------------
        # E. Save results
        # ------------------------------------------

        df.at[index, "same_meaning"] = meaning

        df.at[index, "same_category"] = same_category

        df.at[index, "same_intent"] = same_intent

        df.at[index, "review_decision"] = decision

        df.at[index, "review_notes"] = result["reason"]

        completed += 1

        # ------------------------------------------
        # F. Display progress
        # ------------------------------------------

        print("Meaning:", meaning)

        print("Category:", same_category)

        print("Intent:", same_intent)

        print("Decision:", decision)

        print(
            f"Progress: {completed}/{total}"
        )

        # Save after every successful pair
        df.to_csv(
            OUTPUT_FILE,
            index=False
        )

        # Small delay between API requests
        time.sleep(1)

    except Exception as error:

        failed += 1

        # Save completed progress
        df.to_csv(
            OUTPUT_FILE,
            index=False
        )

        print("\nERROR processing pair:", index + 1)

        print(str(error))

        print(
            "Progress saved. Run the script again "
            "to resume unfinished rows."
        )

        break


# ==================================================
# 8. FINAL SUMMARY
# ==================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n===================================")
print(" AI REVIEW SUMMARY")
print("===================================")

print("Total pairs:", total)

print("Completed pairs:", completed)

print("Failed during this run:", failed)

print(
    "\nRemaining pairs:",
    total - sum(
        is_completed(value)
        for value in df["same_meaning"]
    )
)

print("\nDecision counts:")

print(
    df["review_decision"]
    .value_counts(dropna=False)
)

print("\nMeaning counts:")

print(
    df["same_meaning"]
    .value_counts(dropna=False)
)

print("\nSaved output:", OUTPUT_FILE)

print("\nOpenAI AI review process finished.")
