from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_returns_404():
    response = client.get("/no-existe")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}

def test_existing_resource_returns_200():
    response = client.get("/resources/1")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Identity security lab",
    }


def test_missing_resource_returns_404():
    response = client.get("/resources/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Resource not found"}


def test_invalid_resource_id_returns_422():
    response = client.get("/resources/abc")

    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(
        error["loc"] == ["path", "resource_id"]
        and error["type"] == "int_parsing"
        for error in errors
    )