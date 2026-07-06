package com.toracshalby.emergencymobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent

import com.toracshalby.emergencymobile.ui.theme.EmergencyAppTheme

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            EmergencyAppTheme {
                EmergencyMobileApp()
            }
        }
    }
}