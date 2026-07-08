# CITY - Sistema intelligente per emergenze in Smart City

CITY è un sistema cloud-native, serverless e event-driven pensato per rendere più intelligente la gestione delle emergenze in una Smart City.

L'idea nasce da una domanda semplice: cosa succederebbe se una città fosse in grado di raccogliere segnalazioni da cittadini, sensori e telecamere, comprenderle rapidamente, valutarne la gravità e aggiornare l'utente in tempo reale sullo stato dell'intervento?

CITY prova a rispondere a questa domanda con un prototipo completo basato su AWS. Il sistema riceve segnalazioni da un'app Android, gestisce immagini caricate dagli utenti, simula eventi provenienti da una telecamera urbana, analizza il contenuto visivo con Amazon Rekognition, classifica l'emergenza, valuta la priorità, salva i dati e invia notifiche quando necessario.

Il progetto è pensato a scopo didattico e prototipale, ma riflette un problema reale: coordinare informazioni eterogenee durante situazioni di emergenza.

---

## 1. Visione del progetto

In una città moderna, le emergenze non arrivano tutte dallo stesso canale. Un cittadino può segnalare un incidente tramite smartphone, una telecamera può rilevare una scena anomala, un sensore può generare un evento automatico e un operatore può avere bisogno di dati chiari per capire cosa sta succedendo.

CITY immagina una piattaforma capace di raccogliere questi segnali, portarli dentro un unico flusso di elaborazione e trasformarli in informazioni più utili. Non si limita a ricevere una richiesta: la arricchisce, la analizza, la classifica, decide quali azioni eseguire e mantiene aggiornato l'utente durante l'intero processo.

Il valore del progetto non è solo tecnico. L'obiettivo è mostrare come il cloud possa essere usato per costruire servizi più reattivi, trasparenti e vicini alle persone. Una Smart City non è intelligente perché usa tanti servizi digitali, ma perché riesce a usare quei servizi per migliorare la vita dei cittadini, ridurre i tempi di risposta e rendere più chiara la gestione degli eventi critici.

---

## 2. Cosa fa CITY

CITY gestisce tre scenari principali.

### Segnalazione manuale senza immagine

L'utente invia una segnalazione dall'app Android. Il backend riceve l'evento, avvia il workflow di elaborazione, salva il risultato e aggiorna l'app in tempo reale.

```text
Android App
-> POST /emergency
-> receiveEmergency
-> workflowEmergency
-> DynamoDB
-> WebSocket status updates
```

### Segnalazione manuale con immagine

L'utente allega una foto alla segnalazione. L'app richiede una presigned URL, carica l'immagine direttamente su Amazon S3 e invia al backend il riferimento dell'immagine. Il backend analizza il contenuto tramite Amazon Rekognition e inserisce l'evento nel workflow.

```text
Android App
-> POST /upload-url
-> upload immagine su S3 mobile/
-> POST /emergency
-> MobileIngestion
-> Amazon Rekognition
-> Amazon SQS
-> workflowEmergency
```

### Test telecamera simulata

L'app può avviare un test che simula una telecamera urbana. Il backend seleziona una immagine dal dataset S3, pubblica un evento su AWS IoT Core e avvia lo stesso processo usato per le emergenze reali.

```text
Android App
-> POST /test/camera
-> cameraSimulator
-> S3 dataset/
-> AWS IoT Core
-> lambdaIngestion
-> Amazon Rekognition
-> Amazon SQS
-> workflowEmergency
```

---

## 3. Architettura generale

CITY utilizza una architettura serverless composta da microservizi AWS. L'app Android comunica con il backend tramite API Gateway, mentre la parte di elaborazione è affidata a Lambda, SQS, Step Functions, Rekognition, DynamoDB, S3, SNS e IoT Core.

Il sistema è progettato per separare il punto di ingresso dell'evento dalla sua elaborazione. In questo modo una segnalazione manuale, una segnalazione con immagine o un evento proveniente dalla telecamera simulata possono convergere su una pipeline comune.

```text
Android App
|
|-- HTTP API Gateway
|   |-- /upload-url
|   |-- /emergency
|   |-- /test/camera
|
|-- WebSocket API Gateway
    |-- aggiornamenti real-time

Backend AWS
|
|-- Lambda microservices
|-- Amazon S3
|-- Amazon Rekognition
|-- Amazon SQS
|-- AWS IoT Core
|-- AWS Step Functions
|-- Amazon DynamoDB
|-- Amazon SNS
```

