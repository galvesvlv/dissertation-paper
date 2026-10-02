import numpy as np
import pandas as pd

from src.heatwave import (
    compute_noaa_hwi,
    compute_omm_hwi,
    count_episodes_per_month,
    daily_ind_prod,
    noaa_categories,
    limit_to_study_period,
)


def test_noaa_heat_index_returns_finite_values():
    result = compute_noaa_hwi(pd.Series([30.0]), pd.Series([70.0]))
    assert np.isfinite(result.iloc[0])


def test_noaa_categories_are_mutually_exclusive():
    categories = noaa_categories(pd.Series([79, 80, 90, 103, 125]))
    assert categories.sum(axis=1).tolist() == [0, 1, 1, 1, 1]


def test_omm_reference_period_starts_in_1961():
    reference = pd.date_range("1961-01-01", "1990-12-31", freq="D")
    target = pd.date_range("2020-01-01", "2020-01-02", freq="D")
    index = reference.append(target)
    frame = pd.DataFrame({"t2m": [25.0] * len(reference) + [35.0, 36.0]}, index=index)
    result = compute_omm_hwi(frame)
    assert "anomaly" in result
    assert "omm_hwi" in result


def test_episode_count_resets_at_month_boundaries():
    index = pd.date_range("2020-01-30", periods=5, freq="D")
    result = count_episodes_per_month(pd.Series([1, 1, 1, 1, 1], index=index), 3)
    assert result.loc[pd.Timestamp("2020-01-01")] == 0
    assert result.loc[pd.Timestamp("2020-02-01")] == 1


def test_study_period_ends_in_2023():
    frame = pd.DataFrame({"time": pd.to_datetime(["2023-12-31", "2024-01-01"])})
    result = limit_to_study_period(frame)
    assert result["time"].max() == pd.Timestamp("2023-12-31")


def test_daily_aggregation_uses_daily_maximum_for_omm():
    index = pd.date_range("1961-01-01", "1990-12-31", freq="D")
    frame = pd.DataFrame(
        {"time": index, "t2m": 25.0, "r": 70.0, "XHWI": 0.0}
    )
    result = daily_ind_prod(frame)
    assert "omm_hwi_max" in result
    assert {"anomaly_max", "mask_max"}.issubset(result.columns)
