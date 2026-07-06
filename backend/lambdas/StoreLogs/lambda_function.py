import json
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

s3 = boto3.client("s3")


def lambda_handler(event, context):
    print("STORE LOGS RECEIVED")
    print(json.dumps(event))

    result = dict(event)
    decision = event.get("decision", {})

    if decision.get("status") != "COMPLETED":
        result["storeLogs"] = {
            "status": "SKIPPED",
            "reason": "DecisionLogic was not completed",
            "processedAt": datetime.now(timezone.utc).isoformat()
        }
        return result

    image_archive = decision.get("imageArchive", {})

    if (
        decision.get("shouldArchiveImage") is not True
        or image_archive.get("enabled") is not True
    ):
        result["storeLogs"] = {
            "status": "SKIPPED",
            "reason": image_archive.get(
                "reason",
                "No image associated with the event"
            ),
            "processedAt": datetime.now(timezone.utc).isoformat()
        }
        return result

    source_bucket = image_archive.get("sourceBucket")
    source_key = image_archive.get("sourceKey")
    destination_bucket = image_archive.get("destinationBucket")
    destination_key = image_archive.get("destinationKey")

    missing_fields = []

    if not source_bucket:
        missing_fields.append("sourceBucket")

    if not source_key:
        missing_fields.append("sourceKey")

    if not destination_bucket:
        missing_fields.append("destinationBucket")

    if not destination_key:
        missing_fields.append("destinationKey")

    if missing_fields:
        result["storeLogs"] = {
            "status": "FAILED",
            "reason": "Missing image archive fields",
            "missingFields": missing_fields,
            "processedAt": datetime.now(timezone.utc).isoformat()
        }
        return result

    try:
        response = s3.copy_object(
            CopySource={
                "Bucket": source_bucket,
                "Key": source_key
            },
            Bucket=destination_bucket,
            Key=destination_key,
            MetadataDirective="COPY"
        )

        copy_result = response.get("CopyObjectResult", {})

        result["storeLogs"] = {
            "status": "COMPLETED",
            "operation": "COPY_OBJECT",
            "source": {
                "bucket": source_bucket,
                "key": source_key
            },
            "destination": {
                "bucket": destination_bucket,
                "key": destination_key
            },
            "eTag": copy_result.get("ETag"),
            "lastModified": str(copy_result.get("LastModified")),
            "processedAt": datetime.now(timezone.utc).isoformat()
        }

        print("IMAGE ARCHIVE COMPLETED")
        print(json.dumps(result["storeLogs"]))

        return result

    except ClientError as error:
        error_details = error.response.get("Error", {})

        result["storeLogs"] = {
            "status": "FAILED",
            "reason": "S3 copy operation failed",
            "errorCode": error_details.get("Code"),
            "errorMessage": error_details.get("Message"),
            "source": {
                "bucket": source_bucket,
                "key": source_key
            },
            "destination": {
                "bucket": destination_bucket,
                "key": destination_key
            },
            "processedAt": datetime.now(timezone.utc).isoformat()
        }

        print("IMAGE ARCHIVE FAILED")
        print(json.dumps(result["storeLogs"]))

        return result