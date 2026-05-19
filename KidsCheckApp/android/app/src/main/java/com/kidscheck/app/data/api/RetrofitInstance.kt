package com.kidscheck.app.data.api

import android.content.Context
import com.kidscheck.app.util.TokenManager
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitInstance {
    const val BASE_URL = "http://10.0.2.2:8000"  // Emulator localhost

    private fun createClient(context: Context): OkHttpClient {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        return OkHttpClient.Builder()
            .addInterceptor(Interceptor { chain ->
                val token = TokenManager.getToken(context)
                val request = if (token != null) {
                    chain.request().newBuilder()
                        .addHeader("Authorization", "Bearer $token")
                        .build()
                } else {
                    chain.request()
                }
                chain.proceed(request)
            })
            .addInterceptor(logging)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .build()
    }

    fun getApi(context: Context): ApiService {
        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(createClient(context))
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}
