from sqlalchemy import Column, String

from pytest_rts.models.base import Base


class NewTests(Base):
    __tablename__ = "new_tests"
    name = Column(String, primary_key=True)

    def __init__(self, name):
        self.name = name
