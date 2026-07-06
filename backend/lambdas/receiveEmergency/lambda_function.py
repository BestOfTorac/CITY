import base64
import json
import os
import re
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


stepfunctions = boto3.client("stepfunctions")
lambda_client = boto3.client("lambda")

STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")

MOBILE_INGESTION_FUNCTION_NAME = os.environ.get(
    "MOBILE_INGESTION_FUNCTION_NAME"
)


CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "POST,OPTIONS"
}


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "isBase64Encoded": False,
        "body": json.dumps(
            body,
            ensure_ascii=False
        )
    }


def get_http_method(event):
    method = (
        event.get("requestContext", {})
        .get("http", {})
        .get("method")
    )

    if not method:
        method = event.get("httpMethod")

    return method


def parse_request_body(event):
    body = event.get("body")

    if body is None:
        raise ValueError(
            "Il body della richiesta è assente"
        )

    if (
        event.get("isBase64Encoded")
        and isinstance(body, str)
    ):
        body = base64.b64decode(
            body
        ).decode("utf-8")

    if isinstance(body, str):
        try:
            body = json.loads(body)

        except json.JSONDecodeError as error:
            raise ValueError(
                "Il body non contiene un JSON valido"
            ) from error

    if not isinstance(body, dict):
        raise ValueError(
            "Il body deve essere un oggetto JSON"
        )

    return body


def validate_report(request_body):
    location = request_body.get("location")
    description = request_body.get("description")

    if not location or not str(location).strip():
        raise ValueError(
            "Il campo location è obbligatorio"
        )

    if (
        not description
        or not str(description).strip()
    ):
        raise ValueError(
            "Il campo description è obbligatorio"
        )

    image_data = request_body.get("imageData")

    if image_data is None:
        return

    if not isinstance(image_data, dict):
        raise ValueError(
            "imageData deve essere un oggetto JSON"
        )

    bucket = image_data.get("bucket")
    image_key = image_data.get("imageKey")

    if not bucket:
        raise ValueError(
            "imageData.bucket è obbligatorio"
        )

    if not image_key:
        raise ValueError(
            "imageData.imageKey è obbligatorio"
        )

    # Impedisce di indicare file esterni
    # al percorso dedicato all'app mobile.
    if not str(image_key).startswith("mobile/"):
        raise ValueError(
            "L'immagine deve trovarsi nel percorso mobile/"
        )


def create_execution_name(event_id):
    sanitized_name = re.sub(
        r"[^A-Za-z0-9_-]",
        "-",
        str(event_id)
    )

    return sanitized_name[:80]


def start_workflow(workflow_input):
    event_id = workflow_input["eventId"]

    response = stepfunctions.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=create_execution_name(event_id),
        input=json.dumps(
            workflow_input,
            ensure_ascii=False
        )
    )

    return response["executionArn"]


def start_mobile_ingestion(workflow_input):
    if not MOBILE_INGESTION_FUNCTION_NAME:
        raise RuntimeError(
            "MOBILE_INGESTION_FUNCTION_NAME non configurata"
        )

    response = lambda_client.invoke(
        FunctionName=
            MOBILE_INGESTION_FUNCTION_NAME,
        InvocationType="Event",
        Payload=json.dumps(
            workflow_input,
            ensure_ascii=False
        ).encode("utf-8")
    )

    status_code = response.get(
        "StatusCode"
    )

    if status_code != 202:
        raise RuntimeError(
            "Impossibile avviare MobileIngestion"
        )


def lambda_handler(event, context):
    print("RECEIVE EMERGENCY RECEIVED")
    print(
        json.dumps(
            event,
            ensure_ascii=False
        )[:3000]
    )

    method = get_http_method(event)

    if method == "OPTIONS":
        return build_response(
            204,
            {}
        )

    if method != "POST":
        return build_response(
            405,
            {
                "status": "METHOD_NOT_ALLOWED",
                "message": "Metodo non consentito"
            }
        )

    if not STATE_MACHINE_ARN:
        print("STATE_MACHINE_ARN missing")

        return build_response(
            500,
            {
                "status": "ERROR",
                "message":
                    "Configurazione della Lambda incompleta"
            }
        )

    try:
        request_body = parse_request_body(
            event
        )

        validate_report(
            request_body
        )

        event_id = request_body.get(
            "eventId"
        )

        if not event_id:
            event_id = (
                f"mobile-{uuid.uuid4()}"
            )

        timestamp = request_body.get(
            "timestamp"
        )

        if not timestamp:
            timestamp = datetime.now(
                timezone.utc
            ).isoformat()

        workflow_input = dict(
            request_body
        )

        workflow_input["eventId"] = (
            event_id
        )

        workflow_input["source"] = (
            "mobile"
        )

        workflow_input["timestamp"] = (
            timestamp
        )

        image_data = workflow_input.get(
            "imageData"
        )

        # Caso 1: segnalazione con fotografia
        if image_data:
            start_mobile_ingestion(
                workflow_input
            )

            print(
                "MOBILE INGESTION STARTED"
            )

            return build_response(
                202,
                {
                    "status": "ACCEPTED",
                    "message":
                        "Segnalazione ricevuta. "
                        "Analisi dell'immagine avviata.",
                    "eventId": event_id,
                    "pipeline":
                        "MOBILE_INGESTION"
                }
            )

        # Caso 2: segnalazione senza fotografia
        execution_arn = start_workflow(
            workflow_input
        )

        print("WORKFLOW STARTED")
        print(
            json.dumps(
                {
                    "eventId": event_id,
                    "executionArn":
                        execution_arn
                }
            )
        )

        return build_response(
            202,
            {
                "status": "ACCEPTED",
                "message":
                    "Segnalazione ricevuta "
                    "e workflow avviato",
                "eventId": event_id,
                "executionArn":
                    execution_arn,
                "pipeline":
                    "DIRECT_WORKFLOW"
            }
        )

    except ValueError as error:
        print(
            f"INVALID REQUEST: {error}"
        )

        return build_response(
            400,
            {
                "status":
                    "INVALID_REQUEST",
                "message": str(error)
            }
        )

    except (
        stepfunctions
        .exceptions
        .ExecutionAlreadyExists
    ):
        print(
            "EXECUTION ALREADY EXISTS"
        )

        return build_response(
            409,
            {
                "status":
                    "DUPLICATE_EVENT",
                "message":
                    "Esiste già un'esecuzione "
                    "per questo eventId"
            }
        )

    except ClientError as error:
        print("AWS ERROR")
        print(str(error))

        error_code = (
            error.response
            .get("Error", {})
            .get(
                "Code",
                "Unknown"
            )
        )

        return build_response(
            500,
            {
                "status": "AWS_ERROR",
                "message":
                    "Errore durante l'avvio "
                    "dell'elaborazione",
                "awsErrorCode":
                    error_code
            }
        )

    except Exception as error:
        print("UNEXPECTED ERROR")
        print(str(error))

        return build_response(
            500,
            {
                "status": "ERROR",
                "message":
                    "Errore interno durante "
                    "la ricezione dell'emergenza"
            }
        )