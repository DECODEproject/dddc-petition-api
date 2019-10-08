import json

from sqlalchemy import Column, Integer, Unicode, DateTime, func

from app.model import Base, DBSession


class STATUS:
    CLOSED = "CLOSED"
    OPEN = "OPEN"


class Petition(Base):
    uid = Column(Integer, primary_key=True, index=True)
    petition_id = Column(Unicode, unique=True, index=True)
    tally = Column(Unicode)
    count = Column(Unicode)
    petition = Column(Unicode)
    credential_issuer_uid = Column(Unicode)
    credential_issuer_url = Column(Unicode)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now())

    __mapper_args__ = {"eager_defaults": True}

    @classmethod
    def by_pid(cls, petition_id):
        return DBSession.query(cls).filter_by(petition_id=petition_id).first()

    def publish(self, details=True):
        fields = dict(
            petition_id=self.petition_id,
            credential_issuer_url=self.credential_issuer_url,
            updated_at=self.updated_at,
            status=self.status,
        )

        optional_fields = dict(
            petition=json.loads(self.petition) if self.petition else None,
            tally=json.loads(self.tally) if self.tally else None,
            count=json.loads(self.count) if self.count else None,
        )

        if details:
            fields.update(optional_fields)

        return fields

    @property
    def status(self):
        if not self.tally:
            return "OPEN"
        tally = "petition_tally" in json.loads(self.tally)
        return STATUS.CLOSED if tally else STATUS.OPEN
