from starlette.testclient import TestClient

from app.main import api


def auth():
    client = TestClient(api)
    r = client.post(
        "/token", data=dict(username="demo", password="demo", grant_type="password")
    )
    return r.json()["access_token"]


def test_create_petition():
    client = TestClient(api)
    resp = client.post(
        "/petitions",
        json=dict(
            petition_id="test_petition",
            credential_issuer_url="https://petitions.decodeproject.eu",
        ),
        headers={"Authorization": "Bearer %s" % auth()},
        allow_redirects=False,
    )
    r = client.post(
        resp.headers["location"],
        json=dict(
            petition_id="test_petition",
            credential_issuer_url="https://petitions.decodeproject.eu",
        ),
        headers={"Authorization": "Bearer %s" % auth()},
    )
    assert r.status_code == 200
    assert "petition_id" in r.json()
    assert "credential_issuer_url" in r.json()
    assert "updated_at" in r.json()
