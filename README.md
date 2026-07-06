# CITY — Cloud-based Intelligent emergency response sYstem

CITY è un sistema distribuito serverless per la gestione intelligente di emergenze in contesto smart city.

Il sistema permette di ricevere segnalazioni manuali da app Android e test da telecamera simulata, analizzare eventuali immagini con Amazon Rekognition, classificare l'emergenza, valutarne la gravità, notificare i soccorritori, salvare i dati e mostrare all'utente lo stato dell'elaborazione in tempo reale tramite WebSocket.

---

## 1. Obiettivo del progetto

CITY nasce per simulare una piattaforma smart city capace di:

- ricevere segnalazioni di emergenza da cittadini tramite app mobile;
- ricevere eventi da telecamere IoT simulate;
- analizzare immagini associate all'evento;
- classificare automaticamente il tipo di emergenza;
- valutare gravità e priorità;
- notificare i soccorritori tramite email;
- salvare i risultati in uno stato persistente;
- aggiornare l'app in tempo reale durante il workflow.

---

## 2. Tipologia progetto

Il progetto è stato sviluppato per la traccia:

```text
A1 — Microservice application for sustainable and inclusive Smart Cities
```

L'architettura è basata su microservizi serverless AWS e usa più pattern architetturali:

- API Gateway pattern;
- event-driven architecture;
- message queue tramite Amazon SQS;
- publish/subscribe tramite AWS IoT Core;
- workflow orchestration tramite AWS Step Functions;
- shared state tramite Amazon DynamoDB;
- object storage tramite Amazon S3;
- real-time push tramite API Gateway WebSocket.

---

## 3. Architettura generale

```text
Android App
├── Segnalazione manuale
│   ├── POST /upload-url
│   ├── upload immagine su S3 mobile/
│   └── POST /emergency
│       ├── receiveEmergency
│       ├── MobileIngestion
│       ├── Rekognition
│       └── SQS
│
└── Test telecamera
    └── POST /test/camera
        ├── cameraSimulator
        ├── AWS IoT Core topic emergency/camera
        ├── CameraIngestionRule
        ├── lambdaIngestion
        ├── Rekognition
        └── SQS

SQS emergency-events-queue
└── StartWorkflow
    └── Step Functions workflowEmergency
        ├── ValidateEvent
        ├── ContextualizeEvent
        ├── ClassifyEvent
        ├── EvaluateSeverity
        ├── DecisionLogic
        └── FinalActions
            ├── SNS emergency-alerts-topic
            ├── DynamoDB EmergencyData
            └── S3 events/

WebSocket
├── WebSocketHandler
├── DynamoDB WebSocketSubscriptions
└── SendStatusUpdate
```

---

## 4. Componenti AWS

| Servizio | Uso |
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

---

## 5. Lambda principali

| Lambda | Ruolo |
|---|---|
| `receiveEmergency` | Riceve segnalazioni manuali dall'app |
| `GenerateMobileUploadUrl` | Genera presigned URL per foto mobile |
| `MobileIngestion` | Analizza foto mobile e manda evento a SQS |
| `cameraSimulator` | Sceglie immagine casuale e pubblica evento IoT |
| `lambdaIngestion` | Processa evento telecamera |
| `StartWorkflow` | Avvia Step Functions da SQS |
| `ValidateEvent` | Valida input evento |
| `ContextualizeEvent` | Costruisce contesto |
| `ClassifyEvent` | Classifica FIRE/ACCIDENT/UNKNOWN |
| `EvaluateSeverity` | Calcola gravità e priorità |
| `DecisionLogic` | Decide notifica, salvataggio e archivio |
| `StoreLogs` | Archivia immagini evento |
| `SendStatusUpdate` | Invia update WebSocket all'app |
| `WebSocketHandler` | Gestisce connessioni e subscribe WebSocket |

---

## 6. App Android

L'app Android permette di:

- inviare una segnalazione manuale;
- allegare una foto dalla camera o dalla galleria;
- avviare un test telecamera simulata;
- visualizzare l'immagine selezionata casualmente dal dataset;
- seguire lo stato dell'elaborazione in tempo reale.

File di configurazione endpoint:

```text
app/src/main/java/com/toracshalby/emergencymobile/network/ApiConstants.kt
```

Esempio:

```kotlin
package com.toracshalby.emergencymobile.network


const val WEBSOCKET_URL =
    "wss://jwzc92xi14.execute-api.us-east-1.amazonaws.com/production"

const val UPLOAD_URL_ENDPOINT =
    "https://5q4ao06b12.execute-api.us-east-1.amazonaws.com/upload-url"

const val EMERGENCY_ENDPOINT =
    "https://5q4ao06b12.execute-api.us-east-1.amazonaws.com/emergency"

const val CAMERA_TEST_ENDPOINT =
    "https://5q4ao06b12.execute-api.us-east-1.amazonaws.com/test/camera"
```

---

## 7. Deployment

Il deployment è diviso in quattro stack CloudFormation:

```text
city-storage-messaging
city-lambdas
city-api
city-workflow-iot
```

Ordine di creazione:

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

La guida completa è in:

```text
docs/deployment-guide.md
```

---

## 8. Dataset immagini

Nel bucket S3 creato da CloudFormation bisogna creare il prefix:

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

I prefix generati durante l'esecuzione sono:

```text
mobile/
captured/
events/
```

---

## 9. Test principali

### Test 1 — Segnalazione manuale senza immagine

Atteso:

```text
App Android
→ POST /emergency
→ Step Functions
→ DynamoDB EmergencyData
→ WebSocket 100%
```

### Test 2 — Segnalazione manuale con immagine

Atteso:

```text
App Android
→ POST /upload-url
→ S3 mobile/
→ POST /emergency
→ MobileIngestion
→ Rekognition
→ SQS
→ Step Functions
→ SNS / DynamoDB / S3
→ WebSocket 100%
```

### Test 3 — Telecamera simulata

Atteso:

```text
App Android
→ POST /test/camera
→ cameraSimulator
→ IoT Core
→ lambdaIngestion
→ Rekognition
→ SQS
→ Step Functions
→ SNS / DynamoDB / S3
→ WebSocket 100%
```

---

## 10. Struttura repository consigliata

```text
CITY/
├── README.md
├── android/
│   └── EmergencyMobile/
├── backend/
│   ├── lambdas/
│   └── stepfunctions/
├── infrastructure/
│   └── cloudformation/
│       ├── storage-messaging.yaml
│       ├── lambdas-update-websocket.yaml
│       ├── api-gateway.yaml
│       └── workflow-iot-fixed.yaml
├── docs/
│   ├── aws-inventory.md
│   ├── deployment-guide.md
│   ├── architecture.md
│   └── test-plan.md
├── dataset/
│   └── README.md
├── experiments/
│   └── results/
├── report/
└── slides/
```

---

## 11. Stato del progetto

Funzionalità completate:

```text
Segnalazione manuale senza immagine ✅
Segnalazione manuale con immagine ✅
Telecamera simulata ✅
WebSocket real-time ✅
SNS email ✅
DynamoDB persistence ✅
S3 archive ✅
CloudFormation deployment su nuovo account ✅
```

---

## 12. Possibili sviluppi futuri

- Supporto a più categorie di emergenza.
- Dashboard web per operatori.
- Autenticazione utenti.
- Dataset più ampio e valutazione quantitativa della classificazione.
- Integrazione con mappe reali e unità di soccorso.
- Ottimizzazione costi e cold start.
