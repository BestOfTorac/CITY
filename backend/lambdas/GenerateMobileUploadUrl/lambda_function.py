import base64
import json
import os
import re
import uuid

import boto3
from botocore.config import Config


BUCKET = os.environ.get(
    "BUCKET",
    "emergency-images-camera"
)

PREFIX = os.environ.get(
    "PREFIX",
    "mobile/"
).strip("/")

EXPIRATION_SECONDS = int(
    os.environ.get(
        "URL_EXPIRATION_SECONDS",
        "300"
    )
)

AWS_REGION = os.environ.get(
    "AWS_REGION",
    "us-east-1"
)


s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    config=Config(
        signature_version="s3v4",
        s3={
            "addressing_style": "virtual"
        }
    )
)


ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png"
}

EVENT_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9_-]{1,80}$"
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


def parse_body(event):
    body = event.get("body")

    # Test diretto dalla console Lambda
    if body is None:
        return event

    if (
        event.get("isBase64Encoded")
        and isinstance(body, str)
    ):
        body = base64.b64decode(
            body
        ).decode("utf-8")

    if isinstance(body, str):
        body = json.loads(body)

    if not isinstance(body, dict):
        raise ValueError(
            "Il body deve essere un oggetto JSON"
        )

    return body


def lambda_handler(event, context):
    print("GENERATE MOBILE UPLOAD URL")
    print(
        json.dumps(
            event,
            ensure_ascii=False
        )[:3000]
    )

    try:
        request_context = event.get(
            "requestContext",
            {}
        )

        http_method = (
            request_context
            .get("http", {})
            .get("method")
            or event.get("httpMethod")
        )

        if http_method == "OPTIONS":
            return build_response(
                204,
                {}
            )

        body = parse_body(event)

        event_id = str(
            body.get("eventId", "")
        ).strip()

        file_name = str(
            body.get("fileName", "")
        ).strip()

        content_type = str(
            body.get("contentType", "")
        ).strip().lower()

        if not EVENT_ID_PATTERN.fullmatch(
            event_id
        ):
            return build_response(
                400,
                {
                    "status": "INVALID_EVENT_ID",
                    "message": (
                        "eventId assente o non valido"
                    )
                }
            )

        if not file_name:
            return build_response(
                400,
                {
                    "status": "INVALID_FILE",
                    "message": "fileName è obbligatorio"
                }
            )

        extension = ALLOWED_CONTENT_TYPES.get(
            content_type
        )

        if not extension:
            return build_response(
                400,
                {
                    "status": "INVALID_CONTENT_TYPE",
                    "message": (
                        "Sono consentite soltanto "
                        "immagini JPEG e PNG"
                    )
                }
            )

        image_id = uuid.uuid4().hex

        image_key = (
            f"{PREFIX}/"
            f"{event_id}-{image_id}{extension}"
        )

        upload_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET,
                "Key": image_key,
                "ContentType": content_type
            },
            ExpiresIn=EXPIRATION_SECONDS,
            HttpMethod="PUT"
        )

        response_body = {
            "status": "READY",
            "eventId": event_id,
            "uploadUrl": upload_url,
            "uploadHeaders": {
                "Content-Type": content_type
            },
            "imageData": {
                "bucket": BUCKET,
                "imageKey": image_key,
                "contentType": content_type,
                "originalFileName": file_name
            },
            "expiresIn": EXPIRATION_SECONDS
        }

        print("UPLOAD URL GENERATED")
        print(
            json.dumps(
                {
                    "eventId": event_id,
                    "imageKey": image_key
                }
            )
        )

        return build_response(
            200,
            response_body
        )

    except json.JSONDecodeError:
        return build_response(
            400,
            {
                "status": "INVALID_JSON",
                "message": (
                    "Il body non contiene "
                    "un JSON valido"
                )
            }
        )

    except ValueError as error:
        return build_response(
            400,
            {
                "status": "INVALID_REQUEST",
                "message": str(error)
            }
        )

    except Exception as error:
        print("UNEXPECTED ERROR")
        print(str(error))

        return build_response(
            500,
            {
                "status": "ERROR",
                "message": (
                    "Impossibile generare "
                    "l'URL di caricamento"
                )
            }
        )