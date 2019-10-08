import json
from typing import List, Dict

import requests
from bunch import Bunch
from environs import Env
from requests.exceptions import ConnectionError
from fastapi import APIRouter, HTTPException, Security, Body
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, UrlStr, Schema
from sqlalchemy.exc import IntegrityError
from starlette.status import (
    HTTP_409_CONFLICT,
    HTTP_404_NOT_FOUND,
    HTTP_424_FAILED_DEPENDENCY,
    HTTP_401_UNAUTHORIZED,
)
from zenroom.zenroom import ZenroomException

from app.model import DBSession
from app.model.petition import Petition, STATUS
from app.utils.helpers import (
    CONTRACTS,
    zencode,
    debug,
    allowed_to_control_petition,
    keys,
    get_credential,
    save_credential,
)

router = APIRouter()
security = OAuth2PasswordBearer(tokenUrl="/token")
env = Env()
env.read_env()


@router.get(
    "/{petition_id}", tags=["Petitions"], summary="Retrieves the petition by `id`"
)
async def get_one(petition_id: str, expand: bool = False):
    p = Petition.by_pid(petition_id)
    if not p:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Petition not Found")

    return p.publish(expand)


def _get_token(url):
    r = requests.post(
        f"{url}/token",
        data={
            "username": env("CREDENTIAL_ISSUER_USERNAME"),
            "password": env("CREDENTIAL_ISSUER_PASSWORD"),
        },
    )
    return r.json()["access_token"]


def _retrieve_credential(petition):
    aaid = petition.authorizable_attribute_id
    credential = get_credential(aaid)

    if not credential:
        url = petition.credential_issuer_url
        value = petition.credential_issuer_petition_value
        blind_sign_request = zencode(CONTRACTS.CITIZEN_REQ_BLIND_SIG, keys=keys())
        data = dict(
            authorizable_attribute_id=aaid,
            blind_sign_request=json.loads(blind_sign_request),
            optional_values=[],
            values=value,
        )
        r = requests.post(
            f"{url}/credential/",
            json=data,
            headers={"Authorization": f"Bearer {_get_token(url)}"},
        )
        credential_request = json.dumps(r.json())
        credential = zencode(
            CONTRACTS.AGGREGATE_CREDENTIAL, keys=keys(), data=credential_request
        )
        save_credential(aaid, credential)

    return credential


def _retrieve_verification_key(petition):
    url = petition.credential_issuer_url
    aaid = petition.authorizable_attribute_id
    r = requests.get(f"{url}/authorizable_attribute/{aaid}")
    return r.json()["verification_key"]


def _generate_petition_object(petition, ci_uid=None):
    url = petition.credential_issuer_url
    if not ci_uid:
        r = requests.get(f"{url.rstrip('/')}/uid")
        ci_uid = r.json()["credential_issuer_id"]
    issuer_verify = _retrieve_verification_key(petition)
    credential = _retrieve_credential(petition)
    petition_req = zencode(
        CONTRACTS.CREATE_PETITION,
        keys=credential,
        data=json.dumps(issuer_verify),
        placeholders={"poll": petition.petition_id, "MadHatter": "issuer_identifier"},
    )
    petition = zencode(
        CONTRACTS.APPROVE_PETITION,
        keys=json.dumps(issuer_verify),
        data=petition_req,
        placeholders={"MadHatter": "issuer_identifier"},
    )
    return petition, ci_uid


class PetitionIn(BaseModel):
    petition_id: str
    credential_issuer_url: UrlStr
    authorizable_attribute_id: str
    credential_issuer_petition_value: List[Dict]


@router.post("/", tags=["Petitions"], summary="Creates a new petition")
def create(petition: PetitionIn, expand: bool = False, token: str = Security(security)):
    if not allowed_to_control_petition(token):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authorized to control this petition",
        )
    try:
        petition_object, ci_uid = _generate_petition_object(petition)
    except FileNotFoundError:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Credential issuer is not validated, missing info/keys/credentials",
        )
    except ConnectionError:
        raise HTTPException(
            status_code=HTTP_424_FAILED_DEPENDENCY,
            detail="Credential issuer server is not available",
        )

    p = Petition(
        petition=petition_object,
        petition_id=petition.petition_id,
        credential_issuer_uid=ci_uid,
        credential_issuer_url=petition.credential_issuer_url,
    )

    try:
        DBSession.add(p)
        DBSession.commit()
    except IntegrityError:
        DBSession.rollback()
        raise HTTPException(
            status_code=HTTP_409_CONFLICT, detail="Duplicate Petition Id"
        )
    return p.publish(expand)


class σ_prime(BaseModel):
    h_prime: str
    s_prime: str


class π_v(BaseModel):
    c: str
    rr: str
    rm: str


class Proof(BaseModel):
    sigma_prime: σ_prime
    nu: str
    kappa: str
    encoding: str
    scheme: str = Schema(None, alias="schema")
    curve: str
    pi_v: π_v


class PetitionSignatureBody(BaseModel):
    uid_petition: str
    uid_signature: str
    proof: Proof


class PetitionSignature(BaseModel):
    petition_signature: Dict


@router.post(
    "/{petition_id}/sign",
    tags=["Petitions"],
    summary="Adds a petition signature to the petition object (signs a petition)",
)
def sign(petition_id: str, signature: PetitionSignature, expand: bool = False):
    p = Petition.by_pid(petition_id)
    if not p:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Petition not Found")

    try:
        petition = zencode(
            CONTRACTS.INCREMENT_PETITION, keys=p.petition, data=signature.json()
        )
        json.loads(petition)
        p.petition = petition
        DBSession.commit()
    except ZenroomException as e:
        debug(f"Failed to sign {p.petition_id}")
        debug(p.petition)
        debug(e)
        raise HTTPException(
            status_code=HTTP_424_FAILED_DEPENDENCY,
            detail="Petition signature is duplicate or not valid",
        )

    return p.publish(expand)


class TallyBody(BaseModel):
    authorizable_attribute_id: str


@router.post(
    "/{petition_id}/tally",
    tags=["Petitions"],
    summary="Tally a petition, just by tally admins",
)
def tally(
    petition_id: str,
    authorizable_attribute: TallyBody = Body(...),
    expand: bool = False,
    token: str = Security(security),
):
    if not allowed_to_control_petition(token):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authorized to control this petition",
        )
    p = Petition.by_pid(petition_id)
    if not p:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Petition not Found")
    petition = Bunch(
        petition_id=petition_id,
        credential_issuer_url=p.credential_issuer_url,
        authorizable_attribute_id=authorizable_attribute.authorizable_attribute_id,
    )
    credential = _retrieve_credential(petition)
    p.tally = zencode(CONTRACTS.TALLY_PETITION, keys=credential, data=p.petition)
    DBSession.commit()
    return p.publish(expand)


@router.post(
    "/{petition_id}/count",
    tags=["Petitions"],
    summary="Count the signs of a tallied petition",
)
def count(petition_id: str):
    p = Petition.by_pid(petition_id)
    if not p:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Petition not Found")

    if p.status != STATUS.CLOSED:
        raise HTTPException(
            status_code=HTTP_424_FAILED_DEPENDENCY, detail="Petition still open"
        )

    p.count = zencode(CONTRACTS.COUNT_PETITION, keys=p.tally, data=p.petition)
    DBSession.commit()
    return json.loads(p.count)
