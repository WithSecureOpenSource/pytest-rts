from sqlalchemy import Column, String, Integer, UniqueConstraint

from pytest_rts.models.base import Base


class SourceFile(Base):
    __tablename__ = "src_file"
    __table_args__ = (UniqueConstraint("path", sqlite_on_conflict="IGNORE"),)

    id = Column(Integer, primary_key=True)
    path = Column(String)

    def __init__(self, path):
        self.path = path
