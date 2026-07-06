import json
from datetime import datetime, timezone
from numbers import Number


ALLOWED_SOURCES = {
    "camera",
    "form",
    "lex",
    "mobile"
}

ALLOWED_REPORTED_TYPES = {
    "FIRE",
    "ACCIDENT",
    "UNKNOWN"
}

TRI_STATE_VALUES = {
    "YES",
    "NO",
    "UNKNOWN"
}


def is_non_empty_string(value):
    return (
        isinstance(value, str)
        and bool(value.strip())
    )


def normalize_upper(value):
    if not isinstance(value, str):
        return None

    return value.strip().upper()


def validate_timestamp(value):
    if not isinstance(value, str):
        return False

    try:
        datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00"
            )
        )

        return True

    except ValueError:
        return False


def validate_tri_state(
    value,
    field_name,
    errors
):
    normalized_value = normalize_upper(
        value
    )

    if normalized_value not in TRI_STATE_VALUES:
        errors.append(
            f"{field_name} must be "
            "YES, NO or UNKNOWN"
        )


def validate_confidence(
    value,
    field_name,
    errors
):
    if (
        isinstance(value, bool)
        or not isinstance(
            value,
            Number
        )
    ):
        errors.append(
            f"{field_name} must be numeric"
        )

        return

    if not 0 <= float(value) <= 100:
        errors.append(
            f"{field_name} must be "
            "between 0 and 100"
        )


def validate_labels(
    labels,
    field_name,
    errors,
    allow_empty=False
):
    if not isinstance(labels, list):
        errors.append(
            f"{field_name} must be a list"
        )

        return

    if not labels and not allow_empty:
        errors.append(
            f"{field_name} cannot be empty"
        )

        return

    for index, label in enumerate(labels):
        field_prefix = (
            f"{field_name}[{index}]"
        )

        if not isinstance(label, dict):
            errors.append(
                f"{field_prefix} must be "
                "an object"
            )

            continue

        if not is_non_empty_string(
            label.get("name")
        ):
            errors.append(
                f"{field_prefix}.name "
                "is required"
            )

        validate_confidence(
            label.get("confidence"),
            f"{field_prefix}.confidence",
            errors
        )


def validate_preliminary_detection(
    preliminary_detection,
    field_name,
    errors,
    required=False
):
    if preliminary_detection is None:
        if required:
            errors.append(
                f"{field_name} is required"
            )

        return

    if not isinstance(
        preliminary_detection,
        dict
    ):
        errors.append(
            f"{field_name} must be "
            "an object"
        )

        return

    detection_type = (
        preliminary_detection.get(
            "type"
        )
    )

    if (
        detection_type is not None
        and not is_non_empty_string(
            detection_type
        )
    ):
        errors.append(
            f"{field_name}.type "
            "must be a string"
        )

    if (
        "confidence"
        in preliminary_detection
    ):
        validate_confidence(
            preliminary_detection.get(
                "confidence"
            ),
            f"{field_name}.confidence",
            errors
        )


def validate_camera_event(
    event,
    errors
):
    camera_data = event.get(
        "cameraData"
    )

    if not isinstance(
        camera_data,
        dict
    ):
        errors.append(
            "cameraData is required "
            "for camera events"
        )

        return

    required_string_fields = [
        "cameraId",
        "bucket",
        "imageKey"
    ]

    for field in required_string_fields:
        if not is_non_empty_string(
            camera_data.get(field)
        ):
            errors.append(
                f"cameraData.{field} "
                "is required"
            )

    validate_labels(
        labels=camera_data.get(
            "labels"
        ),
        field_name=
            "cameraData.labels",
        errors=errors
    )

    validate_preliminary_detection(
        preliminary_detection=
            event.get(
                "preliminaryDetection"
            ),
        field_name=
            "preliminaryDetection",
        errors=errors,
        required=False
    )


def validate_people_section(
    people,
    errors
):
    if not isinstance(people, dict):
        errors.append(
            "report.people is required"
        )

        return

    for field in [
        "injured",
        "unresponsive",
        "trapped"
    ]:
        validate_tri_state(
            people.get(field),
            f"report.people.{field}",
            errors
        )


