import json
import re
import unicodedata
from datetime import datetime


FIRE_LABELS = {
    "fire",
    "flame",
    "smoke",
    "wildfire",
    "burning"
}

VEHICLE_LABELS = {
    "car",
    "vehicle",
    "automobile",
    "truck",
    "motorcycle",
    "bus"
}

ACCIDENT_LABELS = {
    "accident",
    "collision",
    "crash",
    "wreck",
    "wreckage",
    "damage",
    "debris"
}

PERSON_LABELS = {
    "person",
    "people",
    "human"
}

DESCRIPTION_KEYWORDS = {
    "fireMentioned": [
        "incendio",
        "fuoco",
        "fiamma",
        "fiamme",
        "brucia",
        "bruciando",
        "in fiamme"
    ],
    "smokeMentioned": [
        "fumo",
        "fumando",
        "odore di bruciato"
    ],
    "collisionMentioned": [
    "incidente",
    "scontro",
    "scontrato",
    "scontrata",
    "scontrati",
    "scontrate",
    "scontrarsi",
    "collisione",
    "tamponamento",
    "tamponato",
    "tamponata",
    "tamponati",
    "tamponate",
    "schianto",
    "schiantato",
    "schiantata"
    ],
    "injuryMentioned": [
        "ferito",
        "ferita",
        "feriti",
        "ferite",
        "sanguina",
        "sanguinamento"
    ],
    "unresponsiveMentioned": [
        "incosciente",
        "privo di sensi",
        "non risponde",
        "non reagisce"
    ],
    "trappedMentioned": [
        "intrappolato",
        "intrappolata",
        "intrappolati",
        "bloccato dentro",
        "non riesce a uscire"
    ],
    "vehicleMentioned": [
        "auto",
        "automobile",
        "macchina",
        "veicolo",
        "moto",
        "camion",
        "autobus"
    ],
    "explosionMentioned": [
        "esplosione",
        "esploso",
        "esplosa",
        "scoppio"
    ]
}


def normalize_text(value):
    if not isinstance(value, str):
        return ""

    normalized = value.lower().strip()

    normalized = unicodedata.normalize(
        "NFD",
        normalized
    )

    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )

    normalized = re.sub(
        r"[^a-z0-9\s]",
        " ",
        normalized
    )

    return re.sub(
        r"\s+",
        " ",
        normalized
    ).strip()


def tri_state_to_value(value):
    """
    Converte:
    YES     -> True
    NO      -> False
    UNKNOWN -> None
    """

    if not isinstance(value, str):
        return None

    normalized = value.strip().upper()

    if normalized == "YES":
        return True

    if normalized == "NO":
        return False

    return None


def extract_time_context(timestamp):
    try:
        parsed = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )

    except (AttributeError, ValueError):
        return {
            "valid": False
        }

    hour = parsed.hour

    if 5 <= hour < 12:
        day_period = "morning"

    elif 12 <= hour < 18:
        day_period = "afternoon"

    elif 18 <= hour < 23:
        day_period = "evening"

    else:
        day_period = "night"

    return {
        "valid": True,
        "hour": hour,
        "dayPeriod": day_period,
        "weekend": parsed.weekday() >= 5
    }


def extract_description_indicators(description):
    normalized_description = normalize_text(
        description
    )

    indicators = {}

    for indicator_name, keywords in (
        DESCRIPTION_KEYWORDS.items()
    ):
        matches = []

        for keyword in keywords:
            normalized_keyword = normalize_text(
                keyword
            )

            pattern = (
                r"\b"
                + re.escape(normalized_keyword).replace(
                    r"\ ",
                    r"\s+"
                )
                + r"\b"
            )

            if re.search(
                pattern,
                normalized_description
            ):
                matches.append(normalized_keyword)

        indicators[indicator_name] = {
            "detected": len(matches) > 0,
            "matches": sorted(set(matches))
        }

    return (
        normalized_description,
        indicators
    )


def labels_to_scores(labels):
    """
    Converte le etichette di Rekognition in:

    {
        "fire": 84.83,
        "person": 98.44
    }
    """

    scores = {}

    if not isinstance(labels, list):
        return scores

    for label in labels:
        if not isinstance(label, dict):
            continue

        name = normalize_text(
            label.get("name")
        )

        confidence = label.get(
            "confidence"
        )

        if (
            not name
            or not isinstance(
                confidence,
                (int, float)
            )
            or isinstance(confidence, bool)
        ):
            continue

        confidence = float(confidence)

        previous = scores.get(name, 0)

        if confidence > previous:
            scores[name] = confidence

    return scores


def strongest_evidence(
    label_scores,
    accepted_labels
):
    matches = [
        {
            "label": label,
            "confidence": label_scores[label]
        }
        for label in accepted_labels
        if label in label_scores
    ]

    if not matches:
        return None

    return max(
        matches,
        key=lambda item: item["confidence"]
    )


