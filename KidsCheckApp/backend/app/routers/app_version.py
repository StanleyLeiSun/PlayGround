from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import json

router = APIRouter(prefix="/api/app", tags=["app"])

VERSION_FILE = Path("uploads/apk/version.json")


@router.get("/version")
async def check_version():
    """检查应用版本"""
    if not VERSION_FILE.exists():
        raise HTTPException(status_code=404, detail="Version info not found")

    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        version_data = json.load(f)

    return {
        "version_code": version_data["version_code"],
        "version_name": version_data["version_name"],
        "apk_url": f"/api/app/download/{version_data['version_name']}",
        "apk_size": version_data.get("apk_size", 0),
        "apk_md5": version_data.get("apk_md5", ""),
        "release_notes": version_data["release_notes"],
        "force_update": version_data["force_update"],
        "min_supported_version": version_data["min_supported_version"],
    }


@router.get("/download/{version_name}")
async def download_apk(version_name: str):
    """下载APK文件"""
    if not VERSION_FILE.exists():
        raise HTTPException(status_code=404, detail="Version info not found")

    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        version_data = json.load(f)

    if version_data["version_name"] != version_name:
        raise HTTPException(status_code=404, detail="Version not found")

    apk_path = Path("uploads/apk") / version_data["apk_filename"]
    if not apk_path.exists():
        raise HTTPException(status_code=404, detail="APK file not found")

    return FileResponse(
        path=str(apk_path),
        filename=version_data["apk_filename"],
        media_type="application/vnd.android.package-archive",
    )
