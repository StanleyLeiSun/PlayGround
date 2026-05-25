"""Tests for app_version router."""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_check_version_success(client):
    """Test successful version check."""
    version_data = {
        "version_code": 1,
        "version_name": "1.0.0",
        "apk_size": 1024000,
        "apk_md5": "abc123",
        "release_notes": "Initial release",
        "force_update": False,
        "min_supported_version": 1,
        "apk_filename": "app-1.0.0.apk",
    }

    with patch("app.routers.app_version.VERSION_FILE") as mock_file:
        mock_file.exists.return_value = True
        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=version_data):
                resp = await client.get("/api/app/version")
                assert resp.status_code == 200
                data = resp.json()
                assert data["version_code"] == 1
                assert data["version_name"] == "1.0.0"
                assert data["apk_url"] == "/api/app/download/1.0.0"
                assert data["release_notes"] == "Initial release"


@pytest.mark.asyncio
async def test_check_version_not_found(client):
    """Test version check when version file doesn't exist."""
    with patch("app.routers.app_version.VERSION_FILE") as mock_file:
        mock_file.exists.return_value = False
        resp = await client.get("/api/app/version")
        assert resp.status_code == 404
        assert "Version info not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_download_apk_version_not_found(client):
    """Test APK download with wrong version name."""
    version_data = {
        "version_name": "1.0.0",
        "apk_filename": "app-1.0.0.apk",
    }

    with patch("app.routers.app_version.VERSION_FILE") as mock_file:
        mock_file.exists.return_value = True
        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=version_data):
                resp = await client.get("/api/app/download/2.0.0")
                assert resp.status_code == 404
                assert "Version not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_download_apk_version_file_not_found(client):
    """Test APK download when version file doesn't exist."""
    with patch("app.routers.app_version.VERSION_FILE") as mock_file:
        mock_file.exists.return_value = False
        resp = await client.get("/api/app/download/1.0.0")
        assert resp.status_code == 404
        assert "Version info not found" in resp.json()["detail"]
