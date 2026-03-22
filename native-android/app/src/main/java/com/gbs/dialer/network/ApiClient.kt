// Android Agent: OkHttp/Retrofit Networking Implementation
package com.gbs.dialer.network
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import okhttp3.Interceptor

object ApiClient {
    private const val BASE_URL = "http://10.0.2.2:8000/"
    
    // Auth Interceptor for secure JWT injection
    val tokenInterceptor = Interceptor { chain ->
        val request = chain.request().newBuilder()
            .addHeader("Authorization", "Bearer \${AuthManager.token}")
            .build()
        chain.proceed(request)
    }
    
    val client = OkHttpClient.Builder().addInterceptor(tokenInterceptor).build()
    
    val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(client)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
}
