from src.main import audit_intermediates, validate_inputs


def test_pipeline_validation_passes_with_current_layout():
    validate_inputs()


def test_intermediate_audit_is_clean_after_preprocessing():
    errors = audit_intermediates()
    assert errors == []
