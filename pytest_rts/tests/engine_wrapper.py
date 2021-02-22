"""Code for helper sqlalchemy engine"""
from functools import wraps

from pytest_rts.connection import MappingConn


def with_engine(func):
    """Provide SQLalchemy engine to a function"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        engine = MappingConn.engine("sqlite:///mapping.db")
        try:
            return func(*args, **kwargs, engine=engine)
        finally:
            engine.dispose()

    return wrapper
