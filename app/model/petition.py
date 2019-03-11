from sqlalchemy import Column, Integer, Unicode, DateTime, func

from app.model import Base, DBSession


class Petition(Base):
    uid = Column(Integer, primary_key=True, index=True)
    petition_id = Column(Unicode, unique=True, index=True)
    tally = Column(Unicode)
    petition = Column(Unicode)
    credential_issuer_uid = Column(Unicode)
    credential_issuer_url = Column(Unicode)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now())

    __mapper_args__ = {"eager_defaults": True}

    @classmethod
    def by_pid(cls, petition_id):
        return DBSession.query(cls).filter_by(petition_id=petition_id).first()

    def publish(self):
        return dict(
            petition_id=self.petition_id,
            credential_issuer_url=self.credential_issuer_url,
            updated_at=self.updated_at,
        )
