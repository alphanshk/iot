package com.example.attendance

import android.content.Context

class SessionManager(context: Context) {
    private val pref = context.getSharedPreferences("attendance_session", Context.MODE_PRIVATE)

    fun saveEmployee(employee: Employee) {
        pref.edit()
            .putInt("employee_id", employee.id)
            .putString("employee_name", employee.name)
            .putString("employee_phone", employee.phone)
            .apply()
    }

    fun getEmployeeId(): Int = pref.getInt("employee_id", -1)

    fun clear() {
        pref.edit().clear().apply()
    }
}
