from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_file():
    response = client.get("/api/files/not-real/")
    assert response.status_code == 404


def test_rejects_unsupported_file():
    response = client.post("/api/files/", files={"file": ("hello.txt", b"hello", "text/plain")})
    assert response.status_code == 400
