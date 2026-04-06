package com.example.attendance

import android.graphics.Bitmap
import android.os.Bundle
import android.util.Base64
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import java.io.ByteArrayOutputStream
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class DashboardActivity : AppCompatActivity() {
    private lateinit var api: ApiService
    private lateinit var sessionManager: SessionManager
    private lateinit var txtStatus: TextView

    private val cameraLauncher = registerForActivityResult(ActivityResultContracts.TakePicturePreview()) { bitmap: Bitmap? ->
        if (bitmap == null) {
            Toast.makeText(this, "Camera image is required", Toast.LENGTH_SHORT).show()
            return@registerForActivityResult
        }
        sendAttendance(bitmap)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_dashboard)

        api = ApiService.create()
        sessionManager = SessionManager(this)

        txtStatus = findViewById(R.id.txtStatus)
        val btnMark = findViewById<Button>(R.id.btnMarkAttendance)

        btnMark.setOnClickListener {
            triggerBiometricThenCapture()
        }
    }

    private fun triggerBiometricThenCapture() {
        val biometricManager = BiometricManager.from(this)
        val canAuth = biometricManager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG)

        if (canAuth != BiometricManager.BIOMETRIC_SUCCESS) {
            Toast.makeText(this, "Biometric not available/enrolled", Toast.LENGTH_LONG).show()
            return
        }

        val executor = ContextCompat.getMainExecutor(this)
        val prompt = BiometricPrompt(this, executor, object : BiometricPrompt.AuthenticationCallback() {
            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                super.onAuthenticationSucceeded(result)
                cameraLauncher.launch(null)
            }

            override fun onAuthenticationFailed() {
                super.onAuthenticationFailed()
                Toast.makeText(this@DashboardActivity, "Fingerprint not recognized", Toast.LENGTH_SHORT).show()
            }

            override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                super.onAuthenticationError(errorCode, errString)
                Toast.makeText(this@DashboardActivity, "Biometric error: $errString", Toast.LENGTH_LONG).show()
            }
        })

        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Fingerprint Verification")
            .setSubtitle("Verify identity before marking attendance")
            .setNegativeButtonText("Cancel")
            .build()

        prompt.authenticate(promptInfo)
    }

    private fun sendAttendance(bitmap: Bitmap) {
        val employeeId = sessionManager.getEmployeeId()
        if (employeeId <= 0) {
            Toast.makeText(this, "Session expired. Login again.", Toast.LENGTH_LONG).show()
            finish()
            return
        }

        val imageBase64 = bitmapToBase64(bitmap)
        val payload = MarkAttendanceRequest(employeeId, imageBase64)

        api.markAttendance(payload).enqueue(object : Callback<MarkAttendanceResponse> {
            override fun onResponse(call: Call<MarkAttendanceResponse>, response: Response<MarkAttendanceResponse>) {
                val body = response.body()
                if (response.isSuccessful && body?.success == true) {
                    txtStatus.text = "${body.message}\nType: ${body.type} | ${body.date} ${body.time}"
                } else {
                    txtStatus.text = body?.message ?: "Attendance failed"
                }
            }

            override fun onFailure(call: Call<MarkAttendanceResponse>, t: Throwable) {
                txtStatus.text = "API error: ${t.message}"
            }
        })
    }

    private fun bitmapToBase64(bitmap: Bitmap): String {
        val stream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 85, stream)
        val bytes = stream.toByteArray()
        return Base64.encodeToString(bytes, Base64.NO_WRAP)
    }
}
