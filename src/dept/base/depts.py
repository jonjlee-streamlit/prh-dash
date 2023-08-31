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


def config_from_route(route_id: str):
    """
    Translate the ID given by route.route_by_query() to a department config that can be used with src.dept.base.data.process().
    """
    return DEPT_CONFIG.get(route_id, None)
