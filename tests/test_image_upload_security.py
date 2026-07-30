import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from backend.main import app
from backend import auth, models
from tests.conftest import TestingSessionLocal

client = TestClient(app)

@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def create_test_user(db, name="Test Customer", phone="0779998877", role="customer"):
    user = models.User(name=name, phone=phone, email=f"{phone}@test.com", password_hash="hashed", role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_dummy_image_bytes(format="JPEG", size=(100, 100)):
    buf = io.BytesIO()
    img = Image.new("RGB", size, color="red")
    img.save(buf, format=format)
    return buf.getvalue()

def test_unauthenticated_review_photo_upload_rejected():
    """Ensure unauthenticated upload to /api/reviews/upload-photo is rejected (401)."""
    img_bytes = create_dummy_image_bytes("JPEG")
    response = client.post(
        "/api/reviews/upload-photo",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 401

def test_authenticated_review_photo_upload_success(db):
    """Ensure authenticated customer can upload valid image photo."""
    user = create_test_user(db, name="Test Customer", phone="0779998877", role="customer")
    token = auth.create_access_token(data={"sub": str(user.id), "role": user.role})
    
    img_bytes = create_dummy_image_bytes("PNG")
    response = client.post(
        "/api/reviews/upload-photo",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("valid.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert "url" in response.json()
    assert response.json()["url"].startswith("/uploads/review_")

def test_fake_image_extension_rejected(db):
    """Ensure uploading fake file (e.g. PHP text named shell.jpg) is rejected with 400."""
    user = create_test_user(db, name="Test Customer 2", phone="0779998878", role="customer")
    token = auth.create_access_token(data={"sub": str(user.id), "role": user.role})
    
    fake_bytes = b"<?php echo 'malicious code'; ?>"
    response = client.post(
        "/api/reviews/upload-photo",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("shell.jpg", fake_bytes, "image/jpeg")}
    )
    assert response.status_code == 400
    assert "بصمة الملف غير صالحة" in response.json()["detail"]

def test_svg_and_script_upload_rejected(db):
    """Ensure SVG vector graphics are rejected due to XSS risk."""
    user = create_test_user(db, name="Test Customer 3", phone="0779998879", role="customer")
    token = auth.create_access_token(data={"sub": str(user.id), "role": user.role})
    
    svg_bytes = b"<svg onload=alert(1)></svg>"
    response = client.post(
        "/api/reviews/upload-photo",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("vector.svg", svg_bytes, "image/svg+xml")}
    )
    assert response.status_code == 400

def test_oversized_image_dimensions_rejected(db):
    """Ensure images exceeding 4096x4096px are rejected (decompression bomb protection)."""
    user = create_test_user(db, name="Test Customer 4", phone="0779998880", role="customer")
    token = auth.create_access_token(data={"sub": str(user.id), "role": user.role})
    
    huge_img = create_dummy_image_bytes("JPEG", size=(4097, 100))
    response = client.post(
        "/api/reviews/upload-photo",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("huge.jpg", huge_img, "image/jpeg")}
    )
    assert response.status_code == 400
    assert "أبعاد الصورة كبيرة جداً" in response.json()["detail"]
