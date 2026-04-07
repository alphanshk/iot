package com.example.attendance

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.example.attendance.api.ApiClient
import com.example.attendance.model.RegisterRequest
import kotlinx.coroutines.launch

class RegisterActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_register)

        val nameEt = findViewById<EditText>(R.id.etName)
        val phoneEt = findViewById<EditText>(R.id.etPhone)
        val passwordEt = findViewById<EditText>(R.id.etPassword)
        findViewById<Button>(R.id.btnRegister).setOnClickListener {
            lifecycleScope.launch {
                val resp = ApiClient.api.register(
                    RegisterRequest(
                        nameEt.text.toString(),
                        phoneEt.text.toString(),
                        passwordEt.text.toString()
                    )
                )
                if (resp.isSuccessful) {
                    Toast.makeText(this@RegisterActivity, "Registered", Toast.LENGTH_SHORT).show()
                    startActivity(Intent(this@RegisterActivity, LoginActivity::class.java))
                    finish()
                } else {
                    Toast.makeText(this@RegisterActivity, "Registration failed", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }
}
