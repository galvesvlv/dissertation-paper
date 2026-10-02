"""Functions for combining capital-level intermediate metrics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .paths import CAPITALS, ERA5_MONTHLY_DIR, HEATWAVE_METRICS


def load_capital_monthly(capital: str, metric: str) -> pd.Series:
    """Load one monthly metric and name it with the capital's UF."""
    path = ERA5_MONTHLY_DIR / capital / f"{capital}_heatwave_ERA5_monthly.parquet"
    frame = pd.read_parquet(path)
    frame["time"] = pd.to_datetime(frame["time"])
    return frame.set_index("time")[metric].rename(CAPITALS[capital])


def build_wide_metric(metric: str, capitals: dict[str, str] = CAPITALS) -> pd.DataFrame:
    """Combine one monthly metric into a capital-wide table."""
    series = [load_capital_monthly(capital, metric) for capital in capitals]
    return pd.concat(series, axis=1).sort_index()


def aggregate_metrics(
    output_directory: Path, metrics: list[str] = HEATWAVE_METRICS
) -> list[Path]:
    """Write the article's wide capital aggregates."""
    output_directory.mkdir(parents=True, exist_ok=True)
    expected = {f"agg_{metric}.parquet" for metric in metrics}
    for stale in output_directory.glob("agg_*.parquet"):
        if stale.name not in expected:
            stale.unlink()
    outputs = []
    for metric in metrics:
        output = output_directory / f"agg_{metric}.parquet"
        build_wide_metric(metric).reset_index(names="time").to_parquet(output, index=False)
        outputs.append(output)
    return outputs
