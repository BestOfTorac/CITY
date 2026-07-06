import json
import os
import time
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ.get(
    "TABLE_NAME",
    "WebSocketSubscriptions"
)

SUBSCRIPTION_TTL_SECONDS = int(
    os.environ.get(
        "SUBSCRIPTION_TTL_SECONDS",
        "7200"
    )
)

subscriptions_table = dynamodb.Table(
    TABLE_NAME
)


def get_management_api(event):
    request_context = event[
        "requestContext"
    ]

    domain_name = request_context[
        "domainName"
    ]

    stage = request_context[
        "stage"
    ]

    return boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=(
            f"https://{domain_name}/{stage}"
        )
    )


def send_message(
    event,
    connection_id,
    message
):
    management_api = get_management_api(
        event
    )

    management_api.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps(
            message,
            ensure_ascii=False
        ).encode("utf-8")
    )


def delete_connection(
    connection_id
):
    if not connection_id:
        return

    subscriptions_table.delete_item(
        Key={
            "connectionId":
                connection_id
        }
    )

    print(
        "CONNECTION REMOVED FROM TABLE"
    )

    print(
        json.dumps({
            "connectionId":
                connection_id
        })
    )


def save_subscription(
    event,
    connection_id,
    event_id
):
    request_context = event.get(
        "requestContext",
        {}
    )

    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        int(time.time())
        + SUBSCRIPTION_TTL_SECONDS
    )

    subscriptions_table.put_item(
        Item={
            "connectionId":
                connection_id,

            "eventId":
                event_id,

            "domainName":
                request_context.get(
                    "domainName"
                ),

            "stage":
                request_context.get(
                    "stage"
                ),

            "createdAt":
                now.isoformat(),

            # Numero UNIX usato dal TTL
            # di DynamoDB.
            "expiresAt":
                expires_at
        }
    )

    print(
        "SUBSCRIPTION SAVED"
    )

    print(
        json.dumps({
            "connectionId":
                connection_id,

            "eventId":
                event_id,

            "expiresAt":
                expires_at
        })
    )


def lambda_handler(
    event,
    context
):
    print(
        "WEBSOCKET EVENT RECEIVED"
    )

    print(
        json.dumps(
            event,
            ensure_ascii=False
        )
    )

    request_context = event.get(
        "requestContext",
        {}
    )

    route_key = request_context.get(
        "routeKey"
    )

    connection_id = (
        request_context.get(
            "connectionId"
        )
    )

    print(
        f"ROUTE: {route_key}"
    )

    print(
        f"CONNECTION ID: "
        f"{connection_id}"
    )

    # API Gateway esegue questa route
    # quando il client apre il WebSocket.
    if route_key == "$connect":
        print(
            "CLIENT CONNECTED"
        )

        return {
            "statusCode": 200
        }

    # Quando la connessione viene chiusa,
    # eliminiamo il record dalla tabella.
    if route_key == "$disconnect":
        try:
            delete_connection(
                connection_id
            )

        except ClientError as error:
            print(
                "DISCONNECT DELETE ERROR"
            )

            print(str(error))

        print(
            "CLIENT DISCONNECTED"
        )

        return {
            "statusCode": 200
        }

    try:
        raw_body = event.get(
            "body"
        ) or "{}"

        try:
            body = json.loads(
                raw_body
            )

        except json.JSONDecodeError:
            send_message(
                event,
                connection_id,
                {
                    "status":
                        "INVALID_REQUEST",

                    "message":
                        "Il messaggio non "
                        "contiene un JSON valido"
                }
            )

            return {
                "statusCode": 400
            }

        if route_key == "subscribe":
            event_id = body.get(
                "eventId"
            )

            if (
                not isinstance(
                    event_id,
                    str
                )
                or not event_id.strip()
            ):
                send_message(
                    event,
                    connection_id,
                    {
                        "status":
                            "INVALID_REQUEST",

                        "message":
                            "eventId mancante "
                            "o non valido"
                    }
                )

                return {
                    "statusCode": 400
                }

            event_id = event_id.strip()

            save_subscription(
                event=event,
                connection_id=
                    connection_id,
                event_id=event_id
            )

            send_message(
                event,
                connection_id,
                {
                    "status":
                        "SUBSCRIBED",

                    "eventId":
                        event_id,

                    "progress":
                        10,

                    "message":
                        "Sottoscrizione agli "
                        "aggiornamenti completata"
                }
            )

            return {
                "statusCode": 200
            }

        send_message(
            event,
            connection_id,
            {
                "status":
                    "UNKNOWN_ACTION",

                "message":
                    "Azione WebSocket "
                    "non riconosciuta"
            }
        )

        return {
            "statusCode": 200
        }

    except ClientError as error:
        error_code = (
            error.response
            .get(
                "Error",
                {}
            )
            .get(
                "Code",
                "Unknown"
            )
        )

        print(
            f"AWS ERROR: "
            f"{error_code}"
        )

        print(str(error))

        # La connessione potrebbe essere
        # giÃ  chiusa.
        if error_code == (
            "GoneException"
        ):
            delete_connection(
                connection_id
            )

            return {
                "statusCode": 410
            }

        return {
            "statusCode": 500
        }

    except Exception as error:
        print(
            "UNEXPECTED ERROR"
        )

        print(str(error))

        return {
            "statusCode": 500
        }