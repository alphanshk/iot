package com.example.attendance

import android.app.Activity
import android.content.Intent
import android.graphics.Bitmap
import android.os.Bundle
import android.provider.MediaStore
import android.util.Base64
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.example.attendance.api.ApiClient
import com.example.attendance.model.MarkRequest
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream

class DashboardActivity : AppCompatActivity() {
    private var employeeId: Int = -1

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_dashboard)

        employeeId = intent.getIntExtra("employee_id", -1)
        val employeeName = intent.getStringExtra("employee_name") ?: "Employee"
        findViewById<TextView>(R.id.tvWelcome).text = "Welcome, $employeeName"

        findViewById<Button>(R.id.btnScan).setOnClickListener {
            startFingerprintAuth()
        }
    }

    private fun startFingerprintAuth() {
        if (BiometricManager.from(this).canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG)
            != BiometricManager.BIOMETRIC_SUCCESS
        ) {
            Toast.makeText(this, "Fingerprint not available", Toast.LENGTH_SHORT).show()
            return
        }

        val executor = ContextCompat.getMainExecutor(this)
        val prompt = BiometricPrompt(this, executor, object : BiometricPrompt.AuthenticationCallback() {
            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                super.onAuthenticationSucceeded(result)
                launchCamera()
            }
        })

        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Fingerprint Required")
            .setSubtitle("Authenticate to mark attendance")
            .setNegativeButtonText("Cancel")
            .build()

        prompt.authenticate(promptInfo)
    }

    private fun launchCamera() {
        val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        startActivityForResult(intent, 101)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 101 && resultCode == Activity.RESULT_OK) {
            val photo = data?.extras?.get("data") as? Bitmap ?: return
            val imageBase64 = bitmapToBase64(photo)
            sendAttendance(imageBase64)
        }
    }

    private fun bitmapToBase64(bitmap: Bitmap): String {
        val output = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 90, output)
        return Base64.encodeToString(output.toByteArray(), Base64.DEFAULT)
    }

    private fun sendAttendance(imageBase64: String) {
        lifecycleScope.launch {
            val response = ApiClient.api.markAttendance(MarkRequest(employeeId, imageBase64))
            if (response.isSuccessful) {
                Toast.makeText(this@DashboardActivity, "Attendance Marked", Toast.LENGTH_LONG).show()
            } else {
                Toast.makeText(this@DashboardActivity, "Attendance failed", Toast.LENGTH_LONG).show()
            }
        }
    }
}
