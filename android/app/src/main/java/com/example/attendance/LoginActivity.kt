package com.example.attendance

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.example.attendance.api.ApiClient
import com.example.attendance.model.LoginRequest
import kotlinx.coroutines.launch

class LoginActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)

        val phoneEt = findViewById<EditText>(R.id.etPhone)
        val passwordEt = findViewById<EditText>(R.id.etPassword)

        findViewById<Button>(R.id.btnLogin).setOnClickListener {
            lifecycleScope.launch {
                val response = ApiClient.api.login(LoginRequest(phoneEt.text.toString(), passwordEt.text.toString()))
                if (response.isSuccessful && response.body() != null) {
                    val user = response.body()!!.user
                    val intent = Intent(this@LoginActivity, DashboardActivity::class.java)
                    intent.putExtra("employee_id", user.id)
                    intent.putExtra("employee_name", user.name)
                    startActivity(intent)
                } else {
                    Toast.makeText(this@LoginActivity, "Invalid credentials", Toast.LENGTH_SHORT).show()
                }
            }
        }

        findViewById<TextView>(R.id.tvGoRegister).setOnClickListener {
            startActivity(Intent(this, RegisterActivity::class.java))
        }
    }
}
