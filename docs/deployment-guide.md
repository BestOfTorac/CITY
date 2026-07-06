# CITY - Deployment Guide

Guida operativa per distribuire CITY su un nuovo account AWS Learner Lab usando CloudFormation.

## Prerequisiti

- Regione consigliata: us-east-1.
- Ruolo IAM Learner Lab esistente: LabRole.
- File CloudFormation:
  - storage-messaging.yaml
  - lambdas-update-websocket.yaml
  - api-gateway.yaml
  - workflow-iot-fixed.yaml
- ZIP Lambda caricati in S3 sotto deployment/lambdas/.

## Stack creati

```text
city-storage-messaging
city-lambdas
city-api
city-workflow-iot
```

## 1. Stack storage e messaging

Template:

```text
storage-messaging.yaml
```

Stack name:

```text
city-storage-messaging
```

Risorse create:

```text
S3 bucket
DynamoDB EmergencyData
DynamoDB WebSocketSubscriptions
SQS emergency-events-queue
SNS emergency-alerts-topic
```

## 2. Upload zip Lambda su S3

Nel bucket creato dallo stack storage, caricare gli zip Lambda in:

```text
deployment/lambdas/
```

## 3. Recupero IoT endpoint

Da CloudShell:

```bash
aws iot describe-endpoint --endpoint-type iot:Data-ATS --query endpointAddress --output text
```

Usare il valore ottenuto come parametro IotDataEndpoint dello stack Lambda.

## 4. Stack Lambda

Template:

```text
lambdas-update-websocket.yaml
```

Stack name:

```text
city-lambdas
```

Parametri principali:

```text
StorageMessagingStackName = city-storage-messaging
LambdaCodeBucketName = NOME_BUCKET_CREATO_DA_CLOUDFORMATION
LambdaCodePrefix = deployment/lambdas/
IotDataEndpoint = OUTPUT_COMANDO_AWS_IOT_DESCRIBE_ENDPOINT
LabRoleName = LabRole
WorkflowStateMachineName = workflowEmergency
```

## 5. Stack API Gateway

Template:

```text
api-gateway.yaml
```

Stack name:

```text
city-api
```

Output importanti:

```text
EmergencyEndpoint
UploadUrlEndpoint
CameraTestEndpoint
WebSocketEndpoint
WebSocketManagementEndpoint
```

## 6. Update Lambda con WebSocket reale

Aggiornare lo stack city-lambdas usando lo stesso template:

```text
lambdas-update-websocket.yaml
```

Parametro da aggiornare:

```text
WebSocketManagementEndpoint = OUTPUT_WEBSOCKET_MANAGEMENT_ENDPOINT_DELLO_STACK_CITY_API
```

## 7. Stack Workflow e IoT

Template:

```text
workflow-iot-fixed.yaml
```

Stack name:

```text
city-workflow-iot
```

Risorse create:

```text
AWS IoT Rule CameraIngestionRule
Step Functions workflowEmergency
```

## 8. Configurazione Android

Aggiornare ApiConstants.kt con gli output dello stack city-api.

Nella repository pubblica tenere placeholder, non endpoint reali.

## 9. Dataset S3

Nel bucket S3 creare il prefix:

```text
dataset/
```

Caricare immagini jpg, jpeg o png.

## 10. SNS

Confermare la subscription SNS via email cliccando Confirm subscription.

## 11. Test end-to-end

```text
Manuale senza immagine
Manuale con immagine
Telecamera simulata
```

Risultato atteso: workflow completato, DynamoDB aggiornato e WebSocket al 100%.
