import json
from datetime import datetime, timezone


BASE_SCORES = {
    "NO_EMERGENCY": 0,
    "UNKNOWN": 20,
    "ACCIDENT": 20,
    "FIRE": 25,
    "FIRE_AND_ACCIDENT": 40
}

PRIORITY_BY_LEVEL = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4
}


def is_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
    )


def add_factor(
    factors,
    condition,
    name,
    points,
    value=None
):
    if not condition:
        return 0

    factor = {
        "factor": name,
        "points": points
    }

    if value is not None:
        factor["value"] = value

    factors.append(factor)

    return points


def add_critical_trigger(
    critical_triggers,
    condition,
    name
):
    if condition:
        critical_triggers.append(name)


def add_classification_base(
    classification,
    factors
):
    event_type = classification.get(
        "type",
        "UNKNOWN"
    )

    base_score = BASE_SCORES.get(
        event_type,
        20
    )

    if base_score > 0:
        factors.append({
            "factor": (
                f"classification={event_type}"
            ),
            "points": base_score
        })

    return base_score


def add_confidence_score(
    classification,
    factors
):
    confidence = classification.get(
        "confidence"
    )

    if not is_number(confidence):
        return 0

    if confidence >= 90:
        points = 10

    elif confidence >= 70:
        points = 5

    else:
        points = 0

    if points > 0:
        factors.append({
            "factor": "classificationConfidence",
            "points": points,
            "value": confidence
        })

    return points


