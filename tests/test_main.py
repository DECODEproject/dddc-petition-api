from starlette.testclient import TestClient

from app.main import api


def test_root():
    client = TestClient(api)
    r = client.get("/")
    assert r.json()["message"] == "Welcome to petitions API"
