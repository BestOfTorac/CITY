import json
import posixpath
from datetime import datetime, timezone


EMERGENCY_TYPES = {
    "FIRE",
    "ACCIDENT",
    "FIRE_AND_ACCIDENT"
}

NOTIFICATION_SEVERITIES = {
    "MEDIUM",
    "HIGH",
    "CRITICAL"
}


def is_human_source(source):
    return str(source).strip().lower() in {
        "mobile",
        "form",
        "lex",
        "user"
    }


def source_display_name(source):
    normalized = str(source).strip().lower()

    if normalized == "mobile":
        return "Segnalazione utente (app mobile)"

    if normalized == "form":
        return "Segnalazione utente (modulo)"

    if normalized == "lex":
        return "Segnalazione utente (assistente)"

    if normalized == "camera":
        return "Telecamera"

    return normalized or "Non disponibile"


def add_service_reason(service, reason):
    if reason not in service["reasons"]:
        service["reasons"].append(reason)


def require_units(service, units, reason):
    service["units"] = max(
        service["units"],
        units
    )

    service["required"] = (
        service["units"] > 0
    )

    add_service_reason(
        service,
        reason
    )


def create_empty_response_plan():
    return {
        "ambulances": {
            "required": False,
            "units": 0,
            "reasons": []
        },
        "patrols": {
            "required": False,
            "units": 0,
            "reasons": []
        },
        "fireBrigade": {
            "required": False,
            "units": 0,
            "reasons": []
        }
    }


