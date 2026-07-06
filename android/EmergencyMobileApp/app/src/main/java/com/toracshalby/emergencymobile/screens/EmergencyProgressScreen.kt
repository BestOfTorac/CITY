package com.toracshalby.emergencymobile.screens

import android.graphics.BitmapFactory
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.toracshalby.emergencymobile.model.EmergencyStatusUpdate
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import com.toracshalby.emergencymobile.ui.theme.AppBorder
import com.toracshalby.emergencymobile.ui.theme.AppMutedText
import com.toracshalby.emergencymobile.ui.theme.AppPurple
import com.toracshalby.emergencymobile.ui.theme.AppPurpleDark
import com.toracshalby.emergencymobile.ui.theme.AppPurpleSoft
import com.toracshalby.emergencymobile.ui.theme.AppPurpleUltraSoft
import com.toracshalby.emergencymobile.ui.theme.AppSuccess
import com.toracshalby.emergencymobile.ui.theme.AppSurface
import com.toracshalby.emergencymobile.ui.theme.AppText

private val ErrorRed = Color(0xFFB3261E)
private val ErrorSoft = Color(0xFFFFEDEA)
private val WarningOrange = Color(0xFFE65100)
private val WarningSoft = Color(0xFFFFF3E0)
private val SuccessSoft = Color(0xFFE8F7EE)

private enum class StepVisualState {
    PENDING,
    ACTIVE,
    COMPLETED,
    ERROR,
    WARNING
}

