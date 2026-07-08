# CITY - Architecture

Questo documento descrive l'architettura del sistema CITY dal punto di vista tecnico.

L'obiettivo e' permettere a una persona che apre il progetto per la prima volta di capire:

```text
1. quali componenti compongono il sistema;
2. quali flussi attraversano l'architettura;
3. quali servizi AWS vengono usati;
4. dove vengono salvati immagini, eventi e stati;
5. come l'app Android riceve aggiornamenti in tempo reale;
6. quali pattern distribuiti sono stati applicati.
```

Per le istruzioni di deploy consultare:

```text
docs/deployment-guide.md
```

---

## 1. Vista generale

CITY e' una applicazione serverless a microservizi per la gestione di emergenze in ambito smart city.

Il sistema ha tre parti principali:

```text
1. App Android
   Punto di ingresso usato dall'utente per inviare segnalazioni,
   allegare immagini e avviare test camera.

2. Backend serverless AWS
   Insieme di API Gateway, Lambda, SQS, IoT Core, Step Functions,
   Rekognition, DynamoDB, SNS e S3.

3. Canale WebSocket
   Usato per inviare all'app aggiornamenti real-time sullo stato
   di elaborazione dell'emergenza.
```

L'architettura gestisce due flussi di ingresso:

```text
A. Segnalazione manuale da app Android
B. Test telecamera simulata
```

Entrambi i flussi producono un evento di emergenza che viene inserito in:

```text
Amazon SQS emergency-events-queue
```

Da qui viene avviato il workflow centrale:

```text
AWS Step Functions workflowEmergency
```

---

## 2. Componenti principali

| Componente | Ruolo |
|---|---|
| Android App | Client mobile usato per inviare emergenze e ricevere stati |
| API Gateway HTTP | Espone gli endpoint REST usati dall'app |
| API Gateway WebSocket | Espone il canale real-time verso l'app |
| AWS Lambda | Implementa i microservizi applicativi |
| Amazon S3 | Salva dataset, immagini mobile, immagini camera e archivio eventi |
| Amazon Rekognition | Analizza le immagini e restituisce label utili alla classificazione |
| Amazon SQS | Disaccoppia ingestion e workflow |
| AWS IoT Core | Simula il canale telecamera tramite topic MQTT |
| AWS Step Functions | Orchestra il workflow di emergenza |
| Amazon DynamoDB | Salva emergenze e sottoscrizioni WebSocket |
| Amazon SNS | Invia notifiche email ai soccorritori |
| AWS CloudFormation | Automatizza il provisioning dell'infrastruttura |

---

## 3. API esposte all'app Android

L'app Android usa quattro endpoint principali.

### 3.1 HTTP API

Creata dallo stack:

```text
city-api
```

Nome logico:

```text
EmergencyResponseAPI
```

Route:

```text
POST /upload-url
POST /emergency
POST /test/camera
```

Significato:

| Endpoint | Uso |
|---|---|
| `POST /upload-url` | Richiede una presigned URL per caricare una foto su S3 |
| `POST /emergency` | Invia una segnalazione manuale |
| `POST /test/camera` | Avvia il test telecamera simulata |

### 3.2 WebSocket API

Nome logico:

```text
EmergencyStatusWebSocket
```

Route WebSocket:

```text
$connect
$disconnect
$default
subscribe
```

Uso:

```text
App Android -> subscribe(eventId) -> ricezione aggiornamenti real-time
```

---

## 4. Flusso 1 - Segnalazione manuale senza immagine

Questo e' il caso piu' semplice.

L'utente invia una segnalazione manuale dall'app senza allegare una foto.

```text
Android App
-> POST /emergency
-> API Gateway HTTP
-> Lambda receiveEmergency
-> Step Functions workflowEmergency
```

In questo caso il sistema non deve analizzare immagini, quindi puo' avviare direttamente il workflow.

### Passaggi

```text
1. L'app genera o riceve un eventId.
2. L'app apre il WebSocket e si sottoscrive all'eventId.
3. L'app invia la segnalazione a POST /emergency.
4. receiveEmergency valida il payload base.
5. receiveEmergency avvia workflowEmergency.
6. Step Functions elabora l'emergenza.
7. SendStatusUpdate invia gli stati all'app.
8. EmergencyData viene aggiornato su DynamoDB.
```

---

## 5. Flusso 2 - Segnalazione manuale con immagine

Quando l'utente allega una foto, il caricamento dell'immagine viene gestito con una presigned URL S3.