def build_human_context(event):
    report = event["report"]

    people = report.get(
        "people",
        {}
    )

    danger = report.get(
        "danger",
        {}
    )

    fire_details = report.get(
        "fireDetails",
        {}
    )

    accident_details = report.get(
        "accidentDetails",
        {}
    )

    description = report.get(
        "description",
        ""
    )

    (
        normalized_description,
        description_indicators
    ) = extract_description_indicators(
        description
    )

    return {
        "sourceType": "HUMAN_REPORT",

        "reportedType": (
            report.get(
                "reportedType",
                "UNKNOWN"
            )
            .strip()
            .upper()
        ),

        "normalizedDescription": (
            normalized_description
        ),

        "humanRisk": {
            "injured": tri_state_to_value(
                people.get("injured")
            ),
            "unresponsive": tri_state_to_value(
                people.get("unresponsive")
            ),
            "trapped": tri_state_to_value(
                people.get("trapped")
            ),
            "immediateDanger": tri_state_to_value(
                danger.get("immediate")
            )
        },

        "fireEvidence": {
            "flamesVisible": tri_state_to_value(
                fire_details.get(
                    "flamesVisible"
                )
            ),
            "smokeVisible": tri_state_to_value(
                fire_details.get(
                    "smokeVisible"
                )
            ),
            "spreading": tri_state_to_value(
                fire_details.get(
                    "spreading"
                )
            ),
            "buildingInvolved": tri_state_to_value(
                fire_details.get(
                    "buildingInvolved"
                )
            ),
            "vehicleOnFire": tri_state_to_value(
                fire_details.get(
                    "vehicleOnFire"
                )
            ),
            "explosionReported": tri_state_to_value(
                fire_details.get(
                    "explosionReported"
                )
            )
        },

        "accidentEvidence": {
            "vehiclesCount": accident_details.get(
                "vehiclesCount"
            ),
            "vehicleOverturned": tri_state_to_value(
                accident_details.get(
                    "vehicleOverturned"
                )
            ),
            "roadBlocked": tri_state_to_value(
                accident_details.get(
                    "roadBlocked"
                )
            ),
            "fuelLeak": tri_state_to_value(
                accident_details.get(
                    "fuelLeak"
                )
            ),
            "debrisPresent": tri_state_to_value(
                accident_details.get(
                    "debrisPresent"
                )
            )
        },

        "descriptionIndicators": (
            description_indicators
        ),

        "evidenceOrigin": "USER_INPUT"
    }


def build_camera_context(event):
    camera_data = event["cameraData"]

    labels = camera_data.get(
        "labels",
        []
    )

    label_scores = labels_to_scores(
        labels
    )

    fire_evidence = strongest_evidence(
        label_scores,
        FIRE_LABELS
    )

    vehicle_evidence = strongest_evidence(
        label_scores,
        VEHICLE_LABELS
    )

    accident_evidence = strongest_evidence(
        label_scores,
        ACCIDENT_LABELS
    )

    person_evidence = strongest_evidence(
        label_scores,
        PERSON_LABELS
    )

    preliminary_detection = event.get(
        "preliminaryDetection",
        {}
    )

    return {
        "sourceType": "CAMERA",

        "cameraId": camera_data.get(
            "cameraId"
        ),

        "imageReference": {
            "bucket": camera_data.get(
                "bucket"
            ),
            "imageKey": camera_data.get(
                "imageKey"
            )
        },

        "humanRisk": {
            "peopleDetected": (
                person_evidence is not None
            ),
            "personEvidence": person_evidence,
            "injured": None,
            "unresponsive": None,
            "trapped": None,
            "immediateDanger": None
        },

        "fireEvidence": {
            "detected": (
                fire_evidence is not None
            ),
            "strongestEvidence": fire_evidence
        },

        "accidentEvidence": {
            "vehicleDetected": (
                vehicle_evidence is not None
            ),
            "vehicleEvidence": vehicle_evidence,
            "accidentIndicatorDetected": (
                accident_evidence is not None
            ),
            "accidentEvidence": accident_evidence
        },

        "labelScores": label_scores,

        "preliminaryDetection": {
            "type": preliminary_detection.get(
                "type"
            ),
            "confidence": preliminary_detection.get(
                "confidence"
            )
        },

        "evidenceOrigin": "REKOGNITION"
    }



