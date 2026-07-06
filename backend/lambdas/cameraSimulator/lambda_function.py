import json
import os
import random
import re
import uuid
from datetime import datetime, timezone
from pathlib import PurePosixPath

import boto3
from botocore.exceptions import ClientError


BUCKET = os.environ["BUCKET"]

DATASET_PREFIX = os.environ.get(
    "DATASET_PREFIX",
    "dataset/"
)

IOT_ENDPOINT = os.environ["IOT_ENDPOINT"]

TOPIC = os.environ.get(
    "TOPIC",
    "emergency/camera"
)

PRESIGNED_URL_EXPIRATION = int(
    os.environ.get(
        "PRESIGNED_URL_EXPIRATION",
        "900"
    )
)


s3 = boto3.client("s3")

iot_data = boto3.client(
    "iot-data",
    endpoint_url=f"https://{IOT_ENDPOINT}"
)


CAMERAS = [
    {
        "cameraId": "CAM01",
        "location":
            "Edificio Ingegneria - Piano 1"
    },
    {
        "cameraId": "CAM02",
        "location":
            "Parcheggio Facoltà di Ingegneria"
    },
    {
        "cameraId": "CAM03",
        "location":
            "Ingresso principale"
    }
]


VALID_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png"
)


EVENT_ID_PATTERN = re.compile(
    r"^camera-[A-Za-z0-9_-]{8,100}$"
)


def get_dataset_images():
    images = []

    paginator = s3.get_paginator(
        "list_objects_v2"
    )

    pages = paginator.paginate(
        Bucket=BUCKET,
        Prefix=DATASET_PREFIX
    )

    for page in pages:
        for item in page.get(
            "Contents",
            []
        ):
            key = item["Key"]

            if (
                not key.endswith("/")
                and key.lower().endswith(
                    VALID_EXTENSIONS
                )
            ):
                images.append(key)

    return images


def create_response(
    status_code,
    body
):
    return {
        "statusCode":
            status_code,

        "headers": {
            "Content-Type":
                "application/json",

            "Access-Control-Allow-Origin":
                "*",

            "Access-Control-Allow-Headers":
                "Content-Type",

            "Access-Control-Allow-Methods":
                "POST,OPTIONS"
        },

        "body":
            json.dumps(
                body,
                ensure_ascii=False
            )
    }


def parse_body(event):
    body = event.get("body")

    if body is None:
        return event

    if isinstance(body, dict):
        return body

    if isinstance(body, str):
        if not body.strip():
            return {}

        try:
            return json.loads(body)

        except json.JSONDecodeError as error:
            raise ValueError(
                "Il body della richiesta "
                "non contiene un JSON valido"
            ) from error

    raise ValueError(
        "Formato body non valido"
    )


def resolve_event_ids(event):
    body = parse_body(event)

    requested_event_id = body.get(
        "eventId"
    )

    if requested_event_id is None:
        raw_uuid = str(
            uuid.uuid4()
        )

        return (
            f"camera-{raw_uuid}",
            raw_uuid
        )

    if not isinstance(
        requested_event_id,
        str
    ):
        raise ValueError(
            "eventId deve essere una stringa"
        )

    event_id = (
        requested_event_id.strip()
    )

    if not EVENT_ID_PATTERN.fullmatch(
        event_id
    ):
        raise ValueError(
            "eventId non valido: deve iniziare "
            "con 'camera-' e contenere soltanto "
            "lettere, numeri, trattini o underscore"
        )

    # Manteniamo testId per compatibilità con
    # lambdaIngestion e StartWorkflow già esistenti.
    test_id = event_id.removeprefix(
        "camera-"
    )

    return (
        event_id,
        test_id
    )


def generate_selected_image_url(
    image_key
):
    return s3.generate_presigned_url(
        ClientMethod="get_object",

        Params={
            "Bucket":
                BUCKET,

            "Key":
                image_key
        },

        ExpiresIn=
            PRESIGNED_URL_EXPIRATION
    )


def lambda_handler(event, context):
    print(
        "CAMERA SIMULATOR STARTED"
    )

    print(
        json.dumps(
            event,
            ensure_ascii=False
        )
    )

    try:
        event_id, test_id = (
            resolve_event_ids(event)
        )

        images = get_dataset_images()

        if not images:
            return create_response(
                404,
                {
                    "status":
                        "DATASET_EMPTY",

                    "message":
                        "Nessuna immagine trovata "
                        "nel dataset",

                    "bucket":
                        BUCKET,

                    "prefix":
                        DATASET_PREFIX
                }
            )

        selected_image = random.choice(
            images
        )

        selected_camera = random.choice(
            CAMERAS
        )

        selected_image_name = (
            PurePosixPath(
                selected_image
            ).name
        )

        selected_image_url = (
            generate_selected_image_url(
                selected_image
            )
        )

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        mqtt_message = {
            # Identificativo usato dall'app
            # e dagli aggiornamenti WebSocket.
            "eventId":
                event_id,

            # Campo mantenuto per compatibilità
            # con il vecchio ramo telecamera.
            "testId":
                test_id,

            "cameraId":
                selected_camera[
                    "cameraId"
                ],

            "location":
                selected_camera[
                    "location"
                ],

            "datasetBucket":
                BUCKET,

            "datasetKey":
                selected_image,

            "timestamp":
                timestamp,

            "source":
                "camera"
        }

        mqtt_payload = json.dumps(
            mqtt_message,
            separators=(",", ":"),
            ensure_ascii=False
        ).encode("utf-8")

        iot_data.publish(
            topic=TOPIC,
            qos=1,
            payload=mqtt_payload
        )

        print(
            "IMAGE SELECTED"
        )

        print(
            selected_image
        )

        print(
            "MQTT MESSAGE PUBLISHED"
        )

        print(
            json.dumps(
                mqtt_message,
                ensure_ascii=False
            )
        )

        return create_response(
            202,
            {
                "status":
                    "CAMERA_TEST_ACCEPTED",

                "message":
                    "Test telecamera avviato",

                "eventId":
                    event_id,

                "testId":
                    test_id,

                "cameraId":
                    selected_camera[
                        "cameraId"
                    ],

                "location":
                    selected_camera[
                        "location"
                    ],

                "selectedImageName":
                    selected_image_name,

                "selectedImageKey":
                    selected_image,

                "selectedImageUrl":
                    selected_image_url,

                "selectedImageExpiresIn":
                    PRESIGNED_URL_EXPIRATION
            }
        )

    except ValueError as error:
        print(
            f"INVALID REQUEST: {error}"
        )

        return create_response(
            400,
            {
                "status":
                    "INVALID_REQUEST",

                "message":
                    str(error)
            }
        )

    except ClientError as error:
        error_code = (
            error.response
            .get("Error", {})
            .get(
                "Code",
                "Unknown"
            )
        )

        print(
            f"AWS ERROR: {error}"
        )

        return create_response(
            500,
            {
                "status":
                    "AWS_ERROR",

                "message":
                    "Errore durante l'avvio "
                    "del test telecamera",

                "awsErrorCode":
                    error_code
            }
        )

    except Exception as error:
        print(
            f"UNEXPECTED ERROR: {error}"
        )

        return create_response(
            500,
            {
                "status":
                    "ERROR",

                "message":
                    "Errore interno durante "
                    "l'avvio del test telecamera"
            }
        )
