import pandas as pd
from dataclasses import dataclass, field

@dataclass(eq=True, frozen=True)
class IncomeStatement:
    """Various tables that represent an income statement"""
    revenue: pd.DataFrame
    deductions: pd.DataFrame
    expenses: pd.DataFrame
