import json
import time
from bunch import Bunch
from starlette.testclient import TestClient
from app.main import api
from app.model.petition import Petition
from app.routers.petitions import _retrieve_verification_key, _retrieve_credential
from app.utils.helpers import zencode, CONTRACTS
from tests.conftest import AAID

PETITION_ID = f"PETITION_{int(time.time())}"


def auth():
    client = TestClient(api)
    r = client.post(
        "/token", data=dict(username="demo", password="demo", grant_type="password")
    )
    return r.json()["access_token"]


def petition_auth():
    client = TestClient(api)
    r = client.post(
        "/token", data=dict(username="tdemo", password="tdemo", grant_type="password")
    )
    return r.json()["access_token"]


def test_create_petition(client):
    r = client.post(
        "/petitions/",
        json=dict(
            petition_id=PETITION_ID,
            credential_issuer_url="https://credential-test.dyne.org",
            authorizable_attribute_id=AAID,
            credential_issuer_petition_value=[
                {"name": "zip_code", "value": "08001"},
                {"name": "email", "value": "puria@example.com"},
            ],
        ),
        headers={"Authorization": f"Bearer {petition_auth()}"},
    )
    assert r.status_code == 200, r.json()
    assert PETITION_ID in json.dumps(r.json())
    assert "credential_issuer_url" in r.json(), r.json()
    assert "updated_at" in r.json(), r.json()
    assert r.json()["status"] == "OPEN", r.json()


def test_get_petition(client):
    r = client.get(
        f"/petitions/{PETITION_ID}", headers={"Authorization": "Bearer %s" % auth()}
    )
    assert r.status_code == 200
    assert PETITION_ID in json.dumps(r.json())
    assert "credential_issuer_url" in r.json()
    assert "updated_at" in r.json()
    assert r.json()["status"] == "OPEN"


def test_not_found_petition(client):
    r = client.get(
        "/petitions/petition_fake", headers={"Authorization": "Bearer %s" % auth()}
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Petition not Found"


def test_not_found_ci_server(client):
    r = client.post(
        "/petitions/",
        json=dict(
            petition_id=PETITION_ID,
            credential_issuer_url="https://supernonexistent.zzz",
            authorizable_attribute_id=AAID,
            credential_issuer_petition_value=[],
        ),
        headers={"Authorization": "Bearer %s" % petition_auth()},
    )
    message = "Credential issuer server is unreachable, please double check the 'credential_issuer_url' field"
    assert r.status_code == 424
    assert r.json()["detail"] == message


def test_duplicate_create_petition(client):
    r = client.post(
        "/petitions/",
        json=dict(
            petition_id=PETITION_ID,
            credential_issuer_url="https://credential-test.dyne.org",
            authorizable_attribute_id=AAID,
            credential_issuer_petition_value=[
                {"name": "zip_code", "value": "08001"},
                {"name": "email", "value": "puria@example.com"},
            ],
        ),
        headers={"Authorization": "Bearer %s" % petition_auth()},
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "Duplicate Petition Id"


def test_sign(client):
    petition = Bunch(
        petition_id=PETITION_ID,
        credential_issuer_url="https://credential-test.dyne.org",
        authorizable_attribute_id=AAID,
        credential_issuer_petition_value=[
            {"name": "zip_code", "value": "08001"},
            {"name": "email", "value": "puria@example.com"},
        ],
    )

    vk = _retrieve_verification_key(petition)
    credential = _retrieve_credential(petition)
    petition_signature = zencode(
        CONTRACTS.SIGN_PETITION,
        keys=credential,
        data=json.dumps(vk),
        placeholders={
            "petition": petition.petition_id,
            "MadHatter": "issuer_identifier",
        },
    )

    r = client.post(
        f"/petitions/{petition.petition_id}/sign",
        headers={"Authorization": "Bearer %s" % auth()},
        json=json.loads(petition_signature),
    )

    assert r.status_code == 200

    p = Petition.by_pid(PETITION_ID)
    petition = json.loads(p.petition)
    assert petition["petition"]["scores"]["pos"]["right"] != "Infinity"
    assert petition["petition"]["scores"]["pos"]["left"] != "Infinity"
    assert petition["petition"]["scores"]["neg"]["right"] != "Infinity"
    assert petition["petition"]["scores"]["neg"]["left"] != "Infinity"


def test_duplicate_sign(client):
    petition = Bunch(
        petition_id=PETITION_ID,
        credential_issuer_url="https://credential-test.dyne.org",
        authorizable_attribute_id=AAID,
        credential_issuer_petition_value=[
            {"name": "zip_code", "value": "08001"},
            {"name": "email", "value": "puria@example.com"},
        ],
    )

    vk = _retrieve_verification_key(petition)
    credential = _retrieve_credential(petition)

    petition_signature = zencode(
        CONTRACTS.SIGN_PETITION,
        keys=credential,
        data=json.dumps(vk),
        placeholders={
            "petition": petition.petition_id,
            "MadHatter": "issuer_identifier",
        },
    )

    r = client.post(
        f"/petitions/{petition.petition_id}/sign",
        headers={"Authorization": "Bearer %s" % auth()},
        json=json.loads(petition_signature),
    )

    assert r.status_code == 424
    assert r.json()["detail"] == "Petition signature is duplicate or not valid"


def test_tally(client):
    r = client.post(
        f"/petitions/{PETITION_ID}/tally",
        json=dict(authorizable_attribute_id=AAID),
        headers={"Authorization": f"Bearer {petition_auth()}"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "CLOSED"


def test_auth_tally(client, mocker):
    r = client.post(
        f"/petitions/{PETITION_ID}/tally",
        json=dict(authorizable_attribute_id=AAID),
        headers={"Authorization": f"Bearer {auth()}"},
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authorized to control this petition"


def test_count(client):
    time.sleep(3)
    r = client.post(f"/petitions/{PETITION_ID}/count")
    assert r.status_code == 200
    assert "results" in r.json()
    assert r.json()["results"]["pos"] == 1
