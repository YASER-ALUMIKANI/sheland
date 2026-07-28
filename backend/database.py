"""
Sheland Backend - Database Connection Setup
# ponytail: Simple SQLite engine using standard SQLAlchemy context manager
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_PATH = os.path.join(os.path.dirname(__file__), "sheland.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ponytail: Ensure SQLite schema compatibility for new parcel columns
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