@Composable
fun EmergencyProgressScreen(
    eventId: String,
    hasImage: Boolean,
    source: String = "mobile",
    connectionStatus: String,
    statusUpdate: EmergencyStatusUpdate,
    cameraImageName: String? = null,
    cameraImageKey: String? = null,
    cameraImageUrl: String? = null,
    cameraImageExpiresIn: Int? = null,
    cameraId: String? = null,
    cameraLocation: String? = null,
    onBack: () -> Unit
) {
    val status =
        statusUpdate.status.uppercase()

    val isCameraTest =
        source.equals(
            "camera",
            ignoreCase = true
        )

    val progress =
        statusUpdate.progress
            .coerceIn(0, 100)

    val isFatalError =
        status == "INVALID_EMERGENCY" ||
                status == "PROCESSING_FAILED" ||
                status == "CAMERA_TEST_FAILED"

    val isArchiveWarning =
        status == "IMAGE_ARCHIVE_FAILED"

    val isTerminalProblem =
        isFatalError || isArchiveWarning

    val isCompleted =
        status == "COMPLETED"

    var lastSuccessfulProgress by
    rememberSaveable(eventId) {
        mutableIntStateOf(0)
    }

    var respondersNotified by
    rememberSaveable(eventId) {
        mutableStateOf(false)
    }

    LaunchedEffect(
        status,
        progress
    ) {
        if (
            status ==
            "RESPONDERS_NOTIFIED"
        ) {
            respondersNotified = true
        }

        if (!isTerminalProblem) {
            lastSuccessfulProgress =
                maxOf(
                    lastSuccessfulProgress,
                    progress
                )
        }
    }

    val timelineProgress =
        if (isTerminalProblem) {
            lastSuccessfulProgress
        } else {
            progress
        }

    val resultColor =
        when {
            isFatalError -> ErrorRed
            isArchiveWarning -> WarningOrange
            isCompleted -> AppSuccess
            else -> AppPurple
        }

    val resultSoftColor =
        when {
            isFatalError -> ErrorSoft
            isArchiveWarning -> WarningSoft
            isCompleted -> SuccessSoft
            else -> AppPurpleSoft
        }

    val resultIcon =
        when {
            isFatalError -> "×"
            isArchiveWarning -> "!"
            isCompleted -> "✓"
            else -> "↗"
        }

    val statusTitle =
        humanReadableStatus(status)

    val photoPreparationStep =
        if (hasImage) {
            "URL caricamento ottenuto"
        } else {
            "Nessuna foto da caricare"
        }

    val photoUploadStep =
        if (hasImage) {
            "Foto caricata su S3"
        } else {
            "Foto facoltativa non presente"
        }

    val steps =
        remember(
            hasImage,
            isCameraTest,
            respondersNotified
        ) {
            buildList {
                if (isCameraTest) {
                    add(
                        "Test telecamera preparato" to 5
                    )
                    add(
                        "Canale aggiornamenti attivo" to 10
                    )
                    add(
                        "Avvio simulazione richiesto" to 40
                    )
                    add(
                        "Test telecamera accettato" to 45
                    )
                    add(
                        "Immagine telecamera analizzata" to 50
                    )

                } else {
                    add(
                        "Segnalazione preparata" to 5
                    )
                    add(
                        "Canale aggiornamenti attivo" to 10
                    )
                    add(
                        photoPreparationStep to 20
                    )
                    add(
                        photoUploadStep to 35
                    )
                    add(
                        "Segnalazione inviata al backend" to 45
                    )

                    if (hasImage) {
                        add(
                            "Analisi immagine completata" to 50
                        )
                    }
                }

                add(
                    "Validazione completata" to 60
                )
                add(
                    "Contestualizzazione completata" to 70
                )
                add(
                    "Emergenza classificata" to 80
                )
                add(
                    "Gravità valutata" to 88
                )
                add(
                    "Decisione operativa completata" to 94
                )

                if (respondersNotified) {
                    add(
                        "Soccorritori notificati" to 97
                    )
                }

                add(
                    "Elaborazione completata" to 100
                )
            }
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
        Row(
            verticalAlignment =
                Alignment.CenterVertically,
            horizontalArrangement =
                Arrangement.spacedBy(14.dp)
        ) {
            Surface(
                modifier =
                    Modifier.size(54.dp),
                shape =
                    RoundedCornerShape(18.dp),
                color = resultSoftColor
            ) {
                Box(
                    contentAlignment =
                        Alignment.Center
                ) {
                    Text(
                        text = resultIcon,
                        color = resultColor,
                        style =
                            MaterialTheme.typography
                                .headlineSmall,
                        fontWeight =
                            FontWeight.Bold
                    )
                }
            }

            Column {
                Text(
                    text =
                        when {
                            isFatalError ->
                                if (isCameraTest) {
                                    "Test telecamera interrotto"
                                } else {
                                    "Elaborazione interrotta"
                                }

                            isArchiveWarning ->
                                "Elaborazione completata con avviso"

                            isCompleted ->
                                if (isCameraTest) {
                                    "Test telecamera completato"
                                } else {
                                    "Segnalazione completata"
                                }

                            else ->
                                if (isCameraTest) {
                                    "Stato del test telecamera"
                                } else {
                                    "Stato della segnalazione"
                                }
                        },
                    style =
                        MaterialTheme.typography
                            .headlineSmall,
                    fontWeight =
                        FontWeight.Bold
                )

                Text(
                    text =
                        when {
                            isFatalError ->
                                if (isCameraTest) {
                                    "Il test automatico non è stato completato"
                                } else {
                                    "La segnalazione non è stata completata"
                                }

                            isArchiveWarning ->
                                "L'emergenza è stata gestita, ma resta un problema"

                            isCompleted ->
                                "Tutte le operazioni sono terminate"

                            else ->
                                "Segui l'elaborazione in tempo reale"
                        },
                    style =
                        MaterialTheme.typography
                            .bodyMedium,
                    color = AppMutedText
                )
            }
        }

        Card(
            modifier =
                Modifier.fillMaxWidth(),
            shape =
                RoundedCornerShape(22.dp),
            colors =
                CardDefaults.cardColors(
                    containerColor =
                        if (isTerminalProblem || isCompleted) {
                            resultSoftColor
                        } else {
                            AppSurface
                        }
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
                Row(
                    modifier =
                        Modifier.fillMaxWidth(),
                    horizontalArrangement =
                        Arrangement.SpaceBetween,
                    verticalAlignment =
                        Alignment.CenterVertically
                ) {
                    Column(
                        verticalArrangement =
                            Arrangement.spacedBy(3.dp)
                    ) {
                        Text(
                            text = "Event ID",
                            style =
                                MaterialTheme.typography
                                    .labelMedium,
                            color = AppMutedText
                        )

                        Text(
                            text = eventId,
                            fontWeight =
                                FontWeight.SemiBold
                        )
                    }

                    ConnectionBadge(
                        connectionStatus =
                            connectionStatus
                    )
                }

                LinearProgressIndicator(
                    progress = {
                        progress / 100f
                    },
                    modifier =
                        Modifier.fillMaxWidth(),
                    color = resultColor,
                    trackColor =
                        resultSoftColor
                )

                Row(
                    modifier =
                        Modifier.fillMaxWidth(),
                    horizontalArrangement =
                        Arrangement.SpaceBetween,
                    verticalAlignment =
                        Alignment.Bottom
                ) {
                    Column(
                        modifier =
                            Modifier.weight(1f),
                        verticalArrangement =
                            Arrangement.spacedBy(4.dp)
                    ) {
                        Text(
                            text = statusTitle,
                            style =
                                MaterialTheme.typography
                                    .titleMedium,
                            color = resultColor,
                            fontWeight =
                                FontWeight.SemiBold
                        )

                        Text(
                            text =
                                statusUpdate.message,
                            style =
                                MaterialTheme.typography
                                    .bodyMedium,
                            color =
                                if (isTerminalProblem) {
                                    AppText
                                } else {
                                    AppMutedText
                                }
                        )
                    }

                    Text(
                        text = "$progress%",
                        modifier =
                            Modifier.padding(
                                start = 12.dp
                            ),
                        style =
                            MaterialTheme.typography
                                .headlineMedium,
                        color = resultColor,
                        fontWeight =
                            FontWeight.Bold
                    )
                }
            }
        }

        if (isCameraTest) {
            CameraSelectedImageCard(
                imageUrl = cameraImageUrl,
                imageName = cameraImageName,
                imageKey = cameraImageKey,
                expiresInSeconds =
                    cameraImageExpiresIn,
                cameraId = cameraId,
                cameraLocation =
                    cameraLocation
            )
        }

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
                    Arrangement.spacedBy(14.dp)
            ) {
                Text(
                    text = "Avanzamento",
                    style =
                        MaterialTheme.typography
                            .titleMedium,
                    color = AppPurpleDark,
                    fontWeight =
                        FontWeight.SemiBold
                )

                steps.forEachIndexed {
                        index,
                        step ->

                    val threshold =
                        step.second

                    val nextThreshold =
                        steps
                            .getOrNull(index + 1)
                            ?.second
                            ?: 101

                    val stepState =
                        when {
                            isTerminalProblem &&
                                    timelineProgress >= threshold ->
                                StepVisualState.COMPLETED

                            isTerminalProblem ->
                                StepVisualState.PENDING

                            isCompleted ->
                                StepVisualState.COMPLETED

                            timelineProgress >= threshold &&
                                    timelineProgress < nextThreshold ->
                                StepVisualState.ACTIVE

                            timelineProgress >= threshold ->
                                StepVisualState.COMPLETED

                            else ->
                                StepVisualState.PENDING
                        }

                    StatusStep(
                        label = step.first,
                        state = stepState
                    )
                }

                if (isTerminalProblem) {
                    StatusStep(
                        label = statusTitle,
                        state =
                            if (isArchiveWarning) {
                                StepVisualState.WARNING
                            } else {
                                StepVisualState.ERROR
                            }
                    )
                }
            }
        }

        OutlinedButton(
            onClick = onBack,
            modifier = Modifier
                .fillMaxWidth()
                .height(54.dp),
            shape =
                RoundedCornerShape(17.dp),
            border =
                BorderStroke(
                    1.dp,
                    AppBorder
                )
        ) {
            Text(
                text =
                    if (isCameraTest) {
                        "Torna al test telecamera"
                    } else {
                        "Torna al modulo"
                    },
                color = AppPurpleDark,
                fontWeight =
                    FontWeight.SemiBold
            )
        }
    }
}

