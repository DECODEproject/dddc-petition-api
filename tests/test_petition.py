import json

from starlette.testclient import TestClient
from app.main import api
from app.model.petition import Petition


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


def test_create_petition(mocker, client):
    def get_petition(url):
        petition = '{"petition":{"owner":"041760bc292c7f2fd0274041698c6d86060263cd06201ae734b0cdbad7d5281f59c04fb8174ca9f47ced35f14d8201014604896f830b6ff6bbbde995a534afc31d829b908d05e1368348fca124bd3c632cf535470746a56cc707a651fc9065eedb","uid":"petition","scores":{"pos":{"right":"Infinity","left":"Infinity"},"schema":"petition_scores","curve":"bls383","neg":{"right":"Infinity","left":"Infinity"},"zenroom":"0.8.1","encoding":"hex"},"schema":"petition","curve":"bls383","zenroom":"0.8.1","encoding":"hex"},"verifier":{"beta":"3d53f5f3c6b87285b4d16adf3f388aedb742e3cce535e0d7aa6f3d64c00636269258ea0166839242a22532e1850a9d5c18aff4e4c20fd1603611ee38bcee31c1fb55a63c3a54b931d91d5b99f53b45913d1947797760e6be7d63a9e761d8a54025cd8867eab8eaa59ffa326b31f5e507dbc76904dc1378daa0a987b79ca497cafac99f67e2dc0ff90f3f514070dae220524bb82745575a8328a7d03115c6af30852afb03088bd44e8f3893d14b2c399e0a25286772d312b0748093b180a5979c","version":"63727970746f5f636f636f6e75742e6c756120312e30","schema":"issue_verify","alpha":"0029b4af71e33a40426e02c722f4fac1e60bdb83d20793045ec96bef24f7b71ae8570c673293c85c292fa8d83e10f4dc10946473fd2154aac5ad1027190fc84192e1cd325dbfadd10c2777b8a8831fd8f9768048f0d198442e8fd2f020d134210588fa17c13acec6eaf96b0473f418e6f614bc0316936928e77a6eb4720bb44d7862735cc6fb19e21ce5a5d3df398b3049460ae593373b14a8125480e64039f30dfadc4bc7e1d0ab7a9012b141f7dc319892c39a1a365d61fb2e46dbb992887a","curve":"bls383","zenroom":"0.8.1","encoding":"hex"}}'
        ci_uid = "issuer_identifier"
        return petition, ci_uid

    mocker.patch(
        "app.routers.petitions._generate_petition_object", side_effect=get_petition
    )

    resp = client.post(
        "/petitions",
        headers={"Authorization": "Bearer %s" % petition_auth()},
        allow_redirects=False,
    )
    r = client.post(
        resp.headers["location"],
        json=dict(
            petition_id="petition",
            credential_issuer_url="https://petitions.decodeproject.eu",
        ),
        headers={"Authorization": "Bearer %s" % petition_auth()},
    )
    assert r.status_code == 200
    assert "petition_id" in r.json()
    assert "credential_issuer_url" in r.json()
    assert "updated_at" in r.json()
    assert r.json()["status"] == "OPEN"


def test_get_petition(client):
    r = client.get(
        "/petitions/petition", headers={"Authorization": "Bearer %s" % auth()}
    )
    assert r.status_code == 200
    assert "petition_id" in r.json()
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
    resp = client.post(
        "/petitions",
        headers={"Authorization": "Bearer %s" % petition_auth()},
        allow_redirects=False,
    )
    r = client.post(
        resp.headers["location"],
        json=dict(
            petition_id="petition", credential_issuer_url="https://supernonexistent.zzz"
        ),
        headers={"Authorization": "Bearer %s" % petition_auth()},
    )
    assert r.status_code == 424
    assert r.json()["detail"] == "Credential issuer server is not available"


