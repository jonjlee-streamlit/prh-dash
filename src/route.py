"""
Route an incoming request to based on the URL query parameters to the corresponding dashboard
"""

import streamlit as st

DEFAULT = "default"
UPDATE = "update"
FETCH = "fetch"

# IDs for department dashboards
ALL_CLINICS = "clinics"
ACUPUNCTURE = "acupuncture"
ADMIN = "admin"
ANESTHESIOLOGY = "anesthesiology"
ATHLETIC_TRAINER = "athletic_trainer"
BEHAVIORAL_HEALTH = "bh"
BIRTHPLACE = "birthplace"
CARDIO_PULM_REHAB = "cardio_pulm_rehab"
CARDIOLOGY = "heart_center"
CARE_COORD = "care_coord"
CENTER_LEARNING_INNOVATION = "cli"
CLINIC_ADMIN = "clinic_admin"
CLINIC_BUSINESS_OFFICE = "clinic_business"
CLINICAL_COORD = "clinical_coord"
CLINICAL_INFORMATICS = "informatics"
ED_DEPT = "ed_dept"
ED_PHYSICIANS = "ed_phys"
ENVIRONMENTAL_SERVICES = "environmental_svc"
EXTERNAL_RELATIONS = "external_relations"
FAMILY_MED = "family_med"
FINANCE = "finance"
FISCAL = "fiscal"
FOUNDATION = "foundation"
HEALTH_CENTER = "health_center"
HIM = "him"
HOSPITALIST = "hospitalist"
HR = "hr"
ICU = "icu"
IMAGING = "imaging"
INFECTION_CONTROL = "infection_control"
IT = "it"
LAB = "lab"
MAINTENANCE = "maintenance"
MEDICAL_STAFF = "medical_staff"
MSU = "medsurg"
NURSERY = "nursery"
NURSING_ADMIN = "nursing_admin"
NUTRITION = "nutrition"
ORTHO = "ortho"
PACU = "pacu"
PAIN = "pain"
PATIENT_FINANCIAL = "patient_financial"
PEDIATRICS = "pediatrics"
PHARMACY = "pharmacy"
PHYSICIANS = "physicians"
PODIATRY = "foot_ankle"
QUALITY_RESOURCES = "quality_resources"
REDSAGE = "redsage"
REGISTRATION = "registration"
RELIABILITY = "reliability"
RESIDENCY = "residency"
RESOURCE_MATERIALS = "resource_materials"
RESPIRATORY = "respiratory"
REVENUE_CYCLE = "revenue_cycle"
SAME_DAY = "same_day"
SLEEP = "sleep"
SLEEP_LAB = "sleep_lab"
SUMMIT = "summit"
SUPPLY_DIST = "supply_dist"
SURGERY = "surgery"
SURGICAL_SVC = "surgical_svc"
UROLOGY = "urology"
DEPTS = (
    ALL_CLINICS,
    ADMIN,
    ANESTHESIOLOGY,
    ATHLETIC_TRAINER,
    BEHAVIORAL_HEALTH,
    BIRTHPLACE,
    CARDIO_PULM_REHAB,
    CARE_COORD,
    CENTER_LEARNING_INNOVATION,
    CLINIC_ADMIN,
    CLINIC_BUSINESS_OFFICE,
    CLINICAL_COORD,
    CLINICAL_INFORMATICS,
    ED_DEPT,
    ED_PHYSICIANS,
    ENVIRONMENTAL_SERVICES,
    EXTERNAL_RELATIONS,
    RESIDENCY,
    FINANCE,
    FISCAL,
    FOUNDATION,
    HIM,
    HOSPITALIST,
    HR,
    ICU,
    IMAGING,
    IT,
    ORTHO,
    LAB,
    MAINTENANCE,
    MEDICAL_STAFF,
    MSU,
    NURSERY,
    NURSING_ADMIN,
    NUTRITION,
    PAIN,
    HEALTH_CENTER,
    CARDIOLOGY,
    PEDIATRICS,
    SLEEP,
    UROLOGY,
    PATIENT_FINANCIAL,
    PHARMACY,
    PHYSICIANS,
    PACU,
    FAMILY_MED,
    PODIATRY,
    SURGERY,
    QUALITY_RESOURCES,
    REDSAGE,
    REGISTRATION,
    RELIABILITY,
    RESOURCE_MATERIALS,
    RESPIRATORY,
    REVENUE_CYCLE,
    SAME_DAY,
    SLEEP_LAB,
    SUMMIT,
    SURGICAL_SVC,
)

# IDs for API calls
CLEAR_CACHE = "clear_cache"
API = CLEAR_CACHE


def route_by_query(query_params: dict) -> str:
    """
    Returns a route ID given the query parameters in the URL.
    Expects query_params to be in the format { "param": ["value 1", "value 2" ] }, corresponding to Streamlit docs:
    https://docs.streamlit.io/library/api-reference/utilities/st.experimental_get_query_params
    """
    update = query_params.get("update")
    dept = query_params.get("dept")
    api = query_params.get("api")
    if update == "1":
        return UPDATE
    if update == "2":
        return FETCH
    if api and api in API:
        return api
    if dept and dept in DEPTS:
        return dept

    return DEFAULT