@Composable
private fun CameraSelectedImageCard(
    imageUrl: String?,
    imageName: String?,
    imageKey: String?,
    expiresInSeconds: Int?,
    cameraId: String?,
    cameraLocation: String?
) {
    var imageBitmap by
    remember(imageUrl) {
        mutableStateOf<ImageBitmap?>(
            null
        )
    }

    var imageError by
    remember(imageUrl) {
        mutableStateOf<String?>(null)
    }

    var isLoading by
    remember(imageUrl) {
        mutableStateOf(
            !imageUrl.isNullOrBlank()
        )
    }

    LaunchedEffect(imageUrl) {
        imageBitmap = null
        imageError = null

        if (imageUrl.isNullOrBlank()) {
            isLoading = false
            return@LaunchedEffect
        }

        isLoading = true

        try {
            imageBitmap =
                loadRemoteImage(
                    imageUrl
                )

        } catch (error: Exception) {
            imageError =
                error.message
                    ?: "Impossibile caricare l'immagine"

        } finally {
            isLoading = false
        }
    }

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
                text =
                    "Immagine selezionata",
                style =
                    MaterialTheme.typography
                        .titleMedium,
                color = AppPurpleDark,
                fontWeight =
                    FontWeight.SemiBold
            )

            when {
                imageBitmap != null -> {
                    Image(
                        bitmap =
                            imageBitmap!!,
                        contentDescription =
                            "Immagine scelta dalla telecamera simulata",
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(220.dp)
                            .clip(
                                RoundedCornerShape(
                                    16.dp
                                )
                            ),
                        contentScale =
                            ContentScale.Crop
                    )
                }

                isLoading -> {
                    Surface(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(180.dp),
                        shape =
                            RoundedCornerShape(
                                16.dp
                            ),
                        color =
                            AppPurpleUltraSoft
                    ) {
                        Box(
                            contentAlignment =
                                Alignment.Center
                        ) {
                            Text(
                                text =
                                    "Caricamento anteprima...",
                                color =
                                    AppMutedText
                            )
                        }
                    }
                }

                imageError != null -> {
                    Surface(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(
                                vertical = 4.dp
                            ),
                        shape =
                            RoundedCornerShape(
                                16.dp
                            ),
                        color = ErrorSoft
                    ) {
                        Text(
                            text =
                                "Anteprima non disponibile: " +
                                        imageError,
                            modifier =
                                Modifier.padding(
                                    14.dp
                                ),
                            color = ErrorRed
                        )
                    }
                }

                else -> {
                    Surface(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(120.dp),
                        shape =
                            RoundedCornerShape(
                                16.dp
                            ),
                        color =
                            AppPurpleUltraSoft
                    ) {
                        Box(
                            contentAlignment =
                                Alignment.Center
                        ) {
                            Text(
                                text =
                                    "In attesa dell'immagine selezionata...",
                                color =
                                    AppMutedText
                            )
                        }
                    }
                }
            }

            imageName?.let {
                Text(
                    text = it,
                    fontWeight =
                        FontWeight.SemiBold,
                    color = AppText
                )
            }

            val cameraDetails =
                listOfNotNull(
                    cameraId,
                    cameraLocation
                ).joinToString(
                    separator = " · "
                )

            if (cameraDetails.isNotBlank()) {
                Text(
                    text = cameraDetails,
                    style =
                        MaterialTheme.typography
                            .bodyMedium,
                    color = AppMutedText
                )
            }

            imageKey?.let {
                Text(
                    text = it,
                    style =
                        MaterialTheme.typography
                            .bodySmall,
                    color = AppMutedText
                )
            }

            expiresInSeconds?.let {
                Text(
                    text =
                        "Link temporaneo valido per " +
                                "${it / 60} minuti",
                    style =
                        MaterialTheme.typography
                            .labelMedium,
                    color = AppMutedText
                )
            }
        }
    }
}