def test_duplicate_create_petition(mocker, client):
    def get_petition(url):
        petition = '{"petition":{"owner":"041760bc292c7f2fd0274041698c6d86060263cd06201ae734b0cdbad7d5281f59c04fb8174ca9f47ced35f14d8201014604896f830b6ff6bbbde995a534afc31d829b908d05e1368348fca124bd3c632cf535470746a56cc707a651fc9065eedb","uid":"petition","scores":{"pos":{"right":"Infinity","left":"Infinity"},"schema":"petition_scores","curve":"bls383","neg":{"right":"Infinity","left":"Infinity"},"zenroom":"0.8.1","encoding":"hex"},"schema":"petition","curve":"bls383","zenroom":"0.8.1","encoding":"hex"},"verifier":{"beta":"3d53f5f3c6b87285b4d16adf3f388aedb742e3cce535e0d7aa6f3d64c00636269258ea0166839242a22532e1850a9d5c18aff4e4c20fd1603611ee38bcee31c1fb55a63c3a54b931d91d5b99f53b45913d1947797760e6be7d63a9e761d8a54025cd8867eab8eaa59ffa326b31f5e507dbc76904dc1378daa0a987b79ca497cafac99f67e2dc0ff90f3f514070dae220524bb82745575a8328a7d03115c6af30852afb03088bd44e8f3893d14b2c399e0a25286772d312b0748093b180a5979c","version":"63727970746f5f636f636f6e75742e6c756120312e30","schema":"issue_verify","alpha":"0029b4af71e33a40426e02c722f4fac1e60bdb83d20793045ec96bef24f7b71ae8570c673293c85c292fa8d83e10f4dc10946473fd2154aac5ad1027190fc84192e1cd325dbfadd10c2777b8a8831fd8f9768048f0d198442e8fd2f020d134210588fa17c13acec6eaf96b0473f418e6f614bc0316936928e77a6eb4720bb44d7862735cc6fb19e21ce5a5d3df398b3049460ae593373b14a8125480e64039f30dfadc4bc7e1d0ab7a9012b141f7dc319892c39a1a365d61fb2e46dbb992887a","curve":"bls383","zenroom":"0.8.1","encoding":"hex"}}'
        ci_uid = "issuer_identifier"
        return petition, ci_uid

    mocker.patch(
        "app.routers.petitions._generate_petition_object", side_effect=get_petition
    )

    resp = client.post(
        "/petitions",
        headers={"Authorization": "Bearer %s" % petition_auth()},
        allow_redirects=False,
    )
    r = client.post(
        resp.headers["location"],
        json=dict(
            petition_id="petition",
            credential_issuer_url="https://petitions.decodeproject.eu",
        ),
        headers={"Authorization": "Bearer %s" % petition_auth()},
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "Duplicate Petition Id"


def test_sign(client):
    r = client.post(
        "/petitions/petition/sign",
        headers={"Authorization": "Bearer %s" % auth()},
        json={
            "petition_signature": {
                "uid_signature": "0429998a1c4cf7e0aba351824c6c2b37200c485fa2a5044b8b0d09962c112dea419b51998f21c4769b7a1e7e0da0f306d14e10c5d9d9d182bb326a80ea7ab2cffcb6f8c90112c124fb0c671efa2edb1b8e89b68c3068673acfb6e2781ad82ea78e",
                "proof": {
                    "zenroom": "0.8.1",
                    "kappa": "02a37d181cd6254ec8809e932cb2dec95613be3d7ce46d8e7b6bdae40ba932b7e08226704f7a697e277f6253637bf2205300ffe39da64079f834c70234d966a931b0e064d6d5003eb7533baf6a6523dac7630df521712e0ba5ecc4f3852e03ca0c99feceb5f50ea530f410493b1a48c7689cfa242371b5d7f4ea2cd56b8172380e7b1e4c639e29e2e0ee906d6998f70d24ec1df0de57f1fef6dbcd0ea70d4d2806aa02cd45923ea6aa8fd48cc337dcb5ddd368d0b701829aed7d02abca18a39e",
                    "encoding": "hex",
                    "schema": "theta",
                    "sigma_prime": {
                        "h_prime": "0442f7e94e618eb45a86add07a124cce8a202135beb49bf1e574c2bbec537d8b648e45cc4b8ab7f70800a0318fe54f5b193c9ad9bc5ea48ae69956b202eccfb64d8539fb69d8e884c6cce93e52cf4739e125759b0c848595679f4bc51994196331",
                        "s_prime": "042b5ce4edade172e3e4f362d3622a9700fc181b3811ce066d2b996d6e6281b320a6734b7ba28d43ce96e639988543dfab3139e33770581e856116c60a2018cc4f4baca43de55dcee6eb6e1a50a10df54e67ef57f4aba3da0bd1ee52124fdec786",
                    },
                    "nu": "0453ec0e9b066157bcb2fe5a1f7cb4c15445825881afa5e91fc906c4b90917caea5e744817d54e915ba20b87fe9190782f123ef3e7e16b0a6f641350f2dfa3cbfb2756237905b7a6fd3a3a1157bbe3d53e598960b1eaac2be2f843e48ef3c4b98c",
                    "pi_v": {
                        "rr": "9d822fb7219f9476a858cdacb596acb7f25a7b0eec3660fa09f02ceca0e0240f",
                        "rm": "9168a7039f9a1967bf137c881e15f09fe6c498262286a2a9cad7b74b75db922d",
                        "c": "b7fe229108d5884093d0736b21ddab269c3457d7e4dd4c0df32f34b507d8d820",
                    },
                    "curve": "bls383",
                },
                "uid_petition": "petition",
            }
        },
    )

    assert r.status_code == 200
    p = Petition.by_pid("petition")
    petition = json.loads(p.petition)
    assert petition["petition"]["scores"]["pos"]["right"] != "Infinity"
    assert petition["petition"]["scores"]["pos"]["left"] != "Infinity"
    assert petition["petition"]["scores"]["neg"]["right"] != "Infinity"
    assert petition["petition"]["scores"]["neg"]["left"] != "Infinity"


def test_duplicate_sign(client):
    r = client.post(
        "/petitions/petition/sign",
        headers={"Authorization": "Bearer %s" % auth()},
        json={
            "petition_signature": {
                "uid_signature": "0429998a1c4cf7e0aba351824c6c2b37200c485fa2a5044b8b0d09962c112dea419b51998f21c4769b7a1e7e0da0f306d14e10c5d9d9d182bb326a80ea7ab2cffcb6f8c90112c124fb0c671efa2edb1b8e89b68c3068673acfb6e2781ad82ea78e",
                "proof": {
                    "zenroom": "0.8.1",
                    "kappa": "02a37d181cd6254ec8809e932cb2dec95613be3d7ce46d8e7b6bdae40ba932b7e08226704f7a697e277f6253637bf2205300ffe39da64079f834c70234d966a931b0e064d6d5003eb7533baf6a6523dac7630df521712e0ba5ecc4f3852e03ca0c99feceb5f50ea530f410493b1a48c7689cfa242371b5d7f4ea2cd56b8172380e7b1e4c639e29e2e0ee906d6998f70d24ec1df0de57f1fef6dbcd0ea70d4d2806aa02cd45923ea6aa8fd48cc337dcb5ddd368d0b701829aed7d02abca18a39e",
                    "encoding": "hex",
                    "schema": "theta",
                    "sigma_prime": {
                        "h_prime": "0442f7e94e618eb45a86add07a124cce8a202135beb49bf1e574c2bbec537d8b648e45cc4b8ab7f70800a0318fe54f5b193c9ad9bc5ea48ae69956b202eccfb64d8539fb69d8e884c6cce93e52cf4739e125759b0c848595679f4bc51994196331",
                        "s_prime": "042b5ce4edade172e3e4f362d3622a9700fc181b3811ce066d2b996d6e6281b320a6734b7ba28d43ce96e639988543dfab3139e33770581e856116c60a2018cc4f4baca43de55dcee6eb6e1a50a10df54e67ef57f4aba3da0bd1ee52124fdec786",
                    },
                    "nu": "0453ec0e9b066157bcb2fe5a1f7cb4c15445825881afa5e91fc906c4b90917caea5e744817d54e915ba20b87fe9190782f123ef3e7e16b0a6f641350f2dfa3cbfb2756237905b7a6fd3a3a1157bbe3d53e598960b1eaac2be2f843e48ef3c4b98c",
                    "pi_v": {
                        "rr": "9d822fb7219f9476a858cdacb596acb7f25a7b0eec3660fa09f02ceca0e0240f",
                        "rm": "9168a7039f9a1967bf137c881e15f09fe6c498262286a2a9cad7b74b75db922d",
                        "c": "b7fe229108d5884093d0736b21ddab269c3457d7e4dd4c0df32f34b507d8d820",
                    },
                    "curve": "bls383",
                },
                "uid_petition": "petition",
            }
        },
    )

    assert r.status_code == 424
    assert r.json()["detail"] == "Petition signature is duplicate or not valid"


def test_second_sign(client):
    signature = {
        "petition_signature": {
            "proof": {
                "zenroom": "0.8.1",
                "schema": "theta",
                "sigma_prime": {
                    "h_prime": "040fbfb4e356958ec30a9ff17ce1418b453218e5fc8c90b5e184490a2a7dddc1c15136df4a98230abfabbde3777fa152d4354685e45ec06cfc9920cfca9203b0f1f84a998c6022342ae3dd4694af2c6787c109f2ada3fac217c3ab08a89e994098",
                    "s_prime": "0406a5556787bc61de0277d870976fdaf1b7eee635cfeafc5901a45f7fe7600e221713ba5c73461dedb67e4cb07e502693225c20782e25a02c744ce674233cf30df31148ae81bf703dd8b412ea13fcec8f87de032f9ec03849f482cca94e765622",
                },
                "kappa": "4ce2dcae6bb9c6b16447ea0be2d0b02cf39e51284d0377a27fa8faa66d91081b74878d0917e7939054ab09ca38090abf0b32fa57d20a061d72dd7f9fb7f53eade11c15c97ff756f69740c37d293f863cbd613f4476f708f80c772e19c50e7420344b1639d01742bc7782fce2d9140c7fd39b8e4b5cf8d3f6414d983628816682dac5ee5e2c23a0001aad40c97b11d86a4da31e3288b5f505588b1b0531ba72a503364172be600b0ab9f623a252d84dda4c85f06dc88b7c8a14b0e2aebc9a58cf",
                "curve": "bls383",
                "pi_v": {
                    "c": "b2bff5660b97f691e44df723bd32c6bb974204e46672a68385edd3447ef1e798",
                    "rm": "99744cfcd802a3fa3e20ed531e516d051114cdaf3525dc948b2c9ea6e48572",
                    "rr": "d370bfcc0290f855c7e19480efe573ed585a09542e834cbb5ca0c9ff09bec220",
                },
                "encoding": "hex",
                "nu": "04472d3da13ca5c5d4692877b2dfbb37fb6187ef58bf860ba98941acf6428e9fef8786424bf881eb1052da2fdbef73469b28ce6a9c9726bbf3cfb737240ae4126d1ba8486022b9cabaa307f0fe8c34c5295450e7bf0eb277da3d88ecb3af09b01f",
            },
            "uid_petition": "petition",
            "uid_signature": "04265eb36ae4abf484252691ea1059523b8825f38e44edbc7b5114acccdbf5467a0ee9aaa69494b1a8bcea57d42883c22427068a7cda8312d0a4b33bf2cf0354e5468a5e239582b411811598f447e24f2db46d93437c59d12ae6cad9fe23493ffc",
        }
    }
    r = client.post(
        "/petitions/petition/sign",
        headers={"Authorization": "Bearer %s" % auth()},
        json=signature,
    )

    assert r.status_code == 200
    p = Petition.by_pid("petition")
    petition = json.loads(p.petition)
    assert petition["petition"]["scores"]["pos"]["right"] != "Infinity"
    assert petition["petition"]["scores"]["pos"]["left"] != "Infinity"
    assert petition["petition"]["scores"]["neg"]["right"] != "Infinity"
    assert petition["petition"]["scores"]["neg"]["left"] != "Infinity"


def test_tally(client, mocker):
    _credential = '{"identifier":{"curve":"bls383","zenroom":"0.8.1","private":"e5b785e6131622ca526676fad40ff8e9ab66629642fe4d957422c59d9de8c67b","schema":"cred_keypair","public":"041760bc292c7f2fd0274041698c6d86060263cd06201ae734b0cdbad7d5281f59c04fb8174ca9f47ced35f14d8201014604896f830b6ff6bbbde995a534afc31d829b908d05e1368348fca124bd3c632cf535470746a56cc707a651fc9065eedb","encoding":"hex"},"credential":{"encoding":"hex","s":"043dab8ade97f8b14ebd02a40e2355f3fb6d52a4c5776f59d960740e069dd79a52e147d55a92098d72ffd72c43b88671813438b4c4ef6d0b45bf3cf16c6ac0d65d53c6f75cebf18916fb7030f7fd791ee6c349e4217d1d9e46124e8eeca7bbfebd","zenroom":"0.8.1","schema":"aggsigma","h":"0427fddcbb32874364799eef2e71ebedaadd0957aba3d88b104eeac5100f73f2e35762a0104b6e456d32535e0ce1423e320ad07289f541a6e83226fb838ccda8a19bd272b527a58f05838bc27913939679bc49479a1d5635e60a6fde1f2ee6fcfb","curve":"bls383"}}'
    _verifier = '{"issuer_identifier":{"verify":{"beta":"3d53f5f3c6b87285b4d16adf3f388aedb742e3cce535e0d7aa6f3d64c00636269258ea0166839242a22532e1850a9d5c18aff4e4c20fd1603611ee38bcee31c1fb55a63c3a54b931d91d5b99f53b45913d1947797760e6be7d63a9e761d8a54025cd8867eab8eaa59ffa326b31f5e507dbc76904dc1378daa0a987b79ca497cafac99f67e2dc0ff90f3f514070dae220524bb82745575a8328a7d03115c6af30852afb03088bd44e8f3893d14b2c399e0a25286772d312b0748093b180a5979c","alpha":"0029b4af71e33a40426e02c722f4fac1e60bdb83d20793045ec96bef24f7b71ae8570c673293c85c292fa8d83e10f4dc10946473fd2154aac5ad1027190fc84192e1cd325dbfadd10c2777b8a8831fd8f9768048f0d198442e8fd2f020d134210588fa17c13acec6eaf96b0473f418e6f614bc0316936928e77a6eb4720bb44d7862735cc6fb19e21ce5a5d3df398b3049460ae593373b14a8125480e64039f30dfadc4bc7e1d0ab7a9012b141f7dc319892c39a1a365d61fb2e46dbb992887a"}}}'
    _keys = '{"identifier":{"private":"e5b785e6131622ca526676fad40ff8e9ab66629642fe4d957422c59d9de8c67b","zenroom":"0.8.1","curve":"bls383","encoding":"hex","public":"041760bc292c7f2fd0274041698c6d86060263cd06201ae734b0cdbad7d5281f59c04fb8174ca9f47ced35f14d8201014604896f830b6ff6bbbde995a534afc31d829b908d05e1368348fca124bd3c632cf535470746a56cc707a651fc9065eedb","schema":"cred_keypair"}}'

    mocker.patch(
        "app.routers.petitions.load_credentials",
        return_value=(_keys, _verifier, _credential),
    )

    r = client.post(
        "/petitions/petition/tally",
        headers={"Authorization": f"Bearer {petition_auth()}"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "CLOSED"


def test_auth_tally(client, mocker):
    _credential = '{"identifier":{"curve":"bls383","zenroom":"0.8.1","private":"e5b785e6131622ca526676fad40ff8e9ab66629642fe4d957422c59d9de8c67b","schema":"cred_keypair","public":"041760bc292c7f2fd0274041698c6d86060263cd06201ae734b0cdbad7d5281f59c04fb8174ca9f47ced35f14d8201014604896f830b6ff6bbbde995a534afc31d829b908d05e1368348fca124bd3c632cf535470746a56cc707a651fc9065eedb","encoding":"hex"},"credential":{"encoding":"hex","s":"043dab8ade97f8b14ebd02a40e2355f3fb6d52a4c5776f59d960740e069dd79a52e147d55a92098d72ffd72c43b88671813438b4c4ef6d0b45bf3cf16c6ac0d65d53c6f75cebf18916fb7030f7fd791ee6c349e4217d1d9e46124e8eeca7bbfebd","zenroom":"0.8.1","schema":"aggsigma","h":"0427fddcbb32874364799eef2e71ebedaadd0957aba3d88b104eeac5100f73f2e35762a0104b6e456d32535e0ce1423e320ad07289f541a6e83226fb838ccda8a19bd272b527a58f05838bc27913939679bc49479a1d5635e60a6fde1f2ee6fcfb","curve":"bls383"}}'
    _verifier = '{"issuer_identifier":{"verify":{"beta":"3d53f5f3c6b87285b4d16adf3f388aedb742e3cce535e0d7aa6f3d64c00636269258ea0166839242a22532e1850a9d5c18aff4e4c20fd1603611ee38bcee31c1fb55a63c3a54b931d91d5b99f53b45913d1947797760e6be7d63a9e761d8a54025cd8867eab8eaa59ffa326b31f5e507dbc76904dc1378daa0a987b79ca497cafac99f67e2dc0ff90f3f514070dae220524bb82745575a8328a7d03115c6af30852afb03088bd44e8f3893d14b2c399e0a25286772d312b0748093b180a5979c","alpha":"0029b4af71e33a40426e02c722f4fac1e60bdb83d20793045ec96bef24f7b71ae8570c673293c85c292fa8d83e10f4dc10946473fd2154aac5ad1027190fc84192e1cd325dbfadd10c2777b8a8831fd8f9768048f0d198442e8fd2f020d134210588fa17c13acec6eaf96b0473f418e6f614bc0316936928e77a6eb4720bb44d7862735cc6fb19e21ce5a5d3df398b3049460ae593373b14a8125480e64039f30dfadc4bc7e1d0ab7a9012b141f7dc319892c39a1a365d61fb2e46dbb992887a"}}}'
    _keys = '{"identifier":{"private":"e5b785e6131622ca526676fad40ff8e9ab66629642fe4d957422c59d9de8c67b","zenroom":"0.8.1","curve":"bls383","encoding":"hex","public":"041760bc292c7f2fd0274041698c6d86060263cd06201ae734b0cdbad7d5281f59c04fb8174ca9f47ced35f14d8201014604896f830b6ff6bbbde995a534afc31d829b908d05e1368348fca124bd3c632cf535470746a56cc707a651fc9065eedb","schema":"cred_keypair"}}'

    mocker.patch(
        "app.routers.petitions.load_credentials",
        return_value=(_keys, _verifier, _credential),
    )

    r = client.post(
        "/petitions/petition/tally", headers={"Authorization": f"Bearer {auth()}"}
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authorized to control this petition"


def test_count(client):
    r = client.post(
        "/petitions/petition/count", headers={"Authorization": "Bearer %s" % auth()}
    )
    assert r.status_code == 200
    assert "uid" in r.json()
    assert r.json()["result"] == 2
    assert r.json()["uid"] == "petition"
