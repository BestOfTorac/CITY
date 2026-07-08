# CITY - Android App

Questo documento descrive la struttura dell'app Android usata nel progetto CITY.

L'app Android rappresenta il client mobile del sistema. Permette all'utente di:

```text
1. inviare una segnalazione manuale di emergenza;
2. allegare una foto alla segnalazione;
3. avviare un test di telecamera simulata;
4. ricevere aggiornamenti real-time sullo stato dell'elaborazione tramite WebSocket.
```

La descrizione completa dell'architettura backend si trova in:

```text
docs/architecture.md
```

La procedura di deploy AWS si trova in:

```text
docs/deployment-guide.md
```

---

## 1. Posizione del progetto Android

Il progetto Android si trova nella cartella:

```text
android/EmergencyMobileApp/
```

La cartella `android/` contiene questo README e il progetto mobile vero e proprio.

Struttura generale:

```text
android/
|-- README.md
|-- EmergencyMobileApp/
    |-- app/
    |-- build.gradle.kts
    |-- settings.gradle.kts
    |-- gradle/
    |-- gradlew
    |-- gradlew.bat
```

Il modulo principale dell'app e':

```text
android/EmergencyMobileApp/app/
```

---

## 2. Ruolo dell'app nel sistema CITY

L'app non contiene la logica cloud principale. La sua responsabilita' e' interagire con il backend AWS tramite gli endpoint esposti da API Gateway.

L'app comunica con:

```text
HTTP API Gateway
WebSocket API Gateway
Amazon S3 tramite presigned URL
```

I flussi principali sono:

```text
Manual report without image
Manual report with image
Camera simulation test
Real-time status updates
```

---

## 3. Endpoint usati dall'app

L'app usa quattro endpoint generati dallo stack CloudFormation `city-api`.

| Costante Android | Output CloudFormation | Uso |
|---|---|---|
| `WEBSOCKET_URL` | `WebSocketEndpoint` | Connessione WebSocket per aggiornamenti real-time |
| `UPLOAD_URL_ENDPOINT` | `UploadUrlEndpoint` | Richiesta presigned URL per upload immagine |
| `EMERGENCY_ENDPOINT` | `EmergencyEndpoint` | Invio segnalazione manuale |
| `CAMERA_TEST_ENDPOINT` | `CameraTestEndpoint` | Avvio test telecamera simulata |

Il file da configurare localmente e':

```text
app/src/main/java/com/toracshalby/emergencymobile/network/ApiConstants.kt
```

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

Sostituire i placeholder con gli output reali dello stack `city-api`.

---

## 4. Configurazione sicura degli endpoint

Gli endpoint reali usati per una demo privata non devono essere pubblicati se non necessario.

Prima del push pubblico verificare che non siano presenti:

```text
endpoint reali temporanei
access key
secret key
token AWS
file local.properties
keystore
credenziali
```

File e cartelle da non versionare:

```text
local.properties
.gradle/
build/
app/build/
*.jks
*.keystore
```

Se nella repository e' presente:

```text
ApiConstants.example.kt
```

questo file deve contenere solo placeholder, non endpoint reali.

---

## 5. Struttura logica dell'app

La struttura puo' variare leggermente in base all'organizzazione del codice, ma la divisione logica dell'app e' la seguente.

```text
com.toracshalby.emergencymobile/
|-- network/
|-- model/
|-- ui/
|-- websocket/
|-- utils/
```

### 5.1 network/

Contiene le classi responsabili della comunicazione HTTP con il backend AWS.

Responsabilita':

```text
chiamare POST /upload-url
chiamare POST /emergency
chiamare POST /test/camera
gestire request e response HTTP
centralizzare gli endpoint in ApiConstants.kt
```

File principale:

```text
ApiConstants.kt
```

Questa divisione evita di spargere URL e logica di rete nelle schermate dell'app.

### 5.2 model/

Contiene i modelli dati usati dall'app.

Esempi di dati rappresentati:

```text
emergency report
location
image upload request
image upload response
camera test response
status update
```

I model servono a separare i dati dalla UI e dalla logica di rete.

### 5.3 ui/

Contiene le schermate e i componenti visuali dell'app.

Responsabilita':

```text
mostrare form di segnalazione
permettere selezione o scatto immagine
mostrare avanzamento del workflow
mostrare risultato finale
mostrare eventuali errori
```

La UI non dovrebbe contenere direttamente dettagli AWS. Deve usare le funzioni offerte dal livello network o da eventuali ViewModel/controller.

### 5.4 websocket/

Contiene la logica per la connessione WebSocket.

Responsabilita':

```text
aprire la connessione verso WEBSOCKET_URL
inviare subscribe(eventId)
ricevere aggiornamenti di stato
aggiornare la UI durante il workflow
gestire disconnessione o errori di rete
```

Il WebSocket e' fondamentale per mostrare il progresso dell'elaborazione in tempo reale.

### 5.5 utils/

Contiene funzioni di supporto.

Esempi:

```text
gestione URI immagini
conversione file/bitmap
validazione input
formattazione date
logging locale
```

---

## 6. Flusso manuale senza immagine

Questo flusso viene usato quando l'utente invia una segnalazione senza allegare foto.

```text
Android App
-> apre WebSocket
-> subscribe(eventId)
-> POST /emergency
-> receiveEmergency
-> workflowEmergency
-> aggiornamenti WebSocket
-> completamento sull'app
```

