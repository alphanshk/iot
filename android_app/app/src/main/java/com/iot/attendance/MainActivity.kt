package com.iot.attendance

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Bundle
import android.util.Base64
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import kotlin.concurrent.thread
import java.io.ByteArrayOutputStream

class MainActivity : AppCompatActivity() {
    private var employeeId: Int = -1
    private var phone: String = ""
    private lateinit var tvResult: TextView
    private lateinit var ivPreview: ImageView
    private var pendingBitmap: Bitmap? = null

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) launchCamera() else tvResult.text = "Camera permission denied"
    }

    private val cameraLauncher = registerForActivityResult(
        ActivityResultContracts.TakePicturePreview()
    ) { bitmap ->
        if (bitmap != null) {
            pendingBitmap = bitmap
            ivPreview.setImageBitmap(bitmap)
            doBiometricThenUpload()
        } else {
            tvResult.text = "No image captured"
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        employeeId = intent.getIntExtra("employee_id", -1)
        phone = intent.getStringExtra("phone").orEmpty()

        tvResult = findViewById(R.id.tvResult)
        ivPreview = findViewById(R.id.ivPreview)
        val btnCapture = findViewById<Button>(R.id.btnCapture)

        btnCapture.setOnClickListener {
            checkCameraPermissionAndCapture()
        }
    }

    private fun checkCameraPermissionAndCapture() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            launchCamera()
        } else {
            requestPermissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    private fun launchCamera() {
        cameraLauncher.launch(null)
    }

    private fun doBiometricThenUpload() {
        val executor = ContextCompat.getMainExecutor(this)
        val biometricPrompt = BiometricPrompt(this, executor,
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    super.onAuthenticationSucceeded(result)
                    uploadAttendance()
                }

                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    super.onAuthenticationError(errorCode, errString)
                    tvResult.text = "Fingerprint error: $errString"
                }

                override fun onAuthenticationFailed() {
                    super.onAuthenticationFailed()
                    tvResult.text = "Fingerprint not recognized"
                }
            })

        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Fingerprint Authentication")
            .setSubtitle("Authenticate to mark attendance")
            .setNegativeButtonText("Cancel")
            .build()

        biometricPrompt.authenticate(promptInfo)
    }

    private fun uploadAttendance() {
        val bmp = pendingBitmap ?: run {
            tvResult.text = "No image available"
            return
        }

        tvResult.text = "Uploading attendance..."
        thread {
            try {
                val stream = ByteArrayOutputStream()
                bmp.compress(Bitmap.CompressFormat.JPEG, 85, stream)
                val imageBase64 = Base64.encodeToString(stream.toByteArray(), Base64.NO_WRAP)

                val response = ApiService.markAttendance(employeeId, phone, imageBase64)
                runOnUiThread {
                    tvResult.text = response.optString("message", "Done")
                }
            } catch (e: Exception) {
                runOnUiThread { tvResult.text = "Upload failed: ${e.message}" }
            }
        }
    }
}
