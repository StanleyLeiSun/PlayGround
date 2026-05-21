package com.kidscheck.app.data.model

import com.google.gson.annotations.SerializedName

data class AppVersion(
    @SerializedName("version_code")
    val versionCode: Int,
    @SerializedName("version_name")
    val versionName: String,
    @SerializedName("apk_url")
    val apkUrl: String,
    @SerializedName("apk_size")
    val apkSize: Long,
    @SerializedName("apk_md5")
    val apkMd5: String,
    @SerializedName("release_notes")
    val releaseNotes: String,
    @SerializedName("force_update")
    val forceUpdate: Boolean,
    @SerializedName("min_supported_version")
    val minSupportedVersion: Int
)
