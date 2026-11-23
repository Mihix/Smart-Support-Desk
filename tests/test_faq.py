
import json
from types import SimpleNamespace

from api import faq_service


def create_test_faq_file(tmp_path, monkeypatch):
    """Create a small FAQ file for predictable tests."""

    faq_data = [
        {
            "id": 1,
            "category": "REFUND",
            "question": "How can I request a refund?",
            "answer": (
                "Customers should provide their order number "
                "and reason for requesting a refund. "
                "The support team must review the request."
            )
        },
        {
            "id": 2,
            "category": "PAYMENT",
            "question": "My payment failed.",
            "answer": (
                "Customers should provide the order number "
                "and describe the payment error. "
                "Never share full card numbers or security codes."
            )
        }
    ]

    faq_file = tmp_path / "test_faq.json"

    faq_file.write_text(
        json.dumps(faq_data),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        faq_service,
        "FAQ_PATH",
        faq_file
    )


def create_fake_openai_client(reply):
    """Create a fake OpenAI client response."""

    def fake_create(**kwargs):
        return SimpleNamespace(
            output_text=reply
        )

    fake_responses = SimpleNamespace(
        create=fake_create
    )

    return SimpleNamespace(
        responses=fake_responses
    )


def test_load_faqs(tmp_path, monkeypatch):
    create_test_faq_file(tmp_path, monkeypatch)

    faqs = faq_service.load_faqs()

    assert len(faqs) == 2
    assert faqs[0]["category"] == "REFUND"


def test_retrieve_relevant_refund_faq(tmp_path, monkeypatch):
    create_test_faq_file(tmp_path, monkeypatch)

    results = faq_service.retrieve_faqs(
        message="I need a refund for my order",
        category="REFUND"
    )

    assert len(results) > 0
    assert results[0]["category"] == "REFUND"


def test_no_faq_match_for_unrelated_message(tmp_path, monkeypatch):
    create_test_faq_file(tmp_path, monkeypatch)

    results = faq_service.retrieve_faqs(
        message="What is the weather forecast today?",
        category="OTHER"
    )

    assert results == []


def test_generate_reply_with_matching_faq(tmp_path, monkeypatch):
    create_test_faq_file(tmp_path, monkeypatch)

    fake_client = create_fake_openai_client(
        "Please provide your order number and refund reason."
    )

    monkeypatch.setattr(
        faq_service,
        "client",
        fake_client
    )

    result = faq_service.generate_suggested_reply(
        message="I want to request a refund for my order.",
        category="REFUND"
    )

    assert result["faq_found"] is True
    assert result["suggested_reply"]
    assert len(result["used_faqs"]) > 0
    assert result["used_faqs"][0]["category"] == "REFUND"


def test_no_match_does_not_call_openai(tmp_path, monkeypatch):
    create_test_faq_file(tmp_path, monkeypatch)

    def unexpected_openai_call(**kwargs):
        raise AssertionError(
            "OpenAI should not be called when no FAQ matches."
        )

    fake_client = SimpleNamespace(
        responses=SimpleNamespace(
            create=unexpected_openai_call
        )
    )

    monkeypatch.setattr(
        faq_service,
        "client",
        fake_client
    )

    result = faq_service.generate_suggested_reply(
        message="What is the weather today?",
        category="OTHER"
    )

    assert result["faq_found"] is False
    assert result["used_faqs"] == []
    assert "No relevant FAQ" in result["suggested_reply"]


def test_empty_openai_response_raises_error(tmp_path, monkeypatch):
    create_test_faq_file(tmp_path, monkeypatch)

    fake_client = create_fake_openai_client("")

    monkeypatch.setattr(
        faq_service,
        "client",
        fake_client
    )

    try:
        faq_service.generate_suggested_reply(
            message="I need a refund for my order.",
            category="REFUND"
        )
        assert False, "Expected RuntimeError was not raised."

    except RuntimeError as error:
        assert "empty suggested reply" in str(error)


def test_suggested_reply_endpoint_uses_service(
    test_client,
    auth_headers,
    monkeypatch
):
    from api import main

    def fake_generate_reply(message, category):
        return {
            "faq_found": True,
            "suggested_reply": "Please provide your order number.",
            "used_faqs": []
        }

    monkeypatch.setattr(
        main,
        "generate_suggested_reply",
        fake_generate_reply
    )

    response = test_client.post(
        "/suggested-reply",
        json={
            "message": "I need a refund for my order.",
            "category": "refund"
        },
        auth=auth_headers["auth"]
    )

    assert response.status_code == 200

    data = response.json()

    assert data["faq_found"] is True
    assert "order number" in data["suggested_reply"]


def test_suggested_reply_endpoint_requires_login(test_client):
    response = test_client.post(
        "/suggested-reply",
        json={
            "message": "I need a refund for my order.",
            "category": "REFUND"
        }
    )

    assert response.status_code == 401
