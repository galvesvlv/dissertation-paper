"""Heatwave indices and temporal aggregation functions."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from .paths import END_DATE, REFERENCE_END_YEAR, REFERENCE_START_YEAR


def compute_noaa_hwi(temperature_c: pd.Series, relative_humidity: pd.Series) -> pd.Series:
    """Compute the NWS heat index, returned in degrees Fahrenheit."""
    temperature_f = temperature_c * 9 / 5 + 32
    return (
        -42.379 + 2.04901523 * temperature_f + 10.14333127 * relative_humidity
        - 0.22475541 * temperature_f * relative_humidity
        - 0.00683783 * temperature_f**2 - 0.05481717 * relative_humidity**2
        + 0.00122874 * temperature_f**2 * relative_humidity
        + 0.00085282 * temperature_f * relative_humidity**2
        - 0.00000199 * temperature_f**2 * relative_humidity**2
    )


def noaa_categories(index: pd.Series) -> pd.DataFrame:
    """Classify heat-index values into mutually exclusive NWS bands."""
    return pd.DataFrame(
        {
            "caution": index.ge(80) & index.lt(90),
            "extreme_caution": index.ge(90) & index.lt(103),
            "danger": index.ge(103) & index.lt(125),
            "extreme_danger": index.ge(125),
        },
        index=index.index,
    )


def compute_omm_hwi(
    frame: pd.DataFrame,
    temperature_column: str = "t2m",
    reference_start: int = REFERENCE_START_YEAR,
    reference_end: int = REFERENCE_END_YEAR,
) -> pd.DataFrame:
    """Compute the anomaly-based heatwave signal using 1961--1990."""
    frame = frame.copy()
    frame.index = pd.to_datetime(frame.index)
    reference = frame.loc[
        f"{reference_start}-01-01":f"{reference_end}-12-31", temperature_column
    ]
    if reference.empty:
        raise ValueError("The 1961-1990 reference period contains no observations")
    climatology = reference.groupby(reference.index.month).mean()
    missing_months = set(range(1, 13)) - set(climatology.index)
    if missing_months:
        raise ValueError(f"Missing reference months: {sorted(missing_months)}")
    anomaly = frame[temperature_column] - frame.index.month.map(climatology)
    frame["anomaly"] = anomaly
    frame["omm_hwi"] = (anomaly - 5).clip(lower=0)
    return frame


def count_episodes_per_month(
    series: pd.Series, min_length: int = 5, name: Optional[str] = None
) -> pd.Series:
    """Count non-overlapping positive runs of a minimum length per month."""
    if series is None or series.empty:
        return pd.Series(dtype="int64", name=name or "episodes")
    values = series.copy()
    values.index = pd.to_datetime(values.index)
    values = values.sort_index().gt(0).fillna(False)
    month = pd.Series(values.index.to_period("M"), index=values.index)
    month_start = month.ne(month.shift()).fillna(True)
    groups = ((~values) | month_start).cumsum()
    run_lengths = values.groupby(groups).cumsum()
    maximum = run_lengths.groupby(groups).max().fillna(0).astype("int64")
    episodes = maximum // min_length
    group_month = month.groupby(groups).first().dt.to_timestamp(how="start")
    monthly = episodes.groupby(group_month).sum()
    full_index = pd.date_range(
        values.index.min().to_period("M").to_timestamp(),
        values.index.max().to_period("M").to_timestamp(),
        freq="MS",
    )
    result = monthly.reindex(full_index, fill_value=0).astype("int64")
    result.name = name or f"episodes_{min_length}d"
    return result


def limit_to_study_period(frame: pd.DataFrame, date_column: str = "time") -> pd.DataFrame:
    """Restrict a table to the article's 1950--2023 study period."""
    result = frame.copy()
    dates = pd.to_datetime(result[date_column])
    mask = (dates >= pd.Timestamp("1950-01-01")) & (dates <= pd.Timestamp(END_DATE))
    result = result.loc[mask].copy()
    result[date_column] = dates.loc[result.index]
    return result