def build_mobile_context(event):
    """
    Costruisce un contesto compatibile con i report umani,
    aggiungendo anche le evidenze ottenute dalla fotografia
    caricata dall'utente, quando presenti.

    Manteniamo sourceType = HUMAN_REPORT per non rompere
    le Lambda successive giÃ  progettate per form e Lex.
    """

    unified_context = build_human_context(
        event
    )

    unified_context["reportChannel"] = "MOBILE"

    image_data = event.get(
        "imageData"
    )

    visual_analysis = event.get(
        "visualAnalysis"
    )

    # La foto Ã¨ facoltativa. In sua assenza il contesto
    # resta un normale report umano.
    if (
        not isinstance(image_data, dict)
        or not isinstance(visual_analysis, dict)
    ):
        unified_context["imageReference"] = None

        unified_context["visualEvidence"] = {
            "available": False
        }

        unified_context["evidenceOrigin"] = (
            "USER_INPUT"
        )

        return unified_context

    labels = visual_analysis.get(
        "labels",
        []
    )

    label_scores = labels_to_scores(
        labels
    )

    fire_evidence = strongest_evidence(
        label_scores,
        FIRE_LABELS
    )

    vehicle_evidence = strongest_evidence(
        label_scores,
        VEHICLE_LABELS
    )

    accident_evidence = strongest_evidence(
        label_scores,
        ACCIDENT_LABELS
    )

    person_evidence = strongest_evidence(
        label_scores,
        PERSON_LABELS
    )

    visual_event_type = (
        visual_analysis.get(
            "eventType",
            "unknown"
        )
    )

    visual_confidence = (
        visual_analysis.get(
            "confidence",
            0
        )
    )

    unified_context["imageReference"] = {
        "bucket": image_data.get(
            "bucket"
        ),
        "imageKey": image_data.get(
            "imageKey"
        ),
        "contentType": image_data.get(
            "contentType"
        ),
        "originalFileName": image_data.get(
            "originalFileName"
        )
    }

    unified_context["labelScores"] = (
        label_scores
    )

    unified_context["visualEvidence"] = {
        "available": True,
        "eventType": visual_event_type,
        "confidence": visual_confidence,
        "labels": labels,
        "analysisSource": (
            visual_analysis.get(
                "analysisSource",
                "user_uploaded_image"
            )
        )
    }

    # Aggiungiamo i risultati della foto senza eliminare
    # le risposte fornite manualmente dall'utente.
    unified_context["humanRisk"].update({
        "peopleDetected": (
            person_evidence is not None
        ),
        "personEvidence": (
            person_evidence
        )
    })

    unified_context["fireEvidence"].update({
        "imageDetected": (
            fire_evidence is not None
        ),
        "strongestImageEvidence": (
            fire_evidence
        )
    })

    unified_context["accidentEvidence"].update({
        "vehicleDetectedFromImage": (
            vehicle_evidence is not None
        ),
        "vehicleImageEvidence": (
            vehicle_evidence
        ),
        "accidentIndicatorDetectedFromImage": (
            accident_evidence is not None
        ),
        "accidentImageEvidence": (
            accident_evidence
        )
    })

    preliminary_detection = event.get(
        "preliminaryDetection",
        {}
    )

    unified_context["preliminaryDetection"] = {
        "type": preliminary_detection.get(
            "type",
            visual_event_type
        ),
        "confidence": preliminary_detection.get(
            "confidence",
            visual_confidence
        )
    }

    unified_context["evidenceOrigin"] = (
        "USER_INPUT_AND_REKOGNITION"
    )

    return unified_context

def calculate_context_completeness(
    event,
    context
):
    source = str(
        event.get(
            "source",
            ""
        )
    ).strip().lower()

    if source == "camera":
        fields = [
            context.get("cameraId"),
            context.get(
                "imageReference",
                {}
            ).get("imageKey"),
            context.get(
                "preliminaryDetection",
                {}
            ).get("type")
        ]

    else:
        fields = [
            event.get("location"),
            event.get(
                "report",
                {}
            ).get("description"),
            context.get("reportedType"),
            context.get(
                "humanRisk",
                {}
            ).get("injured")
        ]

    present = sum(
        value is not None
        and value != ""
        for value in fields
    )

    return {
        "score": round(
            present / len(fields) * 100
        ),
        "presentFields": present,
        "totalFields": len(fields)
    }


def lambda_handler(event, context):
    print("CONTEXTUALIZE EVENT RECEIVED")
    print(json.dumps(event))

    validation = event.get(
        "validation",
        {}
    )

    if not validation.get("valid"):
        result = dict(event)

        result["contextualization"] = {
            "status": "SKIPPED",
            "reason": (
                "Event validation failed"
            )
        }

        print(
            "CONTEXTUALIZATION SKIPPED"
        )

        return result

    source = (
        event.get("source", "")
        .strip()
        .lower()
    )

    if source == "camera":
        unified_context = build_camera_context(
            event
        )

    elif source in {"form", "lex"}:
        unified_context = build_human_context(
            event
        )

    elif source == "mobile":
        unified_context = build_mobile_context(
            event
        )

    else:
        result = dict(event)

        result["contextualization"] = {
            "status": "FAILED",
            "reason": (
                f"Unsupported source: {source}"
            )
        }

        return result

    unified_context["normalizedLocation"] = (
        event.get(
            "location",
            ""
        ).strip()
    )

    unified_context["timeContext"] = (
        extract_time_context(
            event.get("timestamp")
        )
    )

    unified_context["dataQuality"] = (
        calculate_context_completeness(
            event,
            unified_context
        )
    )

    contextualized_event = dict(event)

    contextualized_event["context"] = (
        unified_context
    )

    contextualized_event["contextualization"] = {
        "status": "COMPLETED"
    }

    print("CONTEXTUALIZATION COMPLETED")
    print(json.dumps(unified_context))

    return contextualized_event