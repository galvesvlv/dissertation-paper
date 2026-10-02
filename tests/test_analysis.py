import numpy as np
import pandas as pd
import pytest

from src.clustering import cluster_periods, elbow_inertia, standardize_metrics
from src.correlations import monthly_anomalies, seasonal_spearman
from src.trends import annual_period_mean, percentage_difference
from src.paths import CAPITALS


def test_clustering_helpers_validate_and_return_expected_shapes():
    frame = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [3.0, 2.0, 1.0]})
    assert standardize_metrics(frame).shape == frame.shape
    assert len(cluster_periods(frame, n_clusters=2)) == 3
    assert len(elbow_inertia(frame, [1, 2])) == 2
    with pytest.raises(ValueError):
        cluster_periods(frame, n_clusters=4)


def test_trend_helpers_handle_periods_and_zero_baselines():
    index = pd.date_range("1950-01-01", "1952-12-01", freq="MS")
    series = pd.Series(1.0, index=index)
    assert annual_period_mean(series, 1950, 1952) == 12.0
    assert np.isnan(percentage_difference(0, 0))
    assert percentage_difference(1, 0) == float("inf")


def test_correlation_helpers_handle_short_pairs():
    index = pd.date_range("1999-01-01", periods=1, freq="MS")
    health = pd.DataFrame({capital: np.arange(1, dtype=float) for capital in (
        "Porto Velho", "Rio Branco", "Manaus", "Boa Vista", "Belém", "Macapá",
        "Palmas", "São Luís", "Teresina", "Fortaleza", "Natal", "João Pessoa",
        "Recife", "Maceió", "Aracaju", "Salvador", "Belo Horizonte", "Vitória",
        "Rio de Janeiro", "São Paulo", "Curitiba", "Florianópolis", "Porto Alegre",
        "Campo Grande", "Cuiabá", "Goiânia", "Brasília",
    )}, index=index)
    heatwave = pd.DataFrame(
        {f"Ind_Prod_Monthly_{uf}": np.arange(1, dtype=float) for uf in CAPITALS.values()},
        index=index,
    )
    result = seasonal_spearman(health, heatwave, ["Ind_Prod_Monthly"])
    assert set(result) == {"DJF", "MAM", "JJA", "SON"}
    assert pd.isna(result["DJF"].loc["RO", "Ind_Prod_Monthly"])
    assert monthly_anomalies(health).shape == health.shape
