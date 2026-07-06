import json
import os
import re
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


stepfunctions = boto3.client("stepfunctions")

STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]

DEFAULT_BUCKET = os.environ.get(
    "DEFAULT_BUCKET",
    "emergency-images-camera"
)


def normalize_labels(labels):
    normalized = []

    if not isinstance(labels, list):
        return normalized

    for label in labels:
        if not isinstance(label, dict):
            continue

        name = (
            label.get("name")
            or label.get("Name")
        )

        confidence = (
            label.get("confidence")
            if "confidence" in label
            else label.get("Confidence")
        )

        if (
            not isinstance(name, str)
            or not name.strip()
        ):
            continue

        if (
            not isinstance(
                confidence,
                (int, float)
            )
            or isinstance(
                confidence,
                bool
            )
        ):
            continue

        normalized.append({
            "name": name.strip(),
            "confidence": round(
                float(confidence),
                2
            )
        })

    return normalized


def normalize_confidence(value):
    if (
        not isinstance(
            value,
            (int, float)
        )
        or isinstance(
            value,
            bool
        )
    ):
        return 0.0

    return round(
        float(value),
        2
    )


def is_user_report(body):
    source = str(
        body.get(
            "source",
            ""
        )
    ).strip().lower()

    report_origin = str(
        body.get(
            "reportOrigin",
            ""
        )
    ).strip().lower()

    return (
        source in {
            "mobile",
            "form",
            "user"
        }
        or report_origin == "user"
        or body.get("isUserReport") is True
    )


def build_execution_name(
    message_id,
    source
):
    clean_id = re.sub(
        r"[^A-Za-z0-9-_]",
        "-",
        str(message_id)
    )

    prefix = (
        "mobile"
        if source == "mobile"
        else "camera"
    )

    return (
        f"{prefix}-{clean_id}"
    )[:80]


def get_common_values(
    body,
    message_id
):
    event_id = (
        body.get("eventId")
        or body.get("testId")
        or f"event-{message_id}"
    )

    timestamp = (
        body.get("timestamp")
        or body.get("capturedAt")
        or datetime.now(
            timezone.utc
        ).isoformat()
    )

    location = (
        body.get("location")
        or body.get("cameraLocation")
        or "Posizione non specificata"
    )

    return (
        str(event_id),
        timestamp,
        location
    )


def build_camera_workflow_input(
    body,
    message_id
):
    labels = normalize_labels(
        body.get(
            "labels",
            []
        )
    )

    (
        event_id,
        timestamp,
        location
    ) = get_common_values(
        body,
        message_id
    )

    camera_id = (
        body.get("cameraId")
        or "UNKNOWN_CAMERA"
    )

    bucket = (
        body.get("bucket")
        or body.get("imageBucket")
        or body.get("datasetBucket")
        or DEFAULT_BUCKET
    )

    image_key = (
        body.get("imageKey")
        or body.get("imageName")
        or body.get("key")
    )

    event_type = str(
        body.get(
            "eventType",
            body.get(
                "type",
                "unknown"
            )
        )
    ).strip().lower()

    confidence = normalize_confidence(
        body.get(
            "confidence",
            0
        )
    )

    if (
        not isinstance(
            image_key,
            str
        )
        or not image_key
    ):
        raise ValueError(
            "Il messaggio della telecamera "
            "non contiene imageKey o imageName"
        )

    if not labels:
        raise ValueError(
            "Il messaggio della telecamera "
            "non contiene labels valide"
        )

    return {
        "eventId": event_id,
        "source": "camera",
        "timestamp": timestamp,
        "location": location,

        "cameraData": {
            "cameraId": camera_id,
            "bucket": bucket,
            "imageKey": image_key,
            "labels": labels
        },

        "preliminaryDetection": {
            "type": event_type,
            "confidence": confidence
        }
    }


