"""Parse a Synthea FHIR R4 bundle into structured ClinicalData."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .schema import ClinicalData, Demographics, LabResult, Medication, VitalSigns

# LOINC codes → vital sign field names
_VITAL_LOINC: dict[str, str] = {
    "8310-5": "temperature_c",
    "8867-4": "heart_rate",
    "9279-1": "respiratory_rate",
    "59408-5": "oxygen_saturation",
    "8302-2": "height_cm",
    "29463-7": "weight_kg",
    "39156-5": "bmi",
    # BP is a panel — handled separately
    "55284-4": "blood_pressure",
    "85354-9": "blood_pressure",
}

_ENCOUNTER_CLASS_MAP: dict[str, str] = {
    "AMB": "Outpatient",
    "EMER": "ED",
    "IMP": "Inpatient",
    "ACUTE": "Inpatient",
    "NONAC": "Inpatient",
    "ICU": "ICU",
    "SS": "Outpatient",
    "VR": "Outpatient",
}

# Conditions that are social/administrative rather than clinical
_SOCIAL_SNOMED_PREFIXES = {
    "Received higher education",
    "Not in labor force",
    "Full-time employment",
    "Part-time employment",
    "Unemployed",
    "Retired",
    "Social isolation",
    "Stress",
    "Reports of violence",
    "Limited social contact",
    "Transport",
    "Housing",
    "Educated to",
}


def _is_clinical_condition(display: str) -> bool:
    return not any(display.startswith(p) for p in _SOCIAL_SNOMED_PREFIXES)


def _parse_date(dt_str: str | None) -> str | None:
    if not dt_str:
        return None
    return dt_str[:10]  # keep YYYY-MM-DD


def _age(birth_date_str: str) -> int:
    bd = date.fromisoformat(birth_date_str)
    today = date.today()
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))


def parse_bundle(path: str | Path) -> ClinicalData:
    with open(path) as f:
        bundle = json.load(f)

    resources: list[dict[str, Any]] = [e["resource"] for e in bundle.get("entry", [])]

    def get(rtype: str) -> list[dict]:
        return [r for r in resources if r["resourceType"] == rtype]

    # ── Patient ──────────────────────────────────────────────────────────────
    patient = get("Patient")[0]
    pid = patient["id"]

    birth_date = patient.get("birthDate", "1970-01-01")
    sex = patient.get("gender", "unknown")

    race_ext = next(
        (e for e in patient.get("extension", [])
         if "us-core-race" in e.get("url", "")),
        None,
    )
    race = None
    if race_ext:
        for sub in race_ext.get("extension", []):
            if sub.get("url") == "text":
                race = sub.get("valueString")
                break

    eth_ext = next(
        (e for e in patient.get("extension", [])
         if "us-core-ethnicity" in e.get("url", "")),
        None,
    )
    ethnicity = None
    if eth_ext:
        for sub in eth_ext.get("extension", []):
            if sub.get("url") == "text":
                ethnicity = sub.get("valueString")
                break

    lang = None
    for comm in patient.get("communication", []):
        coding = comm.get("language", {}).get("coding", [{}])[0]
        lang = coding.get("display") or coding.get("code")
        break

    addr = patient.get("address", [{}])[0]
    location = f"{addr.get('city', '')}, {addr.get('state', '')}".strip(", ") or None

    demographics = Demographics(
        age=_age(birth_date),
        sex=sex,
        race=race,
        ethnicity=ethnicity,
        language=lang,
        location=location,
    )

    # ── Encounter (most recent) ───────────────────────────────────────────────
    encounters = get("Encounter")
    encounters.sort(key=lambda e: e.get("period", {}).get("start", ""), reverse=True)
    clinical_context = "Outpatient"
    if encounters:
        enc = encounters[0]
        enc_class_code = (
            enc.get("class", {}).get("code", "AMB")
            if isinstance(enc.get("class"), dict)
            else "AMB"
        )
        clinical_context = _ENCOUNTER_CLASS_MAP.get(enc_class_code.upper(), "Outpatient")

    # ── Conditions ───────────────────────────────────────────────────────────
    conditions_raw = get("Condition")
    active_conditions: list[str] = []
    for c in conditions_raw:
        status = (c.get("clinicalStatus", {})
                   .get("coding", [{}])[0]
                   .get("code", "active"))
        if status not in ("active", "relapse", "recurrence"):
            continue
        display = (c.get("code", {})
                    .get("coding", [{}])[0]
                    .get("display", ""))
        if display and _is_clinical_condition(display):
            active_conditions.append(display)

    # ── Vitals ────────────────────────────────────────────────────────────────
    observations = get("Observation")
    # Sort by date descending to get most recent values
    observations.sort(
        key=lambda o: o.get("effectiveDateTime", o.get("issued", "")),
        reverse=True,
    )

    vitals_dict: dict[str, str] = {}
    for obs in observations:
        codes = obs.get("code", {}).get("coding", [])
        for coding in codes:
            loinc = coding.get("code", "")
            field = _VITAL_LOINC.get(loinc)
            if not field or field in vitals_dict:
                continue
            if field == "blood_pressure":
                # BP panel — pull systolic/diastolic from components
                components = obs.get("component", [])
                sys_val = dia_val = None
                for comp in components:
                    comp_code = comp.get("code", {}).get("coding", [{}])[0].get("code", "")
                    vq = comp.get("valueQuantity", {})
                    val = vq.get("value")
                    if comp_code == "8480-6" and val is not None:  # systolic
                        sys_val = str(int(val))
                    elif comp_code == "8462-4" and val is not None:  # diastolic
                        dia_val = str(int(val))
                if sys_val and dia_val:
                    vitals_dict["blood_pressure"] = f"{sys_val}/{dia_val} mmHg"
            else:
                vq = obs.get("valueQuantity", {})
                val = vq.get("value")
                unit = vq.get("unit", "")
                if val is not None:
                    vitals_dict[field] = f"{val} {unit}".strip()

    recent_vitals = VitalSigns(**vitals_dict)

    # ── Labs ──────────────────────────────────────────────────────────────────
    lab_obs = [
        o for o in observations
        if any(
            cat.get("coding", [{}])[0].get("code") == "laboratory"
            for cat in o.get("category", [])
        )
    ]
    # Deduplicate: keep most recent per test name
    seen_labs: set[str] = set()
    recent_labs: list[LabResult] = []
    for obs in lab_obs:
        name = (obs.get("code", {})
                   .get("coding", [{}])[0]
                   .get("display", "Unknown"))
        if name in seen_labs:
            continue
        seen_labs.add(name)
        vq = obs.get("valueQuantity", {})
        val = vq.get("value")
        unit = vq.get("unit")
        if val is None:
            # Try valueString
            val = obs.get("valueString") or obs.get("valueCodeableConcept", {}).get(
                "coding", [{}]
            )[0].get("display")
        if val is None:
            continue
        interp_codings = obs.get("interpretation", [{}])[0].get("coding", [{}])
        flag = interp_codings[0].get("code") if interp_codings else None
        if flag not in ("H", "L", "HH", "LL"):
            flag = None
        dt = _parse_date(obs.get("effectiveDateTime") or obs.get("issued"))
        recent_labs.append(
            LabResult(name=name, value=str(val), unit=unit, date=dt, flag=flag)
        )
        if len(recent_labs) >= 20:
            break

    # ── Medications ───────────────────────────────────────────────────────────
    med_requests = get("MedicationRequest")
    active_medications: list[Medication] = []
    for mr in med_requests:
        status = mr.get("status", "unknown")
        med_concept = mr.get("medicationCodeableConcept", {})
        name = med_concept.get("coding", [{}])[0].get("display", "Unknown")
        dosage_list = mr.get("dosageInstruction", [{}])
        dosage_text = dosage_list[0].get("text") if dosage_list else None
        active_medications.append(
            Medication(name=name, status=status, dosage=dosage_text)
        )

    # ── Allergies ─────────────────────────────────────────────────────────────
    allergy_resources = get("AllergyIntolerance")
    allergies: list[str] = []
    for a in allergy_resources:
        substance = (a.get("code", {})
                      .get("coding", [{}])[0]
                      .get("display", ""))
        if substance:
            allergies.append(substance)

    return ClinicalData(
        patient_id=pid,
        demographics=demographics,
        clinical_context=clinical_context,
        active_conditions=active_conditions,
        recent_vitals=recent_vitals,
        recent_labs=recent_labs,
        active_medications=active_medications,
        allergies=allergies,
    )
