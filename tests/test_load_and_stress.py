import json

import requests
from bunch import Bunch
from environs import Env
from starlette.testclient import TestClient

from app.main import api
from app.routers.petitions import _retrieve_verification_key
from app.utils.helpers import zencode, CONTRACTS
from tests.conftest import AAID

env = Env()
env.read_env()


def auth():
    client = TestClient(api)
    r = client.post(
        "/token", data=dict(username="demo", password="demo", grant_type="password")
    )
    return r.json()["access_token"]


def petition_auth():
    client = TestClient(api)
    r = client.post(
        "/token",
        data=dict(username="demotally", password="demotally", grant_type="password"),
    )
    return r.json()["access_token"]


def _get_token(url):
    r = requests.post(
        f"{url}/token",
        data={
            "username": env("CREDENTIAL_ISSUER_USERNAME"),
            "password": env("CREDENTIAL_ISSUER_PASSWORD"),
        },
    )
    return r.json()["access_token"]


def stress_sign_petition():
    client = TestClient(api)
    petition = Bunch(
        petition_id="petition",
        credential_issuer_url="http://localhost:5000",
        authorizable_attribute_id=AAID,
        credential_issuer_petition_value=[
            {"name": "zip_code", "value": "08001"},
            {"name": "email", "value": "puria@example.com"},
        ],
    )

    r = client.post(
        "/petitions/",
        json=petition,
        headers={"Authorization": f"Bearer {petition_auth()}"},
    )

    assert r.status_code == 200
    assert petition.petition_id in r.json()

    vk = _retrieve_verification_key(petition)
    url = petition.credential_issuer_url
    value = petition.credential_issuer_petition_value

    for _ in range(500):
        print(f"SIGNING #{_}")
        keys = zencode(CONTRACTS.CITIZEN_KEYGEN)
        blind_sign_request = zencode(CONTRACTS.CITIZEN_REQ_BLIND_SIG, keys=keys)
        data = dict(
            authorizable_attribute_id=AAID,
            blind_sign_request=json.loads(blind_sign_request),
            optional_values=[],
            values=value,
        )
        print(data)
        r = requests.post(
            f"{url}/credential/",
            json=data,
            headers={"Authorization": f"Bearer {_get_token(url)}"},
        )
        credential_request = json.dumps(r.json())
        credential = zencode(
            CONTRACTS.AGGREGATE_CREDENTIAL, keys=keys, data=credential_request
        )
        petition_signature = zencode(
            CONTRACTS.SIGN_PETITION,
            keys=credential,
            data=json.dumps(vk),
            placeholders={"petition": petition.petition_id},
        )

        r = client.post(
            f"/petitions/{petition.petition_id}/sign",
            headers={"Authorization": "Bearer %s" % auth()},
            json=json.loads(petition_signature),
        )

        assert r.status_code == 200