Il cuore applicativo è la state machine:

```text
workflowEmergency
```

che orchestra il processo:

```text
ValidateEvent
-> ContextualizeEvent
-> ClassifyEvent
-> EvaluateSeverity
-> DecisionLogic
-> FinalActions
```

La descrizione tecnica completa dell'architettura si trova in:

```text
docs/architecture.md
```

---

## 4. Servizi AWS utilizzati

| Servizio | Ruolo nel progetto |
|---|---|
| Amazon API Gateway HTTP | Espone gli endpoint REST usati dall'app Android |
| Amazon API Gateway WebSocket | Gestisce gli aggiornamenti real-time verso l'app |
| AWS Lambda | Implementa i microservizi serverless |
| AWS Step Functions | Orchestra il workflow di emergenza |
| Amazon SQS | Disaccoppia ingestion e workflow |
| Amazon SNS | Invia notifiche email quando necessario |
| Amazon DynamoDB | Salva emergenze e sottoscrizioni WebSocket |
| Amazon S3 | Salva dataset, immagini mobile, immagini camera, log e zip Lambda |
| Amazon Rekognition | Analizza le immagini associate agli eventi |
| AWS IoT Core | Simula il ramo telecamera tramite topic MQTT |
| Amazon CloudWatch | Fornisce log e supporto al debug |
| AWS CloudFormation | Automatizza il deploy dell'infrastruttura |

---

## 5. Pattern architetturali

CITY applica pattern tipici dei sistemi distribuiti moderni.

| Pattern | Applicazione in CITY |
|---|---|
| API Gateway pattern | L'app comunica con il backend tramite API Gateway |
| Event-driven architecture | Il sistema reagisce a eventi HTTP, IoT, SQS e workflow |
| Message queue | Amazon SQS separa ingestion e workflow |
| Publish/subscribe | AWS IoT Core gestisce il ramo telecamera |
| Workflow orchestration | AWS Step Functions coordina la logica applicativa |
| Object storage | Amazon S3 gestisce immagini, dataset e archivi |
| Shared state | DynamoDB conserva emergenze e connessioni WebSocket |
| Real-time push | WebSocket invia stati all'app senza polling |
| Infrastructure as Code | CloudFormation permette deploy riproducibili |

---

## 6. Struttura della repository

La repository è organizzata per rendere chiara la separazione tra documentazione, infrastruttura cloud, backend serverless, app mobile e dataset.

```text
CITY/
|-- README.md
|-- docs/
|   |-- architecture.md
|   |-- deployment-guide.md
|   |-- test-plan.md
|
|-- infrastructure/
|   |-- cloudformation/
|       |-- storage-messaging.yaml
|       |-- lambdas-update-websocket.yaml
|       |-- api-gateway.yaml
|       |-- workflow-iot-fixed.yaml
|
|-- backend/
|   |-- lambda-zips/
|       |-- receiveEmergency.zip
|       |-- GenerateMobileUploadUrl.zip
|       |-- MobileIngestion.zip
|       |-- cameraSimulator.zip
|       |-- lambdaIngestion.zip
|       |-- StartWorkflow.zip
|       |-- ValidateEvent.zip
|       |-- ContextualizeEvent.zip
|       |-- ClassifyEvent.zip
|       |-- EvaluateSeverity.zip
|       |-- DecisionLogic.zip
|       |-- StoreLogs.zip
|       |-- SendStatusUpdate.zip
|       |-- WebSocketHandler.zip
|
|-- android/
|   |-- README.md
|   |-- EmergencyMobileApp/
|
|-- dataset/
|   |-- sample images
|
|-- report/
|   |-- project report files
```

### docs/

Contiene la documentazione principale. `architecture.md` spiega come è progettato il sistema, `deployment-guide.md` descrive come tirarlo su su un nuovo account AWS e `test-plan.md` definisce i test funzionali da eseguire.

### infrastructure/

Contiene i template CloudFormation necessari per creare l'infrastruttura AWS. I template sono separati per rendere il deploy più ordinato e più facile da controllare.

### backend/

Contiene i pacchetti `.zip` delle Lambda già pronti per essere caricati su S3 e usati da CloudFormation durante il deploy.

### android/

