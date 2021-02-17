from sqlalchemy import Column, String

from pytest_rts.models.base import Base


class LastUpdateHash(Base):
    __tablename__ = "last_update_hash"
    commithash = Column(String, primary_key=True)

    def __init__(self, commithash):
        self.commithash = commithash
