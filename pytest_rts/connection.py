"""Code for mapping database connectivity"""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from pytest_rts.models.base import Base

DB_FILE_NAME = "mapping.db"


class MappingConn:  # pylint: disable=too-few-public-methods
    """Mapping database connection"""

    _engine: Engine = None
    _session: Session = None

    @classmethod
    def session(cls, connection_string=f"sqlite:///{DB_FILE_NAME}") -> Session:
        """SQLAlchemy session"""
        if not cls._engine:
            cls._engine = create_engine(connection_string)
            Base.metadata.create_all(cls._engine)
        if not cls._session:
            sessionmaker_instance = sessionmaker(bind=cls._engine)
            cls._session = sessionmaker_instance()
        return cls._session
