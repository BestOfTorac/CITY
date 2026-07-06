# CITY â€” AWS Inventory

Documento di inventario delle risorse AWS attualmente usate da CITY e di come verranno rappresentate nel deployment finale CloudFormation.

Contesto: progetto A1 â€” Microservice application for sustainable and inclusive Smart Cities. Architettura giÃ  approvata dalla prof.

---

## 1. Android configuration

File attuale:

`app/src/main/java/com/toracshalby/emergencymobile/network/ApiConstants.kt`

```kotlin
const val WEBSOCKET_URL =
    "INSERISCI_VECCHIO_WEBSOCKET_ENDPOINT"

const val UPLOAD_URL_ENDPOINT =
    "INSERISCI_VECCHIO_UPLOAD_URL_ENDPOINT"

const val EMERGENCY_ENDPOINT =
    "INSERISCI_VECCHIO_EMERGENCY_ENDPOINT"

const val CAMERA_TEST_ENDPOINT =
    "INSERISCI_VECCHIO_CAMERA_TEST_ENDPOINT"
```

CloudFormation dovrÃ  esporre questi output:

| Android constant | CloudFormation output |
|---|---|
| `WEBSOCKET_URL` | `WebSocketEndpoint` |
| `UPLOAD_URL_ENDPOINT` | `UploadUrlEndpoint` |
| `EMERGENCY_ENDPOINT` | `EmergencyEndpoint` |
| `CAMERA_TEST_ENDPOINT` | `CameraTestEndpoint` |

---

## 2. Lambda functions

| Lambda | Runtime | Trigger | Ruolo |
|---|---:|---|---|
| `receiveEmergency` | Python 3.14 | HTTP API `POST /emergency` | Riceve segnalazioni manuali dall'app |
| `GenerateMobileUploadUrl` | Python 3.14 | HTTP API `POST /upload-url` | Genera presigned URL per upload foto |
| `MobileIngestion` | Python 3.14 | Invocata da `receiveEmergency` | Analizza foto mobile e manda evento a SQS |
| `cameraSimulator` | Python 3.14 | HTTP API `POST /test/camera` | Sceglie immagine random e pubblica evento IoT |
| `lambdaIngestion` | Python 3.14 | IoT Rule `CameraIngestionRule` | Gestisce ramo telecamera e manda evento a SQS |
| `StartWorkflow` | Python 3.14 | SQS `emergency-events-queue` | Avvia Step Functions |
| `ValidateEvent` | Python 3.14 | Step Functions | Valida evento |
| `ContextualizeEvent` | Python 3.14 | Step Functions | Costruisce contesto |
| `ClassifyEvent` | Python 3.14 | Step Functions | Classifica emergenza |
| `EvaluateSeverity` | Python 3.14 | Step Functions | Calcola gravitÃ  e prioritÃ  |
| `DecisionLogic` | Python 3.14 | Step Functions | Decide notifica, salvataggio e archivio |
| `StoreLogs` | Python 3.14 | Step Functions | Archivia immagine su S3 |
| `SendStatusUpdate` | Python 3.14 | Step Functions / ingestion Lambda | Invia aggiornamenti WebSocket |
| `WebSocketHandler` | Python 3.14 | WebSocket API | Gestisce connect/disconnect/subscribe |

Da verificare come legacy:
- `saveEmergency`
- `validateEmergency`

---

## 3. Lambda environment variables

### `receiveEmergency`

| Key | Current value | CloudFormation |
|---|---|---|
| `MOBILE_INGESTION_FUNCTION_NAME` | `MobileIngestion` | `!Ref MobileIngestionFunction` |
| `STATE_MACHINE_ARN` | `arn:aws:states:us-east-1:620333538289:stateMachine:workflowEmergency` | `!Ref WorkflowEmergencyStateMachine` |

### `GenerateMobileUploadUrl`

| Key | Current value | CloudFormation |
|---|---|---|
| `BUCKET` | `emergency-images-camera` | `!Ref EmergencyImagesBucket` |
| `PREFIX` | `mobile` | `!Ref MobileUploadPrefix` |
| `URL_EXPIRATION_SECONDS` | `300` | `!Ref UploadUrlExpirationSeconds` |

### `MobileIngestion`

| Key | Current value | CloudFormation |
|---|---|---|
| `ALLOWED_BUCKET` | `emergency-images-camera` | `!Ref EmergencyImagesBucket` |
| `ALLOWED_PREFIX` | `mobile/` | `!Ref MobileUploadPrefixWithSlash` |
| `MAX_LABELS` | `10` | `!Ref RekognitionMaxLabels` |
| `MIN_CONFIDENCE` | `70` | `!Ref RekognitionMinConfidence` |
| `QUEUE_URL` | `https://sqs.us-east-1.amazonaws.com/620333538289/emergency-events-queue` | `!Ref EmergencyEventsQueue` |

