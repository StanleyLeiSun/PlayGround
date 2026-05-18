package com.kidscheck.app

import android.app.Application

class KidsCheckApp : Application() {
    companion object {
        lateinit var instance: KidsCheckApp
            private set
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
    }
}
