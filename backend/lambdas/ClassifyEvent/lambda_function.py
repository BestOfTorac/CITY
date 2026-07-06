import json
from datetime import datetime, timezone


HUMAN_CLASSIFICATION_THRESHOLD = 45
CAMERA_CLASSIFICATION_THRESHOLD = 70


def add_evidence(evidence, name, value, weight):
    if value is True:
        evidence.append({
            "indicator": name,
            "weight": weight
        })

        return weight

    return 0


def indicator_detected(context, name):
    indicators = context.get(
        "descriptionIndicators",
        {}
    )

    indicator = indicators.get(name, {})

    return indicator.get("detected") is True


def build_human_scores(context):
    fire_score = 0
    accident_score = 0

    fire_evidence_list = []
    accident_evidence_list = []

    reported_type = context.get(
        "reportedType",
        "UNKNOWN"
    )

    human_risk = context.get(
        "humanRisk",
        {}
    )

    fire_evidence = context.get(
        "fireEvidence",
        {}
    )

    accident_evidence = context.get(
        "accidentEvidence",
        {}
    )

    visual_evidence = context.get(
        "visualEvidence",
        {}
    )

    # Il tipo dichiarato dall'utente è un indizio,
    # ma non determina da solo la classificazione.
    if reported_type == "FIRE":
        fire_score += 20

        fire_evidence_list.append({
            "indicator": "reportedType=FIRE",
            "weight": 20,
            "origin": "USER_INPUT"
        })

    elif reported_type == "ACCIDENT":
        accident_score += 20

        accident_evidence_list.append({
            "indicator": "reportedType=ACCIDENT",
            "weight": 20,
            "origin": "USER_INPUT"
        })

    # Indizi di incendio provenienti dal form.
    fire_score += add_evidence(
        fire_evidence_list,
        "flamesVisible",
        fire_evidence.get("flamesVisible"),
        35
    )

    fire_score += add_evidence(
        fire_evidence_list,
        "smokeVisible",
        fire_evidence.get("smokeVisible"),
        15
    )

    fire_score += add_evidence(
        fire_evidence_list,
        "fireSpreading",
        fire_evidence.get("spreading"),
        15
    )

    fire_score += add_evidence(
        fire_evidence_list,
        "buildingInvolved",
        fire_evidence.get("buildingInvolved"),
        5
    )

    fire_score += add_evidence(
        fire_evidence_list,
        "vehicleOnFire",
        fire_evidence.get("vehicleOnFire"),
        35
    )

    fire_score += add_evidence(
        fire_evidence_list,
        "explosionReported",
        fire_evidence.get("explosionReported"),
        15
    )

    # Indizi di incendio trovati nella descrizione.
    if indicator_detected(
        context,
        "fireMentioned"
    ):
        fire_score += 25

        fire_evidence_list.append({
            "indicator": "fireMentionedInDescription",
            "weight": 25,
            "origin": "USER_INPUT"
        })

    if indicator_detected(
        context,
        "smokeMentioned"
    ):
        fire_score += 10

        fire_evidence_list.append({
            "indicator": "smokeMentionedInDescription",
            "weight": 10,
            "origin": "USER_INPUT"
        })

    if indicator_detected(
        context,
        "explosionMentioned"
    ):
        fire_score += 15

        fire_evidence_list.append({
            "indicator": "explosionMentionedInDescription",
            "weight": 15,
            "origin": "USER_INPUT"
        })

    # Indizi di incidente provenienti dal form.
    vehicles_count = accident_evidence.get(
        "vehiclesCount"
    )

    if isinstance(vehicles_count, int):
        if vehicles_count >= 2:
            accident_score += 25

            accident_evidence_list.append({
                "indicator": "multipleVehicles",
                "value": vehicles_count,
                "weight": 25,
                "origin": "USER_INPUT"
            })

        elif vehicles_count == 1:
            accident_score += 10

            accident_evidence_list.append({
                "indicator": "singleVehicle",
                "value": vehicles_count,
                "weight": 10,
                "origin": "USER_INPUT"
            })

    accident_score += add_evidence(
        accident_evidence_list,
        "vehicleOverturned",
        accident_evidence.get("vehicleOverturned"),
        20
    )

    accident_score += add_evidence(
        accident_evidence_list,
        "roadBlocked",
        accident_evidence.get("roadBlocked"),
        10
    )

    accident_score += add_evidence(
        accident_evidence_list,
        "fuelLeak",
        accident_evidence.get("fuelLeak"),
        15
    )

    accident_score += add_evidence(
        accident_evidence_list,
        "debrisPresent",
        accident_evidence.get("debrisPresent"),
        15
    )

    # Indizi trovati nella descrizione.
    if indicator_detected(
        context,
        "collisionMentioned"
    ):
        accident_score += 35

        accident_evidence_list.append({
            "indicator": "collisionMentionedInDescription",
            "weight": 35,
            "origin": "USER_INPUT"
        })

    if indicator_detected(
        context,
        "vehicleMentioned"
    ):
        accident_score += 10

        accident_evidence_list.append({
            "indicator": "vehicleMentionedInDescription",
            "weight": 10,
            "origin": "USER_INPUT"
        })

    # Evidenze provenienti dalla foto allegata dall'utente.
    # Una rilevazione visiva diretta e sufficientemente
    # confidente può determinare la classificazione.
    strongest_image_fire = fire_evidence.get(
        "strongestImageEvidence"
    )

    fire_image_used = False

    if (
        fire_evidence.get("imageDetected") is True
        and isinstance(strongest_image_fire, dict)
    ):
        fire_confidence = strongest_image_fire.get(
            "confidence",
            0
        )

        if (
            isinstance(fire_confidence, (int, float))
            and not isinstance(fire_confidence, bool)
        ):
            fire_confidence = max(
                0.0,
                min(float(fire_confidence), 100.0)
            )

            fire_score = max(
                fire_score,
                fire_confidence
            )

            fire_evidence_list.append({
                "indicator": (
                    strongest_image_fire.get("label")
                    or "fireDetectedInUploadedImage"
                ),
                "confidence": round(
                    fire_confidence,
                    2
                ),
                "origin": "USER_UPLOADED_IMAGE"
            })

            fire_image_used = True

    direct_accident_image = accident_evidence.get(
        "accidentImageEvidence"
    )

    accident_image_used = False

    if (
        accident_evidence.get(
            "accidentIndicatorDetectedFromImage"
        ) is True
        and isinstance(
            direct_accident_image,
            dict
        )
    ):
        accident_confidence = direct_accident_image.get(
            "confidence",
            0
        )

        if (
            isinstance(
                accident_confidence,
                (int, float)
            )
            and not isinstance(
                accident_confidence,
                bool
            )
        ):
            accident_confidence = max(
                0.0,
                min(
                    float(accident_confidence),
                    100.0
                )
            )

            accident_score = max(
                accident_score,
                accident_confidence
            )

            accident_evidence_list.append({
                "indicator": (
                    direct_accident_image.get("label")
                    or "accidentDetectedInUploadedImage"
                ),
                "confidence": round(
                    accident_confidence,
                    2
                ),
                "origin": "USER_UPLOADED_IMAGE"
            })

            accident_image_used = True

    # Un veicolo visibile da solo non prova un incidente,
    # ma costituisce un indizio debole.
    vehicle_image_evidence = accident_evidence.get(
        "vehicleImageEvidence"
    )

    if (
        accident_evidence.get(
            "vehicleDetectedFromImage"
        ) is True
        and isinstance(
            vehicle_image_evidence,
            dict
        )
    ):
        accident_score += 10

        accident_evidence_list.append({
            "indicator": (
                vehicle_image_evidence.get("label")
                or "vehicleDetectedInUploadedImage"
            ),
            "confidence": vehicle_image_evidence.get(
                "confidence",
                0
            ),
            "weight": 10,
            "origin": "USER_UPLOADED_IMAGE",
            "note": "Vehicle alone is not sufficient"
        })

    # Fallback sul risultato sintetico di visualAnalysis.
    if (
        visual_evidence.get("available") is True
        and isinstance(
            visual_evidence.get("confidence"),
            (int, float)
        )
        and not isinstance(
            visual_evidence.get("confidence"),
            bool
        )
    ):
        visual_type = str(
            visual_evidence.get(
                "eventType",
                ""
            )
        ).strip().lower()

        visual_confidence = max(
            0.0,
            min(
                float(
                    visual_evidence.get(
                        "confidence",
                        0
                    )
                ),
                100.0
            )
        )

        if (
            visual_type == "fire"
            and not fire_image_used
        ):
            fire_score = max(
                fire_score,
                visual_confidence
            )

            fire_evidence_list.append({
                "indicator": "visualAnalysis=fire",
                "confidence": round(
                    visual_confidence,
                    2
                ),
                "origin": "USER_UPLOADED_IMAGE"
            })

        elif (
            visual_type == "accident"
            and not accident_image_used
        ):
            accident_score = max(
                accident_score,
                visual_confidence
            )

            accident_evidence_list.append({
                "indicator": "visualAnalysis=accident",
                "confidence": round(
                    visual_confidence,
                    2
                ),
                "origin": "USER_UPLOADED_IMAGE"
            })

    # Feriti e pericolo immediato saranno più importanti
    # per EvaluateSeverity che per la classificazione.
    human_risk_summary = {
        "injured": human_risk.get("injured"),
        "unresponsive": human_risk.get("unresponsive"),
        "trapped": human_risk.get("trapped"),
        "immediateDanger": human_risk.get(
            "immediateDanger"
        )
    }

    return {
        "fireScore": round(
            min(fire_score, 100),
            2
        ),
        "accidentScore": round(
            min(accident_score, 100),
            2
        ),
        "fireEvidence": fire_evidence_list,
        "accidentEvidence": accident_evidence_list,
        "humanRiskSummary": human_risk_summary,
        "threshold": HUMAN_CLASSIFICATION_THRESHOLD
    }


