package com.iot.attendance

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

object ApiService {
    // Replace with Raspberry Pi IP
    private const val BASE_URL = "http://192.168.1.100:5000"
    private val client = OkHttpClient()

    fun login(phone: String, password: String): JSONObject {
        val json = JSONObject().apply {
            put("phone", phone)
            put("password", password)
        }
        return postJson("$BASE_URL/login", json)
    }

    fun markAttendance(employeeId: Int, phone: String, imageBase64: String): JSONObject {
        val json = JSONObject().apply {
            put("employee_id", employeeId)
            put("phone", phone)
            put("image_base64", imageBase64)
        }
        return postJson("$BASE_URL/mark_api", json)
    }

    private fun postJson(url: String, data: JSONObject): JSONObject {
        val body = data.toString().toRequestBody("application/json".toMediaType())
        val request = Request.Builder().url(url).post(body).build()
        client.newCall(request).execute().use { response ->
            val bodyText = response.body?.string().orEmpty()
            return if (bodyText.isNotBlank()) JSONObject(bodyText)
            else JSONObject().put("success", false).put("message", "Empty response")
        }
    }
}
