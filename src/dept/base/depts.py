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
    route.ACUPUNCTURE: DeptConfig("Acupunture", ["CC_72045"]),
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
}
