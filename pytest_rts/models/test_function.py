from sqlalchemy import Column, ForeignKey, Float, String, Integer, UniqueConstraint

from pytest_rts.models.base import Base


class TestFunction(Base):
    __tablename__ = "test_function"
    __table_args__ = (UniqueConstraint("name", sqlite_on_conflict="IGNORE"),)

    id = Column(Integer, primary_key=True)
    test_file_id = Column(Integer, ForeignKey("test_file.id"))
    name = Column(String)
    start = Column(Integer)
    end = Column(Integer)
    duration = Column(Float)

    def __init__(self, test_file_id, name, start, end, duration):
        self.test_file_id = test_file_id
        self.name = name
        self.start = start
        self.end = end
        self.duration = duration