La foto non passa da API Gateway e non passa direttamente dalla Lambda. L'app carica la foto direttamente su S3.

### 5.1 Upload della foto

```text
Android App
-> POST /upload-url
-> API Gateway HTTP
-> Lambda GenerateMobileUploadUrl
-> ritorna presigned URL
-> Android App
-> upload diretto immagine su S3 mobile/
```

### 5.2 Invio della segnalazione

Dopo aver caricato la foto, l'app invia l'emergenza con il riferimento all'immagine.

```text
Android App
-> POST /emergency
-> API Gateway HTTP
-> Lambda receiveEmergency
-> Lambda MobileIngestion
-> Amazon Rekognition
-> Amazon SQS emergency-events-queue
-> Lambda StartWorkflow
-> Step Functions workflowEmergency
```

### 5.3 Passaggi dettagliati

```text
1. L'app chiede una presigned URL a /upload-url.
2. GenerateMobileUploadUrl restituisce un URL temporaneo.
3. L'app carica la foto direttamente su S3 nel prefix mobile/.
4. L'app invia a /emergency i dati dell'emergenza e la chiave S3 dell'immagine.
5. receiveEmergency riceve la segnalazione.
6. receiveEmergency invoca MobileIngestion.
7. MobileIngestion legge l'immagine da S3 mobile/.
8. MobileIngestion invoca Amazon Rekognition.
9. MobileIngestion costruisce un evento arricchito.
10. MobileIngestion inserisce l'evento in SQS.
11. StartWorkflow viene attivata dalla coda SQS.
12. StartWorkflow avvia workflowEmergency.
```

---

## 6. Flusso 3 - Test telecamera simulata

Il test telecamera serve a simulare un evento proveniente da una camera urbana.

L'app non usa una telecamera reale. L'app invoca un endpoint che attiva una Lambda di simulazione.

```text
Android App
-> POST /test/camera
-> API Gateway HTTP
-> Lambda cameraSimulator
-> Amazon S3 dataset/
-> AWS IoT Core topic emergency/camera
-> IoT Rule CameraIngestionRule
-> Lambda lambdaIngestion
-> Amazon Rekognition
-> Amazon SQS emergency-events-queue
-> Lambda StartWorkflow
-> Step Functions workflowEmergency
```

### Passaggi dettagliati

```text
1. L'utente preme "Avvia test telecamera" nell'app.
2. L'app chiama POST /test/camera.
3. cameraSimulator seleziona una immagine casuale da S3 dataset/.
4. cameraSimulator restituisce all'app una preview temporanea dell'immagine.
5. cameraSimulator pubblica un evento su AWS IoT Core.
6. Il topic usato e' emergency/camera.
7. CameraIngestionRule intercetta il messaggio IoT.
8. CameraIngestionRule invoca lambdaIngestion.
9. lambdaIngestion salva o usa l'immagine nel prefix captured/.
10. lambdaIngestion invoca Rekognition.
11. lambdaIngestion inserisce l'evento in SQS.
12. StartWorkflow avvia workflowEmergency.
```

---

## 7. Punto di convergenza: Amazon SQS

I flussi con immagine e telecamera convergono su:

```text
Amazon SQS emergency-events-queue
```

Questo significa che il workflow non dipende direttamente dal modo in cui l'emergenza e' stata generata.

```text
MobileIngestion -------------|
                             |-> SQS emergency-events-queue -> StartWorkflow
lambdaIngestion -------------|
```

Vantaggi:

```text
1. disaccoppiamento tra ingestion e workflow;
2. maggiore tolleranza ai picchi di richieste;
3. possibilita' di ritentare l'elaborazione;
4. pipeline piu' robusta in caso di errori temporanei.
```

---

## 8. Avvio del workflow

La Lambda:

```text
StartWorkflow
```

e' collegata alla coda SQS tramite trigger.

Quando arriva un messaggio in:

```text
emergency-events-queue
```

AWS invoca:

```text
StartWorkflow
```

che avvia:

```text
workflowEmergency
```

---

## 9. Workflow Step Functions

La state machine principale e':

```text
workflowEmergency
```

Sequenza logica:

```text
ValidateEvent
-> SendValidatedStatus
-> ContextualizeEvent
-> SendContextualizedStatus
-> ClassifyEvent
-> SendClassifiedStatus
-> EvaluateSeverity
-> SendSeverityStatus
-> DecisionLogic
-> SendDecisionStatus
-> FinalActions
-> SendCompletedStatus
-> Completed
```