Contiene l'app mobile Android e un README dedicato per chi vuole aprire, configurare ed eseguire il client.

### dataset/

Contiene immagini di esempio utilizzate dal test della telecamera simulata. Durante il deploy queste immagini devono essere caricate nel bucket S3 nel prefix `dataset/`.

---

## 7. Deployment

Il deploy è riproducibile tramite CloudFormation. L'infrastruttura viene creata attraverso quattro stack principali:

```text
city-storage-messaging
city-lambdas
city-api
city-workflow-iot
```

Il processo crea prima storage, code, topic e tabelle, poi carica i pacchetti Lambda, espone le API, aggiorna la configurazione WebSocket e infine crea il workflow Step Functions con la regola IoT.

La guida completa è disponibile in:

```text
docs/deployment-guide.md
```

---

## 8. Test e validazione

CITY è stato pensato per essere verificabile end-to-end. I test principali controllano che i tre flussi fondamentali funzionino correttamente: segnalazione manuale senza immagine, segnalazione manuale con immagine e test telecamera simulata.

Durante la validazione vengono controllati il completamento della Step Function, la creazione dei record su DynamoDB, la presenza delle immagini su S3, l'invio delle notifiche SNS, la ricezione degli aggiornamenti WebSocket e l'assenza di errori critici nei log CloudWatch.

Il piano completo dei test è disponibile in:

```text
docs/test-plan.md
```

---

## 9. Stato del progetto

Le funzionalità principali risultano implementate e testate.

```text
Segnalazione manuale senza immagine: completata
Segnalazione manuale con immagine: completata
Test telecamera simulata: completato
Analisi immagini con Rekognition: completata
Workflow Step Functions: completato
WebSocket real-time status: completato
Persistenza DynamoDB: completata
Notifica SNS: completata
Archiviazione S3: completata
Deploy CloudFormation su nuovo account: completato
```

---

## 10. Sicurezza e repository pubblica

La repository non deve contenere credenziali AWS, token, chiavi private o file generati localmente dall'ambiente di sviluppo.

Prima di ogni push è consigliato verificare l'assenza di access key, secret key, session token, endpoint reali non destinati alla pubblicazione, file `local.properties`, file `.env`, keystore Android, cartelle `build/` e cartelle `.gradle/`.

Comandi utili:

```powershell
git grep -n "AKIA"
git grep -n "aws_secret_access_key"
git grep -n "aws_session_token"
git grep -n "execute-api"
git grep -n "wss://"
```

Gli endpoint reali possono essere usati localmente per test e demo, ma devono essere gestiti con attenzione prima di pubblicare modifiche.

---

## 11. Limiti del progetto

CITY è un prototipo e non un sistema certificato per la gestione reale delle emergenze. La telecamera è simulata tramite dataset S3, la classificazione dipende dalle label restituite da Rekognition e la decision logic è costruita per dimostrare il comportamento del sistema.

Questi limiti sono parte della natura prototipale del progetto. Il valore principale di CITY è mostrare come costruire una pipeline distribuita, scalabile e riproducibile capace di integrare app mobile, eventi IoT, analisi immagini, code, workflow, notifiche e aggiornamenti real-time.

---

## 12. Possibili sviluppi futuri

Un'evoluzione naturale di CITY sarebbe l'integrazione con sorgenti reali, come telecamere urbane, sensori ambientali o sistemi di monitoraggio già presenti in una città. Questo permetterebbe al sistema di passare da una simulazione controllata a un contesto più vicino alla realtà operativa.

Un altro sviluppo importante riguarda la sicurezza e la gestione degli utenti. L'introduzione di autenticazione, ruoli, autorizzazioni e policy più granulari renderebbe il sistema più adatto a scenari complessi, dove cittadini, operatori e amministratori hanno responsabilità diverse.

CITY potrebbe inoltre essere esteso con una dashboard web per operatori, una mappa degli eventi, notifiche multi-canale, metriche CloudWatch più avanzate e modelli di classificazione più sofisticati. In questa direzione, il progetto potrebbe diventare una base per sperimentare sistemi urbani più consapevoli, reattivi e orientati al supporto delle persone.

---

## 13. Autori

Progetto sviluppato da:

```text
Valerio Torac
Ali Shalby
```

Corso di riferimento:

```text
Sistemi Distribuiti e Cloud Computing
Tor Vergata Università Degli Studi di Roma
```

---