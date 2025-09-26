import pytest

@pytest.mark.pressure
def test_pressure_marker():
    assert True

@pytest.mark.integration
def test_integration_marker():
    assert True

@pytest.mark.ui
def test_ui_marker():
    assert True

@pytest.mark.performance
def test_performance_marker():
    assert True