Passaggi lato app:

```text
1. L'utente compila la segnalazione.
2. L'app crea o riceve un eventId.
3. L'app apre la connessione WebSocket.
4. L'app invia subscribe(eventId).
5. L'app invia la segnalazione a EMERGENCY_ENDPOINT.
6. L'app riceve gli aggiornamenti real-time.
7. L'app mostra il completamento.
```

---

## 7. Flusso manuale con immagine

Questo flusso viene usato quando l'utente allega una foto.

La foto non viene inviata direttamente a una Lambda. L'app carica l'immagine su S3 usando una presigned URL.

```text
Android App
-> POST /upload-url
-> riceve presigned URL
-> upload diretto foto su S3 mobile/
-> POST /emergency con riferimento immagine
-> MobileIngestion
-> Rekognition
-> SQS
-> workflowEmergency
-> aggiornamenti WebSocket
```

Passaggi lato app:

```text
1. L'utente seleziona o scatta una foto.
2. L'app chiama UPLOAD_URL_ENDPOINT.
3. Il backend restituisce una presigned URL.
4. L'app carica la foto direttamente su S3.
5. L'app invia la segnalazione a EMERGENCY_ENDPOINT includendo imageKey o riferimento immagine.
6. L'app resta in ascolto sul WebSocket.
7. L'app mostra gli stati ricevuti dal backend.
```

---

## 8. Flusso test telecamera simulata

Questo flusso serve a testare il ramo camera senza usare una telecamera reale.

```text
Android App
-> POST /test/camera
-> cameraSimulator
-> S3 dataset/
-> AWS IoT Core
-> lambdaIngestion
-> Rekognition
-> SQS
-> workflowEmergency
-> aggiornamenti WebSocket
```

Passaggi lato app:

```text
1. L'utente preme il pulsante per avviare il test camera.
2. L'app chiama CAMERA_TEST_ENDPOINT.
3. Il backend seleziona una immagine casuale dal dataset S3.
4. Il backend pubblica l'evento su AWS IoT Core.
5. Il workflow viene avviato lato backend.
6. L'app riceve gli aggiornamenti tramite WebSocket.
```

---

## 9. Aggiornamenti real-time

Durante l'elaborazione, l'app riceve stati dal backend.

Esempi di stati:

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

Non tutti gli stati sono presenti in ogni flusso.

Per esempio:

```text
IMAGE_ANALYZED
```

e' previsto solo quando viene elaborata una immagine.

---

## 10. Come eseguire l'app

### 10.1 Aprire il progetto

Aprire Android Studio e selezionare:

```text
android/EmergencyMobileApp/
```

### 10.2 Sincronizzare Gradle

Eseguire:

```text
Sync Project with Gradle Files
```

### 10.3 Configurare ApiConstants.kt

Inserire gli endpoint reali ottenuti da CloudFormation.

### 10.4 Avviare l'app

Collegare un dispositivo Android oppure usare un emulatore, poi premere:

```text
Run
```

---

## 11. Test principali dall'app

Dopo aver avviato l'app, eseguire questi test:

```text
1. Segnalazione manuale senza immagine
2. Segnalazione manuale con immagine
3. Test telecamera simulata
4. Verifica aggiornamenti WebSocket
```

Per il piano di test completo consultare:

```text
docs/test-plan.md
```

---

## 12. Problemi comuni

### 12.1 L'app non si collega al backend

Controllare:

```text
ApiConstants.kt
connessione internet
endpoint copiati correttamente
stack city-api in CREATE_COMPLETE
```

### 12.2 L'upload immagine fallisce

Controllare:

```text
UPLOAD_URL_ENDPOINT corretto
permessi Android per accedere all'immagine
presigned URL non scaduta
bucket S3 creato correttamente
```

### 12.3 Il test camera non funziona

Controllare:

```text
CAMERA_TEST_ENDPOINT corretto
dataset/ presente su S3
dataset/ contiene immagini
city-workflow-iot creato correttamente
```

### 12.4 Non arrivano aggiornamenti real-time

Controllare:

```text
WEBSOCKET_URL corretto
subscribe(eventId) inviato correttamente
WebSocketSubscriptions contiene la connessione
SendStatusUpdate usa WebSocketManagementEndpoint reale
```

---

## 13. Prima del push pubblico

Eseguire sempre:

```powershell
git status
```

Verificare che non siano presenti file sensibili.

Controllare in particolare:

```text
local.properties
build/
.gradle/
app/build/
keystore
credenziali
endpoint reali privati
```

Se serve cercare endpoint reali nel codice:

```powershell
git grep -n "execute-api"
git grep -n "amazonaws.com"
git grep -n "wss://"
```

Se questi valori sono solo placeholder, va bene. Se sono endpoint reali di demo privata, sostituirli prima del push.

---

## 14. Sintesi

L'app Android e' il punto di interazione dell'utente con CITY.

Responsabilita' principali:

```text
inviare emergenze manuali
caricare immagini su S3 tramite presigned URL
avviare test camera simulata
ricevere stati real-time tramite WebSocket
mostrare il completamento del workflow
```

Il backend AWS gestisce invece:

```text
elaborazione immagini
classificazione emergenza
valutazione gravita'
decisione finale
notifiche
persistenza dati
archiviazione
```