### `cameraSimulator`

| Key | Current value | CloudFormation |
|---|---|---|
| `BUCKET` | `emergency-images-camera` | `!Ref EmergencyImagesBucket` |
| `DATASET_PREFIX` | `dataset/` | `!Ref DatasetPrefix` |
| `IOT_ENDPOINT` | `a1uln154sezhzs-ats.iot.us-east-1.amazonaws.com` | `!Ref IotDataEndpoint` |
| `PRESIGNED_URL_EXPIRATION` | `900` | `!Ref CameraPreviewUrlExpirationSeconds` |
| `TOPIC` | `emergency/camera` | `!Ref CameraIotTopic` |

### `lambdaIngestion`

Attualmente non ha env var in console, ma il codice usa default interni. Nel CloudFormation finale dovrÃ  avere:

| Key | CloudFormation |
|---|---|
| `DESTINATION_BUCKET` | `!Ref EmergencyImagesBucket` |
| `CAPTURED_PREFIX` | `!Ref CapturedPrefix` |
| `QUEUE_URL` | `!Ref EmergencyEventsQueue` |
| `STATUS_UPDATE_FUNCTION` | `!Ref SendStatusUpdateFunction` |
| `STATUS_UPDATE_MAX_ATTEMPTS` | `!Ref StatusUpdateMaxAttempts` |
| `STATUS_UPDATE_RETRY_DELAY_SECONDS` | `!Ref StatusUpdateRetryDelaySeconds` |

### `StartWorkflow`

| Key | Current value | CloudFormation |
|---|---|---|
| `DEFAULT_BUCKET` | `emergency-images-camera` | `!Ref EmergencyImagesBucket` |
| `STATE_MACHINE_ARN` | `arn:aws:states:us-east-1:620333538289:stateMachine:workflowEmergency` | `!Ref WorkflowEmergencyStateMachine` |

### `SendStatusUpdate`

| Key | Current value | CloudFormation |
|---|---|---|
| `EVENT_ID_INDEX` | `eventId-index` | `eventId-index` |
| `TABLE_NAME` | `WebSocketSubscriptions` | `!Ref WebSocketSubscriptionsTable` |
| `WEBSOCKET_ENDPOINT` | `INSERISCI_VECCHIO_WEBSOCKET_MANAGEMENT_ENDPOINT` | `!Sub "https://${EmergencyStatusWebSocketApi}.execute-api.${AWS::Region}.amazonaws.com/${WebSocketStageName}"` |

### `WebSocketHandler`

| Key | Current value | CloudFormation |
|---|---|---|
| `SUBSCRIPTION_TTL_SECONDS` | `7200` | `!Ref WebSocketSubscriptionTtlSeconds` |
| `TABLE_NAME` | `WebSocketSubscriptions` | `!Ref WebSocketSubscriptionsTable` |

---

## 4. DynamoDB

### `EmergencyData`

| Property | Value |
|---|---|
| Partition key | `eventId` String |
| Sort key | none |
| Indexes | 0 |
| TTL | disabled |
| Capacity mode | on-demand |
| Usage | stato persistente delle emergenze |

### `WebSocketSubscriptions`

| Property | Value |
|---|---|
| Partition key | `connectionId` String |
| Sort key | none |
| GSI | `eventId-index` on `eventId` |
| TTL | enabled |
| TTL attribute | `expiresAt` |
| Capacity mode | on-demand |
| Usage | sottoscrizioni WebSocket attive |

---

## 5. SQS

| Property | Value |
|---|---|
| Queue name | `emergency-events-queue` |
| Type | Standard |
| ARN | `arn:aws:sqs:us-east-1:620333538289:emergency-events-queue` |
| URL | `https://sqs.us-east-1.amazonaws.com/620333538289/emergency-events-queue` |
| Retention period | 4 days |
| Visibility timeout | 30 seconds |
| Delivery delay | 0 seconds |
| Max message size | 1024 KiB |
| DLQ | none |
| Encryption | Amazon SQS managed encryption |
| Consumer | `StartWorkflow` |
| Lambda batch size | 1 |

---

## 6. S3

| Property | Value |
|---|---|
| Bucket | `emergency-images-camera` |
| Region | `us-east-1` |
| Prefix principali | `captured/`, `dataset/`, `events/`, `mobile/` |

| Prefix | Uso |
|---|---|
| `dataset/` | immagini usate dalla telecamera simulata |
| `mobile/` | foto caricate dall'app Android |
| `captured/` | copia dell'immagine scelta dalla telecamera |
| `events/` | archivio finale per evento |

---

## 7. SNS

| Property | Value |
|---|---|
| Topic name | `emergency-alerts-topic` |
| Type | Standard |
| ARN | `arn:aws:sns:us-east-1:620333538289:emergency-alerts-topic` |
| Subscriptions | 2 email confermate |
| Usage | notifica soccorritori quando `shouldNotify = true` |

