package com.example.attendance

data class LoginRequest(val phone: String, val password: String)

data class Employee(val id: Int, val name: String, val phone: String)

data class LoginResponse(val success: Boolean, val message: String, val employee: Employee?)

data class MarkAttendanceRequest(val employee_id: Int, val image_base64: String)

data class MarkAttendanceResponse(
    val success: Boolean,
    val message: String,
    val employee_id: Int?,
    val date: String?,
    val time: String?,
    val type: String?
)
