"""K-Means period identification used by the article."""

from __future__ import annotations

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def standardize_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    """Standardize numeric heatwave metrics with z-scores."""
    if frame.empty:
        raise ValueError("Cannot standardize an empty frame")
    if frame.isna().any().any():
        raise ValueError("Cannot standardize metrics containing NaN values")
    values = StandardScaler().fit_transform(frame)
    return pd.DataFrame(values, index=frame.index, columns=frame.columns)


def cluster_periods(frame: pd.DataFrame, n_clusters: int = 3) -> pd.Series:
    """Assign each row to one of the K-Means temporal regimes."""
    if n_clusters < 1 or n_clusters > len(frame):
        raise ValueError("n_clusters must be between 1 and the number of rows")
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    labels = model.fit_predict(frame)
    return pd.Series(labels, index=frame.index, name="cluster")


def elbow_inertia(frame: pd.DataFrame, k_values=range(1, 11)) -> pd.Series:
    """Return within-cluster sum of squares for the elbow analysis."""
    k_values = list(k_values)
    if not k_values or min(k_values) < 1 or max(k_values) > len(frame):
        raise ValueError("k_values must be non-empty and within the row count")
    return pd.Series(
        {
            k: KMeans(n_clusters=k, random_state=42, n_init=20).fit(frame).inertia_
            for k in k_values
        },
        name="inertia",
    )
