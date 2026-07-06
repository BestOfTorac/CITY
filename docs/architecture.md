# CITY â€” Architecture

## Overview

CITY Ã¨ una piattaforma serverless a microservizi per la gestione intelligente delle emergenze in una smart city.

## Main flows

### Manual report flow

```text
Android app
â†’ API Gateway HTTP
â†’ receiveEmergency
â†’ MobileIngestion, se Ã¨ presente una foto
â†’ Rekognition
â†’ SQS
â†’ StartWorkflow
â†’ Step Functions
```

### Camera test flow

```text
Android app
â†’ API Gateway HTTP /test/camera
â†’ cameraSimulator
â†’ AWS IoT Core topic emergency/camera
â†’ CameraIngestionRule
â†’ lambdaIngestion
â†’ Rekognition
â†’ SQS
â†’ StartWorkflow
â†’ Step Functions
```

### Real-time status flow

```text
Android app
â†’ WebSocket subscribe(eventId)
â†’ WebSocketHandler
â†’ DynamoDB WebSocketSubscriptions
â†’ SendStatusUpdate
â†’ API Gateway Management API
â†’ Android app
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
