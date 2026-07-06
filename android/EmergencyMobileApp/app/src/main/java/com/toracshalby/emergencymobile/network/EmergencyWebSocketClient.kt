package com.toracshalby.emergencymobile.network

import android.os.Handler
import android.os.Looper
import com.toracshalby.emergencymobile.model.EmergencyStatusUpdate
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class EmergencyWebSocketClient(
    private val onConnectionChanged: (String) -> Unit,
    private val onUpdateReceived: (EmergencyStatusUpdate) -> Unit
) : WebSocketListener() {

    private val mainHandler =
        Handler(Looper.getMainLooper())

    private val client =
        OkHttpClient.Builder()
            .pingInterval(30, TimeUnit.SECONDS)
            .build()

    private var webSocket: WebSocket? = null
    private var pendingEventId: String? = null

    fun connectAndSubscribe(eventId: String) {
        disconnect()

        pendingEventId = eventId

        dispatch {
            onConnectionChanged(
                "Connessione in corso..."
            )
        }

        val request =
            Request.Builder()
                .url(WEBSOCKET_URL)
                .build()

        webSocket =
            client.newWebSocket(
                request,
                this
            )
    }

    private fun subscribe(
        webSocket: WebSocket,
        eventId: String
    ) {
        val message =
            JSONObject()
                .put("action", "subscribe")
                .put("eventId", eventId)
                .toString()

        webSocket.send(message)
    }

    fun disconnect() {
        webSocket?.close(
            1000,
            "Chiusura richiesta dall'app"
        )

        webSocket = null
        pendingEventId = null
    }

    override fun onOpen(
        webSocket: WebSocket,
        response: Response
    ) {
        dispatch {
            onConnectionChanged("Connesso")
        }

        pendingEventId?.let { eventId ->
            subscribe(
                webSocket = webSocket,
                eventId = eventId
            )
        }
    }

    override fun onMessage(
        webSocket: WebSocket,
        text: String
    ) {
        try {
            val json = JSONObject(text)

            val status =
                json.optString(
                    "status",
                    "UNKNOWN"
                ).uppercase()

            val progress =
                json.optInt(
                    "progress",
                    defaultProgressForStatus(
                        status
                    )
                ).coerceIn(0, 100)

            val update =
                EmergencyStatusUpdate(
                    status = status,
                    eventId =
                        json.optString(
                            "eventId",
                            pendingEventId.orEmpty()
                        ),
                    message =
                        json.optString(
                            "message",
                            text
                        ),
                    progress = progress
                )

            dispatch {
                onUpdateReceived(update)
            }

        } catch (_: Exception) {
            dispatch {
                onUpdateReceived(
                    EmergencyStatusUpdate(
                        status = "UNKNOWN",
                        eventId =
                            pendingEventId
                                .orEmpty(),
                        message = text,
                        progress = 0
                    )
                )
            }
        }
    }

    override fun onClosing(
        webSocket: WebSocket,
        code: Int,
        reason: String
    ) {
        dispatch {
            onConnectionChanged(
                "Chiusura connessione..."
            )
        }

        webSocket.close(
            code,
            reason
        )
    }

    override fun onClosed(
        webSocket: WebSocket,
        code: Int,
        reason: String
    ) {
        dispatch {
            onConnectionChanged(
                "Disconnesso"
            )
        }
    }

    override fun onFailure(
        webSocket: WebSocket,
        throwable: Throwable,
        response: Response?
    ) {
        val errorMessage =
            throwable.message
                ?: "Errore WebSocket sconosciuto"

        dispatch {
            onConnectionChanged(
                "Errore: $errorMessage"
            )
        }
    }

    private fun dispatch(
        action: () -> Unit
    ) {
        mainHandler.post(action)
    }
}

fun defaultProgressForStatus(
    status: String
): Int {
    return when (status.uppercase()) {
        "PREPARING" -> 5
        "SUBSCRIBED" -> 10
        "REQUESTING_UPLOAD_URL" -> 15
        "UPLOAD_URL_READY" -> 20
        "IMAGE_UPLOADING" -> 25
        "NO_IMAGE" -> 35
        "IMAGE_UPLOADED" -> 35
        "REPORT_SENDING" -> 40
        "REPORT_ACCEPTED" -> 45
        "CAMERA_TEST_PREPARING" -> 5
        "CAMERA_TEST_STARTING" -> 40
        "CAMERA_TEST_ACCEPTED" -> 45
        "IMAGE_ANALYZED" -> 50
        "VALIDATED" -> 60
        "CONTEXTUALIZED" -> 70
        "CLASSIFIED" -> 80
        "SEVERITY_EVALUATED" -> 88
        "DECISION_COMPLETED" -> 94
        "RESPONDERS_NOTIFIED" -> 97
        "COMPLETED" -> 100

        "INVALID_EMERGENCY",
        "PROCESSING_FAILED",
        "IMAGE_ARCHIVE_FAILED" -> 100

        "FAILED",
        "UPLOAD_FAILED",
        "SUBMISSION_FAILED",
        "CAMERA_TEST_FAILED" -> 0

        else -> 0
    }
}