### 9.1 ValidateEvent

Controlla che l'evento abbia una struttura valida.

Verifica, ad esempio:

```text
eventId
source
timestamp
location
event details
```

Se l'evento non e' valido, il workflow termina nel ramo:

```text
InvalidEmergency
```

### 9.2 ContextualizeEvent

Arricchisce l'evento con informazioni utili al processo decisionale.

Esempi:

```text
origine evento: mobile o camera
presenza immagine
dati estratti dalla segnalazione
label ottenute da Rekognition
```

### 9.3 ClassifyEvent

Classifica il tipo di emergenza.

Esempi di categorie:

```text
FIRE
ACCIDENT
UNKNOWN
```

### 9.4 EvaluateSeverity

Valuta la gravita' dell'evento.

Produce valori utili alla decisione finale, come:

```text
severityLevel
severityScore
priority
```

### 9.5 DecisionLogic

Decide quali azioni eseguire.

Esempi:

```text
shouldNotify
shouldArchiveImage
priority
numero risorse suggerite
record finale da salvare
messaggio di notifica
```

### 9.6 FinalActions

Le azioni finali vengono eseguite in parallelo.

```text
FinalActions
|-- ramo 1: NotifyResponders via SNS
|-- ramo 2: SaveEmergencyData su DynamoDB
|-- ramo 3: StoreLogs su S3 events/
```

---

## 10. Azioni finali

### 10.1 Notifica soccorritori

Se:

```text
shouldNotify = true
```

il workflow pubblica un messaggio su:

```text
SNS emergency-alerts-topic
```

La mail arriva agli indirizzi che hanno confermato la subscription SNS.

### 10.2 Salvataggio dati

Il workflow salva il record finale in:

```text
DynamoDB EmergencyData
```

Chiave principale:

```text
eventId
```

La tabella contiene informazioni come:

```text
source
location
eventType
severityLevel
priority
classificationConfidence
notificationRequired
processingStatus
eventDetailsJson
```

### 10.3 Archiviazione immagini e log

Se:

```text
shouldArchiveImage = true
```

il workflow invoca:

```text
StoreLogs
```

che archivia dati e immagini in:

```text
S3 events/
```

Se l'archiviazione fallisce, viene inviato uno stato:

```text
IMAGE_ARCHIVE_FAILED
```

---

## 11. Real-time status con WebSocket

L'app Android mostra l'avanzamento dell'emergenza grazie al canale WebSocket.

### 11.1 Sottoscrizione dell'app

```text
Android App
-> API Gateway WebSocket
-> WebSocketHandler
-> DynamoDB WebSocketSubscriptions
```

L'app invia un messaggio di subscribe con:

```text
eventId
```

La Lambda `WebSocketHandler` salva la relazione tra:

```text
connectionId
eventId
```

nella tabella:

```text
WebSocketSubscriptions
```

### 11.2 Invio degli aggiornamenti

Durante il workflow, vari step invocano:

```text
SendStatusUpdate
```

Il flusso e':

```text
Step Functions
-> SendStatusUpdate
-> DynamoDB WebSocketSubscriptions
-> API Gateway Management API
-> Android App
```

### 11.3 Stati principali

Esempi di stati inviati all'app:

```text
IMAGE_ANALYZED
VALIDATED
CONTEXTUALIZED
CLASSIFIED
SEVERITY_EVALUATED
DECISION_MADE
RESPONDERS_NOTIFIED
COMPLETED
INVALID_EMERGENCY
PROCESSING_FAILED
IMAGE_ARCHIVE_FAILED
```

---

## 12. Storage S3

Il bucket S3 principale e' usato con piu' prefix logici.

```text
dataset/
mobile/
captured/
events/
deployment/lambdas/
```

Significato:

| Prefix | Uso |
|---|---|
| `dataset/` | immagini usate dal cameraSimulator |
| `mobile/` | immagini caricate dall'app Android |
| `captured/` | immagini prodotte o elaborate dal ramo telecamera |
| `events/` | archivio finale di immagini e log |
| `deployment/lambdas/` | zip Lambda usati da CloudFormation |

---

## 13. DynamoDB

Il sistema usa due tabelle principali.

### 13.1 EmergencyData

Contiene il record finale dell'emergenza.

Chiave:

```text
eventId
```

Uso:

```text
salvataggio classificazione
salvataggio severita'
salvataggio decisione
salvataggio stato finale
```

