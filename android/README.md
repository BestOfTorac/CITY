# CITY - Android Section

Questa cartella contiene il client Android del progetto CITY.

Se stai aprendo il progetto per la prima volta, questa sezione ti serve per capire:

```text
1. dove si trova l'app Android;
2. come aprirla in Android Studio;
3. quali file sono importanti;
4. come configurare gli endpoint AWS dopo il deploy;
5. quali funzionalita' dell'app testare;
6. quali file non devono essere caricati nella repository pubblica.
```

Per capire l'architettura completa del sistema consulta:

```text
../docs/architecture.md
```

Per tirare su il backend AWS consulta:

```text
../docs/deployment-guide.md
```

Per testare il sistema end-to-end consulta:

```text
../docs/test-plan.md
```

---

## 1. Cosa contiene questa cartella

Struttura prevista:

```text
android/
|-- README.md
|-- EmergencyMobileApp/
    |-- app/
    |-- gradle/
    |-- build.gradle.kts
    |-- settings.gradle.kts
    |-- gradlew
    |-- gradlew.bat
```

Il progetto Android da aprire in Android Studio e':

```text
android/EmergencyMobileApp/
```

Non aprire direttamente la cartella root della repository se vuoi lavorare solo sull'app. Apri la cartella `EmergencyMobileApp`.

---

## 2. Ruolo dell'app Android

L'app Android e' il punto di ingresso usato dall'utente.

Permette di:

```text
inviare una segnalazione manuale di emergenza
allegare una foto alla segnalazione
avviare un test di telecamera simulata
ricevere aggiornamenti real-time sullo stato dell'emergenza
```

L'app non contiene la logica cloud principale. La logica di elaborazione e' nel backend AWS.

L'app comunica con il backend tramite:

```text
API Gateway HTTP
API Gateway WebSocket
S3 presigned URL
```

---

## 3. Flussi supportati dall'app

### 3.1 Segnalazione manuale senza immagine

```text
App Android
-> POST /emergency
-> backend AWS
-> workflow Step Functions
-> aggiornamenti WebSocket
-> completamento sull'app
```

Questo flusso serve per inviare una emergenza testuale o manuale senza foto.

### 3.2 Segnalazione manuale con immagine

```text
App Android
-> POST /upload-url
-> riceve presigned URL
-> upload diretto foto su S3
-> POST /emergency
-> backend AWS
-> Rekognition
-> workflow Step Functions
-> aggiornamenti WebSocket
```

La foto non viene inviata direttamente a una Lambda. Viene caricata su S3 tramite presigned URL.

### 3.3 Test telecamera simulata

```text
App Android
-> POST /test/camera
-> backend AWS
-> immagine casuale da S3 dataset/
-> AWS IoT Core
-> workflow Step Functions
-> aggiornamenti WebSocket
```

Questo flusso serve a testare il ramo camera senza usare una telecamera reale.

---

## 4. Come aprire il progetto

1. Aprire Android Studio.
2. Selezionare `Open`.
3. Aprire la cartella:

```text
android/EmergencyMobileApp/
```

4. Attendere il Gradle Sync.
5. Collegare un dispositivo Android oppure avviare un emulatore.
6. Premere `Run`.

---

## 5. File piu' importante: ApiConstants.kt

Dopo aver completato il deploy AWS, bisogna configurare gli endpoint nell'app.

File da modificare localmente:

```text
EmergencyMobileApp/app/src/main/java/com/toracshalby/emergencymobile/network/ApiConstants.kt
```

Il file deve contenere gli output generati dallo stack CloudFormation `city-api`.

Esempio:

```kotlin
package com.toracshalby.emergencymobile.network

const val WEBSOCKET_URL =
    "OUTPUT_WEBSOCKET_ENDPOINT"

const val UPLOAD_URL_ENDPOINT =
    "OUTPUT_UPLOAD_URL_ENDPOINT"

const val EMERGENCY_ENDPOINT =
    "OUTPUT_EMERGENCY_ENDPOINT"

const val CAMERA_TEST_ENDPOINT =
    "OUTPUT_CAMERA_TEST_ENDPOINT"
```

Sostituzioni da fare:

| Costante Android | Output CloudFormation |
|---|---|
| `WEBSOCKET_URL` | `WebSocketEndpoint` |
| `UPLOAD_URL_ENDPOINT` | `UploadUrlEndpoint` |
| `EMERGENCY_ENDPOINT` | `EmergencyEndpoint` |
| `CAMERA_TEST_ENDPOINT` | `CameraTestEndpoint` |

---

## 6. Attenzione agli endpoint reali

Gli endpoint reali generati da AWS possono essere usati localmente per test e demo, ma non devono essere pubblicati se si vuole mantenere la repository pulita.

