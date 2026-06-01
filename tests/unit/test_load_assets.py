from pathlib import Path


def test_k6_load_script_covers_required_workflows() -> None:
    script = Path("tests/load/k6_ecommerce.js").read_text()

    for expected in (
        "/api/v1/products",
        "/api/v1/cart/items",
        "/api/v1/orders",
        "http_req_failed",
        "http_req_duration",
        "http.setResponseCallback(http.expectedStatuses({ min: 200, max: 499 }))",
    ):
        assert expected in script


def test_phase6_docker_runner_propagates_stage_configuration() -> None:
    runner = Path("tests/load/phase6_runner.py").read_text()

    for expected in (
        "for key, value in stage_env.items()",
        'f"{key}={value}"',
        'failed_rate = http_req_failed.get("value")',
    ):
        assert expected in runner


def test_load_and_security_reports_exist() -> None:
    assert Path("tests/load/reports/load-test-report.md").exists()
    assert Path("tests/security/security-report.md").exists()