def build_camera_scores(context):
    fire_score = 0
    accident_score = 0

    fire_evidence_list = []
    accident_evidence_list = []

    fire_context = context.get(
        "fireEvidence",
        {}
    )

    accident_context = context.get(
        "accidentEvidence",
        {}
    )

    preliminary = context.get(
        "preliminaryDetection",
        {}
    )

    strongest_fire = fire_context.get(
        "strongestEvidence"
    )

    if (
        fire_context.get("detected") is True
        and isinstance(strongest_fire, dict)
    ):
        fire_score = float(
            strongest_fire.get(
                "confidence",
                0
            )
        )

        fire_evidence_list.append({
            "indicator": strongest_fire.get("label"),
            "confidence": fire_score,
            "origin": "REKOGNITION"
        })

    vehicle_evidence = accident_context.get(
        "vehicleEvidence"
    )

    direct_accident_evidence = accident_context.get(
        "accidentEvidence"
    )

    vehicle_detected = (
        accident_context.get(
            "vehicleDetected"
        ) is True
    )

    accident_indicator_detected = (
        accident_context.get(
            "accidentIndicatorDetected"
        ) is True
    )

    # Un veicolo da solo non prova che sia avvenuto
    # un incidente.
    if vehicle_detected and isinstance(
        vehicle_evidence,
        dict
    ):
        vehicle_confidence = float(
            vehicle_evidence.get(
                "confidence",
                0
            )
        )

        accident_score += 20

        accident_evidence_list.append({
            "indicator": vehicle_evidence.get("label"),
            "confidence": vehicle_confidence,
            "weight": 20,
            "note": "Vehicle alone is not sufficient"
        })

    if accident_indicator_detected and isinstance(
        direct_accident_evidence,
        dict
    ):
        direct_confidence = float(
            direct_accident_evidence.get(
                "confidence",
                0
            )
        )

        # Se Rekognition rileva direttamente danni,
        # collisione, detriti o incidente, quel valore
        # diventa l'evidenza principale.
        accident_score = max(
            accident_score,
            direct_confidence
        )

        accident_evidence_list.append({
            "indicator": direct_accident_evidence.get(
                "label"
            ),
            "confidence": direct_confidence,
            "origin": "REKOGNITION"
        })

    preliminary_type = str(
        preliminary.get("type", "")
    ).lower()

    preliminary_confidence = preliminary.get(
        "confidence"
    )

    # La rilevazione preliminare rafforza una prova già
    # presente, ma non la sostituisce.
    if (
        preliminary_type == "fire"
        and fire_score > 0
        and isinstance(
            preliminary_confidence,
            (int, float)
        )
    ):
        fire_score = min(
            fire_score + 5,
            100
        )

    if (
        preliminary_type == "accident"
        and accident_indicator_detected
        and isinstance(
            preliminary_confidence,
            (int, float)
        )
    ):
        accident_score = min(
            accident_score + 5,
            100
        )

    return {
        "fireScore": round(
            min(fire_score, 100),
            2
        ),
        "accidentScore": round(
            min(accident_score, 100),
            2
        ),
        "fireEvidence": fire_evidence_list,
        "accidentEvidence": accident_evidence_list,
        "threshold": CAMERA_CLASSIFICATION_THRESHOLD
    }


