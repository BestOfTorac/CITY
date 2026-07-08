# CITY - Test Plan

Questo documento descrive i test da eseguire per verificare il corretto funzionamento del sistema CITY dopo il deployment su AWS.

Il test plan non descrive l'architettura e non spiega come effettuare il deploy. Per questi aspetti consultare:

```text
docs/architecture.md
docs/deployment-guide.md
```

L'obiettivo di questo file e' definire:

```text
1. quali funzionalita' testare;
2. in quale ordine eseguire i test;
3. qual e' il risultato atteso;
4. quali servizi AWS controllare;
5. quali evidenze raccogliere per report e demo.
```

---

## 1. Prerequisiti prima dei test

Prima di eseguire i test verificare che il deployment sia completato.

### 1.1 Stack CloudFormation

Tutti gli stack devono essere in stato corretto:

```text
city-storage-messaging = CREATE_COMPLETE
city-lambdas = CREATE_COMPLETE oppure UPDATE_COMPLETE
city-api = CREATE_COMPLETE
city-workflow-iot = CREATE_COMPLETE
```

### 1.2 Configurazione Android

Il file:

```text
ApiConstants.kt
```

deve contenere gli output reali dello stack `city-api`:

```text
WebSocketEndpoint
UploadUrlEndpoint
EmergencyEndpoint
CameraTestEndpoint
```

### 1.3 Dataset S3

Nel bucket S3 principale deve esistere il prefix:

```text
dataset/
```

e deve contenere almeno alcune immagini `.jpg`, `.jpeg` o `.png`.

### 1.4 SNS

La subscription SNS deve essere confermata tramite email.

Senza conferma, il sistema puo' funzionare ma non arriveranno notifiche email.

---

## 2. Servizi AWS da controllare durante i test

Durante o dopo ogni test e' utile controllare:

| Servizio | Cosa verificare |
|---|---|
| Android App | Stato mostrato all'utente e completamento del flusso |
| API Gateway | Endpoint raggiungibili |
| Lambda | Log CloudWatch senza errori critici |
| S3 | Presenza immagini in `mobile/`, `captured/`, `events/` |
| SQS | Messaggi consumati correttamente |
| Step Functions | Execution terminata con successo |
| DynamoDB | Nuovo record in `EmergencyData` |
| SNS | Email inviata quando prevista |
| WebSocket | Aggiornamenti real-time ricevuti dall'app |

---

## 3. Test funzionali principali

| ID | Test | Obiettivo | Risultato atteso |
|---|---|---|---|
| T1 | Manuale senza immagine | Verificare il flusso base `/emergency` | Workflow completato, record DynamoDB creato, app aggiornata |
| T2 | Manuale con immagine | Verificare upload S3, Rekognition e workflow | Foto in `mobile/`, Rekognition eseguito, workflow completato |
| T3 | Telecamera simulata | Verificare flusso IoT e camera ingestion | Immagine da `dataset/`, evento IoT, `lambdaIngestion`, workflow completato |
| T4 | Notifica SNS | Verificare invio email per emergenze rilevanti | Email ricevuta dal subscriber confermato |
| T5 | WebSocket real-time | Verificare aggiornamenti di stato all'app | App riceve stati fino a `COMPLETED` |
| T6 | Persistenza DynamoDB | Verificare salvataggio record finale | Nuovo item in `EmergencyData` |
| T7 | Archiviazione S3 | Verificare salvataggio log/immagine finale | Oggetti generati in `events/` quando previsto |
| T8 | Input non valido | Verificare gestione errori | Workflow termina con stato di errore controllato |
| T9 | WebSocket disconnesso | Verificare che il backend continui senza client | Workflow completato anche se l'app si disconnette |

---

## 4. Sequenza consigliata dei test

Eseguire i test in questo ordine:

```text
1. Test manuale senza immagine
2. Test manuale con immagine
3. Test telecamera simulata
4. Verifica notifica SNS
5. Verifica WebSocket real-time
6. Verifica persistenza DynamoDB
7. Verifica archiviazione S3
8. Test input non valido
9. Test disconnessione WebSocket
```

I primi tre test sono i piu' importanti per la demo.

---

## 5. Test T1 - Segnalazione manuale senza immagine

### Obiettivo

Verificare che il sistema possa gestire una segnalazione manuale senza foto.

### Procedura

1. Aprire l'app Android.
2. Avviare una nuova segnalazione manuale.
3. Non allegare immagini.
4. Inviare la segnalazione.
5. Attendere il completamento sull'app.

### Flusso atteso

```text
Android App
-> POST /emergency
-> receiveEmergency
-> workflowEmergency
-> DynamoDB EmergencyData
-> WebSocket status updates
```

### Risultato atteso sull'app

L'app deve ricevere aggiornamenti fino al completamento.

Esempi di stati:

```text
VALIDATED
CONTEXTUALIZED
CLASSIFIED
SEVERITY_EVALUATED
DECISION_MADE
COMPLETED
```

