from app.support_scripts import script_for


def test_support_scripts_are_deterministic_and_have_no_provider_output():
    assert script_for("none") is None
    elevated = script_for("elevated")
    crisis = script_for("crisis")
    assert elevated is not None and elevated.id == "elevated_v1"
    assert crisis is not None and crisis.id == "crisis_v1"
    assert "diagnos" not in crisis.body.lower()
    assert "confidential" not in crisis.body.lower()
