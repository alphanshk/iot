# IoT Smart Employee Attendance System

## Folder Structure

```text
iot/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── README.md
│   └── data/
│       └── saved_faces/
└── android/
    ├── README.md
    └── app/src/main/
        ├── AndroidManifest.xml
        ├── java/com/example/attendance/
        │   ├── RegisterActivity.kt
        │   ├── LoginActivity.kt
        │   ├── DashboardActivity.kt
        │   ├── api/
        │   │   ├── ApiClient.kt
        │   │   └── ApiService.kt
        │   └── model/
        │       └── Models.kt
        └── res/layout/
            ├── activity_register.xml
            ├── activity_login.xml
            └── activity_dashboard.xml
```

## Core Features Implemented

- User registration and login APIs
- Default user seeded (`Alphan / 7385520906 / admin123`)
- Attendance alternates IN/OUT by latest record
- Fingerprint + camera flow in Android
- Camera image converted to Base64 and sent to backend
- Face image saved to `data/saved_faces/employeeId_timestamp.jpg`
- GPIO18 buzzer success/error patterns
- SIM900A SMS on each attendance mark
