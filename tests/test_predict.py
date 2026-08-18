from fastapi.testclient import TestClient

from tests.conftest import SAMPLE_PAYLOAD


def test_predict_without_token_returns_401(client: TestClient) -> None:
    response = client.post("/predict", json=SAMPLE_PAYLOAD)
    assert response.status_code == 401


def test_predict_with_invalid_token_returns_401(client: TestClient) -> None:
    response = client.post(
        "/predict", json=SAMPLE_PAYLOAD, headers={"Authorization": "Bearer token-invalido"}
    )
    assert response.status_code == 401


def test_predict_with_valid_token_returns_prediction(client: TestClient, auth_headers: dict) -> None:
    response = client.post("/predict", json=SAMPLE_PAYLOAD, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["sucesso"] is True
    assert body["prediction"]["classe"] == "setosa"
    assert body["prediction"]["classe_idx"] == 0


def test_predict_rejects_invalid_input(client: TestClient, auth_headers: dict) -> None:
    payload = {**SAMPLE_PAYLOAD, "sepal_length": -1}
    response = client.post("/predict", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_predict_batch_returns_one_result_per_item(client: TestClient, auth_headers: dict) -> None:
    payload = {
        "items": [
            SAMPLE_PAYLOAD,
            {"sepal_length": 6.7, "sepal_width": 3.0, "petal_length": 5.2, "petal_width": 2.3},
        ]
    }
    response = client.post("/predict/batch", json=payload, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["resultados"]) == 2
    assert body["resultados"][0]["prediction"]["classe"] == "setosa"
    assert body["resultados"][1]["prediction"]["classe"] == "virginica"


def test_predict_batch_requires_at_least_one_item(client: TestClient, auth_headers: dict) -> None:
    response = client.post("/predict/batch", json={"items": []}, headers=auth_headers)
    assert response.status_code == 422


def test_predict_batch_without_token_returns_401(client: TestClient) -> None:
    response = client.post("/predict/batch", json={"items": [SAMPLE_PAYLOAD]})
    assert response.status_code == 401