private suspend fun loadRemoteImage(
    imageUrl: String
): ImageBitmap =
    withContext(Dispatchers.IO) {
        val connection =
            URL(imageUrl)
                .openConnection()
                    as HttpURLConnection

        try {
            connection.connectTimeout =
                15_000

            connection.readTimeout =
                20_000

            connection.instanceFollowRedirects =
                true

            connection.doInput = true
            connection.connect()

            val responseCode =
                connection.responseCode

            if (
                responseCode !in
                200..299
            ) {
                throw IOException(
                    "HTTP $responseCode"
                )
            }

            val bitmap =
                connection.inputStream
                    .use { stream ->
                        BitmapFactory.decodeStream(
                            stream
                        )
                    }
                    ?: throw IOException(
                        "Formato immagine non valido"
                    )

            bitmap.asImageBitmap()

        } finally {
            connection.disconnect()
        }
    }

@Composable
private fun ConnectionBadge(
    connectionStatus: String
) {
    val isConnected =
        connectionStatus == "Connesso"

    val hasConnectionError =
        connectionStatus.startsWith(
            "Errore",
            ignoreCase = true
        )

    val badgeColor =
        when {
            isConnected -> SuccessSoft
            hasConnectionError -> ErrorSoft
            else -> AppPurpleSoft
        }

    val textColor =
        when {
            isConnected -> AppSuccess
            hasConnectionError -> ErrorRed
            else -> AppPurpleDark
        }

    Surface(
        shape = CircleShape,
        color = badgeColor
    ) {
        Text(
            text =
                "● $connectionStatus",
            modifier =
                Modifier.padding(
                    horizontal = 12.dp,
                    vertical = 7.dp
                ),
            style =
                MaterialTheme.typography
                    .labelMedium,
            color = textColor
        )
    }
}

