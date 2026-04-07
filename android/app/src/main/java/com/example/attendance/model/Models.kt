package com.example.attendance.model

data class RegisterRequest(val name: String, val phone: String, val password: String)
data class LoginRequest(val phone: String, val password: String)
data class MarkRequest(val employee_id: Int, val image_base64: String)

data class User(val id: Int, val name: String, val phone: String)
data class LoginResponse(val message: String, val user: User)
