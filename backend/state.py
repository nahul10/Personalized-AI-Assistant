# backend/state.py
import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "app.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Desired schemas ----------
FILES_SCHEMA = [
    ("id", "INTEGER PRIMARY KEY"),
    ("name", "TEXT"),
    ("filename", "TEXT"),
    ("source_path", "TEXT"),
    ("file_type", "TEXT"),
    ("pages", "INTEGER DEFAULT 0"),
    ("chunks", "INTEGER DEFAULT 0"),
    ("ocr_pages", "INTEGER DEFAULT 0"),
    ("uploaded_at", "DATETIME"),
    ("created_at", "DATETIME"),
]
FILES_COLS = [c[0] for c in FILES_SCHEMA]

CHUNKS_SCHEMA = [
    ("id", "INTEGER PRIMARY KEY"),
    ("file_id", "INTEGER NOT NULL"),
    ("page_no", "INTEGER DEFAULT 0"),
    ("seq_no", "INTEGER DEFAULT 0"),
    ("content", "TEXT NOT NULL"),
    ("emb_dim", "INTEGER DEFAULT 0"),
    ("embedding", "BLOB"),
]
CHUNKS_COLS = [c[0] for c in CHUNKS_SCHEMA]


# ---------- SQLite helpers ----------
def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def _get_columns(conn: sqlite3.Connection, table: str):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    # returns list of (cid, name, type, notnull, dflt_value, pk)
    return [row[1] for row in cur.fetchall()]


def _rebuild_table(conn: sqlite3.Connection, table: str, schema: list, select_builder):
    """
    Create <table>_new with <schema>, copy rows from <table> using select_builder(conn),
    drop old table, rename _new -> table.
    """
    cur = conn.cursor()
    cols_sql = ", ".join([f"{n} {t}" for n, t in schema])
    cur.execute(f"CREATE TABLE IF NOT EXISTS {table}_new ({cols_sql})")

    if _table_exists(conn, table):
        select_sql = select_builder(conn)  # must select same number/order of columns as schema
        cur.execute(
            f"INSERT INTO {table}_new ({', '.join([c[0] for c in schema])}) {select_sql}"
        )
        cur.execute(f"DROP TABLE {table}")

    cur.execute(f"ALTER TABLE {table}_new RENAME TO {table}")
    conn.commit()


# ---------- Rebuilders for each table ----------
def _rebuild_files(conn: sqlite3.Connection):
    def select_builder(c: sqlite3.Connection):
        existing = set(_get_columns(c, "files"))

        def has(col): return col in existing

        # preserve id if it exists
        id_sel = "id" if has("id") else "NULL AS id"

        # prefer filename or fallback to name
        filename_sel = (
            "filename" if has("filename")
            else ("name AS filename" if has("name") else "NULL AS filename")
        )
        name_sel = (
            "name" if has("name")
            else ("filename AS name" if has("filename") else "NULL AS name")
        )

        source_path_sel = "source_path" if has("source_path") else "NULL AS source_path"
        file_type_sel = "file_type" if has("file_type") else "NULL AS file_type"
        pages_sel = "COALESCE(pages,0) AS pages" if has("pages") else "0 AS pages"
        chunks_sel = "COALESCE(chunks,0) AS chunks" if has("chunks") else "0 AS chunks"
        ocr_pages_sel = "COALESCE(ocr_pages,0) AS ocr_pages" if has("ocr_pages") else "0 AS ocr_pages"
        uploaded_sel = (
            "uploaded_at" if has("uploaded_at") else "datetime('now') AS uploaded_at"
        )
        created_sel = (
            "created_at" if has("created_at") else "datetime('now') AS created_at"
        )

        return (
            "SELECT "
            f"{id_sel}, "
            f"{name_sel}, "
            f"{filename_sel}, "
            f"{source_path_sel}, "
            f"{file_type_sel}, "
            f"{pages_sel}, "
            f"{chunks_sel}, "
            f"{ocr_pages_sel}, "
            f"{uploaded_sel}, "
            f"{created_sel} "
            "FROM files"
        )

    _rebuild_table(conn, "files", FILES_SCHEMA, select_builder)


def _rebuild_chunks(conn: sqlite3.Connection):
    def select_builder(c: sqlite3.Connection):
        existing = set(_get_columns(c, "chunks"))

        def has(col): return col in existing

        id_sel = "id" if has("id") else "NULL AS id"
        file_id_sel = "file_id" if has("file_id") else "NULL AS file_id"

        # Map various legacy names to our new ones
        page_no_sel = (
            "page_no" if has("page_no")
            else ("page AS page_no" if has("page") else "0 AS page_no")
        )
        seq_no_sel = (
            "seq_no" if has("seq_no")
            else ("chunk_index AS seq_no" if has("chunk_index") else "0 AS seq_no")
        )
        content_sel = "content" if has("content") else "'' AS content"
        emb_dim_sel = "COALESCE(emb_dim,0) AS emb_dim" if has("emb_dim") else "0 AS emb_dim"
        embedding_sel = "embedding" if has("embedding") else "NULL AS embedding"

        return (
            "SELECT "
            f"{id_sel}, "
            f"{file_id_sel}, "
            f"{page_no_sel}, "
            f"{seq_no_sel}, "
            f"{content_sel}, "
            f"{emb_dim_sel}, "
            f"{embedding_sel} "
            "FROM chunks"
        )

    _rebuild_table(conn, "chunks", CHUNKS_SCHEMA, select_builder)


def _ensure_schema():
    """
    Make both 'files' and 'chunks' tables match our target schemas exactly,
    migrating/copying existing rows. Then let SQLAlchemy create any missing tables.
    """
    conn = sqlite3.connect(DB_PATH)

    # files
    if not _table_exists(conn, "files"):
        _rebuild_files(conn)
    else:
        existing = set(_get_columns(conn, "files"))
        if set(existing) != set(FILES_COLS):
            _rebuild_files(conn)

    # chunks
    if not _table_exists(conn, "chunks"):
        _rebuild_chunks(conn)
    else:
        existing = set(_get_columns(conn, "chunks"))
        if set(existing) != set(CHUNKS_COLS):
            _rebuild_chunks(conn)

    conn.close()


def init_db():
    # 1) migrate our two main tables to the exact shapes we expect
    _ensure_schema()

    # 2) create any remaining tables from ORM models (e.g., history)
    from . import schemas  # noqa: F401
    Base.metadata.create_all(bind=engine)
