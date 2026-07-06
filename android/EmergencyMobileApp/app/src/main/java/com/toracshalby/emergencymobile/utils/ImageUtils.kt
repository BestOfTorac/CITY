package com.toracshalby.emergencymobile.utils

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

import com.toracshalby.emergencymobile.model.SelectedImageInfo

fun createCameraImageUri(
    context: Context
): Uri {
    val imagesDirectory =
        File(
            context.cacheDir,
            "captured_images"
        ).apply {
            if (
                !exists() &&
                !mkdirs()
            ) {
                throw IOException(
                    "Impossibile creare la cartella temporanea."
                )
            }
        }

    val imageFile =
        File.createTempFile(
            "emergency-" +
                    System.currentTimeMillis() +
                    "-",
            ".jpg",
            imagesDirectory
        )

    return FileProvider.getUriForFile(
        context,
        "${context.packageName}.fileprovider",
        imageFile
    )
}


fun resolveSelectedImageInfo(
    context: Context,
    uri: Uri
): SelectedImageInfo {
    val contentResolver =
        context.contentResolver

    var displayName: String? = null

    contentResolver.query(
        uri,
        arrayOf(
            OpenableColumns.DISPLAY_NAME
        ),
        null,
        null,
        null
    )?.use { cursor ->
        val nameIndex =
            cursor.getColumnIndex(
                OpenableColumns.DISPLAY_NAME
            )

        if (
            nameIndex >= 0 &&
            cursor.moveToFirst()
        ) {
            displayName =
                cursor.getString(
                    nameIndex
                )
        }
    }

    val detectedContentType =
        contentResolver
            .getType(uri)
            ?.lowercase()

    val normalizedContentType =
        when (detectedContentType) {
            "image/jpeg",
            "image/jpg" -> {
                "image/jpeg"
            }

            "image/png" -> {
                "image/png"
            }

            else -> {
                val lowerName =
                    displayName
                        ?.lowercase()
                        .orEmpty()

                when {
                    lowerName.endsWith(
                        ".jpg"
                    ) -> {
                        "image/jpeg"
                    }

                    lowerName.endsWith(
                        ".jpeg"
                    ) -> {
                        "image/jpeg"
                    }

                    lowerName.endsWith(
                        ".png"
                    ) -> {
                        "image/png"
                    }

                    else -> {
                        throw IllegalArgumentException(
                            "Formato non supportato. " +
                                    "Seleziona una fotografia JPEG o PNG."
                        )
                    }
                }
            }
        }

    val defaultExtension =
        if (
            normalizedContentType ==
            "image/png"
        ) {
            ".png"
        } else {
            ".jpg"
        }

    val finalFileName =
        displayName
            ?.takeIf {
                it.isNotBlank()
            }
            ?: (
                    "emergency-" +
                            UUID.randomUUID()
                                .toString()
                                .take(8) +
                            defaultExtension
                    )

    return SelectedImageInfo(
        fileName = finalFileName,
        contentType =
            normalizedContentType
    )
}
