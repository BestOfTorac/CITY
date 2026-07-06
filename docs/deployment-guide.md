# CITY â€” Deployment Guide

Guida operativa per distribuire CITY su un nuovo account AWS Learner Lab usando CloudFormation.

## Stack creati e verificati

Nel test su nuovo account risultano funzionanti:

```text
city-storage-messaging âœ…
city-lambdas âœ…
city-api âœ…
city-workflow-iot âœ…
```

## 1. Prerequisiti

- Regione consigliata: `us-east-1`.
- Ruolo IAM Learner Lab esistente: `LabRole`.
- File CloudFormation:
  - `storage-messaging.yaml`
  - `lambdas-update-websocket.yaml`
  - `api-gateway.yaml`
  - `workflow-iot-fixed.yaml`
- ZIP Lambda caricati in S3 sotto `deployment/lambdas/`.

## 2. Stack 1 â€” Storage e messaging

Template:

```text
storage-messaging.yaml
```

Stack name:

```text
city-storage-messaging
```

Risorse create:

```text
S3 bucket
DynamoDB EmergencyData
DynamoDB WebSocketSubscriptions
SQS emergency-events-queue
SNS emergency-alerts-topic
```

Nel test il bucket creato Ã¨:

```text
city-dev-emergency-images-285809320909-us-east-1
```

## 3. ZIP Lambda su S3

Nel bucket creato, caricare gli zip in:

```text
deployment/lambdas/
```

File attesi:

```text
receiveEmergency.zip
GenerateMobileUploadUrl.zip
MobileIngestion.zip
cameraSimulator.zip
lambdaIngestion.zip
StartWorkflow.zip
ValidateEvent.zip
ContextualizeEvent.zip
ClassifyEvent.zip
EvaluateSeverity.zip
DecisionLogic.zip
StoreLogs.zip
SendStatusUpdate.zip
WebSocketHandler.zip
```

## 4. Recupero IoT endpoint

Da CloudShell:

```bash
aws iot describe-endpoint --endpoint-type iot:Data-ATS --query endpointAddress --output text
```

Nel test:

```text
avk5ip4giaq6u-ats.iot.us-east-1.amazonaws.com
```

Usare solo il dominio, senza `https://`.

## 5. Stack 2 â€” Lambda

Template:

```text
lambdas-update-websocket.yaml
```

Stack name:

```text
city-lambdas
```

Parametri principali:

```text
StorageMessagingStackName = city-storage-messaging
LambdaCodeBucketName = city-dev-emergency-images-285809320909-us-east-1
LambdaCodePrefix = deployment/lambdas/
IotDataEndpoint = avk5ip4giaq6u-ats.iot.us-east-1.amazonaws.com
LabRoleName = LabRole
WorkflowStateMachineName = workflowEmergency
```

Al primo deploy, `WebSocketManagementEndpoint` puÃ² restare temporaneamente placeholder.

## 6. Stack 3 â€” API Gateway

Template:

```text
api-gateway.yaml
```

Stack name:

```text
city-api
```

Output generati nel test:

```text
EmergencyEndpoint = INSERISCI_OUTPUT_EMERGENCY_ENDPOINT
UploadUrlEndpoint = INSERISCI_OUTPUT_UPLOAD_URL_ENDPOINT
CameraTestEndpoint = INSERISCI_OUTPUT_CAMERA_TEST_ENDPOINT
WebSocketEndpoint = INSERISCI_OUTPUT_WEBSOCKET_ENDPOINT
WebSocketManagementEndpoint = INSERISCI_OUTPUT_WEBSOCKET_MANAGEMENT_ENDPOINT
```

## 7. Update Lambda con WebSocket reale

Aggiornare lo stack `city-lambdas` con lo stesso template:

```text
lambdas-update-websocket.yaml
```

Parametro da aggiornare:

```text
WebSocketManagementEndpoint = INSERISCI_OUTPUT_WEBSOCKET_MANAGEMENT_ENDPOINT
```

Risultato atteso:

```text
UPDATE_COMPLETE
```

## 8. Stack 4 â€” Workflow e IoT

Template:

```text
workflow-iot-fixed.yaml
```

Stack name:

```text
city-workflow-iot
```

Parametri principali:

```text
StorageMessagingStackName = city-storage-messaging
LambdaStackName = city-lambdas
LabRoleName = LabRole
WorkflowStateMachineName = workflowEmergency
CameraIngestionRuleName = CameraIngestionRule
CameraIotTopic = emergency/camera
```

Risorse create:

```text
AWS IoT Rule CameraIngestionRule
Step Functions workflowEmergency
```

## 9. Configurazione Android

Aggiornare:

```text
network/ApiConstants.kt
```

Con:

```kotlin
package com.toracshalby.emergencymobile.network


const val WEBSOCKET_URL =
    "INSERISCI_OUTPUT_WEBSOCKET_ENDPOINT"

const val UPLOAD_URL_ENDPOINT =
    "INSERISCI_OUTPUT_UPLOAD_URL_ENDPOINT"

const val EMERGENCY_ENDPOINT =
    "INSERISCI_OUTPUT_EMERGENCY_ENDPOINT"

const val CAMERA_TEST_ENDPOINT =
    "INSERISCI_OUTPUT_CAMERA_TEST_ENDPOINT"
```

## 10. Dataset S3

Nel bucket:

```text
city-dev-emergency-images-285809320909-us-east-1
```

creare manualmente la cartella/prefix:

```text
dataset/
```

e caricare immagini `.jpg`, `.jpeg` o `.png`.

Esempio:

```text
dataset/fire_01.jpg
dataset/accident_01.jpg
dataset/normal_01.jpg
```

I prefix `mobile/`, `captured/` ed `events/` vengono creati automaticamente quando le Lambda scrivono oggetti.

## 11. Conferma SNS

Dopo la creazione dello stack storage/messaging, confermare la mail SNS cliccando:

```text
Confirm subscription
```

FinchÃ© la subscription non Ã¨ confermata, SNS non invia email.

## 12. Test end-to-end

### Segnalazione manuale senza immagine

Atteso:

```text
Android app â†’ /emergency
â†’ Step Functions
â†’ DynamoDB EmergencyData
â†’ WebSocket 100%
```

### Segnalazione manuale con immagine

Atteso:

```text
Android app â†’ /upload-url
â†’ upload S3 mobile/
â†’ /emergency
â†’ MobileIngestion
â†’ Rekognition
â†’ SQS
â†’ Step Functions
â†’ S3 events/
â†’ DynamoDB
â†’ eventuale SNS
â†’ WebSocket 100%
```

### Telecamera simulata

Atteso:

```text
Android app â†’ /test/camera
â†’ cameraSimulator
â†’ IoT topic emergency/camera
â†’ CameraIngestionRule
â†’ lambdaIngestion
â†’ Rekognition
â†’ SQS
â†’ Step Functions
â†’ S3 captured/ + events/
â†’ DynamoDB
â†’ eventuale SNS
â†’ WebSocket 100%
```

## 13. Conclusione

Il deployment CloudFormation Ã¨ stato verificato su un nuovo account AWS. Il sistema Ã¨ riproducibile tramite stack modulari e richiede solo:
- caricamento degli zip Lambda su S3;
- caricamento del dataset immagini in `dataset/`;
- aggiornamento degli endpoint Android dagli output CloudFormation;
- conferma delle subscription SNS.
