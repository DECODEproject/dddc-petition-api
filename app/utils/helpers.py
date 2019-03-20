import logging

from pathlib import Path
from hashlib import sha256
from environs import Env
from zenroom import zenroom

env = Env()
env.read_env()


class CONTRACTS:
    ISSUER_KEYGEN = "03-CREDENTIAL_ISSUER-keygen.zencode"
    PUBLIC_VERIFY = "04-CREDENTIAL_ISSUER-publish-verifier.zencode"
    BLIND_SIGN = "05-CREDENTIAL_ISSUER-credential-sign.zencode"
    CITIZEN_KEYGEN = "01-CITIZEN-credential-keygen.zencode"
    CITIZEN_REQ_BLIND_SIG = "02-CITIZEN-credential-request.zencode"
    AGGREGATE_CREDENTIAL = "06-CITIZEN-aggregate-credential-signature.zencode"
    PROVE_CREDENTIAL = "07-CITIZEN-prove-credential.zencode"
    VERIFY_CREDENTIAL = "08-VERIFIER-verify-credential.zencode"
    CREATE_PETITION = "09-CITIZEN-create-petition.zencode"
    APPROVE_PETITION = "10-VERIFIER-approve-petition.zencode"
    SIGN_PETITION = "11-CITIZEN-sign-petition.zencode"
    ADD_SIGNATURE = "12-LEDGER-add-signed-petition.zencode"
    TALLY_PETITION = "13-CITIZEN-tally-petition.zencode"
    COUNT_PETITION = "14-CITIZEN-count-petition.zencode"


def get_logger():
    return logging.getLogger("gunicorn.error")


def debug(msg):
    log = get_logger()
    if env.bool("DEBUG"):
        log.debug(msg)


def get_contract(name):
    contracts = Path(env("CONTRACTS_DIR"))
    return contracts.joinpath(name).read_text()


def load_credentials(ciuid):
    credentials = Path(env("CREDENTIAL_ISSUER_CREDENTIALS_DIR"))
    name = sha256(ciuid.encode()).hexdigest()
    debug(f"loading credentials for {ciuid} => {name}")
    credential = credentials.joinpath(name).read_text()
    verifier = credentials.joinpath(f"{name}.verify").read_text()
    keys = credentials.joinpath(f"{name}.keys").read_text()

    return keys, verifier, credential


def allowed_to_tally(token):
    return token == env("PETITION_CONTROL_TOKEN")


def zencode(name, keys=None, data=None, placeholders={}):
    script = get_contract(name)
    for k, v in placeholders.items():
        script = script.replace(f"'{k}'", f"'{v}'")

    script = script.encode()
    k = keys.encode() if keys else None
    a = data.encode() if data else None
    debug("+" * 50)
    debug(f"EXECUTING {name}")
    debug(f"CODE: \n{script}")
    debug("+" * 50)
    debug(f"DATA: {data}")
    debug(f"KEYS: {keys}")
    debug("+" * 50)

    result, _ = zenroom.execute(script=script, keys=k, data=a)
    return result.decode()
