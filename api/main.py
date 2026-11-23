
from pathlib import Path
from contextlib import closing
from typing import Literal
import os
import re
import sqlite3
import secrets

import joblib

from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Depends,
    status as http_status
)

from fastapi.middleware.cors import CORSMiddleware

from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials
)

from pydantic import BaseModel, Field, field_validator

from api.faq_service import generate_suggested_reply


# ==================================================
# 1. PROJECT PATHS AND ENVIRONMENT VARIABLES
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "models" / "category_classifier.joblib"

DATABASE_PATH = BASE_DIR / "smart_support.db"

# Load environment variables from project root
load_dotenv(BASE_DIR / ".env")

# Team login credentials
TEAM_USERNAME = os.getenv("TEAM_USERNAME", "admin")
TEAM_PASSWORD = os.getenv("TEAM_PASSWORD")

if not TEAM_PASSWORD:
    raise RuntimeError(
        "TEAM_PASSWORD is missing from the project root .env file."
    )


# ==================================================
# 2. LOAD TRAINED ML MODEL
# ==================================================

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Trained ML model not found: {MODEL_PATH}"
    )

model = joblib.load(MODEL_PATH)

print("ML model loaded successfully!")


# ==================================================
# 3. CREATE FASTAPI APPLICATION
# ==================================================

app = FastAPI(
    title="Smart Support Desk API",
    description=(
        "ML-powered customer support ticket management "
        "with FAQ-based AI suggested replies and team login."
    ),
    version="1.2.0"
)


# ==================================================
# 4. CORS CONFIGURATION
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# 5. TEAM LOGIN AUTHENTICATION
# ==================================================

security = HTTPBasic()


def require_team_login(
    credentials: HTTPBasicCredentials = Depends(security)
):

    username_correct = secrets.compare_digest(
        credentials.username,
        TEAM_USERNAME
    )

    password_correct = secrets.compare_digest(
        credentials.password,
        TEAM_PASSWORD
    )

    if not (username_correct and password_correct):

        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={
                "WWW-Authenticate": "Basic"
            }
        )

    return credentials.username


# Login verification endpoint
@app.get("/login")
def team_login(
    username: str = Depends(require_team_login)
):

    return {
        "message": "Login successful!",
        "username": username
    }


# ==================================================
# 6. DATABASE CONNECTION
# ==================================================

def get_connection():

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection


# ==================================================
# 7. CREATE DATABASE TABLE
# ==================================================

def create_database():

    with closing(get_connection()) as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS tickets (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                customer_name TEXT NOT NULL,

                customer_email TEXT NOT NULL,

                message TEXT NOT NULL,

                category TEXT NOT NULL,

                confidence REAL NOT NULL,

                priority TEXT DEFAULT 'MEDIUM',

                status TEXT DEFAULT 'OPEN',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.commit()


create_database()

print("Database initialized successfully!")


# ==================================================
# 8. CUSTOMER TICKET REQUEST VALIDATION
# ==================================================

class TicketRequest(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=100
    )

    email: str = Field(
        min_length=5,
        max_length=150
    )

    message: str = Field(
        min_length=3,
        max_length=2000
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):

        value = value.strip()

        if not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            value
        ):
            raise ValueError("Invalid email address")

        return value

    @field_validator("name", "message")
    @classmethod
    def clean_text(cls, value):

        value = value.strip()

        if not value:
            raise ValueError(
                "This field cannot be empty"
            )

        return value


# ==================================================
# 9. TICKET STATUS VALIDATION
# ==================================================

class StatusUpdate(BaseModel):

    status: Literal[
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED"
    ]


# ==================================================
# 10. AI SUGGESTED REPLY REQUEST VALIDATION
# ==================================================

class SuggestedReplyRequest(BaseModel):

    message: str = Field(
        min_length=3,
        max_length=2000
    )

    category: str = Field(
        min_length=2,
        max_length=50
    )

    @field_validator("message", "category")
    @classmethod
    def clean_suggested_reply_input(cls, value):

        value = value.strip()

        if not value:
            raise ValueError(
                "This field cannot be empty"
            )

        return value


# ==================================================
# 11. ROOT ENDPOINT
# ==================================================

@app.get("/")
def home():

    return {
        "message": "Smart Support Desk API is running!",
        "version": "1.2.0",
        "features": [
            "Team Login Authentication",
            "ML Category Prediction",
            "Customer Ticket Submission",
            "Ticket Management",
            "Dashboard Summary",
            "FAQ-based AI Suggested Replies"
        ]
    }


# ==================================================
# 12. ML CATEGORY PREDICTION
# ==================================================

def predict_message_category(message: str):

    prediction = model.predict([message])[0]

    probabilities = model.predict_proba([message])[0]

    confidence = float(max(probabilities))

    return str(prediction), confidence


# ==================================================
# 13. CATEGORY PREDICTION ENDPOINT
# ==================================================

@app.post("/predict")
def predict_category(
    message: str = Query(
        min_length=3,
        max_length=2000
    )
):

    message = message.strip()

    if len(message) < 3:

        raise HTTPException(
            status_code=400,
            detail="Message must contain at least 3 characters."
        )

    try:

        prediction, confidence = predict_message_category(
            message
        )

        return {
            "predicted_category": prediction,
            "confidence": round(confidence, 4)
        }

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Category prediction failed."
        )


# ==================================================
# 14. CUSTOMER SUBMITS A NEW TICKET
# PUBLIC ENDPOINT - NO LOGIN REQUIRED
# ==================================================

