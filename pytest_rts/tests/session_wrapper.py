from functools import wraps

from pytest_rts.connection import MappingConn


def with_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = MappingConn.session()
        try:
            return func(*args, **kwargs, session=session)
        finally:
            session.close()

    return wrapper