def determine_classification(scores):
    fire_score = scores["fireScore"]
    accident_score = scores["accidentScore"]
    threshold = scores["threshold"]

    fire_detected = fire_score >= threshold
    accident_detected = accident_score >= threshold

    if fire_detected and accident_detected:
        event_type = "FIRE_AND_ACCIDENT"
        confidence = max(
            fire_score,
            accident_score
        )

    elif fire_detected:
        event_type = "FIRE"
        confidence = fire_score

    elif accident_detected:
        event_type = "ACCIDENT"
        confidence = accident_score

    elif fire_score == 0 and accident_score == 0:
        event_type = "NO_EMERGENCY"
        confidence = 100

    else:
        event_type = "UNKNOWN"
        confidence = max(
            fire_score,
            accident_score
        )

    return {
        "type": event_type,
        "confidence": round(
            confidence,
            2
        ),
        "fireScore": round(
            fire_score,
            2
        ),
        "accidentScore": round(
            accident_score,
            2
        ),
        "threshold": threshold,
        "fireEvidence": scores[
            "fireEvidence"
        ],
        "accidentEvidence": scores[
            "accidentEvidence"
        ]
    }


def lambda_handler(event, context):
    print("CLASSIFY EVENT RECEIVED")
    print(json.dumps(event))

    result = dict(event)

    if not event.get(
        "validation",
        {}
    ).get("valid"):
        result["classification"] = {
            "status": "SKIPPED",
            "type": "UNKNOWN",
            "reason": "Event validation failed"
        }

        return result

    if event.get(
        "contextualization",
        {}
    ).get("status") != "COMPLETED":
        result["classification"] = {
            "status": "SKIPPED",
            "type": "UNKNOWN",
            "reason": (
                "Event contextualization "
                "was not completed"
            )
        }

        return result

    unified_context = event.get(
        "context",
        {}
    )

    source_type = unified_context.get(
        "sourceType"
    )

    if source_type == "HUMAN_REPORT":
        scores = build_human_scores(
            unified_context
        )

    elif source_type == "CAMERA":
        scores = build_camera_scores(
            unified_context
        )

    else:
        result["classification"] = {
            "status": "FAILED",
            "type": "UNKNOWN",
            "reason": (
                f"Unsupported source type: "
                f"{source_type}"
            )
        }

        return result

    classification = determine_classification(
        scores
    )

    classification["status"] = "COMPLETED"
    classification["classifiedAt"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    result["classification"] = (
        classification
    )

    print("CLASSIFICATION COMPLETED")
    print(json.dumps(classification))

    return result