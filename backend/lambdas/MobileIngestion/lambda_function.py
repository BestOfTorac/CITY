import json
import os
import time
from datetime import datetime, timezone
from pathlib import PurePosixPath

import boto3
from botocore.exceptions import ClientError


rekognition = boto3.client("rekognition")
sqs = boto3.client("sqs")
lambda_client = boto3.client("lambda")


QUEUE_URL = os.environ.get(
    "QUEUE_URL",
    "https://sqs.us-east-1.amazonaws.com/"
    "620333538289/emergency-events-queue"
)

ALLOWED_BUCKET = os.environ.get(
    "ALLOWED_BUCKET",
    "emergency-images-camera"
)

ALLOWED_PREFIX = os.environ.get(
    "ALLOWED_PREFIX",
    "mobile/"
)

MAX_LABELS = int(
    os.environ.get(
        "MAX_LABELS",
        "10"
    )
)

MIN_CONFIDENCE = float(
    os.environ.get(
        "MIN_CONFIDENCE",
        "70"
    )
)

STATUS_UPDATE_FUNCTION = os.environ.get(
    "STATUS_UPDATE_FUNCTION",
    "SendStatusUpdate"
)

STATUS_UPDATE_MAX_ATTEMPTS = int(
    os.environ.get(
        "STATUS_UPDATE_MAX_ATTEMPTS",
        "3"
    )
)

STATUS_UPDATE_RETRY_DELAY_SECONDS = float(
    os.environ.get(
        "STATUS_UPDATE_RETRY_DELAY_SECONDS",
        "0.5"
    )
)


def classify_event(labels):
    fire_labels = {
        "fire",
        "flame",
        "smoke"
    }

    accident_labels = {
        "accident",
        "collision",
        "crash",
        "car accident",
        "vehicle accident"
    }

    for label in labels:
        name = label["name"].lower()

        if name in fire_labels:
            return (
                "fire",
                label["confidence"]
            )

        if name in accident_labels:
            return (
                "accident",
                label["confidence"]
            )

    return "unknown", 0


def validate_event(event):
    event_id = event.get("eventId")

    if not event_id:
        raise ValueError(
            "eventId assente"
        )

    image_data = event.get(
        "imageData"
    )

    if not isinstance(
        image_data,
        dict
    ):
        raise ValueError(
            "imageData assente o non valido"
        )

    bucket = image_data.get(
        "bucket"
    )

    image_key = image_data.get(
        "imageKey"
    )

    if not bucket:
        raise ValueError(
            "imageData.bucket assente"
        )

    if not image_key:
        raise ValueError(
            "imageData.imageKey assente"
        )

    if bucket != ALLOWED_BUCKET:
        raise ValueError(
            "Bucket non autorizzato"
        )

    if not image_key.startswith(
        ALLOWED_PREFIX
    ):
        raise ValueError(
            "L'immagine deve trovarsi "
            f"nel percorso {ALLOWED_PREFIX}"
        )

    return (
        event_id,
        image_data,
        bucket,
        image_key
    )


def invoke_status_update(event_id):
    payload = {
        "eventId": event_id,
        "status": "IMAGE_ANALYZED",
        "progress": 50,
        "message": "Analisi dell'immagine completata"
    }

    for attempt in range(
        1,
        STATUS_UPDATE_MAX_ATTEMPTS + 1
    ):
        try:
            response = lambda_client.invoke(
                FunctionName=
                    STATUS_UPDATE_FUNCTION,
                InvocationType=
                    "RequestResponse",
                Payload=json.dumps(
                    payload,
                    ensure_ascii=False
                ).encode("utf-8")
            )

            response_payload = (
                response["Payload"]
                .read()
                .decode("utf-8")
            )

            result = (
                json.loads(
                    response_payload
                )
                if response_payload
                else {}
            )

            if response.get(
                "FunctionError"
            ):
                print(
                    "SEND STATUS UPDATE "
                    "FUNCTION ERROR"
                )

                print(
                    json.dumps(
                        result,
                        ensure_ascii=False
                    )
                )

                return False

            subscriptions_found = int(
                result.get(
                    "subscriptionsFound",
                    0
                )
            )

            messages_sent = int(
                result.get(
                    "messagesSent",
                    0
                )
            )

            print(
                "IMAGE ANALYZED STATUS "
                f"ATTEMPT {attempt}: "
                f"subscriptions="
                f"{subscriptions_found}, "
                f"sent={messages_sent}"
            )

            if messages_sent > 0:
                return True

            if (
                attempt
                < STATUS_UPDATE_MAX_ATTEMPTS
            ):
                time.sleep(
                    STATUS_UPDATE_RETRY_DELAY_SECONDS
                )

        except ClientError as error:
            print(
                "IMAGE ANALYZED STATUS "
                f"UPDATE FAILED: {error}"
            )

            return False

        except Exception as error:
            print(
                "UNEXPECTED STATUS "
                f"UPDATE ERROR: {error}"
            )

            return False

    print(
        "IMAGE ANALYZED STATUS NOT SENT: "
        "nessuna sottoscrizione WebSocket "
        "attiva trovata"
    )

    return False


