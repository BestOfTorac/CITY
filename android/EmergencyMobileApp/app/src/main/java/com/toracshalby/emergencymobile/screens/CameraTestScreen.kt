package com.toracshalby.emergencymobile.screens

import androidx.compose.foundation.BorderStroke
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
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.toracshalby.emergencymobile.ui.theme.AppCameraSoft
import com.toracshalby.emergencymobile.ui.theme.AppMutedText
import com.toracshalby.emergencymobile.ui.theme.AppPurple
import com.toracshalby.emergencymobile.ui.theme.AppPurpleDark
import com.toracshalby.emergencymobile.ui.theme.AppPurpleSoft
import com.toracshalby.emergencymobile.ui.theme.AppPurpleUltraSoft
import com.toracshalby.emergencymobile.ui.theme.AppSurface
import com.toracshalby.emergencymobile.ui.theme.AppText

@Composable
fun CameraTestScreen(
    onBackToHome: () -> Unit,
    onStartTest: () -> Unit
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

        Row(
            verticalAlignment =
                Alignment.CenterVertically,
            horizontalArrangement =
                Arrangement.spacedBy(14.dp)
        ) {
            Surface(
                modifier =
                    Modifier.size(62.dp),
                shape =
                    RoundedCornerShape(20.dp),
                color = AppCameraSoft
            ) {
                Box(
                    contentAlignment =
                        Alignment.Center
                ) {
                    Text(
                        text = "◉",
                        style =
                            MaterialTheme.typography
                                .headlineMedium,
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
                        "Test telecamera simulata",
                    style =
                        MaterialTheme.typography
                            .headlineSmall,
                    fontWeight =
                        FontWeight.Bold,
                    color = AppText
                )

                Text(
                    text =
                        "Verifica il percorso automatico end-to-end.",
                    color = AppMutedText
                )
            }
        }

        Card(
            modifier =
                Modifier.fillMaxWidth(),
            shape =
                RoundedCornerShape(24.dp),
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
                    Modifier.padding(20.dp),
                verticalArrangement =
                    Arrangement.spacedBy(14.dp)
            ) {
                Text(
                    text = "Cosa verrà testato",
                    style =
                        MaterialTheme.typography
                            .titleMedium,
                    color = AppPurpleDark,
                    fontWeight =
                        FontWeight.SemiBold
                )

                CameraFlowStep(
                    number = "1",
                    label =
                        "Apertura del canale WebSocket e generazione dell'eventId"
                )

                CameraFlowStep(
                    number = "2",
                    label =
                        "Scelta casuale di un'immagine dal dataset S3"
                )

                CameraFlowStep(
                    number = "3",
                    label =
                        "Pubblicazione dell'evento su AWS IoT Core"
                )

                CameraFlowStep(
                    number = "4",
                    label =
                        "Analisi Rekognition, SQS e avvio Step Functions"
                )

                CameraFlowStep(
                    number = "5",
                    label =
                        "Aggiornamenti in tempo reale fino al completamento"
                )
            }
        }

        Card(
            modifier =
                Modifier.fillMaxWidth(),
            shape =
                RoundedCornerShape(18.dp),
            colors =
                CardDefaults.cardColors(
                    containerColor =
                        AppPurpleUltraSoft
                ),
            border =
                BorderStroke(
                    1.dp,
                    AppPurple.copy(
                        alpha = 0.25f
                    )
                )
        ) {
            Text(
                text =
                    "Il test usa una telecamera simulata: " +
                            "non apre la fotocamera del telefono. " +
                            "AWS selezionerà un'immagine dal dataset " +
                            "e la elaborerà come una cattura automatica.",
                modifier =
                    Modifier.padding(16.dp),
                color = AppPurpleDark
            )
        }

        Button(
            onClick = onStartTest,
            modifier = Modifier
                .fillMaxWidth()
                .height(58.dp),
            shape =
                RoundedCornerShape(18.dp),
            colors =
                ButtonDefaults.buttonColors(
                    containerColor =
                        AppPurple
                )
        ) {
            Text(
                text =
                    "Avvia test telecamera",
                style =
                    MaterialTheme.typography
                        .titleMedium,
                fontWeight =
                    FontWeight.SemiBold
            )
        }
    }
}

@Composable
private fun CameraFlowStep(
    number: String,
    label: String
) {
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
                Modifier.size(34.dp),
            shape = CircleShape,
            color = AppPurpleSoft
        ) {
            Box(
                contentAlignment =
                    Alignment.Center
            ) {
                Text(
                    text = number,
                    color = AppPurpleDark,
                    fontWeight =
                        FontWeight.Bold
                )
            }
        }

        Text(
            text = label,
            modifier =
                Modifier.weight(1f),
            color = AppText
        )
    }
}
