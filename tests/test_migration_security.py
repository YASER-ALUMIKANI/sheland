import pytest
from backend.database import safe_add_column, engine

def test_safe_add_column_valid():
    """Ensure safe_add_column works cleanly for valid column additions."""
    safe_add_column(engine, "users", "test_mig_col", "VARCHAR")

def test_safe_add_column_invalid_identifier_rejected():
    """Ensure malicious identifier syntax is blocked by regex validation."""
    with pytest.raises(ValueError, match="Invalid table or column identifier"):
        safe_add_column(engine, "users; DROP TABLE users;--", "bad_col", "VARCHAR")

    with pytest.raises(ValueError, match="Invalid table or column identifier"):
        safe_add_column(engine, "users", "bad_col; DROP TABLE users;--", "VARCHAR")

def test_safe_add_column_unauthorized_type_rejected():
    """Ensure unauthorized or malformed data types are blocked by type whitelist."""
    with pytest.raises(ValueError, match="Invalid or unauthorized column type"):
        safe_add_column(engine, "users", "bad_col", "UNAUTHORIZED_TYPE")
