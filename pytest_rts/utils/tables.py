"""Database tables for pytest-rts"""
from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    MetaData,
    ForeignKey,
    Float,
    UniqueConstraint,
)


metadata = MetaData()


src_file_table = Table(
    "src_file",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("path", String, unique=True),
)

test_file_table = Table(
    "test_file",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("path", String, unique=True),
)

test_function_table = Table(
    "test_function",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("test_file_id", Integer, ForeignKey("test_file.id")),
    Column("context", String, unique=True),
    Column("start", Integer),
    Column("end", Integer),
    Column("duration", Float),
)

test_map_table = Table(
    "test_map",
    metadata,
    Column("file_id", Integer, ForeignKey("src_file.id")),
    Column(
        "test_function_id",
        Integer,
        ForeignKey("test_function.id"),
    ),
    Column("line_id", Integer),
    UniqueConstraint(
        "file_id",
        "test_function_id",
        "line_id",
    ),
)

new_tests_table = Table(
    "new_tests",
    metadata,
    Column("context", String, primary_key=True),
)

last_update_hash_table = Table(
    "last_update_hash",
    metadata,
    Column("hash", String, primary_key=True),
)
