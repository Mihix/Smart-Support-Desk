
from fastapi.testclient import TestClient


def create_ticket(client):
    """Helper function to create a valid customer ticket."""
    response = client.post(
        "/tickets",
        json={
            "name": "John Silva",
            "email": "john@example.com",
            "message": "I want to request a refund for my order."
        }
    )
    return response


# 1. Test home endpoint
def test_home_endpoint(test_client):
    response = test_client.get("/")

    assert response.status_code == 200


# 2. Test successful team login
def test_team_login_success(test_client, auth_headers):
    response = test_client.get(
        "/login",
        auth=auth_headers["auth"]
    )

    assert response.status_code == 200


# 3. Test login with incorrect password
def test_team_login_invalid_password(test_client):
    response = test_client.get(
        "/login",
        auth=("testadmin", "wrongpassword")
    )

    assert response.status_code == 401


# 4. Test team endpoint requires authentication
def test_team_endpoint_requires_login(test_client):
    response = test_client.get("/tickets")

    assert response.status_code == 401


# 5. Test successful ticket creation
def test_create_ticket_success(test_client):
    response = create_ticket(test_client)

    assert response.status_code == 201

    data = response.json()

    assert "ticket_id" in data
    assert data["category"]
    assert 0 <= data["confidence"] <= 1
    assert data["status"] == "OPEN"


# 6. Test ticket creation with invalid email
def test_create_ticket_invalid_email(test_client):
    response = test_client.post(
        "/tickets",
        json={
            "name": "John Silva",
            "email": "invalid-email",
            "message": "I need help with my order."
        }
    )

    assert response.status_code == 422



# 7. Test retrieving tickets after creation
def test_get_tickets_after_creation(test_client, auth_headers):
    create_response = create_ticket(test_client)
    assert create_response.status_code == 201

    response = test_client.get(
        "/tickets",
        auth=auth_headers["auth"]
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert "total_tickets" in data
    assert "tickets" in data
    assert data["total_tickets"] >= 1
    assert isinstance(data["tickets"], list)
    assert len(data["tickets"]) >= 1

    ticket = data["tickets"][0]
    assert ticket["customer_name"] == "John Silva"



# 8. Test updating ticket status
def test_update_ticket_status(test_client, auth_headers):
    create_response = create_ticket(test_client)
    ticket_id = create_response.json()["ticket_id"]

    response = test_client.patch(
        f"/tickets/{ticket_id}/status",
        json={"status": "IN_PROGRESS"},
        auth=auth_headers["auth"]
    )

    assert response.status_code == 200


# 9. Test invalid ticket status
def test_update_ticket_invalid_status(test_client, auth_headers):
    create_response = create_ticket(test_client)
    ticket_id = create_response.json()["ticket_id"]

    response = test_client.patch(
        f"/tickets/{ticket_id}/status",
        json={"status": "INVALID_STATUS"},
        auth=auth_headers["auth"]
    )

    assert response.status_code == 422


# 10. Test dashboard summary endpoint
def test_dashboard_summary(test_client, auth_headers):
    response = test_client.get(
        "/dashboard/summary",
        auth=auth_headers["auth"]
    )

    assert response.status_code == 200
    assert isinstance(response.json(), dict)