Le email finali vanno gestite come parametri CloudFormation, non hard-coded.

---

## 8. Step Functions

| Property | Value |
|---|---|
| State machine name | `workflowEmergency` |
| Type | Standard |
| Status | Active |
| ARN | `arn:aws:states:us-east-1:620333538289:stateMachine:workflowEmergency` |
| IAM role | `arn:aws:iam::620333538289:role/LabRole` |
| X-Ray | disabled |

Main flow:

```text
ValidateEvent
â†’ SendValidatedStatus
â†’ ContextualizeEvent
â†’ SendContextualizedStatus
â†’ ClassifyEvent
â†’ SendClassifiedStatus
â†’ EvaluateSeverity
â†’ SendSeverityStatus
â†’ DecisionLogic
â†’ SendDecisionStatus
â†’ FinalActions
â†’ SendCompletedStatus
```

Final parallel branches:

| Branch | States |
|---|---|
| Notification | `CheckNotification â†’ NotifyResponders â†’ SendRespondersNotifiedStatus` |
| Database save | `SaveEmergencyData` |
| Image archive | `CheckImageArchive â†’ StoreLogs â†’ CheckStoreLogs` |

---

## 9. API Gateway HTTP

| Property | Value |
|---|---|
| API name | `EmergencyResponseAPI` |
| API ID | `VECCHIO_HTTP_API_ID` |
| Type | HTTP API |
| Stage | `$default` |
| Base endpoint | `VECCHIO_HTTP_API_BASE_ENDPOINT` |

| Route | Method | Lambda |
|---|---|---|
| `/emergency` | `POST` | `receiveEmergency` |
| `/upload-url` | `POST` | `GenerateMobileUploadUrl` |
| `/test/camera` | `POST` | `cameraSimulator` |

---

## 10. API Gateway WebSocket

| Property | Value |
|---|---|
| API name | `EmergencyStatusWebSocket` |
| API ID | `VECCHIO_WEBSOCKET_API_ID` |
| Type | WebSocket API |
| Stage | `production` |
| Endpoint | `INSERISCI_VECCHIO_WEBSOCKET_ENDPOINT` |
| Route selection expression | `$request.body.action` |
| Lambda | `WebSocketHandler` |

| Route | Usage |
|---|---|
| `$connect` | apertura connessione |
| `$disconnect` | chiusura connessione |
| `$default` | messaggi non riconosciuti |
| `subscribe` | iscrizione a `eventId` |

---

## 11. AWS IoT Core

| Property | Value |
|---|---|
| Rule name | `CameraIngestionRule` |
| Status | active |
| Topic | `emergency/camera` |
| Basic ingest topic | `$aws/rules/CameraIngestionRule` |
| SQL | `SELECT * FROM 'emergency/camera'` |
| SQL version | `2016-03-23` |
| Action | invoke Lambda |
| Lambda target | `lambdaIngestion` |

---

## 12. IAM

| Property | Value |
|---|---|
| Execution role | `LabRole` |
| ARN | `arn:aws:iam::620333538289:role/LabRole` |
| Used by | Lambda and Step Functions |

Per compatibilitÃ  con Learner Lab, CloudFormation riceverÃ  `LabRoleArn` come parametro.

---

## 13. CloudFormation parameters

| Parameter | Example |
|---|---|
| `ProjectName` | `city` |
| `LabRoleArn` | `arn:aws:iam::${AWS::AccountId}:role/LabRole` |
| `NotificationEmail1` | user-provided |
| `NotificationEmail2` | user-provided |
| `DatasetPrefix` | `dataset/` |
| `MobileUploadPrefix` | `mobile/` |
| `CapturedPrefix` | `captured/` |
| `ArchivePrefix` | `events/` |
| `RekognitionMaxLabels` | `10` |
| `RekognitionMinConfidence` | `70` |
| `UploadUrlExpirationSeconds` | `300` |
| `CameraPreviewUrlExpirationSeconds` | `900` |
| `CameraIotTopic` | `emergency/camera` |
| `IotDataEndpoint` | account-specific IoT endpoint |
| `WebSocketStageName` | `production` |
| `WebSocketSubscriptionTtlSeconds` | `7200` |

---

## 14. CloudFormation outputs

| Output | Usage |
|---|---|
| `HttpApiEndpoint` | base URL Android |
| `EmergencyEndpoint` | endpoint segnalazione manuale |
| `UploadUrlEndpoint` | endpoint presigned URL |
| `CameraTestEndpoint` | endpoint test telecamera |
| `WebSocketEndpoint` | URL WebSocket Android |
| `EmergencyImagesBucketName` | upload dataset/debug |
| `EmergencyEventsQueueUrl` | debug |
| `EmergencyAlertsTopicArn` | debug |
| `WorkflowEmergencyArn` | debug |

