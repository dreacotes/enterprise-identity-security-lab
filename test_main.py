import pytest
from fastapi.testclient import TestClient

from auth import require_resources_read
from main import app

client = TestClient(app)


@pytest.fixture
def authorized_client():
    def override_permission():
        return {"roles": ["Resources.Read"]}

    app.dependency_overrides[require_resources_read] = override_permission

    try:
        yield client
    finally:
        app.dependency_overrides.pop(require_resources_read, None)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_returns_404():
    response = client.get("/no-existe")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_existing_resource_returns_200(authorized_client):
    response = authorized_client.get("/resources/1")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Identity security lab",
    }


def test_missing_resource_returns_404(authorized_client):
    response = authorized_client.get("/resources/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Resource not found"}


def test_invalid_resource_id_returns_422(authorized_client):
    response = authorized_client.get("/resources/abc")

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(
        error["loc"] == ["path", "resource_id"]
        and error["type"] == "int_parsing"
        for error in errors
    )

def test_resource_without_token_returns_401():
    response = client.get("/resources/1")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Bearer token required"}


def test_resource_without_required_role_returns_403(monkeypatch):
    def fake_validate_access_token(token):
        assert token == "test-token"
        return {"roles": ["Other.Permission"]}

    monkeypatch.setattr(
        "auth.validate_access_token",
        fake_validate_access_token,
    )

    response = client.get(
        "/resources/1",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Resources.Read permission required"
    }