def build_response_plan(
    event_type,
    severity_level,
    context,
    source
):
    plan = create_empty_response_plan()

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

    human_source = is_human_source(
        source
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

    people_detected = (
        human_risk.get("peopleDetected")
        is True
    )

    flames_visible = (
        fire_evidence.get("flamesVisible")
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

    fire_detected_by_camera = (
        fire_evidence.get("detected")
        is True
    )

    fire_detected_in_uploaded_image = (
        fire_evidence.get("imageDetected")
        is True
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

    vehicles_count = accident_evidence.get(
        "vehiclesCount"
    )

    accident_detected_by_camera = (
        accident_evidence.get(
            "accidentIndicatorDetected"
        ) is True
    )

    accident_detected_in_uploaded_image = (
        accident_evidence.get(
            "accidentIndicatorDetectedFromImage"
        ) is True
    )

    # -------------------------
    # AMBULANZE
    # -------------------------

    if injured:
        require_units(
            plan["ambulances"],
            1,
            "Sono state segnalate persone ferite"
        )

    if unresponsive:
        require_units(
            plan["ambulances"],
            2,
            "Sono presenti persone incoscienti o non responsive"
        )

    if trapped:
        require_units(
            plan["ambulances"],
            2,
            "Sono presenti persone intrappolate"
        )

    if immediate_danger:
        require_units(
            plan["ambulances"],
            1,
            "Sono presenti persone in pericolo immediato"
        )

    if (
        people_detected
        and event_type in {
            "FIRE",
            "FIRE_AND_ACCIDENT"
        }
        and severity_level in {
            "HIGH",
            "CRITICAL"
        }
    ):
        if human_source:
            reason = (
                "Nella foto allegata sono state "
                "rilevate persone vicino all'emergenza"
            )
        else:
            reason = (
                "La telecamera ha rilevato persone "
                "vicino all'emergenza"
            )

        require_units(
            plan["ambulances"],
            1,
            reason
        )

    if (
        severity_level == "CRITICAL"
        and plan["ambulances"]["required"]
    ):
        require_units(
            plan["ambulances"],
            2,
            "La gravitÃ  dell'evento Ã¨ critica"
        )

    # -------------------------
    # PATTUGLIE
    # -------------------------

    if event_type in {
        "ACCIDENT",
        "FIRE_AND_ACCIDENT"
    }:
        require_units(
            plan["patrols"],
            1,
            "Ãˆ stato rilevato un incidente stradale"
        )

    if road_blocked:
        require_units(
            plan["patrols"],
            1,
            "La strada risulta bloccata"
        )

    if (
        isinstance(vehicles_count, int)
        and not isinstance(
            vehicles_count,
            bool
        )
        and vehicles_count >= 3
    ):
        require_units(
            plan["patrols"],
            2,
            "Sono coinvolti almeno tre veicoli"
        )

    if accident_detected_by_camera:
        require_units(
            plan["patrols"],
            1,
            "La telecamera ha rilevato evidenze di incidente"
        )

    if accident_detected_in_uploaded_image:
        require_units(
            plan["patrols"],
            1,
            "La foto allegata mostra evidenze di incidente"
        )

    if (
        severity_level == "CRITICAL"
        and event_type in {
            "ACCIDENT",
            "FIRE_AND_ACCIDENT"
        }
    ):
        require_units(
            plan["patrols"],
            2,
            "L'incidente ha gravitÃ  critica"
        )

    # -------------------------
    # VIGILI DEL FUOCO
    # -------------------------

    if event_type in {
        "FIRE",
        "FIRE_AND_ACCIDENT"
    }:
        require_units(
            plan["fireBrigade"],
            1,
            "Ãˆ stato rilevato un incendio"
        )

    if flames_visible:
        require_units(
            plan["fireBrigade"],
            1,
            "Sono state segnalate fiamme visibili"
        )

    if fire_detected_by_camera:
        require_units(
            plan["fireBrigade"],
            1,
            "La telecamera ha rilevato un incendio"
        )

    if fire_detected_in_uploaded_image:
        require_units(
            plan["fireBrigade"],
            1,
            "La foto allegata mostra evidenze di incendio"
        )

    if vehicle_on_fire:
        require_units(
            plan["fireBrigade"],
            1,
            "Ãˆ stato segnalato un veicolo in fiamme"
        )

    if vehicle_overturned:
        require_units(
            plan["fireBrigade"],
            1,
            "Ãˆ presente un veicolo ribaltato"
        )

    if trapped:
        require_units(
            plan["fireBrigade"],
            1,
            "Potrebbe essere necessario liberare persone intrappolate"
        )

    if fuel_leak:
        require_units(
            plan["fireBrigade"],
            1,
            "Ãˆ stata segnalata una perdita di carburante"
        )

    if explosion_reported:
        require_units(
            plan["fireBrigade"],
            2,
            "Ãˆ stata segnalata un'esplosione"
        )

    if spreading and building_involved:
        require_units(
            plan["fireBrigade"],
            2,
            "L'incendio si sta propagando e coinvolge un edificio"
        )

    if (
        severity_level == "CRITICAL"
        and plan["fireBrigade"]["required"]
    ):
        require_units(
            plan["fireBrigade"],
            2,
            "L'incendio ha gravitÃ  critica"
        )

    return plan


def build_observations(
    context,
    source
):
    observations = []

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

    human_source = is_human_source(
        source
    )

    if human_risk.get("injured") is True:
        observations.append(
            "Sono state segnalate persone ferite"
        )

    if human_risk.get("unresponsive") is True:
        observations.append(
            "Sono presenti persone non responsive"
        )

    if human_risk.get("trapped") is True:
        observations.append(
            "Sono presenti persone intrappolate"
        )

    if human_risk.get("immediateDanger") is True:
        observations.append(
            "Ãˆ stato segnalato un pericolo immediato"
        )

    if human_risk.get("peopleDetected") is True:
        if human_source:
            observations.append(
                "Nella foto allegata sono state rilevate persone nell'area"
            )
        else:
            observations.append(
                "La telecamera ha rilevato persone nell'area"
            )

    if fire_evidence.get("flamesVisible") is True:
        observations.append(
            "Sono visibili delle fiamme"
        )

    if fire_evidence.get("smokeVisible") is True:
        observations.append(
            "Ãˆ visibile del fumo"
        )

    if fire_evidence.get("detected") is True:
        observations.append(
            "Il sistema di videosorveglianza ha rilevato un incendio"
        )

    if fire_evidence.get("imageDetected") is True:
        observations.append(
            "La foto allegata mostra evidenze di incendio"
        )

    if fire_evidence.get("spreading") is True:
        observations.append(
            "L'incendio risulta in propagazione"
        )

    if fire_evidence.get("vehicleOnFire") is True:
        observations.append(
            "Ãˆ presente un veicolo in fiamme"
        )

    if fire_evidence.get("explosionReported") is True:
        observations.append(
            "Ãˆ stata segnalata un'esplosione"
        )

    vehicles_count = accident_evidence.get(
        "vehiclesCount"
    )

    if isinstance(vehicles_count, int):
        observations.append(
            f"Veicoli coinvolti: {vehicles_count}"
        )

    if accident_evidence.get("vehicleOverturned") is True:
        observations.append(
            "Ãˆ presente un veicolo ribaltato"
        )

    if accident_evidence.get("roadBlocked") is True:
        observations.append(
            "La strada risulta bloccata"
        )

    if accident_evidence.get("fuelLeak") is True:
        observations.append(
            "Ãˆ stata segnalata una perdita di carburante"
        )

    if accident_evidence.get("debrisPresent") is True:
        observations.append(
            "Sono presenti detriti"
        )

    if (
        accident_evidence.get(
            "accidentIndicatorDetectedFromImage"
        ) is True
    ):
        observations.append(
            "La foto allegata mostra evidenze di incidente"
        )

    if not observations:
        observations.append(
            "Non sono disponibili ulteriori dettagli"
        )

    return observations


def format_service_line(name, service):
    if service["required"]:
        reasons = "; ".join(
            service["reasons"]
        )

        return (
            f"- {name}: {service['units']} "
            f"unitÃ  suggerite. Motivi: {reasons}"
        )

    return (
        f"- {name}: non richiesti"
    )


def build_notification(
    event,
    classification,
    severity,
    response_plan,
    observations,
    should_notify
):
    event_id = event.get(
        "eventId",
        "non disponibile"
    )

    source = event.get(
        "source",
        "non disponibile"
    )

    source_label = source_display_name(
        source
    )

    location = event.get(
        "location",
        "non disponibile"
    )

    event_type = classification.get(
        "type",
        "UNKNOWN"
    )

    confidence = classification.get(
        "confidence",
        0
    )

    severity_level = severity.get(
        "level",
        "UNKNOWN"
    )

    severity_score = severity.get(
        "score",
        0
    )

    priority = severity.get(
        "priority",
        4
    )

    report = event.get(
        "report",
        {}
    )

    description = (
        report.get("description")
        or event.get("description")
    )

    if not description:
        if str(source).strip().lower() == "camera":
            description = (
                "Evento rilevato automaticamente "
                "dal sistema di videosorveglianza."
            )
        else:
            description = (
                "Descrizione non fornita dall'utente."
            )

    observation_lines = "\n".join(
        f"- {item}"
        for item in observations
    )

    service_lines = "\n".join([
        format_service_line(
            "Ambulanze",
            response_plan["ambulances"]
        ),
        format_service_line(
            "Pattuglie",
            response_plan["patrols"]
        ),
        format_service_line(
            "Vigili del Fuoco",
            response_plan["fireBrigade"]
        )
    ])

    subject = (
        f"Emergenza {severity_level}: "
        f"{event_type}"
    )[:100]

    observations_title = (
        "INFORMAZIONI ED EVIDENZE"
        if is_human_source(source)
        else "SITUAZIONE RILEVATA"
    )

    message = (
        "EMERGENZA RILEVATA\n\n"
        f"ID evento: {event_id}\n"
        f"Fonte: {source_label}\n"
        f"Posizione: {location}\n"
        f"Tipo evento: {event_type}\n"
        f"Confidenza classificazione: {confidence}%\n"
        f"Livello di gravitÃ : {severity_level}\n"
        f"Punteggio gravitÃ : {severity_score}\n"
        f"PrioritÃ : {priority}\n\n"
        "DESCRIZIONE\n"
        f"{description}\n\n"
        f"{observations_title}\n"
        f"{observation_lines}\n\n"
        "MEZZI DI SOCCORSO SUGGERITI\n"
        f"{service_lines}\n\n"
        "Nota: il piano dei mezzi Ã¨ una stima "
        "automatica e deve essere verificato "
        "da un operatore."
    )

    return {
        "enabled": should_notify,
        "channel": (
            "SNS"
            if should_notify
            else None
        ),
        "subject": subject,
        "message": message
    }


def build_image_archive(
    event,
    context
):
    image_reference = context.get(
        "imageReference"
    )

    if not isinstance(
        image_reference,
        dict
    ):
        image_reference = {}

    # Fallback per i payload che non sono ancora
    # stati normalizzati nel contesto.
    if not image_reference:
        raw_image_data = event.get(
            "imageData"
        )

        if isinstance(raw_image_data, dict):
            image_reference = raw_image_data

    if not image_reference:
        camera_data = event.get(
            "cameraData"
        )

        if isinstance(camera_data, dict):
            image_reference = camera_data

    source_bucket = image_reference.get(
        "bucket"
    )

    source_key = image_reference.get(
        "imageKey"
    )

    enabled = bool(
        source_bucket
        and source_key
    )

    if not enabled:
        return {
            "enabled": False,
            "sourceBucket": None,
            "sourceKey": None,
            "destinationBucket": None,
            "destinationKey": None,
            "reason": (
                "No image associated with the event"
            )
        }

    filename = posixpath.basename(
        source_key
    )

    event_id = event.get(
        "eventId",
        "unknown-event"
    )

    destination_key = (
        f"events/{event_id}/images/{filename}"
    )

    return {
        "enabled": True,
        "sourceBucket": source_bucket,
        "sourceKey": source_key,
        "destinationBucket": source_bucket,
        "destinationKey": destination_key,
        "reason": None
    }


def build_database_record(
    event,
    classification,
    severity,
    response_plan,
    notification,
    image_archive,
    decided_at
):
    details = {
        "report": event.get("report"),
        "cameraData": event.get(
            "cameraData"
        ),
        "context": event.get("context"),
        "classification": classification,
        "severity": severity,
        "responsePlan": response_plan
    }

    return {
        "eventId": event.get("eventId"),
        "timestamp": event.get("timestamp"),
        "source": event.get("source"),
        "location": event.get("location"),

        "eventType": classification.get(
            "type"
        ),

        "classificationConfidence": (
            classification.get("confidence")
        ),

        "fireScore": classification.get(
            "fireScore"
        ),

        "accidentScore": classification.get(
            "accidentScore"
        ),

        "severityLevel": severity.get(
            "level"
        ),

        "severityScore": severity.get(
            "score"
        ),

        "priority": severity.get(
            "priority"
        ),

        "notificationRequired": (
            notification["enabled"]
        ),

        "ambulances": (
            response_plan[
                "ambulances"
            ]["units"]
        ),

        "patrols": (
            response_plan[
                "patrols"
            ]["units"]
        ),

        "fireBrigade": (
            response_plan[
                "fireBrigade"
            ]["units"]
        ),

        "imageBucket": image_archive.get(
            "destinationBucket"
        ),

        "imageKey": image_archive.get(
            "destinationKey"
        ),

        "processingStatus": "PROCESSED",
        "decidedAt": decided_at,

        "eventDetailsJson": json.dumps(
            details,
            ensure_ascii=False
        )
    }


def lambda_handler(event, context):
    print("DECISION LOGIC RECEIVED")
    print(json.dumps(event))

    result = dict(event)

    validation = event.get(
        "validation",
        {}
    )

    if not validation.get("valid"):
        result["decision"] = {
            "status": "SKIPPED",
            "reason": "Event validation failed"
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
        result["decision"] = {
            "status": "SKIPPED",
            "reason": (
                "Classification was not completed"
            )
        }

        return result

    severity = event.get(
        "severity",
        {}
    )

    if severity.get("status") != "COMPLETED":
        result["decision"] = {
            "status": "SKIPPED",
            "reason": (
                "Severity evaluation was not completed"
            )
        }

        return result

    unified_context = event.get(
        "context",
        {}
    )

    event_type = classification.get(
        "type",
        "UNKNOWN"
    )

    severity_level = severity.get(
        "level",
        "LOW"
    )

    human_risk = unified_context.get(
        "humanRisk",
        {}
    )

    urgent_human_signal = any([
        human_risk.get("injured") is True,
        human_risk.get("unresponsive") is True,
        human_risk.get("trapped") is True,
        human_risk.get("immediateDanger") is True
    ])

    should_notify = (
        severity_level in NOTIFICATION_SEVERITIES
        and (
            event_type in EMERGENCY_TYPES
            or urgent_human_signal
        )
    )

    requires_human_review = (
        event_type == "UNKNOWN"
    )

    source = event.get(
        "source",
        ""
    )

    response_plan = build_response_plan(
        event_type,
        severity_level,
        unified_context,
        source
    )

    observations = build_observations(
        unified_context,
        source
    )

    notification = build_notification(
        event,
        classification,
        severity,
        response_plan,
        observations,
        should_notify
    )

    image_archive = build_image_archive(
        event,
        unified_context
    )

    decided_at = datetime.now(
        timezone.utc
    ).isoformat()

    database_record = build_database_record(
        event,
        classification,
        severity,
        response_plan,
        notification,
        image_archive,
        decided_at
    )

    if should_notify:
        action = "NOTIFY_RESPONDERS"

    elif requires_human_review:
        action = "HUMAN_REVIEW"

    else:
        action = "RECORD_ONLY"

    decision = {
        "status": "COMPLETED",
        "action": action,

        "shouldNotify": should_notify,
        "shouldPersist": True,
        "shouldArchiveImage": (
            image_archive["enabled"]
        ),

        "requiresHumanReview": (
            requires_human_review
        ),

        "responsePlan": response_plan,
        "notification": notification,
        "databaseRecord": database_record,
        "imageArchive": image_archive,

        "decidedAt": decided_at
    }

    result["decision"] = decision

    print("DECISION LOGIC COMPLETED")
    print(json.dumps(decision))

    return result