def validate_danger_section(
    danger,
    errors
):
    if not isinstance(danger, dict):
        errors.append(
            "report.danger is required"
        )

        return

    validate_tri_state(
        danger.get("immediate"),
        "report.danger.immediate",
        errors
    )


def validate_optional_tri_state_section(
    section,
    section_name,
    allowed_fields,
    errors
):
    if section is None:
        return

    if not isinstance(section, dict):
        errors.append(
            f"{section_name} must be "
            "an object"
        )

        return

    for field in allowed_fields:
        if field in section:
            validate_tri_state(
                section.get(field),
                f"{section_name}.{field}",
                errors
            )


def validate_accident_details(
    details,
    errors
):
    if details is None:
        return

    if not isinstance(details, dict):
        errors.append(
            "report.accidentDetails "
            "must be an object"
        )

        return

    vehicles_count = details.get(
        "vehiclesCount"
    )

    if vehicles_count is not None:
        if (
            isinstance(
                vehicles_count,
                bool
            )
            or not isinstance(
                vehicles_count,
                int
            )
            or vehicles_count < 0
        ):
            errors.append(
                "report.accidentDetails."
                "vehiclesCount must be "
                "a non-negative integer"
            )

    for field in [
        "vehicleOverturned",
        "roadBlocked",
        "fuelLeak",
        "debrisPresent"
    ]:
        if field in details:
            validate_tri_state(
                details.get(field),
                (
                    "report.accidentDetails."
                    f"{field}"
                ),
                errors
            )


def validate_human_report(
    report,
    errors
):
    if not isinstance(report, dict):
        errors.append(
            "report is required for "
            "human reports"
        )

        return

    reported_type = normalize_upper(
        report.get("reportedType")
    )

    if (
        reported_type
        not in ALLOWED_REPORTED_TYPES
    ):
        errors.append(
            "report.reportedType must be "
            "FIRE, ACCIDENT or UNKNOWN"
        )

    description = report.get(
        "description"
    )

    if not is_non_empty_string(
        description
    ):
        errors.append(
            "report.description is required"
        )

    validate_people_section(
        report.get("people"),
        errors
    )

    validate_danger_section(
        report.get("danger"),
        errors
    )

    validate_optional_tri_state_section(
        section=report.get(
            "fireDetails"
        ),
        section_name=
            "report.fireDetails",
        allowed_fields=[
            "flamesVisible",
            "smokeVisible",
            "spreading",
            "buildingInvolved",
            "vehicleOnFire",
            "explosionReported"
        ],
        errors=errors
    )

    validate_accident_details(
        report.get(
            "accidentDetails"
        ),
        errors
    )


def build_mobile_report(event):
    user_report = event.get(
        "userReport"
    )

    if not isinstance(
        user_report,
        dict
    ):
        user_report = {}

    reported_type = (
        user_report.get(
            "reportedType"
        )
        or event.get(
            "reportedType"
        )
        or "UNKNOWN"
    )

    description = (
        user_report.get(
            "description"
        )
        or event.get(
            "description"
        )
        or ""
    )

    injured = (
        user_report.get(
            "injured"
        )
        or event.get(
            "injured"
        )
        or "UNKNOWN"
    )

    immediate_danger = (
        user_report.get(
            "immediateDanger"
        )
        or event.get(
            "immediateDanger"
        )
        or "UNKNOWN"
    )

    report = {
        "reportedType":
            normalize_upper(
                reported_type
            )
            or "UNKNOWN",

        "description":
            description,

        "people": {
            "injured":
                normalize_upper(
                    injured
                )
                or "UNKNOWN",

            # L'app per ora non chiede
            # questi due campi.
            "unresponsive":
                "UNKNOWN",

            "trapped":
                "UNKNOWN"
        },

        "danger": {
            "immediate":
                normalize_upper(
                    immediate_danger
                )
                or "UNKNOWN"
        }
    }

    if isinstance(
        user_report.get(
            "fireDetails"
        ),
        dict
    ):
        report["fireDetails"] = (
            user_report[
                "fireDetails"
            ]
        )

    if isinstance(
        user_report.get(
            "accidentDetails"
        ),
        dict
    ):
        report[
            "accidentDetails"
        ] = user_report[
            "accidentDetails"
        ]

    return report


