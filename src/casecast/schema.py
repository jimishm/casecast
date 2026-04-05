from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class Demographics(BaseModel):
    age: int
    sex: str
    race: Optional[str] = None
    ethnicity: Optional[str] = None
    language: Optional[str] = None
    location: Optional[str] = None


class VitalSigns(BaseModel):
    temperature_c: Optional[str] = None
    heart_rate: Optional[str] = None
    blood_pressure: Optional[str] = None
    respiratory_rate: Optional[str] = None
    oxygen_saturation: Optional[str] = None
    height_cm: Optional[str] = None
    weight_kg: Optional[str] = None
    bmi: Optional[str] = None


class LabResult(BaseModel):
    name: str
    value: str
    unit: Optional[str] = None
    date: Optional[str] = None
    flag: Optional[str] = None  # "H", "L", or None


class Medication(BaseModel):
    name: str
    status: str  # "active" | "completed" | "stopped"
    dosage: Optional[str] = None


class ClinicalData(BaseModel):
    """Structured clinical data extracted from a FHIR bundle."""
    patient_id: str
    demographics: Demographics
    clinical_context: str  # "Outpatient", "ED", "Inpatient", "ICU"
    active_conditions: list[str]
    recent_vitals: VitalSigns
    recent_labs: list[LabResult]
    active_medications: list[Medication]
    allergies: list[str]


class Vignette(BaseModel):
    """A complete clinical vignette ready for AI labeling or medical education."""
    patient_id: str
    demographics: Demographics
    clinical_context: str
    conditions: list[str]
    vital_signs: VitalSigns
    labs: list[LabResult]
    medications: list[Medication]
    allergies: list[str]
    # Claude-generated narrative
    chief_complaint: str
    hpi: str
    review_of_systems: str
    physical_exam: str
