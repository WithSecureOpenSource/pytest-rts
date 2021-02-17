from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint

from pytest_rts.models.base import Base


class TestMap(Base):
    __tablename__ = "test_map"
    __table_args__ = (
        UniqueConstraint(
            "file_id", "test_function_id", "line_number", sqlite_on_conflict="IGNORE"
        ),
    )

    file_id = Column(Integer, ForeignKey("src_file.id"), primary_key=True)
    test_function_id = Column(Integer, ForeignKey("test_function.id"), primary_key=True)
    line_number = Column(Integer, primary_key=True)

    def __init__(self, file_id, test_function_id, line_number):
        self.file_id = file_id
        self.test_function_id = test_function_id
        self.line_number = line_number
