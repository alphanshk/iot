package com.example.iotattendance

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.example.iotattendance.api.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject

class LoginActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)

        val phoneEt = findViewById<EditText>(R.id.etPhone)
        val passwordEt = findViewById<EditText>(R.id.etPassword)
        val loginBtn = findViewById<Button>(R.id.btnLogin)

        loginBtn.setOnClickListener {
            val phone = phoneEt.text.toString().trim()
            val password = passwordEt.text.toString().trim()
            if (phone.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Enter phone and password", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            lifecycleScope.launch {
                try {
                    val payload = JSONObject().apply {
                        put("phone", phone)
                        put("password", password)
                    }
                    val res = withContext(Dispatchers.IO) { ApiClient.post("login", payload) }
                    if (res.optBoolean("success")) {
                        val user = res.getJSONObject("user")
                        startActivity(
                            Intent(this@LoginActivity, AttendanceActivity::class.java)
                                .putExtra("employee_id", user.getInt("id"))
                                .putExtra("employee_name", user.getString("name"))
                        )
                        finish()
                    } else {
                        Toast.makeText(this@LoginActivity, res.optString("message", "Login failed"), Toast.LENGTH_SHORT).show()
                    }
                } catch (e: Exception) {
                    Toast.makeText(this@LoginActivity, "Network error: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }
}