@Composable
private fun StatusStep(
    label: String,
    state: StepVisualState
) {
    val circleColor =
        when (state) {
            StepVisualState.ACTIVE ->
                AppPurple

            StepVisualState.COMPLETED ->
                SuccessSoft

            StepVisualState.ERROR ->
                ErrorSoft

            StepVisualState.WARNING ->
                WarningSoft

            StepVisualState.PENDING ->
                AppPurpleUltraSoft
        }

    val icon =
        when (state) {
            StepVisualState.ACTIVE -> "●"
            StepVisualState.COMPLETED -> "✓"
            StepVisualState.ERROR -> "×"
            StepVisualState.WARNING -> "!"
            StepVisualState.PENDING -> "○"
        }

    val iconColor =
        when (state) {
            StepVisualState.ACTIVE ->
                Color.White

            StepVisualState.COMPLETED ->
                AppSuccess

            StepVisualState.ERROR ->
                ErrorRed

            StepVisualState.WARNING ->
                WarningOrange

            StepVisualState.PENDING ->
                AppMutedText
        }

    val textColor =
        when (state) {
            StepVisualState.ERROR ->
                ErrorRed

            StepVisualState.WARNING ->
                WarningOrange

            StepVisualState.PENDING ->
                AppMutedText

            else ->
                AppText
        }

    Row(
        modifier =
            Modifier.fillMaxWidth(),
        verticalAlignment =
            Alignment.CenterVertically,
        horizontalArrangement =
            Arrangement.spacedBy(12.dp)
    ) {
        Surface(
            modifier =
                Modifier.size(30.dp),
            shape = CircleShape,
            color = circleColor,
            border =
                if (
                    state ==
                    StepVisualState.PENDING
                ) {
                    BorderStroke(
                        1.dp,
                        AppBorder
                    )
                } else {
                    null
                }
        ) {
            Box(
                contentAlignment =
                    Alignment.Center
            ) {
                Text(
                    text = icon,
                    color = iconColor,
                    style =
                        MaterialTheme.typography
                            .labelMedium,
                    fontWeight =
                        FontWeight.Bold
                )
            }
        }

        Text(
            text = label,
            style =
                MaterialTheme.typography
                    .bodyLarge,
            color = textColor,
            fontWeight =
                when (state) {
                    StepVisualState.ACTIVE,
                    StepVisualState.ERROR,
                    StepVisualState.WARNING ->
                        FontWeight.SemiBold

                    else ->
                        FontWeight.Normal
                }
        )
    }
}

private fun humanReadableStatus(
    status: String
): String {
    return when (status.uppercase()) {
        "PREPARING" ->
            "Preparazione della segnalazione"

        "SUBSCRIBED" ->
            "Canale aggiornamenti attivo"

        "REQUESTING_UPLOAD_URL" ->
            "Preparazione caricamento foto"

        "UPLOAD_URL_READY" ->
            "Caricamento foto pronto"

        "IMAGE_UPLOADING" ->
            "Caricamento foto in corso"

        "NO_IMAGE" ->
            "Nessuna foto allegata"

        "IMAGE_UPLOADED" ->
            "Foto caricata"

        "REPORT_SENDING" ->
            "Invio della segnalazione"

        "REPORT_ACCEPTED" ->
            "Segnalazione accettata"

        "CAMERA_TEST_PREPARING" ->
            "Preparazione del test telecamera"

        "CAMERA_TEST_STARTING" ->
            "Avvio della telecamera simulata"

        "CAMERA_TEST_ACCEPTED" ->
            "Test telecamera accettato"

        "CAMERA_TEST_FAILED" ->
            "Test telecamera non riuscito"

        "IMAGE_ANALYZED" ->
            "Immagine analizzata"

        "VALIDATED" ->
            "Segnalazione validata"

        "CONTEXTUALIZED" ->
            "Emergenza contestualizzata"

        "CLASSIFIED" ->
            "Emergenza classificata"

        "SEVERITY_EVALUATED" ->
            "Gravità valutata"

        "DECISION_COMPLETED" ->
            "Decisione operativa completata"

        "RESPONDERS_NOTIFIED" ->
            "Soccorritori notificati"

        "COMPLETED" ->
            "Elaborazione completata"

        "INVALID_EMERGENCY" ->
            "Segnalazione non valida"

        "PROCESSING_FAILED" ->
            "Elaborazione non riuscita"

        "IMAGE_ARCHIVE_FAILED" ->
            "Archiviazione immagine non riuscita"

        "UPLOAD_FAILED" ->
            "Caricamento foto non riuscito"

        "SUBMISSION_FAILED" ->
            "Invio della segnalazione non riuscito"

        "FAILED" ->
            "Operazione non riuscita"

        else ->
            status
                .replace(
                    "_",
                    " "
                )
                .lowercase()
                .replaceFirstChar {
                    it.uppercase()
                }
    }
}