Prima del push controllare sempre che non siano presenti endpoint reali non voluti.

Comandi utili:

```powershell
git grep -n "execute-api"
git grep -n "amazonaws.com"
git grep -n "wss://"
```

Se i risultati mostrano solo placeholder, va bene.

Se mostrano endpoint reali di demo privata, sostituirli prima del push.

---

## 7. Organizzazione logica del codice

La struttura esatta puo' variare, ma l'app e' organizzata logicamente in questi blocchi.

```text
network/
model/
ui/
websocket/
utils/
```

### 7.1 network/

Contiene la comunicazione HTTP con il backend.

Responsabilita':

```text
chiamare /upload-url
chiamare /emergency
chiamare /test/camera
gestire richieste e risposte
tenere centralizzati gli endpoint
```

### 7.2 model/

Contiene le classi dati usate dall'app.

Esempi:

```text
segnalazione di emergenza
risposta upload URL
risposta test camera
aggiornamento di stato
```

### 7.3 ui/

Contiene schermate e componenti visuali.

Responsabilita':

```text
form di segnalazione
selezione immagine
pulsante test camera
barra o schermata di avanzamento
messaggi di errore o completamento
```

### 7.4 websocket/

Contiene la gestione della connessione WebSocket.

Responsabilita':

```text
aprire la connessione
inviare subscribe(eventId)
ricevere aggiornamenti di stato
gestire errori o disconnessioni
```

### 7.5 utils/

Contiene funzioni di supporto.

Esempi:

```text
gestione file immagine
conversioni URI/File
validazione input
logging locale
```

---

## 8. Aggiornamenti real-time

Quando viene avviata una segnalazione, l'app si sottoscrive all'evento tramite WebSocket usando un `eventId`.

Flusso:

```text
App Android
-> connessione WebSocket
-> subscribe(eventId)
-> backend salva connectionId + eventId
-> Step Functions invia aggiornamenti
-> app mostra lo stato
```

Esempi di stati ricevibili:

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

Non tutti gli stati compaiono in ogni flusso. Per esempio `IMAGE_ANALYZED` compare solo quando viene elaborata una immagine.

---

## 9. Cosa testare dall'app

Dopo aver configurato gli endpoint, eseguire questi test minimi:

```text
1. invio segnalazione manuale senza immagine;
2. invio segnalazione manuale con immagine;
3. avvio test telecamera simulata;
4. verifica aggiornamenti WebSocket fino a COMPLETED;
5. verifica che DynamoDB e S3 vengano aggiornati lato AWS.
```

Il piano completo dei test e' in:

```text
../docs/test-plan.md
```

---

## 10. Problemi comuni

### 10.1 L'app non comunica con il backend

Controllare:

```text
ApiConstants.kt
connessione internet
endpoint copiati correttamente
stack city-api completato
```

### 10.2 Upload immagine fallisce

Controllare:

```text
UPLOAD_URL_ENDPOINT corretto
permessi Android per selezionare immagini
presigned URL non scaduta
bucket S3 creato correttamente
```

### 10.3 Test camera non funziona

Controllare:

```text
CAMERA_TEST_ENDPOINT corretto
dataset/ presente su S3
dataset/ contiene immagini
stack city-workflow-iot completato
```

### 10.4 Non arrivano aggiornamenti WebSocket

Controllare:

```text
WEBSOCKET_URL corretto
subscribe(eventId) inviato
WebSocketSubscriptions popolata su DynamoDB
SendStatusUpdate configurata con WebSocketManagementEndpoint reale
```

---

## 11. File da non versionare

Prima di fare push, verificare che non siano presenti:

```text
local.properties
.gradle/
build/
app/build/
*.jks
*.keystore
credenziali
endpoint reali privati
```

Questi file devono essere esclusi tramite `.gitignore`.

---

## 12. Checklist per un nuovo sviluppatore

Prima di lavorare sull'app:

```text
[ ] Ho aperto android/EmergencyMobileApp/ in Android Studio
[ ] Il Gradle Sync e' completato
[ ] Il backend AWS e' stato deployato
[ ] Ho copiato gli output city-api in ApiConstants.kt
[ ] Ho avviato l'app su dispositivo o emulatore
[ ] Ho testato almeno un flusso manuale
[ ] Ho verificato gli aggiornamenti WebSocket
```

---

## 13. Sintesi

Questa cartella contiene solo la parte mobile del progetto CITY.

L'app Android si occupa di:

```text
raccogliere input dall'utente
caricare eventuali immagini
chiamare gli endpoint AWS
ricevere stati real-time
mostrare il risultato finale
```

Il backend AWS si occupa di:

```text
analisi immagine
classificazione emergenza
valutazione gravita'
decisione finale
notifiche
salvataggio dati
archiviazione
```