### 13.2 WebSocketSubscriptions

Contiene le connessioni WebSocket attive.

Campi principali:

```text
connectionId
eventId
expiresAt
```

Indice:

```text
eventId-index
```

Uso:

```text
trovare quali connessioni devono ricevere aggiornamenti per un certo eventId
```

---

## 14. Lambda del sistema

| Lambda | Ruolo |
|---|---|
| receiveEmergency | Riceve segnalazioni manuali |
| GenerateMobileUploadUrl | Genera presigned URL per upload foto |
| MobileIngestion | Elabora segnalazione mobile con immagine |
| cameraSimulator | Simula evento camera |
| lambdaIngestion | Elabora evento proveniente da IoT |
| StartWorkflow | Avvia Step Functions da SQS |
| ValidateEvent | Valida l'evento |
| ContextualizeEvent | Arricchisce il contesto |
| ClassifyEvent | Classifica il tipo di emergenza |
| EvaluateSeverity | Calcola la gravita' |
| DecisionLogic | Decide le azioni finali |
| StoreLogs | Archivia immagini e log |
| SendStatusUpdate | Invia stati real-time all'app |
| WebSocketHandler | Gestisce connessione e subscribe WebSocket |

---

## 15. Pattern architetturali usati

### 15.1 API Gateway pattern

L'app non invoca direttamente le Lambda. Tutte le richieste passano da API Gateway.

```text
Android App -> API Gateway -> Lambda
```

### 15.2 Event-driven architecture

Il sistema reagisce a eventi:

```text
HTTP request
S3 upload
IoT message
SQS message
Step Functions state transition
WebSocket message
```

### 15.3 Message queue

Amazon SQS separa ingestion e workflow.

```text
Ingestion Lambda -> SQS -> StartWorkflow
```

### 15.4 Publish/subscribe

Il ramo telecamera usa AWS IoT Core.

```text
cameraSimulator -> topic emergency/camera -> IoT Rule -> lambdaIngestion
```

### 15.5 Workflow orchestration

La logica di business principale e' coordinata da Step Functions.

```text
Validate -> Contextualize -> Classify -> Evaluate -> Decide -> Final actions
```

### 15.6 Shared state

DynamoDB viene usato come stato condiviso.

```text
EmergencyData
WebSocketSubscriptions
```

### 15.7 Real-time push

Il WebSocket permette al backend di inviare aggiornamenti all'app senza polling.

```text
SendStatusUpdate -> WebSocket Management API -> Android App
```

---

## 16. Scalabilita', elasticita' e fault tolerance

### 16.1 Scalabilita'

Il sistema usa servizi gestiti e serverless:

```text
Lambda
API Gateway
SQS
DynamoDB
Step Functions
SNS
S3
```

Questi servizi possono scalare senza dover gestire manualmente server o macchine virtuali.

### 16.2 Elasticita'

Le Lambda vengono eseguite solo quando necessario. La coda SQS assorbe picchi di eventi e permette al sistema di processarli in modo asincrono.

### 16.3 Fault tolerance

Elementi principali:

```text
SQS disaccoppia ingestion e workflow
Step Functions gestisce retry e catch
DynamoDB conserva lo stato
S3 conserva immagini e log
WebSocket non blocca il workflow
FinalActions esegue rami paralleli
```

Se un aggiornamento WebSocket fallisce, il workflow puo' continuare. Se l'archiviazione immagine fallisce, il sistema puo' inviare uno stato specifico senza nascondere il problema.

---

## 17. Riassunto flussi

### Manuale senza immagine

```text
App
-> /emergency
-> receiveEmergency
-> workflowEmergency
-> DynamoDB/SNS/S3
-> WebSocket status
```

### Manuale con immagine

```text
App
-> /upload-url
-> GenerateMobileUploadUrl
-> S3 mobile/
-> /emergency
-> receiveEmergency
-> MobileIngestion
-> Rekognition
-> SQS
-> StartWorkflow
-> workflowEmergency
```

### Camera simulata

```text
App
-> /test/camera
-> cameraSimulator
-> IoT Core
-> CameraIngestionRule
-> lambdaIngestion
-> Rekognition
-> SQS
-> StartWorkflow
-> workflowEmergency
```

### Stato real-time

```text
App
-> WebSocket subscribe(eventId)
-> WebSocketHandler
-> WebSocketSubscriptions

workflowEmergency
-> SendStatusUpdate
-> WebSocket Management API
-> App
```
