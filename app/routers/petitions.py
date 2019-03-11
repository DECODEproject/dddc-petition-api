import requests
from fastapi import APIRouter, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, UrlStr, Schema
from sqlalchemy.exc import IntegrityError
from starlette.status import (
    HTTP_409_CONFLICT,
    HTTP_404_NOT_FOUND,
    HTTP_424_FAILED_DEPENDENCY,
)

from app.model import DBSession
from app.model.petition import Petition
from app.utils.helpers import CONTRACTS, zencode, load_credentials

router = APIRouter()
security = OAuth2PasswordBearer(tokenUrl="/token")


@router.get("/{petition_id}", tags=["petitions"])
async def get_one(petition_id: str, token: str = Security(security)):
    p = Petition.by_pid(petition_id)
    if not p:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Petition not Found")

    return p.publish()


def _generate_petition_object(url):
    r = requests.get(f"{url}/uid")
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


@router.post("/", tags=["petitions"])
def create(petition: PetitionIn, token: str = Security(security)):
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
    return p.publish()


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


@router.post("/sign", tags=["petitions"])
async def sign(signature: PetitionSignature, token: str = Security(security)):
    petition_id = signature.petition_signature.uid_petition
    p = Petition.by_pid(petition_id)
    petition = zencode(CONTRACTS.ADD_SIGNATURE, keys=p.petition, data=signature.json())
    p.petition = petition

    DBSession.commit()
    return p.publish()


@router.post("/tally", tags=["petitions"])
async def tally(token: str = Security(security)):
    pass