def evaluate_human_report(
    context,
    classification
):
    factors = []
    critical_triggers = []

    score = add_classification_base(
        classification,
        factors
    )

    score += add_confidence_score(
        classification,
        factors
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

    injured = (
        human_risk.get("injured") is True
    )

    unresponsive = (
        human_risk.get("unresponsive")
        is True
    )

    trapped = (
        human_risk.get("trapped") is True
    )

    immediate_danger = (
        human_risk.get("immediateDanger")
        is True
    )

    score += add_factor(
        factors,
        injured,
        "injuredPeople",
        20
    )

    score += add_factor(
        factors,
        unresponsive,
        "unresponsivePeople",
        40
    )

    score += add_factor(
        factors,
        trapped,
        "trappedPeople",
        35
    )

    score += add_factor(
        factors,
        immediate_danger,
        "immediateDanger",
        15
    )

    flames_visible = (
        fire_evidence.get("flamesVisible")
        is True
    )

    smoke_visible = (
        fire_evidence.get("smokeVisible")
        is True
    )

    spreading = (
        fire_evidence.get("spreading")
        is True
    )

    building_involved = (
        fire_evidence.get(
            "buildingInvolved"
        ) is True
    )

    vehicle_on_fire = (
        fire_evidence.get("vehicleOnFire")
        is True
    )

    explosion_reported = (
        fire_evidence.get(
            "explosionReported"
        ) is True
    )

    score += add_factor(
        factors,
        flames_visible,
        "visibleFlames",
        15
    )

    score += add_factor(
        factors,
        smoke_visible,
        "visibleSmoke",
        5
    )

    score += add_factor(
        factors,
        spreading,
        "fireSpreading",
        25
    )

    score += add_factor(
        factors,
        building_involved,
        "buildingInvolved",
        15
    )

    score += add_factor(
        factors,
        vehicle_on_fire,
        "vehicleOnFire",
        20
    )

    score += add_factor(
        factors,
        explosion_reported,
        "explosionReported",
        40
    )

    vehicles_count = accident_evidence.get(
        "vehiclesCount"
    )

    if (
        isinstance(vehicles_count, int)
        and not isinstance(
            vehicles_count,
            bool
        )
    ):
        if vehicles_count >= 3:
            score += add_factor(
                factors,
                True,
                "threeOrMoreVehicles",
                15,
                vehicles_count
            )

        elif vehicles_count >= 2:
            score += add_factor(
                factors,
                True,
                "multipleVehicles",
                10,
                vehicles_count
            )

    vehicle_overturned = (
        accident_evidence.get(
            "vehicleOverturned"
        ) is True
    )

    road_blocked = (
        accident_evidence.get(
            "roadBlocked"
        ) is True
    )

    fuel_leak = (
        accident_evidence.get(
            "fuelLeak"
        ) is True
    )

    debris_present = (
        accident_evidence.get(
            "debrisPresent"
        ) is True
    )

    score += add_factor(
        factors,
        vehicle_overturned,
        "vehicleOverturned",
        20
    )

    score += add_factor(
        factors,
        road_blocked,
        "roadBlocked",
        5
    )

    score += add_factor(
        factors,
        fuel_leak,
        "fuelLeak",
        20
    )

    score += add_factor(
        factors,
        debris_present,
        "debrisPresent",
        5
    )

    # Condizioni che rendono direttamente
    # l'evento critico.
    add_critical_trigger(
        critical_triggers,
        unresponsive,
        "UNRESPONSIVE_PEOPLE"
    )

    add_critical_trigger(
        critical_triggers,
        trapped,
        "TRAPPED_PEOPLE"
    )

    add_critical_trigger(
        critical_triggers,
        explosion_reported,
        "EXPLOSION_REPORTED"
    )

    add_critical_trigger(
        critical_triggers,
        spreading and building_involved,
        "SPREADING_BUILDING_FIRE"
    )

    add_critical_trigger(
        critical_triggers,
        fuel_leak
        and (
            vehicle_on_fire
            or flames_visible
        ),
        "FUEL_LEAK_WITH_FIRE"
    )

    add_critical_trigger(
        critical_triggers,
        (
            classification.get("type")
            == "FIRE_AND_ACCIDENT"
            and (
                injured
                or immediate_danger
            )
        ),
        "COMBINED_EVENT_WITH_PEOPLE_AT_RISK"
    )

    return {
        "score": score,
        "factors": factors,
        "criticalTriggers": critical_triggers
    }


def evaluate_camera_event(
    context,
    classification
):
    factors = []
    critical_triggers = []

    score = add_classification_base(
        classification,
        factors
    )

    score += add_confidence_score(
        classification,
        factors
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

    people_detected = (
        human_risk.get("peopleDetected")
        is True
    )

    score += add_factor(
        factors,
        people_detected,
        "peopleDetectedNearEmergency",
        25
    )

    strongest_fire = fire_evidence.get(
        "strongestEvidence"
    )

    if isinstance(strongest_fire, dict):
        fire_confidence = strongest_fire.get(
            "confidence"
        )

        if is_number(fire_confidence):
            if fire_confidence >= 90:
                score += add_factor(
                    factors,
                    True,
                    "veryStrongFireEvidence",
                    20,
                    fire_confidence
                )

            elif fire_confidence >= 80:
                score += add_factor(
                    factors,
                    True,
                    "strongFireEvidence",
                    15,
                    fire_confidence
                )

            elif fire_confidence >= 70:
                score += add_factor(
                    factors,
                    True,
                    "fireEvidence",
                    10,
                    fire_confidence
                )

    vehicle_detected = (
        accident_evidence.get(
            "vehicleDetected"
        ) is True
    )

    accident_indicator = (
        accident_evidence.get(
            "accidentIndicatorDetected"
        ) is True
    )

    score += add_factor(
        factors,
        vehicle_detected,
        "vehicleDetected",
        5
    )

    score += add_factor(
        factors,
        accident_indicator,
        "directAccidentEvidence",
        20
    )

    add_critical_trigger(
        critical_triggers,
        (
            classification.get("type")
            == "FIRE_AND_ACCIDENT"
            and people_detected
        ),
        "COMBINED_EVENT_WITH_PEOPLE_DETECTED"
    )

    return {
        "score": score,
        "factors": factors,
        "criticalTriggers": critical_triggers
    }


def determine_level(
    score,
    critical_triggers,
    event_type
):
    if event_type == "NO_EMERGENCY":
        return "LOW", 0

    if critical_triggers:
        return "CRITICAL", max(
            score,
            100
        )

    if score >= 100:
        return "CRITICAL", score

    if score >= 50:
        return "HIGH", score

    if score >= 20:
        return "MEDIUM", score

    return "LOW", score


def lambda_handler(event, context):
    print("EVALUATE SEVERITY RECEIVED")
    print(json.dumps(event))

    result = dict(event)

    validation = event.get(
        "validation",
        {}
    )

    if not validation.get("valid"):
        result["severity"] = {
            "status": "SKIPPED",
            "level": "UNKNOWN",
            "reason": "Event validation failed"
        }

        return result

    contextualization_status = event.get(
        "contextualization",
        {}
    ).get("status")

    if contextualization_status != "COMPLETED":
        result["severity"] = {
            "status": "SKIPPED",
            "level": "UNKNOWN",
            "reason": (
                "Contextualization was not completed"
            )
        }

        return result

    classification = event.get(
        "classification",
        {}
    )

    if (
        classification.get("status")
        != "COMPLETED"
    ):
        result["severity"] = {
            "status": "SKIPPED",
            "level": "UNKNOWN",
            "reason": (
                "Classification was not completed"
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
        evaluation = evaluate_human_report(
            unified_context,
            classification
        )

    elif source_type == "CAMERA":
        evaluation = evaluate_camera_event(
            unified_context,
            classification
        )

    else:
        result["severity"] = {
            "status": "FAILED",
            "level": "UNKNOWN",
            "reason": (
                f"Unsupported source type: "
                f"{source_type}"
            )
        }

        return result

    event_type = classification.get(
        "type",
        "UNKNOWN"
    )

    level, final_score = determine_level(
        evaluation["score"],
        evaluation["criticalTriggers"],
        event_type
    )

    severity = {
        "status": "COMPLETED",
        "level": level,
        "priority": PRIORITY_BY_LEVEL[level],
        "score": round(final_score, 2),
        "factors": evaluation["factors"],
        "criticalTriggers": (
            evaluation["criticalTriggers"]
        ),
        "evaluatedAt": datetime.now(
            timezone.utc
        ).isoformat()
    }

    result["severity"] = severity

    print("SEVERITY EVALUATION COMPLETED")
    print(json.dumps(severity))

    return result