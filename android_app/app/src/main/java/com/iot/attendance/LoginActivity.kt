package com.iot.attendance

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import kotlin.concurrent.thread

class LoginActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)

        val etPhone = findViewById<EditText>(R.id.etPhone)
        val etPassword = findViewById<EditText>(R.id.etPassword)
        val btnLogin = findViewById<Button>(R.id.btnLogin)
        val tvStatus = findViewById<TextView>(R.id.tvStatus)

        btnLogin.setOnClickListener {
            val phone = etPhone.text.toString().trim()
            val password = etPassword.text.toString().trim()

            if (phone.isEmpty() || password.isEmpty()) {
                tvStatus.text = "Phone and password required"
                return@setOnClickListener
            }

            tvStatus.text = "Logging in..."
            thread {
                try {
                    val res = ApiService.login(phone, password)
                    runOnUiThread {
                        if (res.optBoolean("success", false)) {
                            val user = res.getJSONObject("user")
                            startActivity(Intent(this, MainActivity::class.java).apply {
                                putExtra("employee_id", user.getInt("id"))
                                putExtra("phone", user.getString("phone"))
                                putExtra("name", user.getString("name"))
                            })
                            finish()
                        } else {
                            tvStatus.text = res.optString("message", "Login failed")
                        }
                    }
                } catch (e: Exception) {
                    runOnUiThread { tvStatus.text = "Error: ${e.message}" }
                }
            }
        }
    }
}