### Controlli AWS

| Servizio | Controllo |
|---|---|
| Step Functions | Execution `Succeeded` |
| DynamoDB | Nuovo record in `EmergencyData` |
| CloudWatch | Nessun errore critico in `receiveEmergency` |
| WebSocket | App aggiornata fino al completamento |

### Esito

```text
[ ] Passed
[ ] Failed
```

---

## 6. Test T2 - Segnalazione manuale con immagine

### Obiettivo

Verificare il flusso completo con upload immagine, analisi Rekognition, SQS e workflow.

### Procedura

1. Aprire l'app Android.
2. Avviare una segnalazione manuale.
3. Allegare una foto.
4. Inviare la segnalazione.
5. Attendere il completamento sull'app.

### Flusso atteso

```text
Android App
-> POST /upload-url
-> GenerateMobileUploadUrl
-> upload foto su S3 mobile/
-> POST /emergency
-> receiveEmergency
-> MobileIngestion
-> Rekognition
-> SQS emergency-events-queue
-> StartWorkflow
-> workflowEmergency
```

### Controlli AWS

| Servizio | Controllo |
|---|---|
| S3 | Foto presente in `mobile/` |
| Lambda | `MobileIngestion` eseguita senza errori |
| Rekognition | Label rilevate nei log |
| SQS | Messaggio consumato da `StartWorkflow` |
| Step Functions | Execution `Succeeded` |
| DynamoDB | Nuovo record in `EmergencyData` |
| S3 | Oggetto in `events/`, se archiviazione prevista |
| WebSocket | App aggiornata fino a `COMPLETED` |

### Esito

```text
[ ] Passed
[ ] Failed
```

---

## 7. Test T3 - Telecamera simulata

### Obiettivo

Verificare il ramo telecamera basato su `cameraSimulator`, AWS IoT Core e `lambdaIngestion`.

### Procedura

1. Verificare che `dataset/` contenga immagini.
2. Aprire l'app Android.
3. Premere `Avvia test telecamera`.
4. Attendere il completamento sull'app.

### Flusso atteso

```text
Android App
-> POST /test/camera
-> cameraSimulator
-> S3 dataset/
-> AWS IoT Core topic emergency/camera
-> CameraIngestionRule
-> lambdaIngestion
-> Rekognition
-> SQS emergency-events-queue
-> StartWorkflow
-> workflowEmergency
```

### Controlli AWS

| Servizio | Controllo |
|---|---|
| S3 | `dataset/` contiene immagini |
| Lambda | `cameraSimulator` seleziona una immagine |
| IoT Core | `CameraIngestionRule` attiva |
| Lambda | `lambdaIngestion` invocata |
| S3 | Oggetto presente in `captured/` |
| Rekognition | Label rilevate nei log |
| SQS | Messaggio consumato |
| Step Functions | Execution `Succeeded` |
| DynamoDB | Nuovo record in `EmergencyData` |
| WebSocket | App aggiornata fino a `COMPLETED` |

### Esito

```text
[ ] Passed
[ ] Failed
```

---

## 8. Test T4 - Notifica SNS

### Obiettivo

Verificare che il sistema invii una email quando la logica decisionale richiede la notifica.

### Prerequisito

La subscription SNS deve essere confermata.

### Procedura

1. Eseguire un test che generi una emergenza rilevante.
2. Attendere il completamento del workflow.
3. Controllare la casella email configurata in `NotificationEmail1`.

### Controlli AWS

| Servizio | Controllo |
|---|---|
| SNS | Subscription in stato `Confirmed` |
| Step Functions | Ramo `NotifyResponders` eseguito |
| Email | Messaggio ricevuto |

### Esito

```text
[ ] Passed
[ ] Failed
[ ] Not applicable
```

---

## 9. Test T5 - WebSocket real-time

### Obiettivo

Verificare che l'app riceva gli aggiornamenti real-time durante il workflow.

### Procedura

1. Aprire l'app Android.
2. Avviare un test manuale o camera.
3. Osservare gli stati mostrati nell'app.
4. Verificare che il completamento arrivi senza refresh manuale.

### Stati attesi

```text
IMAGE_ANALYZED
VALIDATED
CONTEXTUALIZED
CLASSIFIED
SEVERITY_EVALUATED
DECISION_MADE
RESPONDERS_NOTIFIED
COMPLETED
```

Non tutti gli stati sono obbligatori in ogni flusso. Per esempio `IMAGE_ANALYZED` e' previsto solo quando viene elaborata una immagine.

### Controlli AWS

| Servizio | Controllo |
|---|---|
| API Gateway WebSocket | Connessione aperta |
| DynamoDB | Record in `WebSocketSubscriptions` |
| Lambda | `SendStatusUpdate` invocata |
| App | Stato aggiornato fino al completamento |

### Esito

```text
[ ] Passed
[ ] Failed
```

---

## 10. Test T6 - Persistenza DynamoDB

### Obiettivo

