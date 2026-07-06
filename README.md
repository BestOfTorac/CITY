# CITY - Sistema intelligente per emergenze in Smart City

CITY e' un sistema distribuito serverless per la gestione intelligente delle emergenze in ambito smart city.

Il sistema riceve segnalazioni manuali da un'app Android e test da una telecamera simulata, analizza eventuali immagini con Amazon Rekognition, classifica l'emergenza, valuta la gravita', invia notifiche, salva i dati e aggiorna l'app in tempo reale tramite WebSocket.

## Obiettivo

- Ricevere segnalazioni da cittadini tramite app mobile.
- Ricevere eventi da telecamere IoT simulate.
- Analizzare immagini associate all'evento.
- Classificare il tipo di emergenza.
- Valutare gravita' e priorita'.
- Notificare i soccorritori tramite email.
- Salvare i risultati in modo persistente.
- Mostrare lo stato del workflow in tempo reale.

## Tipologia del progetto

```text
A1 - Microservice application for sustainable and inclusive Smart Cities
```

Pattern usati:

- API Gateway pattern
- Event-driven architecture
- Message queue con Amazon SQS
- Publish/subscribe con AWS IoT Core
- Workflow orchestration con AWS Step Functions
- Object storage con Amazon S3
- Real-time push con API Gateway WebSocket
- Shared state con Amazon DynamoDB

## Architettura generale

```text
Android App
|
|-- Segnalazione manuale
|   |-- POST /upload-url
|   |-- upload immagine su S3 mobile/
|   |-- POST /emergency
|       |-- receiveEmergency
|       |-- MobileIngestion
|       |-- Amazon Rekognition
|       |-- Amazon SQS
|
|-- Test telecamera
    |-- POST /test/camera
        |-- cameraSimulator
        |-- AWS IoT Core topic emergency/camera
        |-- CameraIngestionRule
        |-- lambdaIngestion
        |-- Amazon Rekognition
        |-- Amazon SQS

SQS emergency-events-queue
|
|-- StartWorkflow
    |-- Step Functions workflowEmergency
        |-- ValidateEvent
        |-- ContextualizeEvent
        |-- ClassifyEvent
        |-- EvaluateSeverity
        |-- DecisionLogic
        |-- FinalActions
            |-- SNS emergency-alerts-topic
            |-- DynamoDB EmergencyData
            |-- S3 events/

WebSocket
|
|-- WebSocketHandler
|-- DynamoDB WebSocketSubscriptions
|-- SendStatusUpdate
|-- Android App
```

## Componenti AWS

| Servizio | Utilizzo |
|---|---|
| Amazon API Gateway HTTP | Endpoint REST per app Android |
| Amazon API Gateway WebSocket | Aggiornamenti real-time verso app |
| AWS Lambda | Microservizi serverless |
| AWS Step Functions | Orchestrazione workflow |
| Amazon SQS | Coda persistente degli eventi |
| Amazon SNS | Notifica email ai soccorritori |
| Amazon DynamoDB | Stato persistente emergenze e WebSocket |
| Amazon S3 | Dataset immagini, upload mobile, archivio eventi |
| Amazon Rekognition | Analisi immagini |
| AWS IoT Core | Simulazione ramo telecamera |
| AWS CloudFormation | Deployment riproducibile |

## Deployment

Il deployment e' diviso in quattro stack CloudFormation:

```text
city-storage-messaging
city-lambdas
city-api
city-workflow-iot
```

Ordine:

```text
1. storage-messaging.yaml
2. upload zip Lambda su S3
3. lambdas-update-websocket.yaml
4. api-gateway.yaml
5. update city-lambdas con WebSocketManagementEndpoint reale
6. workflow-iot-fixed.yaml
7. upload dataset immagini in S3 dataset/
8. aggiornamento ApiConstants.kt Android
```

Guida completa:

```text
docs/deployment-guide.md
```

## Test principali

```text
Manuale senza immagine:
Android -> /emergency -> Step Functions -> DynamoDB -> WebSocket 100%

Manuale con immagine:
Android -> /upload-url -> S3 mobile/ -> /emergency -> MobileIngestion -> Rekognition -> SQS -> Step Functions -> WebSocket 100%

Telecamera simulata:
Android -> /test/camera -> cameraSimulator -> IoT Core -> lambdaIngestion -> Rekognition -> SQS -> Step Functions -> WebSocket 100%
```

## Stato del progetto

```text
Segnalazione manuale senza immagine: completata
Segnalazione manuale con immagine: completata
Telecamera simulata: completata
WebSocket real-time: completato
SNS email: completato
DynamoDB persistence: completato
S3 archive: completato
CloudFormation deployment su nuovo account: completato
```
