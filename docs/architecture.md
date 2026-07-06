# CITY — Architecture

## Overview

CITY è una piattaforma serverless a microservizi per la gestione intelligente delle emergenze in una smart city.

## Main flows

### Manual report flow

```text
Android app
→ API Gateway HTTP
→ receiveEmergency
→ MobileIngestion, se è presente una foto
→ Rekognition
→ SQS
→ StartWorkflow
→ Step Functions
```

### Camera test flow

```text
Android app
→ API Gateway HTTP /test/camera
→ cameraSimulator
→ AWS IoT Core topic emergency/camera
→ CameraIngestionRule
→ lambdaIngestion
→ Rekognition
→ SQS
→ StartWorkflow
→ Step Functions
```

### Real-time status flow

```text
Android app
→ WebSocket subscribe(eventId)
→ WebSocketHandler
→ DynamoDB WebSocketSubscriptions
→ SendStatusUpdate
→ API Gateway Management API
→ Android app
```

## Microservice patterns

- API Gateway pattern
- Event-driven architecture
- Publish/subscribe
- Message queue
- Workflow orchestration
- Shared state
- Object storage
- Real-time push

## Fault tolerance

- SQS decouples ingestion from workflow execution.
- Step Functions uses Retry and Catch.
- WebSocket updates are non-blocking.
- Final actions run in parallel.
- Image archive failures are handled explicitly.
