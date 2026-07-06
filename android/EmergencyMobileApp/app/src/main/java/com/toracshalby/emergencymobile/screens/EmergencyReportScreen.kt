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

import com.toracshalby.emergencymobile.components.*
import com.toracshalby.emergencymobile.model.EmergencyReportDraft
import com.toracshalby.emergencymobile.ui.theme.*
import com.toracshalby.emergencymobile.utils.createCameraImageUri

@Composable
fun EmergencyReportForm(
    onBackToHome: () -> Unit,
    onSubmit:
        (EmergencyReportDraft) -> Unit
) {
    val context = LocalContext.current

    var location by rememberSaveable {
        mutableStateOf("")
    }

    var description by rememberSaveable {
        mutableStateOf("")
    }

    var reportedType by rememberSaveable {
        mutableStateOf("UNKNOWN")
    }

    var injured by rememberSaveable {
        mutableStateOf("UNKNOWN")
    }

    var immediateDanger by rememberSaveable {
        mutableStateOf("UNKNOWN")
    }

    var selectedImageUri by remember {
        mutableStateOf<Uri?>(null)
    }

    var pendingCameraUri by remember {
        mutableStateOf<Uri?>(null)
    }

    var showPhotoSourceDialog by rememberSaveable {
        mutableStateOf(false)
    }

    var validationMessage by rememberSaveable {
        mutableStateOf("")
    }

    val photoPicker =
        rememberLauncherForActivityResult(
            contract = PickVisualMedia()
        ) { uri ->
            if (uri != null) {
                selectedImageUri = uri
                validationMessage = ""
            }
        }

    val cameraLauncher =
        rememberLauncherForActivityResult(
            contract = TakePicture()
        ) { success ->
            val capturedUri = pendingCameraUri

            if (
                success &&
                capturedUri != null
            ) {
                selectedImageUri = capturedUri
                validationMessage = ""
            }

            pendingCameraUri = null
        }

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
            Arrangement.spacedBy(16.dp)
    ) {
        TextButton(
            onClick = onBackToHome
        ) {
            Text(
                text = "← Torna alla home",
                color = AppPurpleDark,
                fontWeight =
                    FontWeight.SemiBold
            )
        }

        EmergencyHeader()

        EmergencySectionCard(
            title = "Tipo di emergenza"
        ) {
            Row(
                modifier =
                    Modifier.fillMaxWidth(),
                horizontalArrangement =
                    Arrangement.spacedBy(10.dp)
            ) {
                ModernChoiceChip(
                    label = "Incendio",
                    icon = "🔥",
                    selected =
                        reportedType == "FIRE",
                    modifier =
                        Modifier.weight(1f),
                    onClick = {
                        reportedType = "FIRE"
                    }
                )

                ModernChoiceChip(
                    label = "Incidente",
                    icon = "🚗",
                    selected =
                        reportedType == "ACCIDENT",
                    modifier =
                        Modifier.weight(1f),
                    onClick = {
                        reportedType = "ACCIDENT"
                    }
                )

                ModernChoiceChip(
                    label = "Non so",
                    icon = "?",
                    selected =
                        reportedType == "UNKNOWN",
                    modifier =
                        Modifier.weight(1f),
                    onClick = {
                        reportedType = "UNKNOWN"
                    }
                )
            }
        }

        EmergencySectionCard(
            title = "Posizione"
        ) {
            OutlinedTextField(
                value = location,
                onValueChange = {
                    location = it
                    validationMessage = ""
                },
                modifier =
                    Modifier.fillMaxWidth(),
                placeholder = {
                    Text(
                        "Es. Via Cambridge 50, Roma"
                    )
                },
                leadingIcon = {
                    Text(
                        text = "📍",
                        style =
                            MaterialTheme.typography
                                .titleMedium
                    )
                },
                singleLine = true,
                shape =
                    RoundedCornerShape(16.dp),
                colors =
                    emergencyTextFieldColors()
            )
        }

        EmergencySectionCard(
            title = "Descrizione"
        ) {
            OutlinedTextField(
                value = description,
                onValueChange = {
                    if (it.length <= 500) {
                        description = it
                        validationMessage = ""
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(154.dp),
                placeholder = {
                    Text(
                        "Descrivi l'accaduto..."
                    )
                },
                supportingText = {
                    Row(
                        modifier =
                            Modifier.fillMaxWidth(),
                        horizontalArrangement =
                            Arrangement.End
                    ) {
                        Text(
                            text =
                                "${description.length}/500",
                            color = AppMutedText
                        )
                    }
                },
                shape =
                    RoundedCornerShape(16.dp),
                colors =
                    emergencyTextFieldColors()
            )
        }

        EmergencySectionCard(
            title = "Ci sono persone ferite?"
        ) {
            TriStateSelector(
                selectedValue = injured,
                onSelected = {
                    injured = it
                }
            )
        }

        EmergencySectionCard(
            title =
                "Esiste un pericolo immediato?"
        ) {
            TriStateSelector(
                selectedValue =
                    immediateDanger,
                onSelected = {
                    immediateDanger = it
                }
            )
        }

        Text(
            text = "Foto dell'emergenza",
            style =
                MaterialTheme.typography
                    .titleMedium,
            color = AppPurpleDark,
            fontWeight = FontWeight.SemiBold
        )

        Surface(
            onClick = {
                showPhotoSourceDialog = true
            },
            modifier =
                Modifier.fillMaxWidth(),
            shape =
                RoundedCornerShape(20.dp),
            color = AppPurpleUltraSoft,
            border = BorderStroke(
                1.5.dp,
                AppPurple.copy(
                    alpha = 0.55f
                )
            )
        ) {
            Row(
                modifier = Modifier.padding(
                    horizontal = 18.dp,
                    vertical = 18.dp
                ),
                verticalAlignment =
                    Alignment.CenterVertically,
                horizontalArrangement =
                    Arrangement.spacedBy(14.dp)
            ) {
                Surface(
                    modifier =
                        Modifier.size(48.dp),
                    shape = CircleShape,
                    color = AppPurpleSoft
                ) {
                    Box(
                        contentAlignment =
                            Alignment.Center
                    ) {
                        Text(
                            text = "📷",
                            style =
                                MaterialTheme.typography
                                    .titleLarge
                        )
                    }
                }

                Column(
                    modifier =
                        Modifier.weight(1f),
                    verticalArrangement =
                        Arrangement.spacedBy(3.dp)
                ) {
                    Text(
                        text =
                            if (
                                selectedImageUri == null
                            ) {
                                "Aggiungi foto"
                            } else {
                                "Cambia foto"
                            },
                        style =
                            MaterialTheme.typography
                                .titleMedium,
                        fontWeight =
                            FontWeight.SemiBold,
                        color = AppText
                    )

                    Text(
                        text =
                            "Scatta una foto o selezionala dalla galleria",
                        style =
                            MaterialTheme.typography
                                .bodySmall,
                        color = AppMutedText
                    )
                }

                Text(
                    text = "›",
                    style =
                        MaterialTheme.typography
                            .headlineSmall,
                    color = AppPurple
                )
            }
        }

        selectedImageUri?.let { uri ->
            ImagePreview(uri = uri)

            OutlinedButton(
                onClick = {
                    selectedImageUri = null
                },
                modifier =
                    Modifier.fillMaxWidth(),
                shape =
                    RoundedCornerShape(16.dp),
                border =
                    BorderStroke(
                        1.dp,
                        AppBorder
                    )
            ) {
                Text(
                    text = "Rimuovi foto",
                    color = AppDanger
                )
            }
        }

        if (
            validationMessage.isNotBlank()
        ) {
            Card(
                modifier =
                    Modifier.fillMaxWidth(),
                shape =
                    RoundedCornerShape(16.dp),
                colors =
                    CardDefaults.cardColors(
                        containerColor =
                            Color(0xFFFFF0EE)
                    ),
                border =
                    BorderStroke(
                        1.dp,
                        AppDanger.copy(
                            alpha = 0.35f
                        )
                    )
            ) {
                Text(
                    text =
                        validationMessage,
                    modifier =
                        Modifier.padding(16.dp),
                    color = AppDanger,
                    fontWeight =
                        FontWeight.Medium
                )
            }
        }

        Button(
            onClick = {
                validationMessage =
                    when {
                        location.isBlank() -> {
                            "Inserisci la posizione."
                        }

                        description.isBlank() -> {
                            "Inserisci una descrizione."
                        }

                        else -> {
                            val eventId =
                                "mobile-" +
                                        UUID.randomUUID()
                                            .toString()
                                            .take(8)

                            onSubmit(
                                EmergencyReportDraft(
                                    eventId =
                                        eventId,
                                    reportedType =
                                        reportedType,
                                    location =
                                        location.trim(),
                                    description =
                                        description.trim(),
                                    injured =
                                        injured,
                                    immediateDanger =
                                        immediateDanger,
                                    imageUri =
                                        selectedImageUri
                                )
                            )

                            ""
                        }
                    }
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(58.dp),
            shape =
                RoundedCornerShape(18.dp),
            colors =
                ButtonDefaults.buttonColors(
                    containerColor =
                        AppPurple,
                    contentColor =
                        Color.White
                )
        ) {
            Text(
                text =
                    "☁  Prepara segnalazione e carica foto",
                style =
                    MaterialTheme.typography
                        .titleMedium,
                fontWeight =
                    FontWeight.SemiBold
            )
        }

        Spacer(
            modifier =
                Modifier.height(8.dp)
        )
    }

    if (showPhotoSourceDialog) {
        AlertDialog(
            onDismissRequest = {
                showPhotoSourceDialog = false
            },
            shape =
                RoundedCornerShape(24.dp),
            containerColor = AppSurface,
            title = {
                Text(
                    text = "Aggiungi una foto",
                    fontWeight =
                        FontWeight.Bold
                )
            },
            text = {
                Column(
                    verticalArrangement =
                        Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text =
                            "Scegli una fotografia dalla galleria " +
                                    "oppure scattane una nuova.",
                        color = AppMutedText
                    )

                    OutlinedButton(
                        onClick = {
                            showPhotoSourceDialog = false

                            photoPicker.launch(
                                PickVisualMediaRequest(
                                    PickVisualMedia.ImageOnly
                                )
                            )
                        },
                        modifier =
                            Modifier.fillMaxWidth(),
                        shape =
                            RoundedCornerShape(14.dp)
                    ) {
                        Text(
                            "🖼  Scegli dalla galleria"
                        )
                    }

                    Button(
                        onClick = {
                            showPhotoSourceDialog = false

                            try {
                                val photoUri =
                                    createCameraImageUri(
                                        context
                                    )

                                pendingCameraUri =
                                    photoUri

                                cameraLauncher.launch(
                                    photoUri
                                )

                            } catch (
                                error: Exception
                            ) {
                                pendingCameraUri = null

                                validationMessage =
                                    "Impossibile aprire la fotocamera: " +
                                            (
                                                    error.message
                                                        ?: "errore sconosciuto"
                                                    )
                            }
                        },
                        modifier =
                            Modifier.fillMaxWidth(),
                        shape =
                            RoundedCornerShape(14.dp),
                        colors =
                            ButtonDefaults.buttonColors(
                                containerColor =
                                    AppPurple
                            )
                    ) {
                        Text(
                            "📷  Scatta una foto"
                        )
                    }
                }
            },
            confirmButton = {},
            dismissButton = {
                TextButton(
                    onClick = {
                        showPhotoSourceDialog = false
                    }
                ) {
                    Text("Annulla")
                }
            }
        )
    }
}
