"""Trend analysis used in the article."""

from __future__ import annotations

import pandas as pd
import pymannkendall as mk
from scipy.stats import kendalltau


def mann_kendall_summary(series: pd.Series, seasonal: bool = False) -> dict:
    """Return the trend, tau and p-value from Mann--Kendall."""
    if seasonal:
        result = mk.seasonal_test(series)
        return {"trend": result.trend, "tau": result.Tau, "p_value": result.p}
    tau, p_value = kendalltau(range(len(series)), series.to_numpy())
    trend = "increasing" if p_value < 0.05 and tau > 0 else "decreasing" if p_value < 0.05 and tau < 0 else "no trend"
    return {"trend": trend, "tau": tau, "p_value": p_value}


def annual_period_mean(series: pd.Series, start_year: int, end_year: int) -> float:
    """Calculate the annual mean accumulated value for one period."""
    data = series.copy()
    data.index = pd.to_datetime(data.index)
    selected = data.loc[f"{start_year}-01-01":f"{end_year}-12-31"]
    return selected.groupby(selected.index.year).sum().mean()


def percentage_difference(current: float, previous: float) -> float:
    """Calculate a finite percentage difference, preserving missing values."""
    if previous == 0:
        return float("nan") if current == 0 else float("inf")
    return (current - previous) / previous * 100