def build_mobile_workflow_input(
    body,
    message_id
):
    (
        event_id,
        timestamp,
        location
    ) = get_common_values(
        body,
        message_id
    )

    labels = normalize_labels(
        body.get(
            "labels",
            []
        )
    )

    visual_analysis = body.get(
        "visualAnalysis"
    )

    if isinstance(
        visual_analysis,
        dict
    ):
        visual_labels = normalize_labels(
            visual_analysis.get(
                "labels",
                []
            )
        )

        if visual_labels:
            labels = visual_labels

        detected_type = str(
            visual_analysis.get(
                "eventType",
                body.get(
                    "eventType",
                    "unknown"
                )
            )
        ).strip().lower()

        confidence = normalize_confidence(
            visual_analysis.get(
                "confidence",
                body.get(
                    "confidence",
                    0
                )
            )
        )

    else:
        detected_type = str(
            body.get(
                "eventType",
                "unknown"
            )
        ).strip().lower()

        confidence = normalize_confidence(
            body.get(
                "confidence",
                0
            )
        )

    raw_image_data = body.get(
        "imageData"
    )

    if not isinstance(
        raw_image_data,
        dict
    ):
        raw_image_data = {}

    bucket = (
        raw_image_data.get("bucket")
        or body.get("bucket")
        or body.get("imageBucket")
        or DEFAULT_BUCKET
    )

    image_key = (
        raw_image_data.get("imageKey")
        or body.get("imageKey")
        or body.get("imageName")
    )

    content_type = (
        raw_image_data.get(
            "contentType"
        )
        or body.get(
            "contentType"
        )
    )

    original_file_name = (
        raw_image_data.get(
            "originalFileName"
        )
        or body.get(
            "imageName"
        )
    )

    workflow_input = {
        "eventId": event_id,

        # Origine reale della segnalazione.
        "source": "mobile",
        "reportOrigin": "user",
        "isUserReport": True,

        "timestamp": timestamp,
        "location": location,

        # Informazioni inserite
        # manualmente dall'utente.
        "description": body.get(
            "description",
            ""
        ),

        "reportedType": body.get(
            "reportedType",
            "UNKNOWN"
        ),

        "injured": body.get(
            "injured",
            "UNKNOWN"
        ),

        "immediateDanger": body.get(
            "immediateDanger",
            "UNKNOWN"
        ),

        "userReport": {
            "description": body.get(
                "description",
                ""
            ),

            "reportedType": body.get(
                "reportedType",
                "UNKNOWN"
            ),

            "injured": body.get(
                "injured",
                "UNKNOWN"
            ),

            "immediateDanger": body.get(
                "immediateDanger",
                "UNKNOWN"
            )
        },

        # Risultato dell'analisi della
        # fotografia caricata dall'utente.
        "visualAnalysis": {
            "eventType": detected_type,
            "confidence": confidence,
            "labels": labels,
            "analysisSource":
                "user_uploaded_image"
        },

        # Conservato per compatibilità
        # con classificazione e gravità.
        "preliminaryDetection": {
            "type": detected_type,
            "confidence": confidence
        }
    }

    if image_key:
        workflow_input["imageData"] = {
            "bucket": bucket,
            "imageKey": image_key,
            "contentType": content_type,
            "originalFileName":
                original_file_name,
            "labels": labels
        }

    return workflow_input


def build_workflow_input(
    body,
    message_id
):
    if not isinstance(
        body,
        dict
    ):
        raise ValueError(
            "Il body SQS deve essere "
            "un oggetto JSON"
        )

    if is_user_report(body):
        return build_mobile_workflow_input(
            body,
            message_id
        )

    return build_camera_workflow_input(
        body,
        message_id
    )


def lambda_handler(event, context):
    print("START WORKFLOW RECEIVED")

    print(
        json.dumps(
            event,
            ensure_ascii=False
        )
    )

    batch_failures = []

    for record in event.get(
        "Records",
        []
    ):
        message_id = record.get(
            "messageId",
            "unknown-message"
        )

        try:
            body = json.loads(
                record.get(
                    "body",
                    "{}"
                )
            )

            workflow_input = (
                build_workflow_input(
                    body,
                    message_id
                )
            )

            source = workflow_input.get(
                "source",
                "camera"
            )

            execution_name = (
                build_execution_name(
                    message_id,
                    source
                )
            )

            print(
                "WORKFLOW INPUT"
            )

            print(
                json.dumps(
                    workflow_input,
                    ensure_ascii=False
                )
            )

            response = (
                stepfunctions
                .start_execution(
                    stateMachineArn=
                        STATE_MACHINE_ARN,

                    name=
                        execution_name,

                    input=json.dumps(
                        workflow_input,
                        ensure_ascii=False
                    )
                )
            )

            print(
                "WORKFLOW STARTED"
            )

            print(
                json.dumps(
                    {
                        "messageId":
                            message_id,

                        "eventId":
                            workflow_input[
                                "eventId"
                            ],

                        "source":
                            source,

                        "executionName":
                            execution_name,

                        "executionArn":
                            response[
                                "executionArn"
                            ]
                    },
                    ensure_ascii=False
                )
            )

        except ClientError as error:
            error_code = (
                error.response
                .get(
                    "Error",
                    {}
                )
                .get("Code")
            )

            # SQS può consegnare nuovamente
            # lo stesso messaggio.
            if (
                error_code ==
                "ExecutionAlreadyExists"
            ):
                print(
                    "Execution already exists "
                    f"for message {message_id}"
                )
                continue

            print(
                f"AWS ERROR FOR "
                f"{message_id}: "
                f"{str(error)}"
            )

            batch_failures.append({
                "itemIdentifier":
                    message_id
            })

        except (
            ValueError,
            TypeError,
            json.JSONDecodeError
        ) as error:
            print(
                f"INVALID MESSAGE "
                f"{message_id}: "
                f"{str(error)}"
            )

            batch_failures.append({
                "itemIdentifier":
                    message_id
            })

        except Exception as error:
            print(
                f"UNEXPECTED ERROR "
                f"{message_id}: "
                f"{str(error)}"
            )

            batch_failures.append({
                "itemIdentifier":
                    message_id
            })

    return {
        "batchItemFailures":
            batch_failures
    }