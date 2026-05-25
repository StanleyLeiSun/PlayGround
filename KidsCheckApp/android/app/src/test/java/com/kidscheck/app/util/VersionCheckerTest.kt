package com.kidscheck.app.util

import com.kidscheck.app.data.model.AppVersion
import org.junit.Assert.*
import org.junit.Test

class VersionCheckerTest {

    // needUpdate Tests
    @Test
    fun `needUpdate returns false when client version is newer`() {
        // BuildConfig.VERSION_CODE is 10104 in build.gradle.kts
        val serverVersion = AppVersion(
            versionCode = 10103,
            versionName = "1.1.3",
            apkUrl = "/api/app/download/1.1.3",
            apkSize = 1024000,
            apkMd5 = "abc",
            releaseNotes = "Old version",
            forceUpdate = false,
            minSupportedVersion = 10100
        )
        // This will use BuildConfig.VERSION_CODE which is 10104
        // Since 10104 >= 10103, should return false
        assertFalse(VersionChecker.needUpdate(serverVersion))
    }

    @Test
    fun `needUpdate returns true when server version is newer`() {
        val serverVersion = AppVersion(
            versionCode = 10105,
            versionName = "1.1.5",
            apkUrl = "/api/app/download/1.1.5",
            apkSize = 1024000,
            apkMd5 = "abc",
            releaseNotes = "New version",
            forceUpdate = false,
            minSupportedVersion = 10100
        )
        // Since 10104 < 10105, should return true
        assertTrue(VersionChecker.needUpdate(serverVersion))
    }

    @Test
    fun `needUpdate returns true when force update is required`() {
        val serverVersion = AppVersion(
            versionCode = 10105,
            versionName = "1.1.5",
            apkUrl = "/api/app/download/1.1.5",
            apkSize = 1024000,
            apkMd5 = "abc",
            releaseNotes = "Force update",
            forceUpdate = true,
            minSupportedVersion = 10100
        )
        assertTrue(VersionChecker.needUpdate(serverVersion))
    }

    @Test
    fun `needUpdate returns true when client below min supported`() {
        val serverVersion = AppVersion(
            versionCode = 10200,
            versionName = "1.2.0",
            apkUrl = "/api/app/download/1.2.0",
            apkSize = 1024000,
            apkMd5 = "abc",
            releaseNotes = "Min version bump",
            forceUpdate = false,
            minSupportedVersion = 10105
        )
        // 10104 < 10105, should return true
        assertTrue(VersionChecker.needUpdate(serverVersion))
    }

    // isForceUpdate Tests
    @Test
    fun `isForceUpdate returns false when client version is newer`() {
        val serverVersion = AppVersion(
            versionCode = 10103,
            versionName = "1.1.3",
            apkUrl = "/api/app/download/1.1.3",
            apkSize = 1024000,
            apkMd5 = "abc",
            releaseNotes = "Old version",
            forceUpdate = true,
            minSupportedVersion = 10100
        )
        assertFalse(VersionChecker.isForceUpdate(serverVersion))
    }

    @Test
    fun `isForceUpdate returns true when force update flag is set`() {
        val serverVersion = AppVersion(
            versionCode = 10105,
            versionName = "1.1.5",
            apkUrl = "/api/app/download/1.1.5",
            apkSize = 1024000,
            apkMd5 = "abc",
            releaseNotes = "Force update",
            forceUpdate = true,
            minSupportedVersion = 10100
        )
        assertTrue(VersionChecker.isForceUpdate(serverVersion))
    }

    @Test
    fun `isForceUpdate returns true when below min supported version`() {
        val serverVersion = AppVersion(
            versionCode = 10200,
            versionName = "1.2.0",
            apkUrl = "/api/app/download/1.2.0",
            apkSize = 1024000,
            apkMd5 = "abc",
            releaseNotes = "Min version bump",
            forceUpdate = false,
            minSupportedVersion = 10105
        )
        // 10104 < 10105, should return true
        assertTrue(VersionChecker.isForceUpdate(serverVersion))
    }

    @Test
    fun `isForceUpdate returns false when optional update`() {
        val serverVersion = AppVersion(
            versionCode = 10105,
            versionName = "1.1.5",
            apkUrl = "/api/app/download/1.1.5",
            apkSize = 1024000,
            apkMd5 = "abc",
            releaseNotes = "Optional update",
            forceUpdate = false,
            minSupportedVersion = 10100
        )
        // 10104 < 10105 but forceUpdate=false and 10104 >= 10100
        assertFalse(VersionChecker.isForceUpdate(serverVersion))
    }
}
