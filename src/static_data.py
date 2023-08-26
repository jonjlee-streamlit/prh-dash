"""
Statically defined data, such as mappings from ID to department names
"""
# Map of Workday IDs to the canonical department or cost center name
WDID_TO_DEPT_NAME = {
    "CC_71750": "340B",
    "CC_72045": "Acupuncture",
    "CC_86000": "Administration",
    "CC_70400": "Anesthesiology",
    "CC_72035": "Athletic Trainer Program",
    "CC_10000": "Balance Sheet Cost Center",
    "CC_60790": "BirthPlace",
    "CC_70710": "Blood Products",
    "CC_86050": "Board of Directors",
    "CC_71850": "Cardiopulmonary Rehab Services",
    "CC_83600": "Care Coordination",
    "CC_86130": "Center of Learning & Innovation",
    "CC_86090": "Clinic Administration",
    "CC_85400": "Clinic Business Office",
    "CC_87185": "Clinical Coordinators",
    "CC_87190": "Clinical Informatics",
    "CC_86530": "Comp & Benefits",
    "CC_93300": "Condominium",
    "CC_58200": "Contractual Adjustments",
    "CC_71300": "CT Scan",
    "CC_88000": "Depreciation",
    "CC_89000": "discounts & rebates",
    "CC_71110": "EKG Services",
    "CC_72300": "Emergency Department",
    "CC_72390": "Emergency Physicians",
    "CC_86200": "Employee Health",
    "CC_84600": "Environmental Services",
    "CC_86300": "External Relations",
    "CC_74910": "Family Residency",
    "CC_85910": "Finance",
    "CC_85900": "Fiscal Services",
    "CC_83200": "Food Services",
    "CC_84960": "Foundation",
    "CC_72055": "Genetic Counseling",
    "CC_58100": "Government Contractual Adjustments",
    "CC_83640": "Health Coaching",
    "CC_86900": "Health Information Management",
    "CC_60150": "Hospitalists",
    "CC_86500": "Human Resources",
    "CC_71400": "Imaging Services",
    "CC_87170": "Infection Control",
    "CC_84800": "Information Technology",
    "CC_72800": "Inland Ortho-ID",
    "CC_72795": "Inland Ortho-WA",
    "CC_60100": "Intensive Care Unit",
    "CC_70700": "Laboratory",
    "CC_83500": "Laundry & Linen",
    "CC_84310": "Maintenance",
    "CC_71450": "Mammography",
    "CC_72025": "Massage Therapy",
    "CC_87000": "Medical Staff Services",
    "CC_60700": "Medical Surgical Unit",
    "CC_93400": "MOB I Condo Association",
    "CC_93100": "MOB II",
    "CC_71200": "MRI",
    "CC_71600": "Nuclear Medicine",
    "CC_61700": "Nursery",
    "CC_87180": "Nursing Administration",
    "CC_83210": "Nutrition Therapy",
    "CC_92000": "other non-op rev/exp",
    "CC_70520": "Oxygen",
    "CC_70270": "Pain Management",
    "CC_72775": "Palouse Health Center",
    "CC_72790": "Palouse Heart Center",
    "CC_93000": "Palouse Millennium",
    "CC_72745": "Palouse Pediatrics -ID",
    "CC_72740": "Palouse Pediatrics-WA",
    "CC_72760": "Palouse Psychiatry & Behavioral Health",
    "CC_72785": "Palouse Sleep Medicine & Pulmonology",
    "CC_93200": "Palouse Specialties LLC",
    "CC_72750": "Palouse Urology",
    "CC_85300": "Patient Financial Services",
    "CC_71700": "Pharmacy",
    "CC_87100": "Physicians",
    "CC_84320": "Plant-Building",
    "CC_70300": "Post Anesthesia Care Unit",
    "CC_72770": "Pullman Family Medicine",
    "CC_72720": "Pullman Foot & Ankle Clinic",
    "CC_72780": "Pullman Surgical Associates",
    "CC_87140": "Quality Resources",
    "CC_85600": "Registration",
    "CC_72000": "Rehabilitation Services",
    "CC_87145": "Reliability",
    "CC_84200": "Resource & Materials Management",
    "CC_71800": "Respiratory Care Services",
    "CC_85500": "Revenue Cycle",
    "CC_70260": "Same Day Services",
    "CC_71810": "Sleep Lab",
    "CC_72015": "Summit Stadium Way",
    "CC_70500": "Supply & Distribution",
    "CC_70200": "Surgical Services",
    "CC_62100": "Swing Bed",
    "CC_73920": "Transports",
    "CC_72301": "Travel Clinic",
    "CC_71430": "Ultrasound",
    "CC_86330": "Volunteers & Auxiliary",
    "CC_58000": "Write Offs",
}

