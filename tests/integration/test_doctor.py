from __future__ import annotations

from formloop.services.doctor import DoctorService


def test_flh_f_013_and_flh_v_007_doctor_checks_live_contracts(test_config) -> None:
    checks = DoctorService(config=test_config).run_checks()
    by_name = {check.name: check for check in checks}
    assert by_name["config"].ok
    assert by_name["blender"].ok
    assert by_name["cad_cli_contract"].ok
