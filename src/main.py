"""Command-line entry point for the reproducible preprocessing pipeline.

The article notebooks remain responsible for statistical tables and maps. This
entry point runs the reusable data preparation and capital aggregation stages,
without executing notebooks or producing article figures by default.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd

from .aggregation import aggregate_metrics
from .heatwave import daily_ind_prod, limit_to_study_period, monthly_ind_prod
from .paths import (
    CAPITALS,
    CAPITAL_AGGREGATES_DIR,
    END_DATE,
    ERA5_CAPITALS_DIR,
    ERA5_DAILY_DIR,
    ERA5_HOURLY_DIR,
    ERA5_MONTHLY_DIR,
    HEALTH_DEATHS_FILE,
    HEALTH_HOSPITALIZATIONS_FILE,
    HEATWAVE_METRICS,
    PROJECT_ROOT,
    RESULTS_DIR,
    XHWI_NETCDF,
    capital_monthly_files,
    ensure_result_directories,
)


INTERMEDIATE_SCHEMAS = {
    "hourly": {"time", "t2m", "r", "XHWI"},
    "daily": {
        "time", "t2m_mean", "t2m_max", "t2m_min", "r",
        "Ind_Prod_Diary", "NOAA_HWI_mean", "NOAA_HWI_max",
        "NOAA_HWI_min", "caution", "extreme_caution", "danger",
        "extreme_danger", "anomaly_max", "mask_max", "omm_hwi_max",
    },
    "monthly": set(HEATWAVE_METRICS) | {
        "time", "caution_qtd_hr_month", "extreme_caution_qtd_hr_month",
        "danger_qtd_hr_month", "extreme_danger_qtd_hr_month",
    },
}

ANALYSIS_NOTEBOOKS = (
    PROJECT_ROOT / "notebooks" / "Oficial_25_11_25.ipynb",
)
MAP_NOTEBOOKS = (
    PROJECT_ROOT / "notebooks" / "paper_19.08.2026.ipynb",
)
ANALYSIS_CELL_TIMEOUT = 300
MAP_CELL_TIMEOUT = 1800


def _has_expected_timestamps(actual: pd.Series, expected: pd.DatetimeIndex) -> bool:
    """Compare timestamps by instant, independent of pandas datetime precision."""
    return len(actual) == len(expected) and (actual.to_numpy() == expected.to_numpy()).all()


def validate_inputs() -> None:
    """Validate the files required before preprocessing can begin."""
    required = [XHWI_NETCDF, HEALTH_DEATHS_FILE, HEALTH_HOSPITALIZATIONS_FILE]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required files:\n" + "\n".join(missing))
    incomplete = {
        capital: len(capital_monthly_files(capital))
        for capital in CAPITALS
        if len(capital_monthly_files(capital)) != 12
    }
    if incomplete:
        raise FileNotFoundError(f"Capitals without twelve monthly files: {incomplete}")


def audit_intermediates() -> list[str]:
    """Return schema and date errors in generated capital products."""
    errors: list[str] = []
    locations = {
        "hourly": ERA5_HOURLY_DIR,
        "daily": ERA5_DAILY_DIR,
        "monthly": ERA5_MONTHLY_DIR,
    }
    for kind, directory in locations.items():
        for capital in CAPITALS:
            files = sorted((directory / capital).glob("*.parquet"))
            if len(files) != 1:
                errors.append(f"{kind}/{capital}: expected one Parquet, found {len(files)}")
                continue
            path = files[0]
            frame = pd.read_parquet(path, columns=None)
            missing = INTERMEDIATE_SCHEMAS[kind] - set(frame.columns)
            if missing:
                errors.append(f"{path}: missing columns {sorted(missing)}")
            if "time" not in frame:
                continue
            dates = pd.to_datetime(frame["time"], errors="coerce")
            if dates.isna().any():
                errors.append(f"{path}: contains invalid timestamps")
            elif dates.duplicated().any():
                errors.append(f"{path}: contains duplicated timestamps")
            elif not dates.is_monotonic_increasing:
                errors.append(f"{path}: timestamps are not sorted")
            elif dates.min() < pd.Timestamp("1950-01-01") or dates.max() > pd.Timestamp(END_DATE):
                errors.append(
                    f"{path}: dates outside study period "
                    f"({dates.min().date()} to {dates.max().date()})"
                )
            elif kind in {"daily", "monthly"}:
                frequency = "D" if kind == "daily" else "MS"
                expected = pd.date_range("1950-01-01", END_DATE, freq=frequency)
                if not _has_expected_timestamps(dates, expected):
                    errors.append(f"{path}: incomplete {frequency} time coverage")

    expected_aggregates = {f"agg_{metric}.parquet" for metric in HEATWAVE_METRICS}
    aggregate_files = {path.name for path in CAPITAL_AGGREGATES_DIR.glob("agg_*.parquet")}
    for missing in sorted(expected_aggregates - aggregate_files):
        errors.append(f"capital_aggregates: missing {missing}")
    for unexpected in sorted(aggregate_files - expected_aggregates):
        errors.append(f"capital_aggregates: unexpected {unexpected}")
    expected_columns = {"time", *CAPITALS.values()}
    for filename in sorted(expected_aggregates & aggregate_files):
        path = CAPITAL_AGGREGATES_DIR / filename
        frame = pd.read_parquet(path)
        missing = expected_columns - set(frame.columns)
        if missing:
            errors.append(f"{path}: missing columns {sorted(missing)}")
        dates = pd.to_datetime(frame.get("time"), errors="coerce")
        if dates.isna().any() or dates.duplicated().any():
            errors.append(f"{path}: invalid or duplicated timestamps")
        elif not dates.is_monotonic_increasing:
            errors.append(f"{path}: timestamps are not sorted")
        elif not _has_expected_timestamps(
            dates, pd.date_range("1950-01-01", END_DATE, freq="MS")
        ):
            errors.append(f"{path}: incomplete monthly time coverage")
    return errors


def prepare_capital(capital: str) -> None:
    """Create hourly, daily, and monthly intermediate products for one capital."""
    files = capital_monthly_files(capital)
    hourly = pd.concat((pd.read_csv(path) for path in files), ignore_index=True)
    hourly["time"] = pd.to_datetime(hourly["time"])
    hourly = limit_to_study_period(hourly).sort_values("time")
    daily = daily_ind_prod(hourly)
    monthly = monthly_ind_prod(daily)

    outputs = {
        ERA5_HOURLY_DIR / capital / f"{capital}_heatwave_ERA5_hourly.parquet": hourly,
        ERA5_DAILY_DIR / capital / f"{capital}_heatwave_ERA5_diary.parquet": daily,
        ERA5_MONTHLY_DIR / capital / f"{capital}_heatwave_ERA5_monthly.parquet": monthly,
    }
    for path, frame in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(path, index=False)


def prepare_all_capitals() -> None:
    """Create intermediate products for all 27 capitals."""
    for capital in CAPITALS:
        prepare_capital(capital)


def aggregate_all_capitals() -> list[Path]:
    """Create the wide article metric tables."""
    return aggregate_metrics(CAPITAL_AGGREGATES_DIR)


def _run_notebooks(notebooks: tuple[Path, ...], cell_timeout: int) -> None:
    """Execute a notebook group with a bounded per-cell timeout."""
    ensure_result_directories()
    output_directory = RESULTS_DIR / "executed_notebooks"
    output_directory.mkdir(parents=True, exist_ok=True)
    for notebook in notebooks:
        if not notebook.is_file():
            raise FileNotFoundError(f"Analysis notebook not found: {notebook}")
        print(f"Executing {notebook.name} (cell timeout: {cell_timeout}s)", flush=True)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                f"--ExecutePreprocessor.timeout={cell_timeout}",
                "--ExecutePreprocessor.force_raise_errors=True",
                f"--output-dir={output_directory}",
                str(notebook),
            ],
            cwd=PROJECT_ROOT,
            check=True,
        )


def run_analysis_notebooks() -> None:
    """Execute statistical analysis notebooks as an explicit opt-in stage."""
    _run_notebooks(ANALYSIS_NOTEBOOKS, ANALYSIS_CELL_TIMEOUT)


def run_map_notebooks() -> None:
    """Execute high-resolution cartographic notebooks separately."""
    _run_notebooks(MAP_NOTEBOOKS, MAP_CELL_TIMEOUT)


def run(stage: str) -> None:
    """Run one documented pipeline stage."""
    if stage in {"validate", "audit", "prepare", "aggregate", "analysis", "maps", "all"}:
        validate_inputs()
    if stage in {"audit", "analysis"}:
        errors = audit_intermediates()
        if errors:
            raise RuntimeError("Intermediate data audit failed:\n" + "\n".join(errors))
    if stage in {"prepare", "all"}:
        ensure_result_directories()
        prepare_all_capitals()
    if stage in {"aggregate", "all"}:
        ensure_result_directories()
        aggregate_all_capitals()
    if stage == "analysis":
        run_analysis_notebooks()
    if stage == "maps":
        run_map_notebooks()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("validate", "audit", "prepare", "aggregate", "analysis", "maps", "all"),
        default="validate",
        help="Pipeline stage to run; defaults to lightweight validation.",
    )
    args = parser.parse_args()
    run(args.stage)


if __name__ == "__main__":
    main()
