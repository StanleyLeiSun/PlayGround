package com.kidscheck.app.util

import android.content.Context
import com.kidscheck.app.BuildConfig
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.AppVersion

object VersionChecker {

    suspend fun checkForUpdate(context: Context): AppVersion? {
        return try {
            val api = RetrofitInstance.getApi(context)
            val response = api.checkVersion()
            if (response.isSuccessful) {
                val serverVersion = response.body()
                if (serverVersion != null && needUpdate(serverVersion)) {
                    serverVersion
                } else {
                    null
                }
            } else {
                null
            }
        } catch (e: Exception) {
            null
        }
    }

    fun needUpdate(serverVersion: AppVersion): Boolean {
        val clientVersionCode = BuildConfig.VERSION_CODE

        // 如果本地版本比服务器版本新，不提示更新
        if (clientVersionCode >= serverVersion.versionCode) {
            return false
        }

        // 如果强制更新，必须更新
        if (serverVersion.forceUpdate) {
            return true
        }

        // 如果本地版本低于最低支持版本，强制更新
        if (clientVersionCode < serverVersion.minSupportedVersion) {
            return true
        }

        // 有新版本可选更新
        return true
    }

    fun isForceUpdate(serverVersion: AppVersion): Boolean {
        val clientVersionCode = BuildConfig.VERSION_CODE

        // 如果本地版本比服务器版本新，不强制更新
        if (clientVersionCode >= serverVersion.versionCode) {
            return false
        }

        // 如果强制更新标志为true，强制更新
        if (serverVersion.forceUpdate) {
            return true
        }

        // 如果本地版本低于最低支持版本，强制更新
        if (clientVersionCode < serverVersion.minSupportedVersion) {
            return true
        }

        return false
    }
}
