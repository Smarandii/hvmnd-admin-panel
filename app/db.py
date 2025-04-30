import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from flask import current_app

_pool: pool.SimpleConnectionPool | None = None


def init_pool(dsn: str, minconn: int = 1, maxconn: int = 10) -> None:
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(minconn, maxconn, dsn)


@contextmanager
def get_conn():
    """Yields a connection & cursor, always returning them to the pool."""
    conn = _pool.getconn()
    try:
        yield conn, conn.cursor()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)
