package com.toracshalby.emergencymobile.network

import android.content.Context
import android.net.Uri
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit
import com.toracshalby.emergencymobile.model.PresignedUploadData
import com.toracshalby.emergencymobile.model.SelectedImageInfo

private val uploadHttpClient =
    OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .callTimeout(90, TimeUnit.SECONDS)
        .build()

suspend fun requestPresignedUploadUrl(
    eventId: String,
    imageInfo: SelectedImageInfo
): PresignedUploadData =
    withContext(Dispatchers.IO) {
        val requestJson =
            JSONObject()
                .put(
                    "eventId",
                    eventId
                )
                .put(
                    "fileName",
                    imageInfo.fileName
                )
                .put(
                    "contentType",
                    imageInfo.contentType
                )
                .toString()

        val requestBody =
            requestJson.toRequestBody(
                "application/json; charset=utf-8"
                    .toMediaType()
            )

        val request =
            Request.Builder()
                .url(
                    UPLOAD_URL_ENDPOINT
                )
                .post(requestBody)
                .build()

        uploadHttpClient
            .newCall(request)
            .execute()
            .use { response ->
                val responseText =
                    response.body.string()

                if (
                    !response.isSuccessful
                ) {
                    throw IOException(
                        "Errore nella richiesta " +
                                "dell'URL di caricamento " +
                                "(${response.code}): " +
                                responseText.take(300)
                    )
                }

                val responseJson =
                    JSONObject(responseText)

                if (
                    responseJson
                        .optString("status") !=
                    "READY"
                ) {
                    throw IOException(
                        responseJson.optString(
                            "message",
                            "La Lambda non ha restituito " +
                                    "un URL valido."
                        )
                    )
                }

                val uploadUrl =
                    responseJson.optString(
                        "uploadUrl"
                    )

                if (
                    uploadUrl.isBlank()
                ) {
                    throw IOException(
                        "uploadUrl assente " +
                                "nella risposta."
                    )
                }

                val imageData =
                    responseJson
                        .getJSONObject(
                            "imageData"
                        )

                val uploadHeaders =
                    responseJson
                        .optJSONObject(
                            "uploadHeaders"
                        )

                val signedContentType =
                    uploadHeaders
                        ?.optString(
                            "Content-Type"
                        )
                        ?.takeIf {
                            it.isNotBlank()
                        }
                        ?: imageInfo.contentType

                PresignedUploadData(
                    uploadUrl = uploadUrl,
                    bucket =
                        imageData.optString(
                            "bucket"
                        ),
                    imageKey =
                        imageData.optString(
                            "imageKey"
                        ),
                    contentType =
                        signedContentType,
                    originalFileName =
                        imageData.optString(
                            "originalFileName",
                            imageInfo.fileName
                        )
                )
            }
    }


suspend fun uploadImageToS3(
    context: Context,
    uri: Uri,
    uploadData: PresignedUploadData
) = withContext(Dispatchers.IO) {
    val imageBytes =
        context.contentResolver
            .openInputStream(uri)
            ?.use { inputStream ->
                inputStream.readBytes()
            }
            ?: throw IOException(
                "Impossibile leggere " +
                        "la fotografia selezionata."
            )

    if (imageBytes.isEmpty()) {
        throw IOException(
            "La fotografia selezionata è vuota."
        )
    }

    val mediaType =
        uploadData.contentType
            .toMediaType()

    val requestBody =
        imageBytes.toRequestBody(
            mediaType
        )

    val request =
        Request.Builder()
            .url(uploadData.uploadUrl)
            .header(
                "Content-Type",
                uploadData.contentType
            )
            .put(requestBody)
            .build()

    uploadHttpClient
        .newCall(request)
        .execute()
        .use { response ->
            if (
                !response.isSuccessful
            ) {
                val responseText =
                    response.body
                        .string()
                        .take(300)

                throw IOException(
                    "Caricamento S3 non riuscito " +
                            "(${response.code}): " +
                            responseText
                )
            }
        }
}
