# CITY - Deployment Guide

Guida operativa per distribuire l'intero sistema CITY su un nuovo account AWS Learner Lab.

Questa guida contiene solo i passaggi di setup e deploy. Per la descrizione del progetto, dell'architettura e delle scelte progettuali consultare gli altri file nella cartella `docs/`.

---

## Indice rapido

```text
Passo 0  - File necessari
Passo 1  - Avviare AWS Learner Lab
Passo 2  - Creare lo stack city-storage-messaging
Passo 3  - Caricare gli zip Lambda su S3
Passo 4  - Recuperare endpoint IoT
Passo 5  - Creare lo stack city-lambdas
Passo 6  - Creare lo stack city-api
Passo 7  - Aggiornare city-lambdas con WebSocketManagementEndpoint reale
Passo 8  - Creare lo stack city-workflow-iot
Passo 9  - Creare dataset/ su S3 e caricare immagini
Passo 10 - Confermare SNS
Passo 11 - Configurare Android
Passo 12 - Test end-to-end
Passo 13 - Troubleshooting
```

---

## Passo 0 - File necessari

Prima di iniziare assicurarsi di avere questi file nella repository.

### 0.1 Template CloudFormation

Percorso:

```text
infrastructure/cloudformation/
```

File richiesti:

```text
storage-messaging.yaml
lambdas-update-websocket.yaml
api-gateway.yaml
workflow-iot-fixed.yaml
```

### 0.2 Zip Lambda gia' pronti

Per semplificare il deploy, la repository contiene gia' gli zip Lambda pronti all'uso.

Percorso consigliato:

```text
backend/lambda-zips/
```

File richiesti:

```text
backend/lambda-zips/receiveEmergency.zip
backend/lambda-zips/GenerateMobileUploadUrl.zip
backend/lambda-zips/MobileIngestion.zip
backend/lambda-zips/cameraSimulator.zip
backend/lambda-zips/lambdaIngestion.zip
backend/lambda-zips/StartWorkflow.zip
backend/lambda-zips/ValidateEvent.zip
backend/lambda-zips/ContextualizeEvent.zip
backend/lambda-zips/ClassifyEvent.zip
backend/lambda-zips/EvaluateSeverity.zip
backend/lambda-zips/DecisionLogic.zip
backend/lambda-zips/StoreLogs.zip
backend/lambda-zips/SendStatusUpdate.zip
backend/lambda-zips/WebSocketHandler.zip
```

I nomi devono essere identici, comprese maiuscole e minuscole.

> Importante: CloudFormation non legge direttamente gli zip dalla repository GitHub. Gli zip presenti in `backend/lambda-zips/` devono essere caricati manualmente su S3 nel Passo 3.

### 0.3 Progetto Android

Percorso consigliato:

```text
android/EmergencyMobileApp/
```

File da modificare dopo il deploy:

```text
android/EmergencyMobileApp/app/src/main/java/com/toracshalby/emergencymobile/network/ApiConstants.kt
```

### 0.4 Dataset immagini

Preparare alcune immagini `.jpg`, `.jpeg` o `.png` per il test telecamera.

Esempio:

```text
fire_01.jpg
accident_01.jpg
normal_01.jpg
```

---

## Passo 1 - Avviare AWS Learner Lab

1. Aprire AWS Academy.
2. Entrare nel Learner Lab.
3. Cliccare su `Start Lab`.
4. Attendere che il laboratorio sia attivo.
5. Cliccare su `AWS` per aprire la console AWS.

In alto a destra selezionare la regione:

```text
US East (N. Virginia) - us-east-1
```

Tutto il deploy deve essere fatto in:

```text
us-east-1
```

---

## Passo 2 - Creare lo stack city-storage-messaging

Questo stack va creato per primo.

### 2.1 Aprire CloudFormation

Andare su:

```text
CloudFormation
-> Create stack
-> With new resources
-> Upload a template file
```

Caricare:

```text
infrastructure/cloudformation/storage-messaging.yaml
```

Cliccare `Next`.

