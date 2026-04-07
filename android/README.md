# Android App (Kotlin)

## Required dependencies (app-level Gradle)

```gradle
implementation "org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1"
implementation "androidx.lifecycle:lifecycle-runtime-ktx:2.8.3"
implementation "com.squareup.retrofit2:retrofit:2.11.0"
implementation "com.squareup.retrofit2:converter-gson:2.11.0"
implementation "androidx.biometric:biometric:1.1.0"
```

Update `ApiClient.BASE_URL` to your Raspberry Pi LAN IP.

Flow:
- RegisterActivity: register new users
- LoginActivity: login with phone/password
- DashboardActivity: fingerprint auth -> camera capture -> Base64 -> `/mark_api`
