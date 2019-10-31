import logging

from pathlib import Path
from hashlib import sha256

import jwt
from environs import Env
from fastapi import HTTPException
from jwt import PyJWTError
from pydantic import BaseModel
from starlette.status import HTTP_403_FORBIDDEN
from zenroom import zenroom

env = Env()
env.read_env()


class CONTRACTS:
    ISSUER_KEYGEN = "issuer_keygen.zen"
    PUBLIC_VERIFY = "publish_verifier.zen"
    BLIND_SIGN = "issuer_sign.zen"
    CITIZEN_KEYGEN = "credential_keygen.zen"
    CITIZEN_REQ_BLIND_SIG = "create_request.zen"
    AGGREGATE_CREDENTIAL = "aggregate_signature.zen"
    PROVE_CREDENTIAL = "create_proof.zen"
    VERIFY_CREDENTIAL = "verify_proof.zen"
    CREATE_PETITION = "create_petition.zen"
    APPROVE_PETITION = "approve_petition.zen"
    SIGN_PETITION = "sign_petition.zen"
    INCREMENT_PETITION = "aggregate_petition_signature.zen"
    TALLY_PETITION = "tally_petition.zen"
    COUNT_PETITION = "count_petition.zen"


def get_logger():
    return logging.getLogger("gunicorn.error")


def debug(msg):
    get_logger()
    if env.bool("DEBUG"):
        logging.debug(msg)


def get_contract(name):
    contracts = Path(env("CONTRACTS_DIR"))
    return contracts.joinpath(name).read_text()


def keys():
    name = sha256(b"issuer_identifier").hexdigest()
    credentials = Path(env("CREDENTIAL_ISSUER_CREDENTIALS_DIR"))
    return credentials.joinpath(f"{name}.keys").read_text()


def get_credential(aaid):
    credentials = Path(env("CREDENTIAL_ISSUER_CREDENTIALS_DIR"))
    name = sha256(aaid.encode()).hexdigest()
    file = credentials.joinpath(name)
    if file.is_file():
        return file.read_text()
    return False


def save_credential(aaid, credential):
    credentials = Path(env("CREDENTIAL_ISSUER_CREDENTIALS_DIR"))
    name = sha256(aaid.encode()).hexdigest()
    credentials.joinpath(name).write_text(credential)


def allowed_to_control_petition(token):
    class TokenPayload(BaseModel):
        username: str = None
        password: str = None

    try:
        payload = jwt.decode(
            token, env("JWT_RANDOM_SECRET"), algorithms=env("JWT_ALGORITHM")
        )
        token_data = TokenPayload(**payload)
    except PyJWTError:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
    username = env("JWT_TALLY_USERNAME")
    password = env("JWT_TALLY_PASSWORD")
    if token_data.username == username and token_data.password == password:
        return True

    return False


def zencode(name, keys=None, data=None, placeholders={}):
    script = get_contract(name)
    for k, v in placeholders.items():
        script = script.replace(f"'{k}'", f"'{v}'")

    debug("+" * 50)
    debug(f"EXECUTING {name}")
    debug(f"CODE: \n{script}")
    debug("+" * 50)
    debug(f"DATA: {data}")
    debug(f"KEYS: {keys}")
    debug("+" * 50)

    result = zenroom.zencode_exec(script=script, keys=keys, data=data)
    return result.stdout
