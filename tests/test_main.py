def test_token(client):
    r = client.post(
        "/token", data=dict(username="demo", password="demo", grant_type="password")
    )
    assert r.json()["access_token"]
    assert r.json()["token_type"] == "bearer"


def test_wrong_auth(client):
    r = client.post(
        "/token", data=dict(username="fake", password="fake", grant_type="password")
    )
    assert r.status_code == 400
