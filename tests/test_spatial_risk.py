import numpy as np

from src.spatial_risk import multiply_hazard_vulnerability, normalize_to_classes


def test_normalization_uses_five_ordinal_classes():
    result = normalize_to_classes([0, 1, 2, 3, 4])
    assert np.array_equal(result, [1, 2, 3, 4, 5])


def test_risk_product_is_normalized():
    result = multiply_hazard_vulnerability([1, 3, 5], [1, 3, 5])
    assert result.min() == 1
    assert result.max() == 5