### 2.2 Nome stack

Inserire:

```text
city-storage-messaging
```

### 2.3 Parametri

Usare questi valori:

```text
ProjectName = city
EnvironmentName = dev
EmergencyDataTableName = EmergencyData
WebSocketSubscriptionsTableName = WebSocketSubscriptions
EmergencyEventsQueueName = emergency-events-queue
EmergencyAlertsTopicName = emergency-alerts-topic
NotificationEmail1 = EMAIL_DA_USARE_PER_RICEVERE_GLI_ALERT
NotificationEmail2 = opzionale
```

Il parametro:

```text
NotificationEmail1
```

deve essere valorizzato con una email reale, per esempio la mail dello studente che sta facendo il deploy. Questa email ricevera' le notifiche SNS quando il sistema decide di avvisare i soccorritori.

Dopo la creazione dello stack, AWS inviera' una mail di conferma a questo indirizzo. La conferma viene fatta nel Passo 10.

Se compare il parametro:

```text
EmergencyImagesBucketName
```

lasciarlo vuoto se il template lo permette. In questo modo viene generato automaticamente un nome bucket univoco.

### 2.4 Creazione

Cliccare:

```text
Next
Next
Submit
```

Attendere:

```text
CREATE_COMPLETE
```

### 2.5 Output da salvare

Aprire la scheda `Outputs` dello stack e copiare questi valori:

```text
EmergencyImagesBucketName
EmergencyEventsQueueUrl
EmergencyEventsQueueArn
EmergencyAlertsTopicArn
EmergencyDataTableName
WebSocketSubscriptionsTableName
WebSocketEventIdIndexName
```

Il valore da usare subito dopo e':

```text
EmergencyImagesBucketName
```

Questo e' il nome esatto del bucket S3 creato da CloudFormation.

Non bisogna inventare il nome del bucket e non bisogna crearne un altro manualmente. Nel Passo 3 bisogna aprire proprio il bucket indicato da questo output.

---

## Passo 3 - Caricare gli zip Lambda su S3

### 3.1 Aprire il bucket creato dallo stack precedente

Andare su:

```text
S3
-> Buckets
-> EmergencyImagesBucketName
```

Sostituire `EmergencyImagesBucketName` con il valore ottenuto negli output del Passo 2.

Esempio generico:

```text
city-dev-emergency-images-ACCOUNT-us-east-1
```

### 3.2 Creare il percorso deployment/lambdas/

Dentro il bucket creare la cartella:

```text
deployment
```

Entrare in `deployment` e creare:

```text
lambdas
```

Percorso finale su S3:

```text
deployment/lambdas/
```

### 3.3 Caricare gli zip dalla repository

Prendere gli zip dalla cartella locale:

```text
backend/lambda-zips/
```

e caricarli su S3 dentro:

```text
deployment/lambdas/
```

Alla fine il bucket deve contenere:

```text
deployment/lambdas/receiveEmergency.zip
deployment/lambdas/GenerateMobileUploadUrl.zip
deployment/lambdas/MobileIngestion.zip
deployment/lambdas/cameraSimulator.zip
deployment/lambdas/lambdaIngestion.zip
deployment/lambdas/StartWorkflow.zip
deployment/lambdas/ValidateEvent.zip
deployment/lambdas/ContextualizeEvent.zip
deployment/lambdas/ClassifyEvent.zip
deployment/lambdas/EvaluateSeverity.zip
deployment/lambdas/DecisionLogic.zip
deployment/lambdas/StoreLogs.zip
deployment/lambdas/SendStatusUpdate.zip
deployment/lambdas/WebSocketHandler.zip
```

### 3.4 Nota su LambdaCodePrefix

Nel deploy consigliato gli zip sono caricati su S3 in:

```text
deployment/lambdas/
```

Quindi, nello stack Lambda, il parametro dovra' essere:

```text
LambdaCodePrefix = deployment/lambdas/
```

Se invece gli zip vengono caricati direttamente nella root del bucket, il parametro deve essere vuoto. Questa guida usa sempre `deployment/lambdas/`.