def daily_ind_prod(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate hourly XHWI data to daily metrics."""
    data = frame.copy()
    data["time"] = pd.to_datetime(data["time"])
    data = data.set_index("time").sort_index()
    if "NOAA_HWI" not in data:
        data["NOAA_HWI"] = compute_noaa_hwi(data["t2m"], data["r"])

    diary_sum = data["XHWI"].resample("D").sum().rename("diary_sum")
    non_zero = data["XHWI"].gt(0).resample("D").sum().rename("non_zero_hours")
    ind_prod = (diary_sum * non_zero).rename("Ind_Prod_Diary")
    daily_noaa = data["NOAA_HWI"].resample("D")
    noaa = data["NOAA_HWI"]
    categories = noaa_categories(noaa)
    caution = categories["caution"]
    extreme_caution = categories["extreme_caution"]
    danger = categories["danger"]
    extreme_danger = categories["extreme_danger"]
    caution = caution.astype(int).resample("D").sum()
    extreme_caution = extreme_caution.astype(int).resample("D").sum()
    danger = danger.astype(int).resample("D").sum()
    extreme_danger = extreme_danger.astype(int).resample("D").sum()
    daily_tmax = data["t2m"].resample("D").max().rename("t2m_max")
    omm = compute_omm_hwi(daily_tmax.to_frame(), temperature_column="t2m_max")

    result = pd.concat(
        [data["t2m"].resample("D").mean().rename("t2m_mean"),
         daily_tmax,
         data["t2m"].resample("D").min().rename("t2m_min"),
         data["r"].resample("D").mean().rename("r"), diary_sum, non_zero, ind_prod],
        axis=1,
    )
    result["NOAA_HWI_mean"] = daily_noaa.mean()
    result["NOAA_HWI_max"] = daily_noaa.max()
    result["NOAA_HWI_min"] = daily_noaa.min()
    result["caution"] = caution
    result["extreme_caution"] = extreme_caution
    result["danger"] = danger
    result["extreme_danger"] = extreme_danger
    result["noaa_qtd"] = daily_noaa.max().ge(80).astype(int)
    result["anomaly_max"] = omm["anomaly"]
    result["mask_max"] = omm["anomaly"].where(omm["anomaly"] > 5, 0)
    result["omm_hwi_max"] = omm["omm_hwi"]
    return result.reset_index()


def monthly_ind_prod(daily: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily metrics and calculate XHWI, NWS and OMM counts."""
    data = daily.copy()
    data["time"] = pd.to_datetime(data["time"])
    data = data.set_index("time").sort_index()
    monthly = pd.DataFrame(index=data.resample("MS").asfreq().index)
    monthly["Ind_Prod_Monthly"] = data["Ind_Prod_Diary"].resample("MS").sum()
    xhwi_days = data["Ind_Prod_Diary"].gt(0).astype(int)
    monthly["ind_prod_monthly_qtd"] = xhwi_days.resample("MS").sum()
    monthly["ind_prod_3episodes"] = count_episodes_per_month(xhwi_days, 3)
    monthly["ind_prod_5episodes"] = count_episodes_per_month(xhwi_days, 5)
    monthly["NOAA_HWI_mean"] = data["NOAA_HWI_mean"].resample("MS").mean()
    monthly["NOAA_HWI_max"] = data["NOAA_HWI_max"].resample("MS").max()
    monthly["NOAA_HWI_min"] = data["NOAA_HWI_min"].resample("MS").min()

    monthly["caution_qtd_hr_month"] = data["caution"].resample("MS").sum()
    monthly["extreme_caution_qtd_hr_month"] = data["extreme_caution"].resample("MS").sum()
    monthly["danger_qtd_hr_month"] = data["danger"].resample("MS").sum()
    monthly["extreme_danger_qtd_hr_month"] = data["extreme_danger"].resample("MS").sum()

    noaa_days = data["noaa_qtd"].astype(int)
    monthly["noaa_qtd_monthly"] = noaa_days.resample("MS").sum()
    monthly["noaa_3episodes"] = count_episodes_per_month(noaa_days, 3, "noaa_3episodes")
    monthly["noaa_5episodes"] = count_episodes_per_month(noaa_days, 5, "noaa_5episodes")

    omm_days = data["omm_hwi_max"].gt(0).astype(int)
    monthly["omm_qtd_monthly"] = omm_days.resample("MS").sum()
    monthly["omm_3episodes"] = count_episodes_per_month(omm_days, 3, "omm_3episodes")
    monthly["omm_5episodes"] = count_episodes_per_month(omm_days, 5, "omm_5episodes")
    return monthly.reset_index(names="time")
