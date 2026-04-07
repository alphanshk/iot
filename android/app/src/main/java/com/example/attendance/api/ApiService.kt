package com.example.attendance.api

import com.example.attendance.model.LoginRequest
import com.example.attendance.model.LoginResponse
import com.example.attendance.model.MarkRequest
import com.example.attendance.model.RegisterRequest
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface ApiService {
    @POST("register")
    suspend fun register(@Body body: RegisterRequest): Response<ResponseBody>

    @POST("login")
    suspend fun login(@Body body: LoginRequest): Response<LoginResponse>

    @POST("mark_api")
    suspend fun markAttendance(@Body body: MarkRequest): Response<ResponseBody>

    @GET("attendance")
    suspend fun getAttendance(): Response<ResponseBody>
}