---

## Passo 4 - Recuperare endpoint IoT

### 4.1 Aprire CloudShell

Dalla console AWS cliccare sull'icona CloudShell.

### 4.2 Eseguire il comando

Eseguire:

```bash
aws iot describe-endpoint --endpoint-type iot:Data-ATS --query endpointAddress --output text
```

Il risultato sara' simile a:

```text
xxxxxxxxxxxxxx-ats.iot.us-east-1.amazonaws.com
```

Copiare il valore. Servira' nel parametro:

```text
IotDataEndpoint
```

Non aggiungere `https://`.

---

## Passo 5 - Creare lo stack city-lambdas

### 5.1 Aprire CloudFormation

Andare su:

```text
CloudFormation
-> Create stack
-> With new resources
-> Upload a template file
```

Caricare:

```text
infrastructure/cloudformation/lambdas-update-websocket.yaml
```

Questo template viene usato due volte:

```text
1. nel Passo 5 per creare tutte le Lambda;
2. nel Passo 7 per aggiornare solo il WebSocketManagementEndpoint.
```

Il motivo e' che il WebSocketManagementEndpoint reale esiste solo dopo aver creato lo stack `city-api`, quindi al primo deploy viene lasciato un valore temporaneo e poi viene aggiornato.

### 5.2 Nome stack

Inserire:

```text
city-lambdas
```

### 5.3 Parametri

Impostare:

```text
StorageMessagingStackName = city-storage-messaging
LambdaCodeBucketName = EmergencyImagesBucketName
LambdaCodePrefix = deployment/lambdas/
IotDataEndpoint = valore ottenuto da CloudShell
LabRoleName = LabRole
WorkflowStateMachineName = workflowEmergency
```

Per il parametro:

```text
WebSocketManagementEndpoint
```

lasciare temporaneamente il valore placeholder presente nel template. Verra' aggiornato nel Passo 7.

### 5.4 Creazione

Cliccare:

```text
Next
Next
Submit
```

Attendere:

```text
CREATE_COMPLETE
```

### 5.5 Verifica

Andare su:

```text
AWS Lambda
-> Functions
```

Verificare che siano presenti:

```text
receiveEmergency
GenerateMobileUploadUrl
MobileIngestion
cameraSimulator
lambdaIngestion
StartWorkflow
ValidateEvent
ContextualizeEvent
ClassifyEvent
EvaluateSeverity
DecisionLogic
StoreLogs
SendStatusUpdate
WebSocketHandler
```

---

## Passo 6 - Creare lo stack city-api

### 6.1 Aprire CloudFormation

Andare su:

```text
CloudFormation
-> Create stack
-> With new resources
-> Upload a template file
```

Caricare:

```text
infrastructure/cloudformation/api-gateway.yaml
```

### 6.2 Nome stack

Inserire:

```text
city-api
```

### 6.3 Parametri

Impostare:

```text
LambdaStackName = city-lambdas
ProjectName = city
EnvironmentName = dev
HttpApiName = EmergencyResponseAPI
WebSocketApiName = EmergencyStatusWebSocket
WebSocketStageName = production
```

### 6.4 Creazione

Cliccare:

```text
Next
Next
Submit
```

Attendere:

```text
CREATE_COMPLETE
```

### 6.5 Output da salvare

Aprire `Outputs` e copiare:

```text
EmergencyEndpoint
UploadUrlEndpoint
CameraTestEndpoint
WebSocketEndpoint
WebSocketManagementEndpoint
```

Questi valori servono nei passi successivi.

---

## Passo 7 - Aggiornare city-lambdas con WebSocketManagementEndpoint reale

Lo stack `city-lambdas` deve essere aggiornato con il valore reale di:

```text
WebSocketManagementEndpoint
```

ottenuto dallo stack `city-api`.

### 7.1 Aprire lo stack

Andare su:

```text
CloudFormation
-> Stacks
-> city-lambdas
-> Update
```

### 7.2 Ricaricare lo stesso template Lambda

Scegliere:

