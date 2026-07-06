package com.toracshalby.emergencymobile.network

import com.toracshalby.emergencymobile.model.EmergencyReportDraft
import com.toracshalby.emergencymobile.model.EmergencySubmissionResponse
import com.toracshalby.emergencymobile.model.PresignedUploadData
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit


data class CameraTestResponse(
    val status: String,
    val message: String,
    val eventId: String,
    val testId: String?,
    val cameraId: String?,
    val location: String?,
    val selectedImageName: String?,
    val selectedImageKey: String?,
    val selectedImageUrl: String?,
    val selectedImageExpiresIn: Int?
)

private val emergencyHttpClient =
    OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .callTimeout(90, TimeUnit.SECONDS)
        .build()


suspend fun startCameraTest(
    eventId: String
): CameraTestResponse =
    withContext(Dispatchers.IO) {
        val requestJson =
            JSONObject()
                .put("eventId", eventId)

        val requestBody =
            requestJson
                .toString()
                .toRequestBody(
                    "application/json; charset=utf-8"
                        .toMediaType()
                )

        val request =
            Request.Builder()
                .url(CAMERA_TEST_ENDPOINT)
                .post(requestBody)
                .build()

        emergencyHttpClient
            .newCall(request)
            .execute()
            .use { response ->
                val responseText =
                    response.body.string()

                val responseJson =
                    try {
                        JSONObject(responseText)
                    } catch (
                        error: Exception
                    ) {
                        throw IOException(
                            "Il backend del test telecamera " +
                                    "ha restituito una risposta " +
                                    "non valida (${response.code})."
                        )
                    }

                if (!response.isSuccessful) {
                    val backendMessage =
                        responseJson.optString(
                            "message",
                            "Avvio del test telecamera non riuscito."
                        )

                    throw IOException(
                        "$backendMessage " +
                                "(HTTP ${response.code})"
                    )
                }

                val status =
                    responseJson.optString(
                        "status"
                    )

                val responseEventId =
                    responseJson.optString(
                        "eventId"
                    )

                if (
                    status !=
                    "CAMERA_TEST_ACCEPTED"
                ) {
                    throw IOException(
                        "Il backend non ha accettato " +
                                "il test telecamera."
                    )
                }

                if (
                    responseEventId.isBlank()
                    || responseEventId != eventId
                ) {
                    throw IOException(
                        "L'eventId restituito dal backend " +
                                "non coincide con quello dell'app."
                    )
                }

                CameraTestResponse(
                    status = status,
                    message =
                        responseJson.optString(
                            "message",
                            "Test telecamera avviato."
                        ),
                    eventId =
                        responseEventId,
                    testId =
                        responseJson
                            .optString(
                                "testId"
                            )
                            .takeIf {
                                it.isNotBlank()
                            },
                    cameraId =
                        responseJson
                            .optString(
                                "cameraId"
                            )
                            .takeIf {
                                it.isNotBlank()
                            },
                    location =
                        responseJson
                            .optString(
                                "location"
                            )
                            .takeIf {
                                it.isNotBlank()
                            },
                    selectedImageName =
                        responseJson
                            .optString(
                                "selectedImageName"
                            )
                            .takeIf {
                                it.isNotBlank()
                            },
                    selectedImageKey =
                        responseJson
                            .optString(
                                "selectedImageKey"
                            )
                            .takeIf {
                                it.isNotBlank()
                            },
                    selectedImageUrl =
                        responseJson
                            .optString(
                                "selectedImageUrl"
                            )
                            .takeIf {
                                it.isNotBlank()
                            },
                    selectedImageExpiresIn =
                        responseJson
                            .optInt(
                                "selectedImageExpiresIn",
                                -1
                            )
                            .takeIf {
                                it > 0
                            }
                )
            }
    }


suspend fun sendEmergencyReport(
    report: EmergencyReportDraft,
    uploadData: PresignedUploadData?
): EmergencySubmissionResponse =
    withContext(Dispatchers.IO) {
        val requestJson =
            JSONObject()
                .put("eventId", report.eventId)
                .put("source", "mobile")
                .put(
                    "reportedType",
                    report.reportedType
                )
                .put(
                    "location",
                    report.location
                )
                .put(
                    "description",
                    report.description
                )
                .put(
                    "injured",
                    report.injured
                )
                .put(
                    "immediateDanger",
                    report.immediateDanger
                )

        if (uploadData != null) {
            val imageData =
                JSONObject()
                    .put(
                        "bucket",
                        uploadData.bucket
                    )
                    .put(
                        "imageKey",
                        uploadData.imageKey
                    )
                    .put(
                        "contentType",
                        uploadData.contentType
                    )
                    .put(
                        "originalFileName",
                        uploadData.originalFileName
                    )

            requestJson.put(
                "imageData",
                imageData
            )
        }

        val requestBody =
            requestJson
                .toString()
                .toRequestBody(
                    "application/json; charset=utf-8"
                        .toMediaType()
                )

        val request =
            Request.Builder()
                .url(EMERGENCY_ENDPOINT)
                .post(requestBody)
                .build()

        emergencyHttpClient
            .newCall(request)
            .execute()
            .use { response ->
                val responseText =
                    response.body.string()

                val responseJson =
                    try {
                        JSONObject(responseText)
                    } catch (
                        error: Exception
                    ) {
                        throw IOException(
                            "Il backend ha restituito " +
                                    "una risposta non valida " +
                                    "(${response.code})."
                        )
                    }

                if (!response.isSuccessful) {
                    val backendMessage =
                        responseJson.optString(
                            "message",
                            "Invio della segnalazione non riuscito."
                        )

                    throw IOException(
                        "$backendMessage " +
                                "(HTTP ${response.code})"
                    )
                }

                val status =
                    responseJson.optString(
                        "status"
                    )

                val eventId =
                    responseJson.optString(
                        "eventId"
                    )

                if (
                    status.isBlank() ||
                    eventId.isBlank()
                ) {
                    throw IOException(
                        "La risposta del backend " +
                                "non contiene status o eventId."
                    )
                }

                EmergencySubmissionResponse(
                    status = status,
                    message =
                        responseJson.optString(
                            "message",
                            "Segnalazione accettata."
                        ),
                    eventId = eventId,
                    pipeline =
                        responseJson
                            .optString(
                                "pipeline"
                            )
                            .takeIf {
                                it.isNotBlank()
                            },
                    executionArn =
                        responseJson
                            .optString(
                                "executionArn"
                            )
                            .takeIf {
                                it.isNotBlank()
                            }
                )
            }
    }
