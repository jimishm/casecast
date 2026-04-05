"""Generate narrative vignette components from structured clinical data using Claude."""
from __future__ import annotations

import json

import anthropic

from .schema import ClinicalData, LabResult, Medication, Vignette, VitalSigns

_CLIENT = None


def _client() -> anthropic.Anthropic:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = anthropic.Anthropic()
    return _CLIENT


def _format_vitals(v: VitalSigns) -> str:
    lines = []
    if v.blood_pressure:
        lines.append(f"BP: {v.blood_pressure}")
    if v.heart_rate:
        lines.append(f"HR: {v.heart_rate}")
    if v.respiratory_rate:
        lines.append(f"RR: {v.respiratory_rate}")
    if v.temperature_c:
        lines.append(f"Temp: {v.temperature_c}")
    if v.oxygen_saturation:
        lines.append(f"SpO2: {v.oxygen_saturation}")
    if v.height_cm:
        lines.append(f"Height: {v.height_cm}")
    if v.weight_kg:
        lines.append(f"Weight: {v.weight_kg}")
    if v.bmi:
        lines.append(f"BMI: {v.bmi}")
    return ", ".join(lines) if lines else "Not available"


def _format_labs(labs: list[LabResult]) -> str:
    if not labs:
        return "None available"
    lines = []
    for lab in labs[:15]:
        flag = f" [{lab.flag}]" if lab.flag else ""
        unit = f" {lab.unit}" if lab.unit else ""
        lines.append(f"  {lab.name}: {lab.value}{unit}{flag}")
    return "\n".join(lines)


def _format_meds(meds: list[Medication]) -> str:
    active = [m for m in meds if m.status == "active"]
    if not active:
        return "None"
    lines = []
    for m in active:
        dosage = f" — {m.dosage}" if m.dosage else ""
        lines.append(f"  {m.name}{dosage}")
    return "\n".join(lines)


def _build_prompt(data: ClinicalData) -> str:
    d = data.demographics
    sex_label = "male" if d.sex == "male" else "female" if d.sex == "female" else d.sex
    race_eth = " ".join(filter(None, [d.race, d.ethnicity])) or "not recorded"

    conditions = "\n".join(f"  - {c}" for c in data.active_conditions) or "  None documented"
    allergies = ", ".join(data.allergies) or "NKDA"

    return f"""You are a clinical educator writing a realistic patient vignette for medical education.

Given the structured patient data below, write the following four sections. Be clinically accurate, specific, and use realistic medical language appropriate for a clinical case. Do not invent conditions that are not in the data.

PATIENT DATA:
- Demographics: {d.age}-year-old {sex_label}, {race_eth}, speaks {d.language or "English"}, from {d.location or "Massachusetts"}
- Clinical Setting: {data.clinical_context}
- Active Medical Problems:
{conditions}
- Vital Signs (most recent): {_format_vitals(data.recent_vitals)}
- Recent Labs:
{_format_labs(data.recent_labs)}
- Active Medications:
{_format_meds(data.active_medications)}
- Allergies: {allergies}

Write exactly four sections with these exact headers:

## Chief Complaint
One to two sentences in the patient's own words describing why they are seeking care today. Choose the most clinically significant active problem as the presenting concern.

## History of Present Illness
Two to three paragraphs. Describe the onset, duration, character, aggravating/relieving factors, and associated symptoms of the presenting problem. Weave in relevant past medical history and current medications naturally. Write in third person (e.g., "The patient reports...").

## Review of Systems
List pertinent positives and negatives by system. Format as bullet points grouped by system (e.g., Constitutional, Cardiovascular, Respiratory, GI, MSK, Neuro). Include at least 4 systems.

## Physical Examination
One to two paragraphs describing expected exam findings consistent with the vital signs and conditions above. Include general appearance, relevant system findings, and any notable abnormalities.
"""


def generate_narrative(data: ClinicalData) -> Vignette:
    """Call Claude to generate the narrative sections, return a complete Vignette."""
    prompt = _build_prompt(data)

    with _client().messages.stream(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        response_text = stream.get_final_message().content[0].text

    sections = _parse_sections(response_text)

    return Vignette(
        patient_id=data.patient_id,
        demographics=data.demographics,
        clinical_context=data.clinical_context,
        conditions=data.active_conditions,
        vital_signs=data.recent_vitals,
        labs=data.recent_labs,
        medications=data.active_medications,
        allergies=data.allergies,
        chief_complaint=sections.get("Chief Complaint", ""),
        hpi=sections.get("History of Present Illness", ""),
        review_of_systems=sections.get("Review of Systems", ""),
        physical_exam=sections.get("Physical Examination", ""),
    )


def _parse_sections(text: str) -> dict[str, str]:
    """Split Claude's response into labelled sections."""
    import re

    headers = [
        "Chief Complaint",
        "History of Present Illness",
        "Review of Systems",
        "Physical Examination",
    ]
    pattern = r"##\s*(" + "|".join(re.escape(h) for h in headers) + r")\s*\n"
    parts = re.split(pattern, text)

    result: dict[str, str] = {}
    # parts: [pre, header1, body1, header2, body2, ...]
    i = 1
    while i < len(parts) - 1:
        header = parts[i].strip()
        body = parts[i + 1].strip()
        result[header] = body
        i += 2
    return result
