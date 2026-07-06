import json
import os

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


TABLE_NAME = os.environ.get(
    "TABLE_NAME",
    "WebSocketSubscriptions"
)

EVENT_ID_INDEX = os.environ.get(
    "EVENT_ID_INDEX",
    "eventId-index"
)

WEBSOCKET_ENDPOINT = os.environ.get(
    "WEBSOCKET_ENDPOINT",
    "https://k0jbltzn00.execute-api.us-east-1.amazonaws.com/production"
)

dynamodb = boto3.resource("dynamodb")
subscriptions_table = dynamodb.Table(TABLE_NAME)

management_api = boto3.client(
    "apigatewaymanagementapi",
    endpoint_url=WEBSOCKET_ENDPOINT
)


def validate_event(event):
    if not isinstance(event, dict):
        raise ValueError("L'input deve essere un oggetto JSON")

    event_id = event.get("eventId")
    status = event.get("status")
    message = event.get("message")
    progress = event.get("progress")

    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError("eventId è obbligatorio")

    if not isinstance(status, str) or not status.strip():
        raise ValueError("status è obbligatorio")

    if not isinstance(message, str) or not message.strip():
        raise ValueError("message è obbligatorio")

    if isinstance(progress, bool) or not isinstance(progress, (int, float)):
        raise ValueError("progress deve essere numerico")

    progress = int(progress)

    if not 0 <= progress <= 100:
        raise ValueError("progress deve essere compreso tra 0 e 100")

    return {
        "eventId": event_id.strip(),
        "status": status.strip(),
        "message": message.strip(),
        "progress": progress
    }


def find_subscriptions(event_id):
    response = subscriptions_table.query(
        IndexName=EVENT_ID_INDEX,
        KeyConditionExpression=Key("eventId").eq(event_id)
    )

    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = subscriptions_table.query(
            IndexName=EVENT_ID_INDEX,
            KeyConditionExpression=Key("eventId").eq(event_id),
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )

        items.extend(response.get("Items", []))

    return items


def delete_stale_connection(connection_id):
    subscriptions_table.delete_item(
        Key={"connectionId": connection_id}
    )

    print(f"STALE CONNECTION REMOVED: {connection_id}")


def send_to_connection(connection_id, payload):
    management_api.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps(
            payload,
            ensure_ascii=False
        ).encode("utf-8")
    )


def lambda_handler(event, context):
    print("SEND STATUS UPDATE RECEIVED")
    print(json.dumps(event, ensure_ascii=False))

    try:
        payload = validate_event(event)
        subscriptions = find_subscriptions(payload["eventId"])

        print(f"SUBSCRIPTIONS FOUND: {len(subscriptions)}")

        sent_count = 0
        removed_count = 0
        failed_count = 0

        for subscription in subscriptions:
            connection_id = subscription.get("connectionId")

            if not connection_id:
                continue

            try:
                send_to_connection(
                    connection_id,
                    payload
                )

                sent_count += 1
                print(f"UPDATE SENT TO {connection_id}")

            except management_api.exceptions.GoneException:
                print(f"CONNECTION GONE: {connection_id}")

                delete_stale_connection(
                    connection_id
                )

                removed_count += 1

            except ClientError as error:
                print(
                    f"ERROR SENDING TO {connection_id}: {str(error)}"
                )

                failed_count += 1

        result = {
            "status": "STATUS_UPDATE_PROCESSED",
            "eventId": payload["eventId"],
            "updateStatus": payload["status"],
            "progress": payload["progress"],
            "subscriptionsFound": len(subscriptions),
            "messagesSent": sent_count,
            "staleConnectionsRemoved": removed_count,
            "messagesFailed": failed_count
        }

        print("SEND STATUS UPDATE COMPLETED")
        print(json.dumps(result, ensure_ascii=False))

        return result

    except ValueError as error:
        print(f"INVALID UPDATE: {error}")

        return {
            "status": "INVALID_STATUS_UPDATE",
            "message": str(error)
        }

    except ClientError as error:
        print(f"AWS ERROR: {error}")
        raise

    except Exception as error:
        print(f"UNEXPECTED ERROR: {error}")
        raise
