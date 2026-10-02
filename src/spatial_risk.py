"""Spatial hazard, vulnerability and risk helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def normalize_to_classes(values, lower=None, upper=None) -> np.ndarray:
    """Normalize values to the article's ordinal scale from 1 to 5."""
    array = np.asarray(values, dtype=float)
    if array.size == 0 or not np.isfinite(array).any():
        raise ValueError("Cannot normalize an empty or entirely infinite array")
    if np.isnan(array).all():
        raise ValueError("Cannot normalize an entirely NaN array")
    lower = np.nanmin(array) if lower is None else lower
    upper = np.nanmax(array) if upper is None else upper
    if not np.isfinite(lower) or not np.isfinite(upper):
        raise ValueError("Normalization bounds must be finite")
    if upper == lower:
        return np.ones_like(array, dtype=float)
    normalized = 1 + 4 * (array - lower) / (upper - lower)
    return np.clip(np.rint(normalized), 1, 5)


def multiply_hazard_vulnerability(hazard, vulnerability) -> np.ndarray:
    """Calculate and renormalize the scalar hazard-vulnerability product."""
    product = np.asarray(hazard, dtype=float) * np.asarray(vulnerability, dtype=float)
    return normalize_to_classes(product)


def elderly_density(population: pd.Series, area_km2: pd.Series) -> pd.Series:
    """Calculate older-population density per square kilometre."""
    area = area_km2.astype(float)
    if (area <= 0).any():
        raise ValueError("Municipal area must be positive")
    return population.astype(float) / area