def lambda_handler(event, context):
    print(
        "MOBILE INGESTION EVENT RECEIVED"
    )

    print(
        json.dumps(
            event,
            ensure_ascii=False
        )[:5000]
    )

    try:
        (
            event_id,
            image_data,
            bucket,
            image_key
        ) = validate_event(event)

        original_filename = (
            image_data.get(
                "originalFileName"
            )
            or PurePosixPath(
                image_key
            ).name
        )

        print(
            f"Analyzing "
            f"s3://{bucket}/{image_key}"
        )

        rekognition_response = (
            rekognition.detect_labels(
                Image={
                    "S3Object": {
                        "Bucket": bucket,
                        "Name": image_key
                    }
                },
                MaxLabels=MAX_LABELS,
                MinConfidence=
                    MIN_CONFIDENCE
            )
        )

        detected_labels = [
            {
                "name": label["Name"],
                "confidence": round(
                    label["Confidence"],
                    2
                )
            }
            for label
            in rekognition_response.get(
                "Labels",
                []
            )
        ]

        detected_event_type, confidence = (
            classify_event(
                detected_labels
            )
        )

        timestamp = event.get(
            "timestamp"
        )

        if not timestamp:
            timestamp = datetime.now(
                timezone.utc
            ).isoformat()

        # Conserviamo i dati inviati
        # dall'applicazione mobile.
        sqs_message = dict(event)

        # Garantiamo che una segnalazione
        # mobile non venga interpretata
        # come evento proveniente da telecamera.
        sqs_message.pop(
            "cameraId",
            None
        )

        sqs_message.pop(
            "datasetBucket",
            None
        )

        sqs_message.pop(
            "datasetKey",
            None
        )

        sqs_message.update({
            "eventId": event_id,

            # Conservato per compatibilità
            # con il flusso SQS esistente.
            "testId": event_id,

            # Origine reale dell'evento.
            "source": "mobile",
            "reportOrigin": "user",
            "isUserReport": True,

            "location": event.get(
                "location",
                "Unknown location"
            ),

            "description": event.get(
                "description",
                ""
            ),

            # Tipo dichiarato manualmente
            # dall'utente.
            "reportedType": event.get(
                "reportedType",
                "UNKNOWN"
            ),

            "injured": event.get(
                "injured",
                "UNKNOWN"
            ),

            "immediateDanger": event.get(
                "immediateDanger",
                "UNKNOWN"
            ),

            "imageName":
                original_filename,

            "bucket": bucket,

            "imageKey": image_key,

            # Tipo individuato attraverso
            # l'analisi della foto allegata.
            "eventType":
                detected_event_type,

            "confidence":
                confidence,

            "labels":
                detected_labels,

            "visualAnalysis": {
                "eventType":
                    detected_event_type,
                "confidence":
                    confidence,
                "labels":
                    detected_labels,
                "analysisSource":
                    "user_uploaded_image"
            },

            "timestamp": timestamp
        })

        print(
            "FINAL MOBILE SQS MESSAGE"
        )

        print(
            json.dumps(
                sqs_message,
                ensure_ascii=False
            )
        )

        # L'aggiornamento viene inviato prima di SQS,
        # così il 50% arriva prima degli stati
        # prodotti dalla Step Function.
        status_update_sent = (
            invoke_status_update(
                event_id
            )
        )

        # Anche se il telefono non è connesso,
        # il flusso principale deve continuare.
        sqs_response = (
            sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(
                    sqs_message,
                    ensure_ascii=False
                )
            )
        )

        print(
            "MOBILE MESSAGE SENT TO SQS"
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "status":
                        "IMAGE_ANALYZED",

                    "message":
                        "Immagine della segnalazione "
                        "utente analizzata",

                    "eventId":
                        event_id,

                    "source":
                        "mobile",

                    "reportOrigin":
                        "user",

                    "statusUpdateSent":
                        status_update_sent,

                    "sqsMessageId":
                        sqs_response[
                            "MessageId"
                        ],

                    "result":
                        sqs_message
                },
                ensure_ascii=False
            )
        }

    except ValueError as error:
        print(
            f"INVALID EVENT: {error}"
        )

        return {
            "statusCode": 400,
            "body": json.dumps(
                {
                    "status":
                        "INVALID_EVENT",
                    "message":
                        str(error)
                },
                ensure_ascii=False
            )
        }

    except ClientError as error:
        print(
            f"AWS service error: {error}"
        )

        error_code = (
            error.response
            .get("Error", {})
            .get(
                "Code",
                "Unknown"
            )
        )

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "status":
                        "AWS_ERROR",

                    "message":
                        "Errore durante "
                        "l'analisi dell'immagine",

                    "awsErrorCode":
                        error_code
                },
                ensure_ascii=False
            )
        }

    except Exception as error:
        print(
            f"Unexpected error: {error}"
        )

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "status":
                        "ERROR",

                    "message":
                        "Errore interno durante "
                        "l'elaborazione "
                        "dell'immagine mobile"
                },
                ensure_ascii=False
            )
        }