@app.post("/tickets", status_code=201)
def create_ticket(ticket: TicketRequest):

    try:

        # Step 1: Predict ticket category

        prediction, confidence = predict_message_category(
            ticket.message
        )

        # Step 2: Save ticket in SQLite database

        with closing(get_connection()) as connection:

            cursor = connection.execute("""
                INSERT INTO tickets (
                    customer_name,
                    customer_email,
                    message,
                    category,
                    confidence,
                    priority,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket.name,
                ticket.email,
                ticket.message,
                prediction,
                confidence,
                "MEDIUM",
                "OPEN"
            ))

            ticket_id = cursor.lastrowid

            connection.commit()

        # Step 3: Return ticket confirmation

        return {
            "message": "Ticket submitted successfully!",
            "ticket_id": ticket_id,
            "category": prediction,
            "confidence": round(confidence, 4),
            "priority": "MEDIUM",
            "status": "OPEN"
        }

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Ticket submission failed."
        )


# ==================================================
# 15. VIEW ALL TICKETS
# TEAM LOGIN REQUIRED
# ==================================================

@app.get("/tickets")
def get_tickets(

    category: str | None = Query(default=None),

    status: Literal[
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED"
    ] | None = Query(default=None),

    username: str = Depends(require_team_login)

):

    try:

        query = """
            SELECT
                id,
                customer_name,
                customer_email,
                message,
                category,
                confidence,
                priority,
                status,
                created_at
            FROM tickets
            WHERE 1=1
        """

        parameters = []

        # Filter by category

        if category:

            query += " AND category = ?"

            parameters.append(
                category.strip().upper()
            )

        # Filter by status

        if status:

            query += " AND status = ?"

            parameters.append(status)

        # Latest tickets first

        query += " ORDER BY created_at DESC, id DESC"

        with closing(get_connection()) as connection:

            tickets = connection.execute(
                query,
                parameters
            ).fetchall()

        return {
            "total_tickets": len(tickets),
            "tickets": [
                dict(ticket) for ticket in tickets
            ]
        }

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve tickets."
        )


# ==================================================
# 16. VIEW INDIVIDUAL TICKET DETAILS
# TEAM LOGIN REQUIRED
# ==================================================

@app.get("/tickets/{ticket_id}")
def get_ticket(

    ticket_id: int,

    username: str = Depends(require_team_login)

):

    try:

        with closing(get_connection()) as connection:

            ticket = connection.execute("""
                SELECT *
                FROM tickets
                WHERE id = ?
            """, (ticket_id,)).fetchone()

        if ticket is None:

            raise HTTPException(
                status_code=404,
                detail="Ticket not found."
            )

        return dict(ticket)

    except HTTPException:

        raise

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve ticket details."
        )


# ==================================================
# 17. UPDATE TICKET STATUS
# TEAM LOGIN REQUIRED
# ==================================================

@app.patch("/tickets/{ticket_id}/status")
def update_ticket_status(

    ticket_id: int,

    request: StatusUpdate,

    username: str = Depends(require_team_login)

):

    try:

        with closing(get_connection()) as connection:

            # Check whether ticket exists

            ticket = connection.execute(
                "SELECT id FROM tickets WHERE id = ?",
                (ticket_id,)
            ).fetchone()

            if ticket is None:

                raise HTTPException(
                    status_code=404,
                    detail="Ticket not found."
                )

            # Update ticket status

            connection.execute("""
                UPDATE tickets
                SET status = ?
                WHERE id = ?
            """, (
                request.status,
                ticket_id
            ))

            connection.commit()

        return {
            "message": "Ticket status updated successfully!",
            "ticket_id": ticket_id,
            "status": request.status
        }

    except HTTPException:

        raise

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Unable to update ticket status."
        )


# ==================================================
# 18. DASHBOARD SUMMARY
# TEAM LOGIN REQUIRED
# ==================================================

@app.get("/dashboard/summary")
def dashboard_summary(

    username: str = Depends(require_team_login)

):

    try:

        with closing(get_connection()) as connection:

            total = connection.execute("""
                SELECT COUNT(*) FROM tickets
            """).fetchone()[0]

            open_count = connection.execute("""
                SELECT COUNT(*) FROM tickets
                WHERE status = 'OPEN'
            """).fetchone()[0]

            in_progress = connection.execute("""
                SELECT COUNT(*) FROM tickets
                WHERE status = 'IN_PROGRESS'
            """).fetchone()[0]

            resolved = connection.execute("""
                SELECT COUNT(*) FROM tickets
                WHERE status = 'RESOLVED'
            """).fetchone()[0]

        return {
            "total_tickets": total,
            "open_tickets": open_count,
            "in_progress_tickets": in_progress,
            "resolved_tickets": resolved
        }

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve dashboard summary."
        )


# ==================================================
# 19. AI SUGGESTED REPLY GENERATOR
# TEAM LOGIN REQUIRED
# ==================================================

@app.post("/suggested-reply")
def suggested_reply_endpoint(
    request: SuggestedReplyRequest,
    username: str = Depends(require_team_login)
):
    try:
        result = generate_suggested_reply(
            message=request.message,
            category=request.category.upper()
        )

        return result

    except RuntimeError:
        logger.exception("AI service configuration/runtime error")

        raise HTTPException(
            status_code=503,
            detail="AI service is not configured or temporarily unavailable."
        )

    except Exception:
        logger.exception("Unexpected error while generating AI reply")

        raise HTTPException(
            status_code=502,
            detail="Unable to generate an AI suggested reply."
        )
