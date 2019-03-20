import json
import unittest
import requests

from app.utils.helpers import zencode, CONTRACTS

CREDENTIALS_API_URL = "https://credentials.decodeproject.eu"
PETITION_API_URL = "https://petitions.decodeproject.eu"


class IntegrationTester:
    def __init__(self):
        self.verification_key = None
        self.sk = None
        self.credential = None
        self.aa_id = "93de1fc34fab8497bdcb5e211ae96aba1416cc35"

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
        values = [
            {"name": "DNI", "value": "111222333A"},
            {"name": "Census postal code", "value": "08003"},
        ]

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
        )

    def sign_petition(self, petition_signature):
        return self.petition_call(
            "/petitions/some_petition_test/sign", data=json.loads(petition_signature)
        )

    def run(self):
        self.aggregate_credential()
        petition_signature = self.petition_signature()
        print(self.verification_key)
        return self.sign_petition(petition_signature)


class IntegrationTest(unittest.TestCase):
    def test_whole(self):
        t = IntegrationTester()
        result = t.run()
        assert "credential_issuer_url" in result
        assert "petition_id" in result
        assert "status" in result