```text
Replace current template
-> Upload a template file
```

Caricare di nuovo:

```text
infrastructure/cloudformation/lambdas-update-websocket.yaml
```

E' corretto usare lo stesso file del Passo 5. In questo passaggio non si stanno creando nuove Lambda: si sta aggiornando lo stesso stack, cambiando il valore della variabile d'ambiente usata da `SendStatusUpdate`.

### 7.3 Aggiornare il parametro

Nel parametro:

```text
WebSocketManagementEndpoint
```

inserire l'output:

```text
WebSocketManagementEndpoint
```

dello stack:

```text
city-api
```

Gli altri parametri devono rimanere invariati.

### 7.4 Eseguire update

Cliccare:

```text
Next
Next
Submit
```

Attendere:

```text
UPDATE_COMPLETE
```

---

## Passo 8 - Creare lo stack city-workflow-iot

### 8.1 Aprire CloudFormation

Andare su:

```text
CloudFormation
-> Create stack
-> With new resources
-> Upload a template file
```

Caricare:

```text
infrastructure/cloudformation/workflow-iot-fixed.yaml
```

### 8.2 Nome stack

Inserire:

```text
city-workflow-iot
```

### 8.3 Parametri

Impostare:

```text
StorageMessagingStackName = city-storage-messaging
LambdaStackName = city-lambdas
ProjectName = city
EnvironmentName = dev
LabRoleName = LabRole
WorkflowStateMachineName = workflowEmergency
CameraIngestionRuleName = CameraIngestionRule
CameraIotTopic = emergency/camera
```

### 8.4 Creazione

Cliccare:

```text
Next
Next
Submit
```

Attendere:

```text
CREATE_COMPLETE
```

### 8.5 Verifica

Aprire `Outputs` e controllare:

```text
WorkflowEmergencyArn
WorkflowEmergencyName
CameraIngestionRuleArn
```

Poi verificare anche:

```text
Step Functions
-> State machines
-> workflowEmergency
```

---

## Passo 9 - Creare dataset/ su S3

### 9.1 Aprire il bucket

Andare su:

```text
S3
-> EmergencyImagesBucketName
```

### 9.2 Creare la cartella dataset

Cliccare:

```text
Create folder
```

Nome:

```text
dataset
```

Percorso finale:

```text
dataset/
```

### 9.3 Caricare immagini

Caricare immagini `.jpg`, `.jpeg` o `.png`.

Esempio:

```text
dataset/fire_01.jpg
dataset/accident_01.jpg
dataset/normal_01.jpg
```

Non e' necessario creare manualmente questi prefissi:

```text
mobile/
captured/
events/
```

Vengono creati automaticamente quando il sistema scrive oggetti su S3.

---

## Passo 10 - Confermare SNS

Se nel Passo 2 e' stata inserita una email in:

```text
NotificationEmail1
```

arrivera' una mail da AWS SNS.

Aprire la mail e cliccare:

```text
Confirm subscription
```

Senza conferma, SNS non invia notifiche.

---

## Passo 11 - Configurare Android

### 11.1 Aprire Android Studio

Aprire il progetto:

```text
android/EmergencyMobileApp/
```

### 11.2 Aprire ApiConstants.kt

Aprire:

```text
app/src/main/java/com/toracshalby/emergencymobile/network/ApiConstants.kt
```

### 11.3 Inserire gli output di city-api

Il file deve avere questa forma:

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

Sostituire:

```text
OUTPUT_WEBSOCKET_ENDPOINT      con WebSocketEndpoint
OUTPUT_UPLOAD_URL_ENDPOINT     con UploadUrlEndpoint
OUTPUT_EMERGENCY_ENDPOINT      con EmergencyEndpoint
OUTPUT_CAMERA_TEST_ENDPOINT    con CameraTestEndpoint
```

### 11.4 Build e run

In Android Studio:

```text
Sync Project with Gradle Files
Build
Run
```

---

## Passo 12 - Test end-to-end

Eseguire i test nell'ordine seguente.

