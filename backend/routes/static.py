"""
CityLand Backend - Static File Serving Routes
"""
import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

from backend.main import FRONTEND_DIR

router = APIRouter()


@router.get("/")
@router.get("/index.html")
def read_root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Welcome to Sheland API", "status": "running"}


@router.get("/admin")
def read_admin():
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return {"message": "Admin dashboard page not found"}


@router.get("/admin/styles.css")
def get_admin_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin", "styles.css"))


@router.get("/admin/app.js")
def get_admin_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin", "app.js"))


@router.get("/vendor")
def read_vendor():
    vendor_path = os.path.join(FRONTEND_DIR, "vendor.html")
    if os.path.exists(vendor_path):
        return FileResponse(vendor_path)
    return {"message": "Vendor portal page not found"}


@router.get("/styles.css")
def get_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "styles.css"))


@router.get("/app.js")
def get_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.js"))


@router.get("/qrcode.min.js")
def get_qrcode_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "qrcode.min.js"))


@router.get("/manifest.json")
def get_manifest():
    return FileResponse(os.path.join(FRONTEND_DIR, "manifest.json"), media_type="application/manifest+json")


@router.get("/sw.js")
def get_sw():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "sw.js"),
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"}
    )


@router.get("/icon-192.png")
def get_icon192():
    return FileResponse(os.path.join(FRONTEND_DIR, "icon-192.png"), media_type="image/png")


@router.get("/icon-512.png")
def get_icon512():
    return FileResponse(os.path.join(FRONTEND_DIR, "icon-512.png"), media_type="image/png")


@router.get("/icon-maskable-192.png")
def get_iconmask192():
    return FileResponse(os.path.join(FRONTEND_DIR, "icon-maskable-192.png"), media_type="image/png")


@router.get("/icon-maskable-512.png")
def get_iconmask512():
    return FileResponse(os.path.join(FRONTEND_DIR, "icon-maskable-512.png"), media_type="image/png")
