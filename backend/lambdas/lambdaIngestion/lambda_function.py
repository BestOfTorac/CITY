import json
import os
import time
from datetime import datetime, timezone
from pathlib import PurePosixPath

import boto3
from botocore.exceptions import ClientError


s3 = boto3.client("s3")
rekognition = boto3.client("rekognition")
sqs = boto3.client("sqs")
lambda_client = boto3.client("lambda")


DESTINATION_BUCKET = os.environ.get(
    "DESTINATION_BUCKET",
    "emergency-images-camera"
)

CAPTURED_PREFIX = os.environ.get(
    "CAPTURED_PREFIX",
    "captured/"
)

QUEUE_URL = os.environ.get(
    "QUEUE_URL",
    "https://sqs.us-east-1.amazonaws.com/"
    "620333538289/emergency-events-queue"
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
    """
    Classificazione semplice basata sulle etichette
    restituite da Amazon Rekognition.
    """

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


def resolve_event_id(event):
    """
    Usa eventId quando arriva dal nuovo ramo app.
    Mantiene la compatibilitÃ  con il vecchio ramo che
    forniva soltanto testId.
    """

    event_id = event.get("eventId")
    test_id = event.get("testId")

    if isinstance(event_id, str):
        event_id = event_id.strip()

    if isinstance(test_id, str):
        test_id = test_id.strip()

    if event_id:
        if not test_id:
            test_id = event_id.removeprefix(
                "camera-"
            )

        return event_id, test_id

    if test_id:
        return (
            f"camera-{test_id}",
            test_id
        )

    raise ValueError(
        "eventId e testId assenti"
    )


def send_image_analyzed_status(event_id):
    """
    Invia il 50% all'app senza bloccare il flusso
    principale quando il WebSocket non Ã¨ disponibile.
    """

    payload = {
        "eventId": event_id,
        "status": "IMAGE_ANALYZED",
        "progress": 50,
        "message":
            "Immagine della telecamera analizzata"
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
                "CAMERA IMAGE STATUS "
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
                "CAMERA IMAGE STATUS "
                f"UPDATE FAILED: {error}"
            )

            return False

        except Exception as error:
            print(
                "UNEXPECTED CAMERA STATUS "
                f"UPDATE ERROR: {error}"
            )

            return False

    print(
        "CAMERA IMAGE STATUS NOT SENT: "
        "nessuna sottoscrizione WebSocket "
        "attiva trovata"
    )

    return False


def lambda_handler(event, context):
    print(
        "INGESTION EVENT RECEIVED"
    )

    print(
        json.dumps(
            event,
            ensure_ascii=False
        )
    )

    try:
        event_id, test_id = (
            resolve_event_id(event)
        )

        camera_id = event.get(
            "cameraId",
            "unknown"
        )

        location = event.get(
            "location",
            "Unknown location"
        )

        dataset_bucket = event.get(
            "datasetBucket"
        )

        dataset_key = event.get(
            "datasetKey"
        )

        if (
            not dataset_bucket
            or not dataset_key
        ):
            raise ValueError(
                "datasetBucket o datasetKey assenti"
            )

        original_filename = (
            PurePosixPath(
                dataset_key
            ).name
        )

        timestamp_for_name = (
            datetime.now(
                timezone.utc
            ).strftime(
                "%Y%m%dT%H%M%SZ"
            )
        )

        captured_key = (
            f"{CAPTURED_PREFIX}"
            f"{camera_id}-"
            f"{timestamp_for_name}-"
            f"{original_filename}"
        )

        # Simula la cattura della telecamera copiando
        # l'immagine dal dataset alla cartella captured/.
        s3.copy_object(
            CopySource={
                "Bucket":
                    dataset_bucket,
                "Key":
                    dataset_key
            },
            Bucket=
                DESTINATION_BUCKET,
            Key=
                captured_key
        )

        print(
            "IMAGE COPIED"
        )

        print(
            f"s3://{dataset_bucket}/"
            f"{dataset_key} -> "
            f"s3://{DESTINATION_BUCKET}/"
            f"{captured_key}"
        )

        # Analizza l'immagine catturata.
        rekognition_response = (
            rekognition.detect_labels(
                Image={
                    "S3Object": {
                        "Bucket":
                            DESTINATION_BUCKET,
                        "Name":
                            captured_key
                    }
                },
                MaxLabels=10,
                MinConfidence=70
            )
        )

        detected_labels = [
            {
                "name":
                    label["Name"],

                "confidence":
                    round(
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

        event_type, confidence = (
            classify_event(
                detected_labels
            )
        )

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        sqs_message = {
            # Identificativo condiviso con
            # app, WebSocket e Step Functions.
            "eventId":
                event_id,

            # Conservato per compatibilitÃ 
            # con il vecchio ramo telecamera.
            "testId":
                test_id,

            "cameraId":
                camera_id,

            "location":
                location,

            "imageName":
                original_filename,

            "bucket":
                DESTINATION_BUCKET,

            "imageKey":
                captured_key,

            "eventType":
                event_type,

            "confidence":
                confidence,

            "labels":
                detected_labels,

            "visualAnalysis": {
                "eventType":
                    event_type,
                "confidence":
                    confidence,
                "labels":
                    detected_labels,
                "analysisSource":
                    "camera_capture"
            },

            "source":
                "camera",

            "timestamp":
                timestamp
        }

        # Il 50% viene inviato dopo Rekognition e prima
        # dell'invio a SQS, cosÃ¬ precede gli stati
        # prodotti dalla Step Function.
        status_update_sent = (
            send_image_analyzed_status(
                event_id
            )
        )

        sqs_response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(
                sqs_message,
                ensure_ascii=False
            )
        )

        print(
            "MESSAGE SENT TO SQS"
        )

        print(
            json.dumps(
                sqs_message,
                ensure_ascii=False
            )
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "status":
                        "CAMERA_IMAGE_ANALYZED",

                    "message":
                        "Immagine della telecamera "
                        "elaborata",

                    "eventId":
                        event_id,

                    "testId":
                        test_id,

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
            f"AWS error: {error}"
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
                        "l'elaborazione "
                        "dell'immagine telecamera",

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
                        "della telecamera"
                },
                ensure_ascii=False
            )
        }