### 12.1 Test manuale senza immagine

Da app Android inviare una segnalazione senza foto.

Risultato atteso:

```text
App riceve aggiornamenti real-time
Step Functions termina correttamente
DynamoDB EmergencyData contiene un nuovo record
```

Controlli AWS:

```text
Step Functions -> workflowEmergency -> execution succeeded
DynamoDB -> EmergencyData -> nuovo record
CloudWatch Logs -> nessun errore critico
```

### 12.2 Test manuale con immagine

Da app Android inviare una segnalazione con foto.

Risultato atteso:

```text
S3 mobile/ contiene la foto caricata
Step Functions termina correttamente
DynamoDB EmergencyData contiene un nuovo record
S3 events/ contiene archivio, se previsto dalla decision logic
App arriva al completamento
```

Controlli AWS:

```text
S3 -> mobile/
S3 -> events/
DynamoDB -> EmergencyData
Step Functions -> workflowEmergency
CloudWatch Logs -> MobileIngestion
```

### 12.3 Test telecamera simulata

Da app Android premere:

```text
Avvia test telecamera
```

Risultato atteso:

```text
cameraSimulator seleziona una immagine da dataset/
IoT Core riceve l'evento
lambdaIngestion viene invocata
Step Functions termina correttamente
DynamoDB EmergencyData contiene un nuovo record
App arriva al completamento
```

Controlli AWS:

```text
S3 -> dataset/
S3 -> captured/
Step Functions -> workflowEmergency
DynamoDB -> EmergencyData
CloudWatch Logs -> cameraSimulator
CloudWatch Logs -> lambdaIngestion
```

---

## Passo 13 - Troubleshooting

### 13.1 city-lambdas fallisce per zip non trovato

Controllare:

```text
LambdaCodeBucketName
LambdaCodePrefix
nome esatto dello zip
posizione dello zip su S3
```

Se gli zip sono in:

```text
deployment/lambdas/
```

allora:

```text
LambdaCodePrefix = deployment/lambdas/
```

Se gli zip sono nella root:

```text
LambdaCodePrefix = vuoto
```

### 13.2 Il test telecamera non funziona

Controllare:

```text
dataset/ esiste
dataset/ contiene immagini
IotDataEndpoint e' corretto
city-workflow-iot e' CREATE_COMPLETE
CameraIngestionRule esiste
```

Log utili:

```text
CloudWatch Logs -> cameraSimulator
CloudWatch Logs -> lambdaIngestion
```

### 13.3 Non arrivano email

Controllare:

```text
SNS subscription confermata
email corretta
topic emergency-alerts-topic esiste
```

### 13.4 L'app non arriva al completamento

Controllare:

```text
WebSocketEndpoint in ApiConstants.kt
WebSocketManagementEndpoint nello stack city-lambdas
Lambda SendStatusUpdate
DynamoDB WebSocketSubscriptions
CloudWatch Logs di SendStatusUpdate
```

### 13.5 Step Functions non parte

Controllare:

```text
SQS emergency-events-queue
trigger SQS su StartWorkflow
workflowEmergency
variabile STATE_MACHINE_ARN nelle Lambda
CloudWatch Logs di StartWorkflow
```

---

## Checklist finale

Prima di considerare completato il deploy, verificare:

```text
city-storage-messaging = CREATE_COMPLETE
city-lambdas = CREATE_COMPLETE oppure UPDATE_COMPLETE
city-api = CREATE_COMPLETE
city-workflow-iot = CREATE_COMPLETE
```

Verificare anche:

```text
zip Lambda caricati in S3
dataset/ caricato in S3
SNS confermato via email
ApiConstants.kt aggiornato localmente
test manuale senza immagine superato
test manuale con immagine superato
test telecamera simulata superato
DynamoDB EmergencyData contiene record
S3 mobile/ contiene immagini caricate dall'app
S3 captured/ contiene immagini del ramo camera
S3 events/ contiene archivi finali quando previsti
Step Functions mostra execution succeeded
App Android riceve gli aggiornamenti real-time
```
