from dataclasses import dataclass, asdict


@dataclass
class FTEParams:
    """Represents configurable parameters used for FTE calculator"""

    prior_year_volume: int = 14577
    prior_year_uos: int = 26157
    budget_volume: int = 16500
    budget_uos: int = 29628
    budget_fte: float = 32.0
    std_fte_hours: int = 2080
    std_salary_per_hour: float = 37.06
    percent_productive_hours: float = 0.884423297881127


@dataclass
class FTEResult:
    productive_hours_needed_for_volume: int
    standard_volume: int
    statistical_impact_volume: int
    salary_impact_dollars: float
    reimbursement_dollars: float
    net_impact_dollars: float


def calc(fte_requested, params: FTEParams | None = None):
    """
    Main calculator for this module. Return calculations representing the impact of adding additional FTE
    """
    params = params if params is not None else FTEParams()

    budget_fte = params.budget_fte
    budgeted_hours = budget_fte * params.std_fte_hours
    productive_hours = params.percent_productive_hours * budgeted_hours
    productive_man_hour_per_volume = productive_hours / params.budget_volume
    productive_hours_per_fte = params.std_fte_hours * params.percent_productive_hours
    productive_hours_needed_for_volume = fte_requested * productive_hours_per_fte
    standard_volume = params.budget_volume / params.budget_fte * fte_requested

    statistical_impact_volume = standard_volume - params.budget_volume
    salary_impact_dollars = (
        (fte_requested - budget_fte) * params.std_fte_hours * params.std_salary_per_hour
    )
    reimbursement_dollars = statistical_impact_volume * 370 * 0.507
    net_impact_dollars = reimbursement_dollars - salary_impact_dollars

    return FTEResult(
        productive_hours_needed_for_volume=productive_hours_needed_for_volume,
        standard_volume=standard_volume,
        statistical_impact_volume=statistical_impact_volume,
        salary_impact_dollars=salary_impact_dollars,
        reimbursement_dollars=reimbursement_dollars,
        net_impact_dollars=net_impact_dollars,
    )


def _merge_params(params, defaults):
    """
    Merge in values from params into defaults and return a new FTEParams object
    """
    params_dict = asdict(params)
    defaults_dict = asdict(defaults)

    merged_dict = {
        k: (params_dict.get(k) if params_dict.get(k) is not None else v)
        for k, v in defaults_dict.items()
    }
    return params.__class__(**merged_dict)
