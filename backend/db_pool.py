"""
Shared psycopg2 ThreadedConnectionPool for backend/db.py and backend/retriever.py.

Why: v0.4 opened a fresh psycopg2 connection on every internal search call (5+ per
chat turn). Concurrent sessions exhausted PostgreSQL's `max_connections`. This pool
caps connections, registers pgvector once per physical connection, and exposes a
context-manager helper so callers don't have to remember to release.
"""
import os
import threading
from contextlib import contextmanager
from psycopg2 import pool
from pgvector.psycopg2 import register_vector

DB_DSN = os.environ.get(
    "DATABASE_URL",
    "dbname=bri610 user=tutor password=tutor610 host=localhost",
)
_MIN = int(os.environ.get("DB_POOL_MIN", "1"))
_MAX = int(os.environ.get("DB_POOL_MAX", "20"))

_pool: pool.ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()
_registered: set[int] = set()  # id(conn) of connections that already had register_vector


def _get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = pool.ThreadedConnectionPool(_MIN, _MAX, dsn=DB_DSN)
    return _pool


def acquire():
    """Return a pooled connection with pgvector registered. Caller must release()."""
    p = _get_pool()
    conn = p.getconn()
    if id(conn) not in _registered:
        register_vector(conn)
        _registered.add(id(conn))
    return conn


def release(conn) -> None:
    """Return a connection to the pool. Safe to call with None."""
    if conn is None:
        return
    _get_pool().putconn(conn)


@contextmanager
def get_conn():
    """Context manager: `with get_conn() as conn:`"""
    conn = acquire()
    try:
        yield conn
    finally:
        release(conn)


def close_all() -> None:
    """For graceful shutdown / test teardown."""
    global _pool
    if _pool is not None:
        with _pool_lock:
            if _pool is not None:
                _pool.closeall()
                _pool = None
                _registered.clear()
