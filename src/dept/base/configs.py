"""
Definitions for supported departments
"""
from dataclasses import dataclass, field
from ... import route


@dataclass(frozen=True)
class DeptConfig:
    name: str
    wd_ids: list = field(default_factory=list)


DEPT_CONFIG = {
    route.BEHAVIORAL_HEALTH: DeptConfig(
        "Palouse Psychiatry and Behavioral Health", ["CC_72760"]
    ),
    route.BIRTHPLACE: DeptConfig("Birthplace", ["CC_60790"]),
    route.CARDIO_PULM_REHAB: DeptConfig("Cardiopulmonary Rehabilitation", ["CC_71850"]),
    route.CARDIOLOGY: DeptConfig("Palouse Heart Center", ["CC_72790"]),
    route.ED_DEPT: DeptConfig("Emergency Department", ["CC_72300"]),
    route.ED_PHYSICIANS: DeptConfig("Emergency Physicians", ["CC_72390"]),
    route.FAMILY_MED: DeptConfig("Pullman Family Medicine", ["CC_72770"]),
    route.HOSPITALIST: DeptConfig("Hospitalist", ["CC_60150"]),
    route.ICU: DeptConfig("ICU", ["CC_60100"]),
    route.IMAGING: DeptConfig(
        "Imaging",
        [
            "CC_71300",  # CT
            "CC_71200",  # MRI
            "CC_71400",  # Imaging Services
            "CC_71430",  # Ultrasound
            "CC_71600",  # NM / PET
            "CC_71450",  # Mammography
        ],
    ),
    route.LAB: DeptConfig("Laboratory", ["CC_70700"]),
    route.MSU: DeptConfig("Medical Surgical Unit", ["CC_60700"]),
    route.NUTRITION: DeptConfig("Nutrition Therapy", ["CC_83210"]),
    route.PEDIATRICS: DeptConfig("Palouse Pediatrics", ["CC_72745", "CC_72740"]),
    route.PHARMACY: DeptConfig("Pharmacy", ["CC_71700"]),
    route.PODIATRY: DeptConfig("Pullman Foot and Ankle Clinic", ["CC_72720"]),
    route.REDSAGE: DeptConfig("Red Sage", ["CC_83200"]),
    route.RESIDENCY: DeptConfig("Family Medicine Residency", ["CC_74910"]),
    route.RESPIRATORY: DeptConfig("Respiratory Care Services", ["CC_71800"]),
    route.SAME_DAY: DeptConfig("Same Day Services", ["CC_70260"]),
    route.SLEEP: DeptConfig("Palouse Sleep Medicine and Pulmonology", ["CC_72785"]),
    route.SLEEP_LAB: DeptConfig("Sleep Lab", ["CC_71810"]),
    route.SUMMIT: DeptConfig(
        "Summit",
        [
            "CC_72000",  # Rehab PT/OT/ST
            "CC_72015",  # Stadium Way
            "CC_72045",  # Acupuncture
            "CC_72025",  # Massage
            "CC_72055",  # Genetics
        ],
    ),
    route.SURGERY: DeptConfig("Pullman Surgical Associates", ["CC_72780"]),
    route.SURGICAL_SVC: DeptConfig("Surgical Services", ["CC_70200"]),
    route.UROLOGY: DeptConfig("Palouse Urology", ["CC_72750"]),
    route.ALL_CLINICS: DeptConfig(
        "Outpatient Clinics",
        [
            "CC_74910",  # Family Residency
            "CC_72800",  # Inland Ortho ID
            "CC_72795",  # Inland Ortho WA
            "CC_72775",  # Palouse Health Center
            "CC_72790",  # Palouse Heart Center
            "CC_72745",  # Palouse Peds ID
            "CC_72740",  # Palouse Peds WA
            "CC_72760",  # Palouse Psych & Behavioral Health
            "CC_72785",  # Palouse Sleep
            "CC_72750",  # Palouse Urology
            "CC_72770",  # Pullman Family Med
            "CC_72720",  # Pullman Foot & Ankle
            "CC_72780",  # Pullman Surgical Assoc
        ],
    ),
}


def config_from_route(route_id: str):
    """
    Return the configuration for a given department by route_id.
    route_id is generated by route.route_by_query() based on the "dept" URL query param.
    """
    return DEPT_CONFIG.get(route_id, None)