def validate_mobile_image(
    event,
    errors
):
    image_data = event.get(
        "imageData"
    )

    visual_analysis = event.get(
        "visualAnalysis"
    )

    # La fotografia Ã¨ facoltativa.
    if image_data is None:
        if visual_analysis is not None:
            errors.append(
                "visualAnalysis cannot be "
                "present without imageData"
            )

        return

    if not isinstance(
        image_data,
        dict
    ):
        errors.append(
            "imageData must be an object"
        )

        return

    for field in [
        "bucket",
        "imageKey"
    ]:
        if not is_non_empty_string(
            image_data.get(field)
        ):
            errors.append(
                f"imageData.{field} "
                "is required"
            )

    content_type = image_data.get(
        "contentType"
    )

    if (
        content_type is not None
        and not is_non_empty_string(
            content_type
        )
    ):
        errors.append(
            "imageData.contentType "
            "must be a string"
        )

    if visual_analysis is None:
        errors.append(
            "visualAnalysis is required "
            "when imageData is present"
        )

        return

    if not isinstance(
        visual_analysis,
        dict
    ):
        errors.append(
            "visualAnalysis must be "
            "an object"
        )

        return

    event_type = visual_analysis.get(
        "eventType"
    )

    if not is_non_empty_string(
        event_type
    ):
        errors.append(
            "visualAnalysis.eventType "
            "is required"
        )

    validate_confidence(
        visual_analysis.get(
            "confidence"
        ),
        (
            "visualAnalysis."
            "confidence"
        ),
        errors
    )

    validate_labels(
        labels=visual_analysis.get(
            "labels"
        ),
        field_name=
            "visualAnalysis.labels",
        errors=errors,
        allow_empty=True
    )


def validate_mobile_event(
    event,
    errors
):
    report = build_mobile_report(
        event
    )

    validate_human_report(
        report,
        errors
    )

    validate_mobile_image(
        event,
        errors
    )

    validate_preliminary_detection(
        preliminary_detection=
            event.get(
                "preliminaryDetection"
            ),
        field_name=
            "preliminaryDetection",
        errors=errors,
        required=False
    )

    return report


def lambda_handler(
    event,
    context
):
    print(
        "VALIDATE EVENT RECEIVED"
    )

    print(
        json.dumps(
            event,
            ensure_ascii=False
        )
    )

    errors = []

    if not isinstance(event, dict):
        return {
            "validation": {
                "valid": False,
                "errors": [
                    "The input event must "
                    "be a JSON object"
                ],
                "validatedAt":
                    datetime.now(
                        timezone.utc
                    ).isoformat()
            }
        }

    if not is_non_empty_string(
        event.get("eventId")
    ):
        errors.append(
            "eventId is required"
        )

    source = (
        event.get(
            "source",
            ""
        ).strip().lower()
        if isinstance(
            event.get("source"),
            str
        )
        else ""
    )

    if source not in ALLOWED_SOURCES:
        errors.append(
            "source must be camera, "
            "form, lex or mobile"
        )

    if not is_non_empty_string(
        event.get("location")
    ):
        errors.append(
            "location is required"
        )

    if not validate_timestamp(
        event.get("timestamp")
    ):
        errors.append(
            "timestamp must be a valid "
            "ISO-8601 string"
        )

    normalized_report = None

    if source == "camera":
        validate_camera_event(
            event,
            errors
        )

    elif source in {
        "form",
        "lex"
    }:
        validate_human_report(
            event.get("report"),
            errors
        )

    elif source == "mobile":
        normalized_report = (
            validate_mobile_event(
                event,
                errors
            )
        )

    validated_event = dict(event)

    # Per il mobile aggiungiamo anche
    # il formato report standard usato
    # dagli altri eventi umani.
    if normalized_report is not None:
        validated_event[
            "report"
        ] = normalized_report

        validated_event[
            "source"
        ] = "mobile"

        validated_event[
            "reportOrigin"
        ] = "user"

        validated_event[
            "isUserReport"
        ] = True

    validated_event["validation"] = {
        "valid":
            len(errors) == 0,

        "errors":
            errors,

        "validatedAt":
            datetime.now(
                timezone.utc
            ).isoformat()
    }

    print(
        "VALIDATION RESULT"
    )

    print(
        json.dumps(
            validated_event[
                "validation"
            ],
            ensure_ascii=False
        )
    )

    return validated_event