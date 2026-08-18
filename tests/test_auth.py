from fastapi.testclient import TestClient


def test_login_with_valid_credentials_returns_token(client: TestClient) -> None:
    response = client.post("/auth/login", data={"username": "demo", "password": "demo123"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_invalid_password_returns_401(client: TestClient) -> None:
    response = client.post("/auth/login", data={"username": "demo", "password": "senha-errada"})
    assert response.status_code == 401


def test_login_with_unknown_user_returns_401(client: TestClient) -> None:
    response = client.post("/auth/login", data={"username": "ghost", "password": "demo123"})
    assert response.status_code == 401
