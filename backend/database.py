"""
Sheland Backend - Database Connection Setup
# ponytail: Dual-mode SQLAlchemy engine supporting PostgreSQL (Production/Render) & SQLite (Local/Test).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

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

# Schema column migration check for existing tables
try:
    with engine.connect() as conn:
        from sqlalchemy import text
        for col, default_val in [("parcel_count", "'1 من 1'"), ("weight", "'0.85 كجم'"), ("dimensions", "'25 × 15 × 10 سم'")]:
            try:
                conn.execute(text(f"ALTER TABLE orders ADD COLUMN {col} VARCHAR DEFAULT {default_val}"))
                conn.commit()
            except Exception:
                pass
except Exception:
    pass

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
