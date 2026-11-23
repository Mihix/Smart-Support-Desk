# B1 – Dataset Exploration and ML Classifier Report

## 1. Dataset Overview

The project uses the publicly available Bitext Customer Support LLM Chatbot Training Dataset from Hugging Face.

**Dataset:** `bitext/Bitext-customer-support-llm-chatbottraining-dataset`

The original dataset contains:

- Total records: 26,872
- Total columns: 5
- Categories: 11
- Intents: 27
- Missing values: 0

The five columns are:
- `flags`
- `instruction`
- `category`
- `intent`
- `response`

The `instruction` column contains customer messages, while the `category` column is used as the target label for classification.

## 2. Data Quality Exploration

Before training the classifier, the dataset was explored to identify potential data quality problems.

### 2.1 Missing Values

No missing values were found in the initial dataset.

### 2.2 Duplicate Messages

The analysis identified 2,237 repeated instruction rows after the first occurrence.

Repeated customer messages can cause data leakage if similar messages appear in both training and testing datasets.

### 2.3 Near-Duplicate Messages

Character-level TF-IDF and nearest-neighbour similarity were used to identify potentially similar messages.

A similarity threshold of 0.90 or higher was used.

The analysis produced 3,976 high-similarity candidate pairs.

A sample of approximately 100 candidate pairs was manually reviewed with AI assistance:

| Review result | Count |
|---|---:|
| Same meaning | 76 |
| Different meaning | 24 |
| Same category | 99 |
| Different category | 1 |
| Same intent | 99 |
| Different intent | 1 |

This review was preliminary and AI-assisted, rather than a fully human-verified ground-truth evaluation.

### 2.4 Data Quality Decisions

The following decisions were made:

- Repeated customer instructions were reduced to one record.
- No rows were removed for missing values.
- Near-duplicate messages were considered during the evaluation split.
- Different messages were not automatically removed only because they had high similarity.

## 3. Data Cleaning

The original dataset contained 26,872 rows.

After removing repeated instructions, the cleaned dataset contained 24,274 rows.

| Description | Records |
|---|---:|
| Original dataset | 26,872 |
| Repeated rows removed | 2,598 |
| Final cleaned dataset | 24,274 |
| Records retained | 90.33% |
| Records removed | 9.67% |

The cleaned dataset was saved as:

`data/cleaned_dataset.csv`

## 4. Category Distribution

The cleaned dataset contains 11 customer support categories.

| Category | Records |
|---|---:|
| ACCOUNT | 5,358 |
| ORDER | 3,067 |
| REFUND | 2,577 |
| FEEDBACK | 1,990 |
| PAYMENT | 1,986 |
| CONTACT | 1,966 |
| SHIPPING | 1,951 |
| INVOICE | 1,801 |
| DELIVERY | 1,645 |
| SUBSCRIPTION | 992 |
| CANCEL | 941 |

ACCOUNT is the largest category, while CANCEL is the smallest.

## 5. Feature Engineering

TF-IDF (Term Frequency–Inverse Document Frequency) was used to convert customer messages into numerical features.

Configuration:

- Unigrams and bigrams: `(1, 2)`
- Minimum document frequency: `2`
- Maximum features: `50,000`
- Lowercase text: Enabled
- Sublinear term frequency: Enabled

The resulting feature matrix contained:

- Messages: 24,274
- Extracted features: 5,531

Feature matrix shape: `(24274, 5531)`

## 6. Model Training

A Logistic Regression classifier was selected for category prediction.

Configuration:

- Algorithm: Logistic Regression
- Maximum iterations: 2,000
- Class weighting: Balanced
- Random state: 42

The trained model was saved as:

`models/category_classifier.joblib`

The model is integrated into the backend to predict the category of every newly submitted customer ticket.

## 7. Leakage-Safe Evaluation

A grouped stratified splitting strategy was used to reduce data leakage.

The evaluation used `StratifiedGroupKFold` with five folds.

Exact normalized-message matches and detected near-duplicate pairs were grouped together before splitting.

This ensured that messages belonging to the same identified group were not distributed between training and testing datasets.

| Dataset | Records |
|---|---:|
| Training | 19,419 |
| Testing | 4,855 |
| Group overlap | 0 |

### Evaluation Results

| Metric | Score |
|---|---:|
| Accuracy | 99.86% |
| Weighted F1-score | 99.86% |

Although the model achieved a high score, the dataset contains many templated customer messages. Near-duplicate detection is also not exhaustive.

Therefore, the reported score should not be interpreted as guaranteed real-world classification performance.

## 8. Evaluation Using Original Customer Messages

To test performance beyond the public dataset, 20 original short customer messages were written manually.

The messages included informal language, abbreviations, spelling mistakes and typing errors.

### Results

| Metric | Result |
|---|---:|
| Total messages | 20 |
| Correct predictions | 16 |
| Incorrect predictions | 4 |
| Accuracy | 80% |

### Incorrect Predictions

The following four incorrect predictions were identified:

| Customer message | Expected | Predicted |
|---|---|---|
| pls cancel my order asap | CANCEL | ORDER |
| i dont want this order anymore cancel it | CANCEL | ORDER |
| money got deducted twice from my card | PAYMENT | REFUND |
| really happy with the service thank u | FEEDBACK | CONTACT |

### Error Analysis

**1. Cancellation versus Order**

The model predicted ORDER instead of CANCEL because the message contained the word "order". The model may have relied more heavily on the order-related vocabulary than the cancellation intent.

**2. Cancellation intent**

The second message also contained the word "order", which may have influenced the prediction. The model did not correctly identify the cancellation request.

**3. Payment versus Refund**

The phrase "money got deducted twice" can be associated with both payment problems and refund requests. The model predicted REFUND instead of PAYMENT.

**4. Feedback versus Contact**

The phrase "thank u" may have been interpreted as a customer contact or interaction message rather than positive feedback.

These errors show that the classifier can struggle with short, informal and ambiguous customer messages.

Only four incorrect predictions were identified in the recorded evaluation. No additional incorrect prediction has been invented.

## 9. Limitations and Future Improvements

The classifier achieved strong results on the public dataset, but several limitations remain:

- The dataset contains repeated and templated messages.
- Near-duplicate detection may miss some paraphrased messages.
- Informal language and spelling mistakes can reduce prediction accuracy.
- Some categories have similar vocabulary, such as ORDER and CANCEL or PAYMENT and REFUND.
- Prediction confidence scores should not be treated as calibrated probabilities.

Possible future improvements:

1. Collect more real-world customer messages.
2. Expand the manually labelled test dataset.
3. Improve text preprocessing for spelling mistakes and abbreviations.
4. Evaluate additional classification models.
5. Monitor model performance using human-corrected ticket categories.

## 10. Conclusion

A customer support category classifier was developed using the Bitext dataset and Logistic Regression.

The model achieved 99.86% accuracy on the grouped test dataset and 80% accuracy on 20 original manually written customer messages.

The evaluation demonstrated that the model performs well on the provided dataset but still has difficulties with informal and ambiguous customer messages.

The trained classifier is integrated into the Smart Support Desk application to automatically categorize incoming customer tickets.