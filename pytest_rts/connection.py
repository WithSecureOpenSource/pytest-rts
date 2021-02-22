"""Code for mapping database connectivity"""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


DB_FILE_NAME = "mapping.db"


class MappingConn:  # pylint: disable=too-few-public-methods
    """Mapping database connection"""

    _engine = None
    connection_string = None

    @classmethod
    def engine(cls, connection_string) -> Engine:
        """SQLalchemy engine"""
        if not cls._engine:
            cls.connection_string = connection_string
            cls._engine = create_engine(connection_string)
        return cls._engine
