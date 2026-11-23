
from api.main import model, predict_message_category


def test_model_is_loaded():
    assert model is not None


def test_model_has_categories():
    assert hasattr(model, "classes_")
    assert len(model.classes_) > 0


def test_model_prediction_returns_valid_category():
    message = "I want to request a refund for my order."

    category, confidence = predict_message_category(message)

    valid_categories = set(model.classes_)

    assert category in valid_categories
    assert isinstance(confidence, float)
    assert 0 <= confidence <= 1


def test_model_prediction_is_not_empty():
    category, confidence = predict_message_category(
        "My payment failed."
    )

    assert category.strip() != ""
    assert confidence is not None


def test_predict_endpoint(test_client):
    response = test_client.post(
        "/predict",
        params={
            "message": "I want to request a refund."
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["predicted_category"]
    assert 0 <= data["confidence"] <= 1


def test_predict_endpoint_rejects_short_message(test_client):
    response = test_client.post(
        "/predict",
        params={"message": "Hi"}
    )

    assert response.status_code == 422
