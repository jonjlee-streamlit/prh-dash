"""
Route an incoming request to based on the URL query parameters to the corresponding dashboard
"""
import streamlit as st

DEFAULT = "default"
UPDATE = "update"

# IDs for department dashboards
ACUPUNCTURE = "acupuncture"
BEHAVIORAL_HEALTH = "bh"
BIRTHPLACE = "birthplace"
CARDIO_PULM_REHAB = "cardio_pulm_rehab"
CARDIOLOGY = "heart_center"
ED = "ed"
FAMILY_MED = "family_med"
GENETICS = "genetics"
HOSPITALIST = "hospitalist"
ICU = "icu"
IMAGING = "imaging"
LAB = "lab"
MASSAGE = "massage"
MSU = "medsurg"
NUTRITION = "nutrition"
PEDIATRICS = "pediatrics"
PHARMACY = "pharmacy"
PODIATRY = "foot_ankle"
REDSAGE = "redsage"
REHAB = "rehab"
RESIDENCY = "residency"
RESPIRATORY = "respiratory"
SAME_DAY = "same_day"
SLEEP = "sleep"
SUMMIT = "summit"
SURGERY = "surgery"
UROLOGY = "urology"
DEPTS = (
    ACUPUNCTURE,
    BEHAVIORAL_HEALTH,
    BIRTHPLACE,
    CARDIOLOGY,
    ED,
    FAMILY_MED,
    GENETICS,
    ICU,
    IMAGING,
    LAB,
    MASSAGE,
    MSU,
    PEDIATRICS,
    PODIATRY,
    REDSAGE,
    REHAB,
    RESIDENCY,
    SLEEP,
    SUMMIT,
    SURGERY,
    UROLOGY,
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
    if update and len(update) > 0 and update[0] == "1":
        return UPDATE
    if api and len(api) > 0 and api[0] in API:
        return api[0]
    if dept and len(dept) > 0 and dept[0] in DEPTS:
        return dept[0]

    return DEFAULT
