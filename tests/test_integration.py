import json
import uuid

import pytest
import requests

from environs import Env
from app.utils.helpers import zencode, CONTRACTS

env = Env()
env.read_env()

CREDENTIALS_API_URL = env("CREDENTIALS_API_URL")
PETITION_API_URL = env("PETITION_API_URL")
PETITION_USERNAME = env("PETITION_USERNAME")
PETITION_PASSWORD = env("PETITION_PASSWORD")
CREDENTIAL_ISSUER_USERNAME = env("CREDENTIAL_ISSUER_USERNAME")
CREDENTIAL_ISSUER_PASSWORD = env("CREDENTIAL_ISSUER_PASSWORD")
AUTH_ATTR_CODE_VALID_VALUE = env("AUTH_ATTR_CODE_VALID_VALUE")
TALLY_USERNAME = env("TALLY_USERNAME")
TALLY_PASSWORD = env("TALLY_PASSWORD")


class PetitionSignIntegrationTester:
    def __init__(self, petition_id=None):
        self.verification_key = None
        self.sk = None
        self.credential = None
        self.aa_id = "***"
        self.petition_id = petition_id

    @staticmethod
    def _auth_call(url, data):
        r = requests.post(url, json=data)
        return r.json()

    def ci_call(self, endpoint, data):
        url = f"{CREDENTIALS_API_URL}{endpoint}"
        return self._auth_call(url, data)

    def petition_call(self, endpoint, data):
        url = f"{PETITION_API_URL}{endpoint}"
        return self._auth_call(url, data)

    def get_credential(self):
        self.sk = zencode(CONTRACTS.CITIZEN_KEYGEN)
        blind_sign_request = zencode(CONTRACTS.CITIZEN_REQ_BLIND_SIG, keys=self.sk)
        values = [{"name": "code", "value": AUTH_ATTR_CODE_VALID_VALUE}]

        data = dict(
            authorizable_attribute_id=self.aa_id,
            blind_sign_request=json.loads(blind_sign_request),
            values=values,
        )
        return self.ci_call("/credential", data=data)

    def get_verification_key(self):
        r = requests.get(f"{CREDENTIALS_API_URL}/authorizable_attribute/{self.aa_id}")
        self.verification_key = r.json()["verification_key"]
        return self.verification_key

    def aggregate_credential(self):
        data = self.get_credential()
        self.credential = zencode(
            CONTRACTS.AGGREGATE_CREDENTIAL, keys=self.sk, data=json.dumps(data)
        )
        return self.credential

    def petition_signature(self):
        self.get_verification_key()
        return zencode(
            CONTRACTS.SIGN_PETITION,
            keys=self.credential,
            data=json.dumps(self.verification_key),
            placeholders={"petition": self.petition_id},
        )

    def sign_petition(self, petition_signature):
        petition = self.petition_id if self.petition_id else "29"
        return self.petition_call(
            f"/petitions/{petition}/sign", data=json.loads(petition_signature)
        )

    def run(self):
        self.aggregate_credential()
        petition_signature = self.petition_signature()
        return self.sign_petition(petition_signature)


class PetitionTallyIntegrationTester:
    def __init__(self):
        self._get_token()
        self.petition_id = None

    def _get_token(self):
        r = requests.post(
            f"{PETITION_API_URL}/token",
            data={"username": TALLY_USERNAME, "password": TALLY_PASSWORD},
        )
        self.petition_token = r.json()["access_token"]
        return self.petition_token

    @staticmethod
    def _auth_call(url, data, token):
        r = requests.post(url, json=data, headers={"Authorization": f"Bearer {token}"})
        return r.json()

    def petition_call(self, endpoint, data):
        url = f"{PETITION_API_URL}{endpoint}"
        return self._auth_call(url, data, self.petition_token)

    def create_petition(self):
        self.petition_id = str(uuid.uuid4())
        data = dict(
            petition_id=self.petition_id, credential_issuer_url=CREDENTIALS_API_URL
        )
        result = self.petition_call("/petitions/", data=data)
        assert "petition_id" in result
        assert self.petition_id == result["petition_id"]
        return result

    def tally_petition(self):
        r = requests.post(
            f"{PETITION_API_URL}/token",
            data=dict(
                username=TALLY_USERNAME, password=TALLY_PASSWORD, grant_type="password"
            ),
        )
        token = r.json()["access_token"]

        r = requests.post(
            f"{PETITION_API_URL}/petitions/{self.petition_id}/tally",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "CLOSED"

    def run(self):
        self.create_petition()
        t = PetitionSignIntegrationTester(petition_id=self.petition_id)
        result = t.run()
        assert "petition_id" in result
        assert self.petition_id == result["petition_id"]
        self.tally_petition()
        return result


def test_whole_tally(request):
    if not request.config.getoption("--with-integration-test"):
        pytest.skip("Need --with-integration-test option to run")
    else:
        t = PetitionTallyIntegrationTester()
        t.run()
