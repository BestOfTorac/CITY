# CITY - AWS Inventory

Documento riassuntivo delle risorse AWS usate dal progetto CITY.

## Account e regione

```text
Region = us-east-1
AccountId = ACCOUNT_ID_DA_SOSTITUIRE
Role = LabRole
```

## API Gateway HTTP

```text
API name = EmergencyResponseAPI
API ID = OUTPUT_HTTP_API_ID
Base endpoint = OUTPUT_HTTP_API_BASE_ENDPOINT
```

Routes:

```text
POST /emergency
POST /upload-url
POST /test/camera
```

## API Gateway WebSocket

```text
API name = EmergencyStatusWebSocket
API ID = OUTPUT_WEBSOCKET_API_ID
Endpoint = OUTPUT_WEBSOCKET_ENDPOINT
Management endpoint = OUTPUT_WEBSOCKET_MANAGEMENT_ENDPOINT
Stage = production
```

Routes:

```text
$connect
$disconnect
$default
subscribe
```

## S3

```text
Bucket = OUTPUT_EMERGENCY_IMAGES_BUCKET_NAME
```

Prefixes:

```text
dataset/
mobile/
captured/
events/
deployment/lambdas/
```

## DynamoDB

```text
EmergencyData
WebSocketSubscriptions
```

## SQS

```text
Queue = emergency-events-queue
```

## SNS

```text
Topic = emergency-alerts-topic
```

## IoT Core

```text
Topic = emergency/camera
Rule = CameraIngestionRule
```

## Step Functions

```text
State machine = workflowEmergency
```

## Lambda functions

```text
receiveEmergency
GenerateMobileUploadUrl
MobileIngestion
cameraSimulator
lambdaIngestion
StartWorkflow
ValidateEvent
ContextualizeEvent
ClassifyEvent
EvaluateSeverity
DecisionLogic
StoreLogs
SendStatusUpdate
WebSocketHandler
```

## Notes

This public inventory intentionally uses placeholders instead of real API identifiers and endpoints.
