package com.toracshalby.emergencymobile.screens

import android.content.Context
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.OpenableColumns
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts.PickVisualMedia
import androidx.activity.result.contract.ActivityResultContracts.TakePicture
import androidx.compose.foundation.Image
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.util.UUID
import java.util.concurrent.TimeUnit

import com.toracshalby.emergencymobile.ui.theme.*

@Composable
fun EmergencyHomeScreen(
    onReportEmergency: () -> Unit,
    onOpenCameraTest: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .statusBarsPadding()
            .navigationBarsPadding()
            .verticalScroll(
                rememberScrollState()
            )
            .padding(
                horizontal = 20.dp,
                vertical = 18.dp
            ),
        verticalArrangement =
            Arrangement.spacedBy(18.dp)
    ) {
        Text(
            text = "Benvenuto",
            style =
                MaterialTheme.typography
                    .titleLarge,
            color = AppPurple,
            fontWeight =
                FontWeight.SemiBold
        )

        Text(
            text = "Cosa vuoi fare?",
            style =
                MaterialTheme.typography
                    .displaySmall,
            color = AppText,
            fontWeight =
                FontWeight.Bold
        )

        Text(
            text =
                "Puoi inviare una segnalazione manuale " +
                        "oppure avviare il test del flusso telecamera.",
            style =
                MaterialTheme.typography
                    .bodyLarge,
            color = AppMutedText
        )

        HomeActionCard(
            title = "Segnala emergenza",
            description =
                "Invia una segnalazione manuale con posizione, dettagli e foto.",
            badge = "Assistenza immediata",
            icon = "!",
            accentColor = AppEmergency,
            accentDarkColor =
                AppEmergencyDark,
            softColor =
                AppEmergencySoft,
            onClick =
                onReportEmergency
        )

        HomeActionCard(
            title = "Avvia telecamera",
            description =
                "Simula una telecamera IoT e avvia il percorso automatico.",
            badge = "Modalità di test",
            icon = "◉",
            accentColor = AppPurple,
            accentDarkColor =
                AppPurpleDark,
            softColor =
                AppCameraSoft,
            onClick =
                onOpenCameraTest
        )

        Card(
            modifier =
                Modifier.fillMaxWidth(),
            shape =
                RoundedCornerShape(20.dp),
            colors =
                CardDefaults.cardColors(
                    containerColor =
                        AppSurface
                ),
            elevation =
                CardDefaults.cardElevation(
                    defaultElevation = 1.dp
                )
        ) {
            Row(
                modifier =
                    Modifier.padding(16.dp),
                verticalAlignment =
                    Alignment.CenterVertically,
                horizontalArrangement =
                    Arrangement.spacedBy(12.dp)
            ) {
                Surface(
                    modifier =
                        Modifier.size(42.dp),
                    shape = CircleShape,
                    color = AppPurpleSoft
                ) {
                    Box(
                        contentAlignment =
                            Alignment.Center
                    ) {
                        Text(
                            text = "✓",
                            color = AppPurple,
                            fontWeight =
                                FontWeight.Bold
                        )
                    }
                }

                Column(
                    modifier =
                        Modifier.weight(1f)
                ) {
                    Text(
                        text =
                            "La tua sicurezza è importante",
                        fontWeight =
                            FontWeight.SemiBold,
                        color = AppText
                    )

                    Text(
                        text =
                            "Le segnalazioni vengono gestite " +
                                    "attraverso il sistema cloud.",
                        style =
                            MaterialTheme.typography
                                .bodySmall,
                        color = AppMutedText
                    )
                }
            }
        }
    }
}


@Composable
private fun HomeActionCard(
    title: String,
    description: String,
    badge: String,
    icon: String,
    accentColor: Color,
    accentDarkColor: Color,
    softColor: Color,
    onClick: () -> Unit
) {
    Surface(
        onClick = onClick,
        modifier =
            Modifier.fillMaxWidth(),
        shape =
            RoundedCornerShape(26.dp),
        color = AppSurface,
        border =
            BorderStroke(
                1.25.dp,
                accentColor.copy(
                    alpha = 0.32f
                )
            ),
        shadowElevation = 3.dp
    ) {
        Column(
            modifier =
                Modifier.padding(20.dp),
            verticalArrangement =
                Arrangement.spacedBy(16.dp)
        ) {
            Row(
                modifier =
                    Modifier.fillMaxWidth(),
                verticalAlignment =
                    Alignment.CenterVertically,
                horizontalArrangement =
                    Arrangement.spacedBy(16.dp)
            ) {
                Surface(
                    modifier =
                        Modifier.size(82.dp),
                    shape = CircleShape,
                    color = softColor
                ) {
                    Box(
                        contentAlignment =
                            Alignment.Center
                    ) {
                        Text(
                            text = icon,
                            style =
                                MaterialTheme.typography
                                    .displaySmall,
                            color = accentColor,
                            fontWeight =
                                FontWeight.Bold
                        )
                    }
                }

                Column(
                    modifier =
                        Modifier.weight(1f),
                    verticalArrangement =
                        Arrangement.spacedBy(7.dp)
                ) {
                    Text(
                        text = title,
                        style =
                            MaterialTheme.typography
                                .headlineSmall,
                        color =
                            accentDarkColor,
                        fontWeight =
                            FontWeight.Bold
                    )

                    Text(
                        text = description,
                        style =
                            MaterialTheme.typography
                                .bodyMedium,
                        color = AppMutedText
                    )
                }

                Surface(
                    modifier =
                        Modifier.size(46.dp),
                    shape = CircleShape,
                    color = accentColor
                ) {
                    Box(
                        contentAlignment =
                            Alignment.Center
                    ) {
                        Text(
                            text = "›",
                            style =
                                MaterialTheme.typography
                                    .headlineMedium,
                            color = Color.White
                        )
                    }
                }
            }

            Surface(
                shape =
                    RoundedCornerShape(12.dp),
                color = softColor
            ) {
                Text(
                    text = badge,
                    modifier =
                        Modifier.padding(
                            horizontal = 12.dp,
                            vertical = 7.dp
                        ),
                    style =
                        MaterialTheme.typography
                            .labelLarge,
                    color =
                        accentDarkColor,
                    fontWeight =
                        FontWeight.Medium
                )
            }
        }
    }
}
