# CITY â€” Cloud-based Intelligent emergency response sYstem

CITY Ã¨ un sistema distribuito serverless per la gestione intelligente di emergenze in contesto smart city.

Il sistema permette di ricevere segnalazioni manuali da app Android e test da telecamera simulata, analizzare eventuali immagini con Amazon Rekognition, classificare l'emergenza, valutarne la gravitÃ , notificare i soccorritori, salvare i dati e mostrare all'utente lo stato dell'elaborazione in tempo reale tramite WebSocket.

---

## 1. Obiettivo del progetto

CITY nasce per simulare una piattaforma smart city capace di:

- ricevere segnalazioni di emergenza da cittadini tramite app mobile;
- ricevere eventi da telecamere IoT simulate;
- analizzare immagini associate all'evento;
- classificare automaticamente il tipo di emergenza;
- valutare gravitÃ  e prioritÃ ;
- notificare i soccorritori tramite email;
- salvare i risultati in uno stato persistente;
- aggiornare l'app in tempo reale durante il workflow.

---

## 2. Tipologia progetto

Il progetto Ã¨ stato sviluppato per la traccia:

```text
A1 â€” Microservice application for sustainable and inclusive Smart Cities
```

L'architettura Ã¨ basata su microservizi serverless AWS e usa piÃ¹ pattern architetturali:

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
â”œâ”€â”€ Segnalazione manuale
â”‚   â”œâ”€â”€ POST /upload-url
â”‚   â”œâ”€â”€ upload immagine su S3 mobile/
â”‚   â””â”€â”€ POST /emergency
â”‚       â”œâ”€â”€ receiveEmergency
â”‚       â”œâ”€â”€ MobileIngestion
â”‚       â”œâ”€â”€ Rekognition
â”‚       â””â”€â”€ SQS
â”‚
â””â”€â”€ Test telecamera
    â””â”€â”€ POST /test/camera
        â”œâ”€â”€ cameraSimulator
        â”œâ”€â”€ AWS IoT Core topic emergency/camera
        â”œâ”€â”€ CameraIngestionRule
        â”œâ”€â”€ lambdaIngestion
        â”œâ”€â”€ Rekognition
        â””â”€â”€ SQS

SQS emergency-events-queue
â””â”€â”€ StartWorkflow
    â””â”€â”€ Step Functions workflowEmergency
        â”œâ”€â”€ ValidateEvent
        â”œâ”€â”€ ContextualizeEvent
        â”œâ”€â”€ ClassifyEvent
        â”œâ”€â”€ EvaluateSeverity
        â”œâ”€â”€ DecisionLogic
        â””â”€â”€ FinalActions
            â”œâ”€â”€ SNS emergency-alerts-topic
            â”œâ”€â”€ DynamoDB EmergencyData
            â””â”€â”€ S3 events/

WebSocket
â”œâ”€â”€ WebSocketHandler
â”œâ”€â”€ DynamoDB WebSocketSubscriptions
â””â”€â”€ SendStatusUpdate
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
| `EvaluateSeverity` | Calcola gravitÃ  e prioritÃ  |
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
    "INSERISCI_OUTPUT_WEBSOCKET_ENDPOINT"

const val UPLOAD_URL_ENDPOINT =
    "INSERISCI_OUTPUT_UPLOAD_URL_ENDPOINT"

const val EMERGENCY_ENDPOINT =
    "INSERISCI_OUTPUT_EMERGENCY_ENDPOINT"

const val CAMERA_TEST_ENDPOINT =
    "INSERISCI_OUTPUT_CAMERA_TEST_ENDPOINT"
```

---

## 7. Deployment

Il deployment Ã¨ diviso in quattro stack CloudFormation:

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

La guida completa Ã¨ in:

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

### Test 1 â€” Segnalazione manuale senza immagine

Atteso:

```text
App Android
â†’ POST /emergency
â†’ Step Functions
â†’ DynamoDB EmergencyData
â†’ WebSocket 100%
```

### Test 2 â€” Segnalazione manuale con immagine

Atteso:

```text
App Android
â†’ POST /upload-url
â†’ S3 mobile/
â†’ POST /emergency
â†’ MobileIngestion
â†’ Rekognition
â†’ SQS
â†’ Step Functions
â†’ SNS / DynamoDB / S3
â†’ WebSocket 100%
```

### Test 3 â€” Telecamera simulata

Atteso:

```text
App Android
â†’ POST /test/camera
â†’ cameraSimulator
â†’ IoT Core
â†’ lambdaIngestion
â†’ Rekognition
â†’ SQS
â†’ Step Functions
â†’ SNS / DynamoDB / S3
â†’ WebSocket 100%
```

---

## 10. Struttura repository consigliata

```text
CITY/
â”œâ”€â”€ README.md
â”œâ”€â”€ android/
â”‚   â””â”€â”€ EmergencyMobile/
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ lambdas/
â”‚   â””â”€â”€ stepfunctions/
â”œâ”€â”€ infrastructure/
â”‚   â””â”€â”€ cloudformation/
â”‚       â”œâ”€â”€ storage-messaging.yaml
â”‚       â”œâ”€â”€ lambdas-update-websocket.yaml
â”‚       â”œâ”€â”€ api-gateway.yaml
â”‚       â””â”€â”€ workflow-iot-fixed.yaml
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ aws-inventory.md
â”‚   â”œâ”€â”€ deployment-guide.md
â”‚   â”œâ”€â”€ architecture.md
â”‚   â””â”€â”€ test-plan.md
â”œâ”€â”€ dataset/
â”‚   â””â”€â”€ README.md
â”œâ”€â”€ experiments/
â”‚   â””â”€â”€ results/
â”œâ”€â”€ report/
â””â”€â”€ slides/
```

---

## 11. Stato del progetto

FunzionalitÃ  completate:

```text
Segnalazione manuale senza immagine âœ…
Segnalazione manuale con immagine âœ…
Telecamera simulata âœ…
WebSocket real-time âœ…
SNS email âœ…
DynamoDB persistence âœ…
S3 archive âœ…
CloudFormation deployment su nuovo account âœ…
```

---

## 12. Possibili sviluppi futuri

- Supporto a piÃ¹ categorie di emergenza.
- Dashboard web per operatori.
- Autenticazione utenti.
- Dataset piÃ¹ ampio e valutazione quantitativa della classificazione.
- Integrazione con mappe reali e unitÃ  di soccorso.
- Ottimizzazione costi e cold start.
