package com.example.iotattendance.api

import org.json.JSONObject
import java.io.BufferedReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

object ApiClient {
    private const val BASE_URL = "http://<RASPBERRY_PI_IP>:5000/"

    fun post(path: String, body: JSONObject): JSONObject {
        val conn = (URL(BASE_URL + path).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            setRequestProperty("Content-Type", "application/json")
            doOutput = true
            connectTimeout = 5000
            readTimeout = 10000
        }

        OutputStreamWriter(conn.outputStream).use { it.write(body.toString()) }

        val stream = if (conn.responseCode in 200..299) conn.inputStream else conn.errorStream
        val response = BufferedReader(stream.reader()).readText()
        return JSONObject(response)
    }
}