# Map of various identifiers to their Workday ID. 
# These aliases represent IDs used in Workday, Meditech, adhoc Excel reports, etc.
# Use WDID_TO_DEPT_NAME to get the canonical name from the ID.
ALIASES_TO_WDID = {
    "Acupuncture": "CC_72045",
    "PRH ACUPUNCTURE": "CC_72045",
    "Administration": "CC_86000",
    "PRH ADMINISTRATION": "CC_86000",
    "Athletic Trainer Program": "CC_72035",
    "PRH CERT ATHLETIC TRAINING": "CC_72035",
    "BirthPlace": "CC_60790",
    "PRH BIRTHPLACE": "CC_60790",
    "Cardiopulmonary Rehab Services": "CC_71850",
    "Cardio Pulm Rehab": "CC_71850",
    "PRH CARDIO PULM REHAB": "CC_71850",
    "Center of Learning & Innovation": "CC_86130",
    "PRH CENTER OF INNOVATION": "CC_86130",
    "Clinic Administration": "CC_86090",
    "PRHCN ADMINISTRATION": "CC_86090",
    "Clinic Business Office": "CC_85400",
    "PRHCN CLINIC BUSINESS OFFICE": "CC_85400",
    "Clinical Informatics": "CC_87190",
    "PRH CLINICAL INFORMATIC": "CC_87190",
    "Comp & Benefits": "CC_86530",
    "PRH COMP & BENEFITS": "CC_86530",
    "CT Scan": "CC_71300",
    "PRH CT SCAN": "CC_71300",
    "Emergency Department": "CC_72300",
    "Emergency Dept": "CC_72300",
    "PRH EMERGENCY DEPARTMEN": "CC_72300",
    "Emergency Physicians": "CC_72390",
    "PRH EMERGENCY PHYSICIAN": "CC_72390",
    "Employee Health": "CC_86200",
    "PRH EMPLOYEE HEALTH": "CC_86200",
    "Environmental Services": "CC_84600",
    "PRH ENVIRONMENTAL SVCS": "CC_84600",
    "External Relations": "CC_86300",
    "PRH COMMUNITY RELATIONS": "CC_86300",
    "Family Residency": "CC_74910",
    "PRH FAMILY RESIDENCY": "CC_74910",
    "Fiscal Services": "CC_85900",
    "PRH FISCAL SERVICES": "CC_85900",
    "Food Services": "CC_83200",
    "Red Sage": "CC_83200",
    "PRH RED SAGE CAFE": "CC_83200",
    "Genetic Counseling": "CC_72055",
    "PRH GENETIC COUNSELING": "CC_72055",
    "Health Coaching": "CC_83640",
    "PRH HRSA HEALTH COACHING": "CC_83640",
    "Health Information Management": "CC_86900",
    "PRH HEALTH INFORMATION ": "CC_86900",
    "Hospitalist": "CC_60150",
    "Hospitalists": "CC_60150",
    "PRH HOSPITALISTS": "CC_60150",
    "Imaging Services": "CC_71400",
    "PRH IMAGING SERVICES": "CC_71400",
    "Infection Control": "CC_87170",
    "PRH INFECTION CONTROL": "CC_87170",
    "Information Technology": "CC_84800",
    "PRH INFORMATION TECHNOL": "CC_84800",
    "ICU": "CC_60100",
    "Intensive Care Unit": "CC_60100",
    "PRH INTENSIVE CARE UNIT": "CC_60100",
    "Laboratory": "CC_70700",
    "PRH LABORATORY": "CC_70700",
    "Laundry & Linen": "CC_83500",
    "PRH LAUNDRY & LINEN": "CC_83500",
    "Maintenance": "CC_84310",
    "PRH MAINTENANCE": "CC_84310",
    "Mammography": "CC_71450",
    "PRH MAMMOGRAPHY": "CC_71450",
    "Massage Therapy": "CC_72025",
    "PRH MASSAGE THERAPY": "CC_72025",
    "Medical Staff Services": "CC_87000",
    "PRH MEDICAL STAFF SERV": "CC_87000",
    "Medical Surgical Unit": "CC_60700",
    "Med-Surg Unit": "CC_60700",
    "PRH MEDICAL/SURGICAL UN": "CC_60700",
    "MRI": "CC_71200",
    "PRH MRI": "CC_71200",
    "Nuclear Medicine": "CC_71600",
    "Nuclear Medicine & PET": "CC_71600",
    "PRH NUCLEAR MEDICINE": "CC_71600",
    "Nursing Administration": "CC_87180",
    "PRH NURSING ADMINISTRAT": "CC_87180",
    "Nutrition Therapy": "CC_83210",
    "PRH NUTRITION THERAPY": "CC_83210",
    "Palouse Health Center": "CC_72775",
    "PRHCN PALOUSE HEALTH CENTER": "CC_72775",
    "Palouse Heart Center": "CC_72790",
    "PRHCN PALOUSE HEART CENTER": "CC_72790",
    "Palouse Pediatrics -ID": "CC_72745",
    "Pediatrics ID": "CC_72745",
    "PRHCN PEDIATRICS ID": "CC_72745",
    "Palouse Pediatrics-WA": "CC_72740",
    "Pediatrics WA": "CC_72740",
    "PRHCN PEDIATRICS WA": "CC_72740",
    "Palouse Psychiatry & Behavioral Health": "CC_72760",
    "Behavioral Health": "CC_72760",
    "PRHCN BEHAVIORAL HEALTH": "CC_72760",
    "Palouse Sleep Medicine & Pulmonology": "CC_72785",
    "Palouse Sleep": "CC_72785",
    "PRHCN PALOUSE SLEEP": "CC_72785",
    "Palouse Urology": "CC_72750",
    "Urology": "CC_72750",
    "Patient Financial Services": "CC_85300",
    "PRH PATIENT FINANCL SVC": "CC_85300",
    "Pharmacy": "CC_71700",
    "PRH PHARMACY": "CC_71700",
    "Physicians": "CC_87100",
    "PRH PHYSICIANS": "CC_87100",
    "Pullman Family Medicine": "CC_72770",
    "PRHCN PULLMAN FAMILY MED": "CC_72770",
    "Pullman Foot & Ankle": "CC_72720",
    "Pullman Foot & Ankle Clinic": "CC_72720",
    "PRHCN PULLMAN FOOT & ANKLE": "CC_72720",
    "Pullman Surgical Associates": "CC_72780",
    "PRHCN SURGICAL GROUP": "CC_72780",
    "Quality Resources": "CC_87140",
    "PRH QUALITY RESOURCES": "CC_87140",
    "Registration": "CC_85600",
    "PRH REGISTRATION": "CC_85600",
    "Rehabilitation Services": "CC_72000",
    "PRH REHABILITATION SVCS": "CC_72000",
    "Reliability": "CC_87145",
    "PRH RELIABILITY": "CC_87145",
    "Resource & Materials Management": "CC_84200",
    "PRH RESOURCE & MATERIAL": "CC_84200",
    "Respiratory Care Services": "CC_71800",
    "PRH RESPIRATORY CARE SV": "CC_71800",
    "Revenue Cycle": "CC_85500",
    "PRH REVENUE CYCLE": "CC_85500",
    "Same Day Services": "CC_70260",
    "Same Day Surgery": "CC_70260",
    "PRH SAME DAY SURGERY": "CC_70260",
    "Sleep Lab": "CC_71810",
    "PRH SLEEP LAB": "CC_71810",
    "Summit Stadium Way": "CC_72015",
    "PRH SUMMIT THERAPY STADIUM WAY": "CC_72015",
    "Surgical Services": "CC_70200",
    "PRH SURGICAL SERVICES": "CC_70200",
    "Travel Clinic": "CC_72301",
    "PRH TRAVEL ClaIC": "CC_72301",
    "Ultrasound": "CC_71430",
    "PRH ULTRASOUND": "CC_71430",
    "Volunteers & Auxiliary": "CC_86330",
    "PRH VOLUNTEERS/AUXILIARY": "CC_86330",
}
