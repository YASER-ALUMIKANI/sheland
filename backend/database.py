"""
Sheland Backend - Database Connection Setup
# ponytail: Dual-mode SQLAlchemy engine supporting PostgreSQL (Production/Render) & SQLite (Local/Test).
"""
import os
import re
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger("sheland.database")

ALLOWED_COLUMN_TYPES = {"VARCHAR", "BOOLEAN", "FLOAT", "INTEGER", "TEXT", "DATETIME"}

def safe_add_column(engine_instance, table_name: str, column_name: str, column_type_sql: str):
    """
    Safely adds a column to an existing table if missing, enforcing strict identifier length,
    regex matching, column type whitelisting, and inspection check to prevent SQL injection.
    """
    # 1. Identifier Regex & Length Validation (Max 64 chars)
    if not re.match(r"^[a-zA-Z0-9_]{1,64}$", table_name) or not re.match(r"^[a-zA-Z0-9_]{1,64}$", column_name):
        raise ValueError(f"Invalid table or column identifier: {table_name}.{column_name}")

    # 2. Base Data Type Whitelist Validation
    base_type = column_type_sql.strip().split()[0].upper()
    if base_type not in ALLOWED_COLUMN_TYPES:
        raise ValueError(f"Invalid or unauthorized column type: {column_type_sql}")

    try:
        inspector = inspect(engine_instance)
        if table_name not in inspector.get_table_names():
            return

        existing_columns = [col["name"] for col in inspector.get_columns(table_name)]
        if column_name not in existing_columns:
            with engine_instance.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type_sql}"))
            logger.info(f"Successfully added column {column_name} to table {table_name}.")
    except Exception as err:
        logger.warning(f"Migration check warning for {table_name}.{column_name}: {err}")


# Read DATABASE_URL from environment variable or default to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Fix Render/Heroku legacy "postgres://" prefix to SQLAlchemy 2.0 "postgresql://"
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "sheland.db")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Safe schema column migrations check for existing tables
for col, default_val in [
    ("payment_status", "'pending'"),
    ("payment_tx_id", "NULL"),
    ("parcel_count", "'1 من 1'"),
    ("weight", "'0.85 كجم'"),
    ("dimensions", "'25 × 15 × 10 سم'")
]:
    safe_add_column(engine, "orders", col, f"VARCHAR DEFAULT {default_val}")


Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
