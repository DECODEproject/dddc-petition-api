import json

import requests
from requests.exceptions import ConnectionError
from fastapi import APIRouter, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from pydantic import BaseModel, UrlStr, Schema
from sqlalchemy.exc import IntegrityError
from starlette.status import (
    HTTP_409_CONFLICT,
    HTTP_404_NOT_FOUND,
    HTTP_424_FAILED_DEPENDENCY,
    HTTP_401_UNAUTHORIZED,
)
from zenroom.zenroom import Error

from app.model import DBSession
from app.model.petition import Petition, STATUS
from app.utils.helpers import (
    CONTRACTS,
    zencode,
    load_credentials,
    debug,
    allowed_to_tally,
)

router = APIRouter()
security = OAuth2PasswordBearer(tokenUrl="/token")


@router.get(
    "/{petition_id}", tags=["Petitions"], summary="Retrieves the petition by `id`"
)
async def get_one(
    petition_id: str, expand: bool = False, token: str = Security(security)
):
    p = Petition.by_pid(petition_id)
    if not p:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Petition not Found")

    return p.publish(expand)


def _generate_petition_object(url, ci_uid=None):
    if not ci_uid:
        r = requests.get(f"{url.rstrip('/')}/uid")
        ci_uid = r.json()["credential_issuer_id"]
    _, issuer_verify, credential = load_credentials(ci_uid)
    petition_req = zencode(
        CONTRACTS.CREATE_PETITION, keys=credential, data=issuer_verify
    )
    petition = zencode(
        CONTRACTS.APPROVE_PETITION, keys=issuer_verify, data=petition_req
    )
    return petition, ci_uid


class PetitionIn(BaseModel):
    petition_id: str
    credential_issuer_url: UrlStr


@router.post("/", tags=["Petitions"], summary="Creates a new petition")
def create(petition: PetitionIn, expand: bool = False, token: str = Security(security)):
    try:
        petition_object, ci_uid = _generate_petition_object(
            petition.credential_issuer_url
        )
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
    petition_signature: PetitionSignatureBody


@router.post(
    "/{petition_id}/sign",
    tags=["Petitions"],
    summary="Adds a petition signature to the petition object (signs a petition)",
)
async def sign(petition_id: str, signature: PetitionSignature, expand: bool = False):
    p = Petition.by_pid(petition_id)
    if not p:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Petition not Found")

    try:
        petition = zencode(
            CONTRACTS.ADD_SIGNATURE, keys=p.petition, data=signature.json()
        )
    except Error as e:
        debug(e)
        raise HTTPException(
            status_code=HTTP_424_FAILED_DEPENDENCY,
            detail="Petition signature is duplicate or not valid",
        )
    p.petition = petition

    DBSession.commit()
    return p.publish(expand)


tally_api_key = APIKeyHeader(name="tally_api_key")


@router.post(
    "/{petition_id}/tally",
    tags=["Petitions"],
    summary="Tally a petition, just by tally admins",
)
async def tally(
    petition_id: str, expand: bool = False, token: str = Security(tally_api_key)
):
    if not allowed_to_tally(token):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authorized to control this petition",
        )
    p = Petition.by_pid(petition_id)
    if not p:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Petition not Found")
    _, issuer_verify, credential = load_credentials(p.credential_issuer_uid)
    p.tally = zencode(CONTRACTS.TALLY_PETITION, keys=credential, data=p.petition)
    DBSession.commit()
    return p.publish(expand)


@router.post(
    "/{petition_id}/count",
    tags=["Petitions"],
    summary="Count the signs of a tallied petition",
)
async def count(petition_id: str, token: str = Security(security)):
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