Verificare che il sistema salvi correttamente i dati finali dell'emergenza.

### Procedura

1. Eseguire uno dei flussi principali.
2. Aprire DynamoDB.
3. Controllare la tabella `EmergencyData`.

### Campi da verificare

```text
eventId
timestamp
source
location
eventType
severityLevel
processingStatus
classificationConfidence
severityScore
priority
notificationRequired
eventDetailsJson
```

### Esito

```text
[ ] Passed
[ ] Failed
```

---

## 11. Test T7 - Archiviazione S3

### Obiettivo

Verificare che immagini e log vengano archiviati quando previsto dalla decision logic.

### Procedura

1. Eseguire un test con immagine.
2. Aprire il bucket S3 principale.
3. Controllare i prefix:

```text
mobile/
captured/
events/
```

### Risultati attesi

| Prefix | Quando si popola |
|---|---|
| `mobile/` | Test manuale con immagine |
| `captured/` | Test telecamera simulata |
| `events/` | Quando `StoreLogs` archivia un evento |

### Esito

```text
[ ] Passed
[ ] Failed
[ ] Not applicable
```

---

## 12. Test T8 - Input non valido

### Obiettivo

Verificare che il sistema gestisca un evento non valido senza fallimenti incontrollati.

### Procedura possibile

Inviare una richiesta incompleta a `/emergency`, ad esempio senza campi obbligatori.

### Risultato atteso

```text
workflow termina nel ramo InvalidEmergency
oppure la Lambda restituisce errore gestito
nessun crash non controllato
nessun dato sporco salvato in DynamoDB
```

### Controlli AWS

| Servizio | Controllo |
|---|---|
| Lambda | Errore gestito nei log |
| Step Functions | Stato `InvalidEmergency`, se il workflow parte |
| DynamoDB | Nessun record finale non valido |
| App | Messaggio di errore comprensibile |

### Esito

```text
[ ] Passed
[ ] Failed
```

---

## 13. Test T9 - WebSocket disconnesso

### Obiettivo

Verificare che il workflow backend continui anche se il client mobile si disconnette.

### Procedura

1. Avviare una segnalazione dall'app.
2. Chiudere l'app o interrompere la connessione prima del completamento.
3. Controllare il backend su AWS.

### Risultato atteso

```text
workflowEmergency continua
DynamoDB viene aggiornato
eventuali notifiche SNS vengono inviate
l'assenza del client WebSocket non blocca il workflow
```

### Controlli AWS

| Servizio | Controllo |
|---|---|
| Step Functions | Execution `Succeeded` |
| DynamoDB | Record creato |
| CloudWatch | Eventuali errori WebSocket gestiti |
| SendStatusUpdate | Non blocca il workflow |

### Esito

```text
[ ] Passed
[ ] Failed
```

---

## 14. Metriche da raccogliere

Durante i test, raccogliere alcune metriche utili per relazione e demo.

| Metrica | Come misurarla |
|---|---|
| Tempo risposta API | Differenza tra invio richiesta e risposta endpoint |
| Tempo al primo stato WebSocket | Tempo tra invio segnalazione e primo update |
| Tempo al 100% | Tempo tra invio segnalazione e `COMPLETED` |
| Durata Step Functions | Campo duration nella execution |
| Durata Rekognition | Stimabile dai log Lambda |
| Numero record DynamoDB | Conteggio record creati dopo i test |
| Numero immagini archiviate | Oggetti creati in `events/` |
| Stato SNS | Email ricevuta oppure non prevista |

### Tabella risultati da compilare

| Test | Tempo completamento | Step Functions | DynamoDB | S3 | SNS | WebSocket | Esito |
|---|---:|---|---|---|---|---|---|
| T1 | `...` | `...` | `...` | `...` | `N/A` | `...` | `...` |
| T2 | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| T3 | `...` | `...` | `...` | `...` | `...` | `...` | `...` |

---

## 15. Evidenze consigliate per report e presentazione

Durante i test salvare screenshot di:

```text
1. App Android con workflow completato
2. Step Functions execution succeeded
3. DynamoDB EmergencyData con record creato
4. S3 mobile/ con immagine caricata
5. S3 captured/ o events/ dopo test camera o archiviazione
6. SNS email ricevuta
7. CloudWatch Logs senza errori critici
```

Queste evidenze sono utili per dimostrare che il sistema funziona realmente end-to-end.

---

## 16. Criteri di accettazione

Il sistema puo' essere considerato funzionante se sono soddisfatte queste condizioni:

```text
[ ] T1 superato
[ ] T2 superato
[ ] T3 superato
[ ] DynamoDB aggiornato correttamente
[ ] Step Functions completa le execution principali
[ ] App riceve aggiornamenti real-time
[ ] S3 contiene immagini nei prefix previsti
[ ] SNS funziona quando la notifica e' prevista
[ ] Non ci sono errori critici ricorrenti in CloudWatch
```

I test T1, T2 e T3 sono obbligatori per validare i flussi principali del progetto.
