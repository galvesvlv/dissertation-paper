"""Health-rate preparation and seasonal Spearman correlations."""

from __future__ import annotations

import pandas as pd

from .paths import CAPITALS, SEASONS


def rate_per_100k(frame: pd.DataFrame, population: dict[str, float]) -> pd.DataFrame:
    """Normalize capital columns to rates per 100,000 inhabitants."""
    result = frame.copy().astype(float)
    for capital in result.columns:
        result[capital] = result[capital] / population[capital] * 100000
    return result


def monthly_anomalies(
    frame: pd.DataFrame, start: str = "1999-01-01", end: str = "2023-12-31"
) -> pd.DataFrame:
    """Remove monthly means calculated within the article's P3 period."""
    result = frame.copy()
    result.index = pd.to_datetime(result.index)
    result = result.loc[start:end]
    monthly_mean = result.groupby(result.index.month).transform("mean")
    return result - monthly_mean


def seasonal_spearman(
    health: pd.DataFrame, heatwave: pd.DataFrame, metric_columns: list[str]
) -> dict[str, pd.DataFrame]:
    """Calculate city-level seasonal Spearman correlations."""
    outputs = {}
    for season, months in SEASONS.items():
        mask = health.index.month.isin(months)
        health_subset = health.loc[mask]
        heatwave_subset = heatwave.loc[mask]
        table = pd.DataFrame(index=list(CAPITALS.values()), columns=metric_columns, dtype=float)
        for capital, uf in CAPITALS.items():
            for metric in metric_columns:
                pair = pd.concat([health_subset[capital], heatwave_subset[f"{metric}_{uf}"]], axis=1).dropna()
                table.loc[uf, metric] = (
                    pair.iloc[:, 0].corr(pair.iloc[:, 1], method="spearman")
                    if len(pair) >= 2
                    else float("nan")
                )
        outputs[season] = table
    return outputs
