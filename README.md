
# Smart Support Desk

A full-stack customer support application with Machine Learning and AI-powered suggested replies.

The application allows customers to submit support tickets and helps support teams manage tickets, predict ticket categories, and generate suggested replies using an FAQ knowledge base.

## 1. Main Features

### Customer Features
- Submit a support ticket.
- Enter customer name, email, and message.
- Automatically predict the ticket category.
- Receive a ticket reference ID.

### Support Team Features
- Simple team login.
- View customer support tickets.
- Filter tickets by category and status.
- View individual ticket details.
- Update ticket status:
  - OPEN
  - IN_PROGRESS
  - RESOLVED
- View dashboard summary.
- Generate AI-powered suggested replies.
- Review the FAQ entries used for each suggested reply.

### Machine Learning Features
- Customer message classification.
- TF-IDF text feature extraction.
- Logistic Regression classification model.
- Prediction confidence scores.

### AI Features
- FAQ-based suggested reply generation.
- FAQ retrieval using keyword matching.
- OpenAI API integration.
- No-match handling for unsupported questions.
- Protection against tested prompt injection attempts.

## 2. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend and ML development |
| FastAPI | Backend REST API |
| SQLite | Database |
| Scikit-learn | Machine Learning |
| TF-IDF | Text feature extraction |
| Logistic Regression | Category classification |
| OpenAI API | AI suggested reply generation |
| JSON | FAQ knowledge base |
| HTML, CSS, TypeScript | Frontend |
| Vite | Frontend development server |
| Pytest | Automated testing |

## 3. AI Tools Used

This project uses OpenAI technologies only:

- **OpenAI API:** Generates suggested replies using information retrieved from the FAQ knowledge base.
- **ChatGPT:** Used to assist with coding, debugging, testing, and documentation.

No other AI providers are used.

The OpenAI API key is stored in the `.env` file. It is not hardcoded into the source code or included in the GitHub repository.

## 4. Project Structure

```text
smart-support-desk/
│
├── api/
│   ├── main.py
│   └── faq_service.py
│
├── data/
│   ├── faq.json
│   └── cleaned_dataset.csv
│
├── models/
│   └── category_classifier.joblib
│
├── frontend/
│   ├── src/
│   │   ├── main.ts
│   │   └── style.css
│   ├── package.json
│   └── index.html
│
├── ml/
│   ├── feature_engineering.py
│   └── ...
│
├── reports/
│   ├── REPORT.md
│   ├── B2_AI_EVALUATION.md
│   └── B3_REPLY_EVALUATION.md
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_faq.py
│   └── test_model.py
│
├── .env
├── .gitignore
├── smart_support.db
├── README.md
└── NOTES.md
```

The project structure above shows the main application files. Some additional ML scripts and configuration files may also be present.

## 5. Installation and Setup

### Requirements

- Python 3.10 or later
- Node.js and npm
- Git
- An OpenAI API key

### Step 1: Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Open the project folder:

```bash
cd smart-support-desk
```

### Step 2: Create a Python Virtual Environment

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Backend Dependencies

```powershell
pip install fastapi "uvicorn[standard]" scikit-learn joblib pandas python-dotenv openai pytest httpx
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root directory.

Add the following settings:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4.1-mini

TEAM_USERNAME=admin
TEAM_PASSWORD=your_team_password
```

Replace the example values with your own credentials.

**Important:** Never upload the `.env` file or your API key to GitHub.

### Step 5: Install Frontend Dependencies

Open another PowerShell terminal:

```powershell
cd frontend
npm install
```

## 6. Running the Application

### Start the Backend

From the project root directory:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start the FastAPI server:

```powershell
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### Start the Frontend

Open a second terminal:

```powershell
cd frontend
npm run dev
```

Open the local URL displayed by Vite in your terminal.

## 7. Environment and Data

- The application uses SQLite to store support tickets.
- The database is initialized by the backend.
- The trained classification model is loaded from `models/category_classifier.joblib`.
- FAQ information is loaded from `data/faq.json`.
- OpenAI settings are loaded from the root `.env` file.

The trained model file and FAQ file must be available before starting the backend.

The FAQ entries are starter examples and should be reviewed and replaced with approved company policies before production use.

## 8. Machine Learning Model

The application uses the Bitext Customer Support LLM Chatbot Training Dataset from Hugging Face.

Dataset:

`bitext/Bitext-customer-support-llm-chatbottraining-dataset`

The classifier uses:

- TF-IDF for text feature extraction.
- Logistic Regression for category prediction.
- Eleven customer support categories.

### Model Evaluation

| Evaluation | Result |
|---|---:|
| Grouped test dataset accuracy | 99.86% |
| Grouped test dataset weighted F1 | 99.86% |
| Original manually written messages | 80% |

The model achieved 16 correct predictions out of 20 manually written customer messages.

The high grouped test score should be interpreted carefully because the dataset contains templated messages and near-duplicate detection is not exhaustive.

See `reports/REPORT.md` for the full evaluation.

## 9. AI Suggested Reply Generator

The AI Suggested Reply Generator uses:

- A JSON-based FAQ knowledge base.
- Keyword-based FAQ retrieval.
- The OpenAI API.

The system retrieves relevant FAQ entries before generating a suggested reply.

The AI is instructed to:

- Use only the retrieved FAQ information.
- Avoid inventing company policies.
- Avoid guaranteeing refunds or cancellations.
- Ignore instructions inside customer messages that attempt to override its rules.
- Return a no-match response when relevant FAQ information is unavailable.

AI-generated replies are suggestions for support team members. They are not automatically sent to customers.

See `reports/B2_AI_EVALUATION.md` and `reports/B3_REPLY_EVALUATION.md` for the evaluation results.

## 10. Automated Testing

The project includes 24 automated tests using Pytest.

| Test Area | Number of Tests |
|---|---:|
| API tests | 10 |
| FAQ and AI reply tests | 8 |
| ML model tests | 6 |
| **Total** | **24** |

### Run Automated Tests

From the project root:

```powershell
pytest -v
```

### Final Test Results

```text
24 passed in 0.39s
```

All 24 tests passed during the recorded final test run.

The AI reply tests use mocked OpenAI responses for automated testing. They do not require a live OpenAI API call for every test.

## 11. Evaluation Reports

The `reports/` directory contains:

- `REPORT.md` – Dataset exploration and ML classifier evaluation.
- `B2_AI_EVALUATION.md` – Initial AI suggested reply evaluation.
- `B3_REPLY_EVALUATION.md` – Evaluation of 10 AI-generated replies.

## 12. Security Notes

- Keep API keys inside environment variables.
- Do not commit `.env` to GitHub.
- Use team authentication for protected support endpoints.
- Validate customer input before processing.
- Treat customer messages as untrusted input.
- Keep human review before sending AI-generated replies.

## 13. Future Improvements

Possible improvements include:

1. Improve FAQ retrieval using semantic search.
2. Add more verified FAQ entries.
3. Improve classification for short and informal customer messages.
4. Add more automated security tests.
5. Improve AI reply evaluation using larger datasets.
6. Add monitoring for AI quality, response time, and API usage.

## 14. Conclusion

Smart Support Desk combines a full-stack ticket management application with Machine Learning and AI-powered suggested replies.

It demonstrates customer ticket management, automatic category prediction, FAQ-based AI assistance, and automated software testing.

The project provides a foundation for improving customer support workflows while keeping human support teams responsible for reviewing AI-generated responses.
