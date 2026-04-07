package com.example.iotattendance

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
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.example.iotattendance.api.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.ByteArrayOutputStream

class AttendanceActivity : AppCompatActivity() {
    private var employeeId: Int = -1
    private lateinit var statusTv: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_attendance)

        employeeId = intent.getIntExtra("employee_id", -1)
        val employeeName = intent.getStringExtra("employee_name") ?: "Employee"

        val nameTv = findViewById<TextView>(R.id.tvName)
        statusTv = findViewById(R.id.tvStatus)
        val markBtn = findViewById<Button>(R.id.btnMarkAttendance)

        nameTv.text = "Welcome, $employeeName"

        markBtn.setOnClickListener {
            if (employeeId <= 0) {
                Toast.makeText(this, "Invalid employee", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            authenticateAndOpenCamera()
        }
    }

    private fun authenticateAndOpenCamera() {
        val executor = ContextCompat.getMainExecutor(this)
        val biometricPrompt = BiometricPrompt(
            this,
            executor,
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    openCamera()
                }

                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    Toast.makeText(this@AttendanceActivity, "Fingerprint error: $errString", Toast.LENGTH_SHORT).show()
                }

                override fun onAuthenticationFailed() {
                    Toast.makeText(this@AttendanceActivity, "Fingerprint failed", Toast.LENGTH_SHORT).show()
                }
            }
        )

        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Fingerprint Required")
            .setSubtitle("Authenticate to mark attendance")
            .setNegativeButtonText("Cancel")
            .build()

        biometricPrompt.authenticate(promptInfo)
    }

    private fun openCamera() {
        val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        startActivityForResult(intent, 1001)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 1001 && resultCode == Activity.RESULT_OK) {
            val bitmap = data?.extras?.get("data") as? Bitmap
            if (bitmap == null) {
                Toast.makeText(this, "Camera image missing", Toast.LENGTH_SHORT).show()
                return
            }
            sendAttendance(bitmap)
        }
    }

    private fun sendAttendance(bitmap: Bitmap) {
        lifecycleScope.launch {
            try {
                val imageBase64 = bitmapToBase64(bitmap)
                val payload = JSONObject().apply {
                    put("employee_id", employeeId)
                    put("image_base64", imageBase64)
                }

                val res = withContext(Dispatchers.IO) { ApiClient.post("mark_api", payload) }
                if (res.optBoolean("success")) {
                    val markType = res.optString("type")
                    val time = res.optString("time")
                    statusTv.text = "Attendance $markType marked at $time"
                } else {
                    statusTv.text = "Failed: ${res.optString("message")}" 
                }
            } catch (e: Exception) {
                statusTv.text = "Network error: ${e.message}"
            }
        }
    }

    private fun bitmapToBase64(bitmap: Bitmap): String {
        val output = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 85, output)
        return Base64.encodeToString(output.toByteArray(), Base64.NO_WRAP)
    }
}
