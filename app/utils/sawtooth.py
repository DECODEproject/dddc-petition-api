import json
import urllib

import requests
from environs import Env

env = Env()
env.read_env()

with env.prefixed("SAWTOOTH_MIDDLEWARE_PETITION_API_"):
    address = env("ADDRESS")
    server = env("SERVER_ADDRESS")
    username = env("USERNAME")
    password = env("PASSWORD")


def _build_url(api_endpoint, sawtooth_endpoint="/batches"):
    server_uri = f"{server}{sawtooth_endpoint}" if sawtooth_endpoint else server
    url = urllib.parse.quote_plus(server_uri)
    return f"{address}{api_endpoint}?address={url}"


def _get_token():
    r = requests.post(
        f"{address}/token",
        data=dict(username=username, password=password, grant_type="password"),
    )
    return r.json()["access_token"]


def save_petition(petition_request, verifier, petition_id):
    params = dict(
        petition_id=petition_id,
        petition_request=json.loads(petition_request),
        verifier=verifier,
    )

    r = requests.post(
        _build_url("/petitions/"),
        json=params,
        headers={"Authorization": f"Bearer {_get_token()}"},
        allow_redirects=True,
    )
    return r


def sign_petition(signature, petition_id):
    print(signature)
    r = requests.post(
        _build_url(f"/petitions/{petition_id}/sign"),
        json=signature,
        headers={"Authorization": f"Bearer {_get_token()}"},
        allow_redirects=True,
    )
    return r


def tally_petition(credentials, petition_id):
    r = requests.post(
        _build_url(f"/petitions/{petition_id}/tally"),
        json=json.loads(credentials),
        headers={"Authorization": f"Bearer {_get_token()}"},
        allow_redirects=True,
    )
    return r


def count_petition(petition_id):
    r = requests.get(
        _build_url(f"/petitions/{petition_id}/count", sawtooth_endpoint=None),
        headers={"Authorization": f"Bearer {_get_token()}"},
        allow_redirects=False,
    )
    return r
