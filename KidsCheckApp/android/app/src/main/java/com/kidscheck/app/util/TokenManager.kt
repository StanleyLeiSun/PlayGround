package com.kidscheck.app.util

import android.content.Context
import android.content.SharedPreferences

object TokenManager {
    private const val PREF_NAME = "kidscheck_prefs"
    private const val KEY_TOKEN = "auth_token"
    private const val KEY_USERNAME = "username"
    private const val KEY_ROLE = "role"
    private const val KEY_USER_ID = "user_id"

    private fun getPrefs(context: Context): SharedPreferences {
        return context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    }

    fun saveToken(context: Context, token: String, username: String, role: String, userId: Int) {
        getPrefs(context).edit()
            .putString(KEY_TOKEN, token)
            .putString(KEY_USERNAME, username)
            .putString(KEY_ROLE, role)
            .putInt(KEY_USER_ID, userId)
            .apply()
    }

    fun getToken(context: Context): String? {
        return getPrefs(context).getString(KEY_TOKEN, null)
    }

    fun getUsername(context: Context): String? {
        return getPrefs(context).getString(KEY_USERNAME, null)
    }

    fun getRole(context: Context): String? {
        return getPrefs(context).getString(KEY_ROLE, null)
    }

    fun getUserId(context: Context): Int {
        return getPrefs(context).getInt(KEY_USER_ID, -1)
    }

    fun isLoggedIn(context: Context): Boolean {
        return getToken(context) != null
    }

    fun clear(context: Context) {
        getPrefs(context).edit().clear().apply()
    }
}
