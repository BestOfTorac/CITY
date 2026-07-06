package com.toracshalby.emergencymobile.components

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
fun EmergencyHeader() {
    Row(
        modifier =
            Modifier.fillMaxWidth(),
        verticalAlignment =
            Alignment.CenterVertically,
        horizontalArrangement =
            Arrangement.spacedBy(14.dp)
    ) {
        Surface(
            modifier =
                Modifier.size(58.dp),
            shape =
                RoundedCornerShape(18.dp),
            color = AppPurpleSoft
        ) {
            Box(
                contentAlignment =
                    Alignment.Center
            ) {
                Text(
                    text = "!",
                    style =
                        MaterialTheme.typography
                            .headlineSmall,
                    color = AppPurple,
                    fontWeight =
                        FontWeight.Bold
                )
            }
        }

        Column(
            modifier =
                Modifier.weight(1f),
            verticalArrangement =
                Arrangement.spacedBy(4.dp)
        ) {
            Text(
                text = "Segnala un'emergenza",
                style =
                    MaterialTheme.typography
                        .headlineSmall,
                color = AppText,
                fontWeight =
                    FontWeight.Bold
            )

            Text(
                text =
                    "Inserisci le informazioni disponibili. " +
                            "La fotografia è facoltativa.",
                style =
                    MaterialTheme.typography
                        .bodyMedium,
                color = AppMutedText
            )
        }
    }
}


@Composable
fun EmergencySectionCard(
    title: String,
    content: @Composable () -> Unit
) {
    Card(
        modifier =
            Modifier.fillMaxWidth(),
        shape =
            RoundedCornerShape(22.dp),
        colors =
            CardDefaults.cardColors(
                containerColor =
                    AppSurface
            ),
        elevation =
            CardDefaults.cardElevation(
                defaultElevation = 2.dp
            )
    ) {
        Column(
            modifier =
                Modifier.padding(18.dp),
            verticalArrangement =
                Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = title,
                style =
                    MaterialTheme.typography
                        .titleMedium,
                color = AppPurpleDark,
                fontWeight =
                    FontWeight.SemiBold
            )

            content()
        }
    }
}


@Composable
fun ModernChoiceChip(
    label: String,
    icon: String,
    selected: Boolean,
    modifier: Modifier = Modifier,
    iconColor: Color = AppPurple,
    onClick: () -> Unit
) {
    Surface(
        onClick = onClick,
        modifier = modifier
            .height(52.dp),
        shape =
            RoundedCornerShape(15.dp),
        color =
            if (selected) {
                AppPurpleSoft
            } else {
                AppSurface
            },
        border =
            BorderStroke(
                if (selected) {
                    1.5.dp
                } else {
                    1.dp
                },
                if (selected) {
                    AppPurple
                } else {
                    AppBorder
                }
            )
    ) {
        Row(
            modifier =
                Modifier.padding(
                    horizontal = 10.dp
                ),
            verticalAlignment =
                Alignment.CenterVertically,
            horizontalArrangement =
                Arrangement.Center
        ) {
            Text(
                text = icon,
                color = iconColor,
                fontWeight =
                    FontWeight.Bold
            )

            Spacer(
                modifier =
                    Modifier.size(7.dp)
            )

            Text(
                text = label,
                style =
                    MaterialTheme.typography
                        .labelLarge,
                color =
                    if (selected) {
                        AppPurpleDark
                    } else {
                        AppText
                    },
                fontWeight =
                    if (selected) {
                        FontWeight.SemiBold
                    } else {
                        FontWeight.Normal
                    }
            )
        }
    }
}


@Composable
fun TriStateSelector(
    selectedValue: String,
    onSelected: (String) -> Unit
) {
    Row(
        modifier =
            Modifier.fillMaxWidth(),
        horizontalArrangement =
            Arrangement.spacedBy(10.dp)
    ) {
        ModernChoiceChip(
            label = "Sì",
            icon = "✓",
            selected =
                selectedValue == "YES",
            modifier =
                Modifier.weight(1f),
            iconColor = AppSuccess,
            onClick = {
                onSelected("YES")
            }
        )

        ModernChoiceChip(
            label = "No",
            icon = "×",
            selected =
                selectedValue == "NO",
            modifier =
                Modifier.weight(1f),
            iconColor = AppDanger,
            onClick = {
                onSelected("NO")
            }
        )

        ModernChoiceChip(
            label = "Non so",
            icon = "?",
            selected =
                selectedValue == "UNKNOWN",
            modifier =
                Modifier.weight(1f),
            iconColor = AppPurple,
            onClick = {
                onSelected("UNKNOWN")
            }
        )
    }
}


@Composable
fun emergencyTextFieldColors() =
    OutlinedTextFieldDefaults.colors(
        focusedBorderColor = AppPurple,
        unfocusedBorderColor = AppBorder,
        focusedLabelColor = AppPurple,
        cursorColor = AppPurple,
        focusedContainerColor =
            AppPurpleUltraSoft,
        unfocusedContainerColor =
            AppPurpleUltraSoft
    )
