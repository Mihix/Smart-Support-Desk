
# Project Notes – Smart Support Desk

## 1. Design Choices and Trade-offs

**FastAPI and SQLite:** I selected FastAPI because it makes it easy to build REST APIs using Python. SQLite was selected because it is simple to configure and suitable for this small application.

**TF-IDF and Logistic Regression:** I used TF-IDF to convert customer messages into numerical features and Logistic Regression for category classification. This approach is simple, fast, and easy to maintain. However, it may struggle with spelling mistakes, short messages, and similar categories.

**Keyword-Based FAQ Retrieval:** I used keyword matching to find relevant FAQ entries. It is easy to implement and does not require an embedding service. However, it may retrieve irrelevant FAQs or miss questions with different wording.

**OpenAI API:** I used the OpenAI API to generate suggested replies using retrieved FAQ information. Replies are shown to support team members for review instead of being sent automatically.

## 2. AI Tools Used

I used OpenAI technologies only:

- **ChatGPT:** Assisted with coding, debugging, testing, and documentation.
- **OpenAI API:** Generated FAQ-based suggested replies.

## 3. Two AI-Assisted Development Mistakes

**Mistake 1 – Python Import Path**

An initial AI-assisted test setup did not correctly handle the project import path. Running Pytest resulted in `ModuleNotFoundError: No module named 'api'`.

I identified the issue from the test output and updated `conftest.py` to add the project root to Python's import path.

**Mistake 2 – Incorrect API Response Assumption**

An initial AI-assisted API test expected the `/tickets` endpoint to return a list. However, the actual API returned a dictionary containing `total_tickets` and `tickets`.

I identified the incorrect assumption from the failed test and updated the test to check the actual API response structure.

These issues were detected by running the application tests and checking the actual outputs.

## 4. Testing Results

I implemented 24 automated tests using Pytest.

- API tests: 10 passed.
- FAQ and AI reply tests: 8 passed.
- ML model tests: 6 passed.

**Final result: 24 passed in 0.39 seconds.**

The AI reply tests use mocked OpenAI responses.

## 5. Improvements for the Next Week

If I had another week, I would:

1. Improve FAQ retrieval using semantic search.
2. Add more verified customer support FAQs.
3. Improve the classifier using more real-world customer messages.
4. Add more tests for invalid input and prompt injection.
5. Improve error handling and logging.
6. Monitor AI response quality, API usage, and response time.
7. Improve the frontend user experience.

## 6. Final Note

This project demonstrates full-stack development, Machine Learning, and AI integration in a customer support application.

AI-generated replies are treated as suggestions, and human review remains important before sending responses to customers.
