# CITY - Architecture

## Overview

CITY e' una piattaforma serverless a microservizi per la gestione intelligente delle emergenze in una smart city.

Il sistema ha due flussi principali:

1. segnalazione manuale da app Android;
2. test telecamera simulata tramite AWS IoT Core.

Entrambi i flussi convergono su Amazon SQS e poi su AWS Step Functions.

## Manual report flow

```text
Android App
|
|-- POST /upload-url
|   |-- GenerateMobileUploadUrl
|   |-- S3 presigned URL
|
|-- upload immagine su S3 mobile/
|
|-- POST /emergency
    |-- receiveEmergency
    |-- MobileIngestion
    |-- Amazon Rekognition
    |-- Amazon SQS
    |-- StartWorkflow
    |-- Step Functions workflowEmergency
```

## Camera test flow

```text
Android App
|
|-- POST /test/camera
    |-- cameraSimulator
    |-- selezione immagine casuale da S3 dataset/
    |-- pubblicazione su AWS IoT Core topic emergency/camera
    |-- CameraIngestionRule
    |-- lambdaIngestion
    |-- Amazon Rekognition
    |-- Amazon SQS
    |-- StartWorkflow
    |-- Step Functions workflowEmergency
```

## Workflow Step Functions

```text
ValidateEvent
|
|-- ContextualizeEvent
|
|-- ClassifyEvent
|
|-- EvaluateSeverity
|
|-- DecisionLogic
|
|-- FinalActions
    |-- NotifyResponders via SNS
    |-- SaveEmergencyData via DynamoDB
    |-- StoreLogs via S3
```

## WebSocket status flow

```text
Android App
|
|-- WebSocket subscribe(eventId)
|
|-- WebSocketHandler
|
|-- DynamoDB WebSocketSubscriptions
|
|-- SendStatusUpdate
|
|-- API Gateway Management API
|
|-- Android App
```

## Microservice patterns

- API Gateway pattern
- Event-driven architecture
- Message queue
- Publish/subscribe
- Workflow orchestration
- Shared state
- Object storage
- Real-time push

## Fault tolerance

- SQS decouples ingestion from workflow execution.
- Step Functions manages retry and catch logic.
- WebSocket updates are non-blocking.
- Final actions run in parallel.
- Image archive failures are handled explicitly.
