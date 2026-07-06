package com.toracshalby.emergencymobile

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import com.toracshalby.emergencymobile.model.EmergencyStatusUpdate
import com.toracshalby.emergencymobile.model.PresignedUploadData
import com.toracshalby.emergencymobile.navigation.AppScreen
import com.toracshalby.emergencymobile.network.EmergencyWebSocketClient
import com.toracshalby.emergencymobile.network.requestPresignedUploadUrl
import com.toracshalby.emergencymobile.network.sendEmergencyReport
import com.toracshalby.emergencymobile.network.startCameraTest
import com.toracshalby.emergencymobile.network.uploadImageToS3
import com.toracshalby.emergencymobile.screens.CameraTestScreen
import com.toracshalby.emergencymobile.screens.EmergencyHomeScreen
import com.toracshalby.emergencymobile.screens.EmergencyProgressScreen
import com.toracshalby.emergencymobile.screens.EmergencyReportForm
import com.toracshalby.emergencymobile.utils.resolveSelectedImageInfo
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import java.util.UUID

@Composable
fun EmergencyMobileApp() {
    val context = LocalContext.current
    val coroutineScope =
        rememberCoroutineScope()

    var currentScreen by remember {
        mutableStateOf(
            AppScreen.HOME
        )
    }

    var activeEventId by remember {
        mutableStateOf("")
    }

    var activeHasImage by remember {
        mutableStateOf(false)
    }

    var progressSource by remember {
        mutableStateOf("mobile")
    }

    var cameraSelectedImageName by remember {
        mutableStateOf<String?>(null)
    }

    var cameraSelectedImageKey by remember {
        mutableStateOf<String?>(null)
    }

    var cameraSelectedImageUrl by remember {
        mutableStateOf<String?>(null)
    }

    var cameraSelectedImageExpiresIn by remember {
        mutableStateOf<Int?>(null)
    }

    var activeCameraId by remember {
        mutableStateOf<String?>(null)
    }

    var activeCameraLocation by remember {
        mutableStateOf<String?>(null)
    }

    var cameraSubscriptionReady by remember {
        mutableStateOf<
                CompletableDeferred<Unit>?
                >(null)
    }

    var cameraSubscriptionEventId by remember {
        mutableStateOf<String?>(null)
    }

    var connectionStatus by remember {
        mutableStateOf("Disconnesso")
    }

    var statusUpdate by remember {
        mutableStateOf(
            EmergencyStatusUpdate(
                status = "NOT_STARTED",
                eventId = "",
                message =
                    "Segnalazione non ancora inviata",
                progress = 0
            )
        )
    }

    var submissionJob by remember {
        mutableStateOf<Job?>(null)
    }

    val webSocketClient = remember {
        EmergencyWebSocketClient(
            onConnectionChanged = { status ->
                connectionStatus = status
            },
            onUpdateReceived = { update ->
                if (
                    update.status.equals(
                        "SUBSCRIBED",
                        ignoreCase = true
                    ) &&
                    update.eventId ==
                    cameraSubscriptionEventId
                ) {
                    cameraSubscriptionReady
                        ?.complete(Unit)
                }

                val belongsToActiveEvent =
                    activeEventId.isBlank() ||
                            update.eventId.isBlank() ||
                            update.eventId ==
                            activeEventId

                if (
                    belongsToActiveEvent &&
                    update.progress >=
                    statusUpdate.progress
                ) {
                    statusUpdate = update
                }
            }
        )
    }

    DisposableEffect(Unit) {
        onDispose {
            submissionJob?.cancel()
            cameraSubscriptionReady
                ?.cancel()
            webSocketClient.disconnect()
        }
    }

    when (currentScreen) {
        AppScreen.HOME -> {
            EmergencyHomeScreen(
                onReportEmergency = {
                    currentScreen =
                        AppScreen.REPORT_FORM
                },
                onOpenCameraTest = {
                    currentScreen =
                        AppScreen.CAMERA_TEST
                }
            )
        }

        AppScreen.REPORT_FORM -> {
            EmergencyReportForm(
                onBackToHome = {
                    currentScreen =
                        AppScreen.HOME
                },
                onSubmit = { report ->
                    submissionJob?.cancel()
                    cameraSubscriptionReady
                        ?.cancel()
                    cameraSubscriptionReady = null
                    cameraSubscriptionEventId = null

                    activeEventId =
                        report.eventId
                    activeHasImage =
                        report.imageUri != null
                    progressSource =
                        "mobile"

                    cameraSelectedImageName = null
                    cameraSelectedImageKey = null
                    cameraSelectedImageUrl = null
                    cameraSelectedImageExpiresIn = null
                    activeCameraId = null
                    activeCameraLocation = null

                    statusUpdate =
                        EmergencyStatusUpdate(
                            status = "PREPARING",
                            eventId =
                                report.eventId,
                            message =
                                "Preparazione della segnalazione",
                            progress = 5
                        )

                    currentScreen =
                        AppScreen.PROGRESS

                    webSocketClient
                        .connectAndSubscribe(
                            report.eventId
                        )

                    submissionJob =
                        coroutineScope.launch {
                            var uploadData:
                                    PresignedUploadData? =
                                null

                            try {
                                if (
                                    report.imageUri != null
                                ) {
                                    statusUpdate =
                                        EmergencyStatusUpdate(
                                            status =
                                                "REQUESTING_UPLOAD_URL",
                                            eventId =
                                                report.eventId,
                                            message =
                                                "Richiesta dell'URL di caricamento...",
                                            progress = 15
                                        )

                                    val imageInfo =
                                        withContext(
                                            Dispatchers.IO
                                        ) {
                                            resolveSelectedImageInfo(
                                                context =
                                                    context,
                                                uri =
                                                    report.imageUri
                                            )
                                        }

                                    uploadData =
                                        requestPresignedUploadUrl(
                                            eventId =
                                                report.eventId,
                                            imageInfo =
                                                imageInfo
                                        )

                                    statusUpdate =
                                        EmergencyStatusUpdate(
                                            status =
                                                "UPLOAD_URL_READY",
                                            eventId =
                                                report.eventId,
                                            message =
                                                "URL temporaneo ottenuto.",
                                            progress = 20
                                        )

                                    statusUpdate =
                                        EmergencyStatusUpdate(
                                            status =
                                                "IMAGE_UPLOADING",
                                            eventId =
                                                report.eventId,
                                            message =
                                                "Caricamento della fotografia su S3...",
                                            progress = 25
                                        )

                                    uploadImageToS3(
                                        context = context,
                                        uri =
                                            report.imageUri,
                                        uploadData =
                                            uploadData
                                    )

                                    statusUpdate =
                                        EmergencyStatusUpdate(
                                            status =
                                                "IMAGE_UPLOADED",
                                            eventId =
                                                report.eventId,
                                            message =
                                                "Foto caricata correttamente su S3.",
                                            progress = 35
                                        )

                                } else {
                                    statusUpdate =
                                        EmergencyStatusUpdate(
                                            status =
                                                "NO_IMAGE",
                                            eventId =
                                                report.eventId,
                                            message =
                                                "Nessuna fotografia da caricare.",
                                            progress = 35
                                        )
                                }

                            } catch (
                                cancelled:
                                CancellationException
                            ) {
                                throw cancelled

                            } catch (
                                error: Exception
                            ) {
                                statusUpdate =
                                    EmergencyStatusUpdate(
                                        status =
                                            "UPLOAD_FAILED",
                                        eventId =
                                            report.eventId,
                                        message =
                                            error.message
                                                ?: "Caricamento della fotografia non riuscito.",
                                        progress =
                                            statusUpdate
                                                .progress
                                                .coerceAtLeast(
                                                    10
                                                )
                                    )

                                return@launch
                            }

                            try {
                                statusUpdate =
                                    EmergencyStatusUpdate(
                                        status =
                                            "REPORT_SENDING",
                                        eventId =
                                            report.eventId,
                                        message =
                                            "Invio della segnalazione al backend...",
                                        progress = 40
                                    )

                                val response =
                                    sendEmergencyReport(
                                        report =
                                            report,
                                        uploadData =
                                            uploadData
                                    )

                                val pipelineText =
                                    when (
                                        response.pipeline
                                    ) {
                                        "MOBILE_INGESTION" ->
                                            "Analisi dell'immagine avviata."

                                        "DIRECT_WORKFLOW" ->
                                            "Workflow avviato senza immagine."

                                        else ->
                                            "Elaborazione avviata."
                                    }

                                statusUpdate =
                                    EmergencyStatusUpdate(
                                        status =
                                            "REPORT_ACCEPTED",
                                        eventId =
                                            response.eventId,
                                        message =
                                            "${response.message}\n$pipelineText",
                                        progress = 45
                                    )

                            } catch (
                                cancelled:
                                CancellationException
                            ) {
                                throw cancelled

                            } catch (
                                error: Exception
                            ) {
                                statusUpdate =
                                    EmergencyStatusUpdate(
                                        status =
                                            "SUBMISSION_FAILED",
                                        eventId =
                                            report.eventId,
                                        message =
                                            error.message
                                                ?: "Invio della segnalazione non riuscito.",
                                        progress =
                                            statusUpdate
                                                .progress
                                                .coerceAtLeast(
                                                    35
                                                )
                                    )
                            }
                        }
                }
            )
        }

        AppScreen.CAMERA_TEST -> {
            CameraTestScreen(
                onBackToHome = {
                    currentScreen =
                        AppScreen.HOME
                },
                onStartTest = {
                    submissionJob?.cancel()
                    cameraSubscriptionReady
                        ?.cancel()

                    val eventId =
                        "camera-${UUID.randomUUID()}"

                    val subscriptionReady =
                        CompletableDeferred<Unit>()

                    activeEventId = eventId
                    activeHasImage = true
                    progressSource = "camera"

                    cameraSelectedImageName = null
                    cameraSelectedImageKey = null
                    cameraSelectedImageUrl = null
                    cameraSelectedImageExpiresIn = null
                    activeCameraId = null
                    activeCameraLocation = null

                    cameraSubscriptionReady =
                        subscriptionReady
                    cameraSubscriptionEventId =
                        eventId

                    statusUpdate =
                        EmergencyStatusUpdate(
                            status =
                                "CAMERA_TEST_PREPARING",
                            eventId =
                                eventId,
                            message =
                                "Preparazione del test telecamera",
                            progress = 5
                        )

                    currentScreen =
                        AppScreen.PROGRESS

                    webSocketClient
                        .connectAndSubscribe(
                            eventId
                        )

                    submissionJob =
                        coroutineScope.launch {
                            try {
                                withTimeout(
                                    8_000L
                                ) {
                                    subscriptionReady
                                        .await()
                                }

                                statusUpdate =
                                    EmergencyStatusUpdate(
                                        status =
                                            "CAMERA_TEST_STARTING",
                                        eventId =
                                            eventId,
                                        message =
                                            "Avvio della telecamera simulata...",
                                        progress = 40
                                    )

                                val response =
                                    startCameraTest(
                                        eventId
                                    )

                                cameraSelectedImageName =
                                    response.selectedImageName

                                cameraSelectedImageKey =
                                    response.selectedImageKey

                                cameraSelectedImageUrl =
                                    response.selectedImageUrl

                                cameraSelectedImageExpiresIn =
                                    response.selectedImageExpiresIn

                                activeCameraId =
                                    response.cameraId

                                activeCameraLocation =
                                    response.location

                                val details =
                                    listOfNotNull(
                                        response.cameraId,
                                        response.location
                                    ).joinToString(
                                        separator = " Â· "
                                    )

                                if (
                                    statusUpdate.progress <
                                    45
                                ) {
                                    statusUpdate =
                                        EmergencyStatusUpdate(
                                            status =
                                                response.status,
                                            eventId =
                                                response.eventId,
                                            message =
                                                if (
                                                    details.isBlank()
                                                ) {
                                                    response.message
                                                } else {
                                                    "${response.message}\n$details"
                                                },
                                            progress = 45
                                        )
                                }

                            } catch (
                                timeout:
                                TimeoutCancellationException
                            ) {
                                statusUpdate =
                                    EmergencyStatusUpdate(
                                        status =
                                            "CAMERA_TEST_FAILED",
                                        eventId =
                                            eventId,
                                        message =
                                            "Il canale WebSocket non Ã¨ diventato pronto in tempo.",
                                        progress =
                                            statusUpdate
                                                .progress
                                                .coerceAtLeast(
                                                    5
                                                )
                                    )

                            } catch (
                                cancelled:
                                CancellationException
                            ) {
                                throw cancelled

                            } catch (
                                error: Exception
                            ) {
                                statusUpdate =
                                    EmergencyStatusUpdate(
                                        status =
                                            "CAMERA_TEST_FAILED",
                                        eventId =
                                            eventId,
                                        message =
                                            error.message
                                                ?: "Avvio del test telecamera non riuscito.",
                                        progress =
                                            statusUpdate
                                                .progress
                                                .coerceAtLeast(
                                                    10
                                                )
                                    )

                            } finally {
                                if (
                                    cameraSubscriptionEventId ==
                                    eventId
                                ) {
                                    cameraSubscriptionReady =
                                        null
                                    cameraSubscriptionEventId =
                                        null
                                }
                            }
                        }
                }
            )
        }

        AppScreen.PROGRESS -> {
            EmergencyProgressScreen(
                eventId =
                    activeEventId,
                hasImage =
                    activeHasImage,
                source =
                    progressSource,
                connectionStatus =
                    connectionStatus,
                statusUpdate =
                    statusUpdate,
                cameraImageName =
                    cameraSelectedImageName,
                cameraImageKey =
                    cameraSelectedImageKey,
                cameraImageUrl =
                    cameraSelectedImageUrl,
                cameraImageExpiresIn =
                    cameraSelectedImageExpiresIn,
                cameraId =
                    activeCameraId,
                cameraLocation =
                    activeCameraLocation,
                onBack = {
                    submissionJob?.cancel()
                    submissionJob = null

                    cameraSubscriptionReady
                        ?.cancel()
                    cameraSubscriptionReady = null
                    cameraSubscriptionEventId = null

                    webSocketClient
                        .disconnect()

                    cameraSelectedImageName = null
                    cameraSelectedImageKey = null
                    cameraSelectedImageUrl = null
                    cameraSelectedImageExpiresIn = null
                    activeCameraId = null
                    activeCameraLocation = null

                    currentScreen =
                        if (
                            progressSource ==
                            "camera"
                        ) {
                            AppScreen.CAMERA_TEST
                        } else {
                            AppScreen.REPORT_FORM
                        }
                }
            )
        }
    }
}
