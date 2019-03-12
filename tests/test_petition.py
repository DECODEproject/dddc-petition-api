import pytest
from starlette.testclient import TestClient
from app.main import api
from app.model import Base, engine


@pytest.fixture(scope="session")
def teardown(request):
    def fn():
        Base.metadata.drop_all(bind=engine)

    request.addfinalizer(fn)


def auth():
    client = TestClient(api)
    r = client.post(
        "/token", data=dict(username="demo", password="demo", grant_type="password")
    )
    return r.json()["access_token"]


def test_create_petition(teardown, mocker):
    def get_petition(url):
        petition = '{"petition":{"owner":"042a83a3432eb01db3085ebd0249a72801f41b0b5c6a8937ef1f3dbf49dab2e44642abb3b01b50dccdd0f51ea2f57b4099340fd89ec09febafc9822cd2324e3100cbbfca36fe4286e3e29fc9d411f255f037d829f3d9732d9efa4f90931e10fa88","scores":{"pos":{"left":"Infinity","right":"Infinity"},"schema":"petition_scores","encoding":"hex","zenroom":"0.8.1","neg":{"left":"Infinity","right":"Infinity"},"curve":"bls383"},"schema":"petition","encoding":"hex","uid":"test_petition","zenroom":"0.8.1","curve":"bls383"},"verifier":{"version":"63727970746f5f636f636f6e75742e6c756120312e30","alpha":"497fbf58544670ede3ffd8876fb59e9b180ee576886e2fa38be85e4e7e51acf2986d0aac9316406dcbb3a0471733b6e3246d9df692d65f1618e88c96bf8a9c531edaad84c0ff870a17919d3d4d63ce3bb2ad4c1487d18dc8b44563786a3a331735115a0c82815226f65f5fc0c0680a7de480ff6313e64389eaf4003277e65603746fe6ed7d0a43cc2963d4a7a6d3f1c10704f55b474d3845915a293dba6d5c214de2a1468c1f963dd9cdbde9c5a0a04492d4032a6ae939d803e69867f8f9c322","schema":"issue_verify","encoding":"hex","beta":"464905d0833fb34adeb37c9f197e5a6e6f52601c74a47c3645fd0fed9d06f1890c9bdac2a168791d2f2a40b9c83c39ef36ab8d94191538ee46a85d6a0d09049f592c8953f075f30bc7fdab88ee54a61b21781917c446b2bd9ee7d6f8137f37bc3bc8ebd155141237b5df4b7e24fd1e5e52257e5be6c1aef101a8ba23b143cc939efd587d27d1d060cb06d57cb24261b931c0c5ea337aff24c74095df6eb61b51b9153fa5f801feb6ca47d066cb1da338ac49c702cde4d44d66646a9cd1a83ffd","zenroom":"0.8.1","curve":"bls383"}}'
        ci_uid = "issuer_identifier"
        return petition, ci_uid

    mocker.patch(
        "app.routers.petitions._generate_petition_object", side_effect=get_petition
    )

    client = TestClient(api)
    resp = client.post(
        "/petitions",
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


def test_get_petition():
    client = TestClient(api)
    r = client.get(
        "/petitions/test_petition", headers={"Authorization": "Bearer %s" % auth()}
    )
    assert r.status_code == 200
    assert "petition_id" in r.json()
    assert "credential_issuer_url" in r.json()
    assert "updated_at" in r.json()


def test_not_found_petition():
    client = TestClient(api)
    r = client.get(
        "/petitions/test_petition_fake", headers={"Authorization": "Bearer %s" % auth()}
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Petition not Found"


def test_not_found_ci_server():
    client = TestClient(api)
    resp = client.post(
        "/petitions",
        headers={"Authorization": "Bearer %s" % auth()},
        allow_redirects=False,
    )
    r = client.post(
        resp.headers["location"],
        json=dict(
            petition_id="test_petition",
            credential_issuer_url="https://supernonexistent.zzz",
        ),
        headers={"Authorization": "Bearer %s" % auth()},
    )
    assert r.status_code == 424
    assert r.json()["detail"] == "Credential issuer server is not available"
