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
    route.ADMIN: DeptConfig("Administration", ["CC_86000"]),
    route.ANESTHESIOLOGY: DeptConfig("Anesthesiology", ["CC_70400"]),
    route.ATHLETIC_TRAINER: DeptConfig("Athletic Trainer Program", ["CC_72035"]),
    route.BEHAVIORAL_HEALTH: DeptConfig(
        "Palouse Psychiatry and Behavioral Health", ["CC_72760"]
    ),
    route.BIRTHPLACE: DeptConfig("Birthplace", ["CC_60790"]),
    route.CARDIO_PULM_REHAB: DeptConfig("Cardiopulmonary Rehabilitation", ["CC_71850"]),
    route.CARDIOLOGY: DeptConfig("Palouse Heart Center", ["CC_72790"]),
    route.CARE_COORD: DeptConfig("Care Coordination", ["CC_83600"]),
    route.CENTER_LEARNING_INNOVATION: DeptConfig("Center of Learning & Innovation", ["CC_86130"]),
    route.CLINIC_ADMIN: DeptConfig("Clinic Administration", ["CC_86090"]),
    route.CLINIC_BUSINESS_OFFICE: DeptConfig("Clinic Business Office", ["CC_85400"]),
    route.CLINICAL_COORD: DeptConfig("Clinical Coordinators", ["CC_87185"]),
    route.CLINICAL_INFORMATICS: DeptConfig("Clinical Informatics", ["CC_87190"]),
    route.ED_DEPT: DeptConfig("Emergency Department", ["CC_72300"]),
    route.ED_PHYSICIANS: DeptConfig("Emergency Physicians", ["CC_72390"]),
    route.ENVIRONMENTAL_SERVICES: DeptConfig("Environmental Services", ["CC_84600"]),
    route.EXTERNAL_RELATIONS: DeptConfig("External Relations", ["CC_86300"]),
    route.FAMILY_MED: DeptConfig("Pullman Family Medicine", ["CC_72770"]),
    route.FINANCE: DeptConfig("Finance", ["CC_85910"]),
    route.FISCAL: DeptConfig("Fiscal Services", ["CC_85900"]),
    route.FOUNDATION: DeptConfig("Foundation", ["CC_84960"]),
    route.HEALTH_CENTER: DeptConfig("Palouse Health Center", ["CC_72775"]),
    route.HIM: DeptConfig("Health Information Management", ["CC_86900"]),
    route.HOSPITALIST: DeptConfig("Hospitalist", ["CC_60150"]),
    route.HR: DeptConfig("Human Resources", ["CC_86500"]),
    route.ICU: DeptConfig("ICU", ["CC_60100"]),
    route.IMAGING: DeptConfig(
        "Imaging",
        [
            DeptConfig(
                "CT/Imaging",
                [
                    "CC_71300",  # CT
                    "CC_71400",  # Imaging Services
                ],
            ),
            "CC_71200",  # MRI
            "CC_71430",  # Ultrasound
            "CC_71600",  # NM / PET
            "CC_71450",  # Mammography
        ],
    ),
    route.INFECTION_CONTROL: DeptConfig("Infection Control", ["CC_87170"]),
    route.IT: DeptConfig("Information Technology", ["CC_84800"]),
    route.LAB: DeptConfig("Laboratory", ["CC_70700"]),
    route.MAINTENANCE: DeptConfig("Maintenance", ["CC_84310"]),
    route.MEDICAL_STAFF: DeptConfig("Medical Staff Services", ["CC_87000"]),
    route.MSU: DeptConfig("Medical Surgical Unit", ["CC_60700"]),
    route.NURSERY: DeptConfig("Nursery", ["CC_61700"]),
    route.NURSING_ADMIN: DeptConfig("Nursing Administration", ["CC_87180"]),
    route.NUTRITION: DeptConfig("Nutrition Therapy", ["CC_83210"]),
    route.ORTHO: DeptConfig("Inland Orthopedics", ["CC_72800", "CC_72795"]),
    route.PACU: DeptConfig("Post Anesthesia Care Unit", ["CC_70300"]),
    route.PAIN: DeptConfig("Pain Management", ["CC_70270"]),
    route.PATIENT_FINANCIAL: DeptConfig("Patient Financial Services", ["CC_85300"]),
    route.PHYSICIANS: DeptConfig("Physicians", ["CC_87100"]),
    route.PEDIATRICS: DeptConfig("Palouse Pediatrics", ["CC_72745", "CC_72740"]),
    route.PHARMACY: DeptConfig("Pharmacy", ["CC_71700"]),
    route.PODIATRY: DeptConfig("Pullman Foot and Ankle Clinic", ["CC_72720"]),
    route.QUALITY_RESOURCES: DeptConfig("Quality Resources", ["CC_87140"]),
    route.REDSAGE: DeptConfig("Red Sage", ["CC_83200"]),
    route.REGISTRATION: DeptConfig("Registration", ["CC_85600"]),
    route.RELIABILITY: DeptConfig("Reliability", ["CC_87145"]),
    route.RESIDENCY: DeptConfig("Family Medicine Residency", ["CC_74910"]),
    route.RESOURCE_MATERIALS: DeptConfig("Resource & Materials Management", ["CC_84200"]),
    route.RESPIRATORY: DeptConfig("Respiratory Care Services", ["CC_71800"]),
    route.REVENUE_CYCLE: DeptConfig("Revenue Cycle", ["CC_85500"]),
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
    route.SUPPLY_DIST: DeptConfig("Supply & Distribution", ["CC_70500"]),
    route.SURGERY: DeptConfig("Pullman Surgical Associates", ["CC_72780"]),
    route.SURGICAL_SVC: DeptConfig("Surgical Services", ["CC_70200"]),
    route.UROLOGY: DeptConfig("Palouse Urology", ["CC_72750"]),
    route.ALL_CLINICS: DeptConfig(
        "All Outpatient Clinics",
        [
            "CC_74910",  # Family Residency
            DeptConfig(
                "Inland Orthopedics",
                [
                    "CC_72800",  # Inland Ortho ID
                    "CC_72795",  # Inland Ortho WA
                ],
            ),
            "CC_72775",  # Palouse Health Center
            "CC_72790",  # Palouse Heart Center
            DeptConfig(
                "Palouse Pediatrics",
                [
                    "CC_72745",  # Palouse Peds ID
                    "CC_72740",  # Palouse Peds WA
                ],
            ),
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
