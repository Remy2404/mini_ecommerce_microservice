from pathlib import Path


def test_k6_load_script_covers_required_workflows() -> None:
    script = Path("tests/load/k6_ecommerce.js").read_text()

    for expected in (
        "/api/v1/products",
        "/api/v1/cart/items",
        "/api/v1/orders",
        "http_req_failed",
        "http_req_duration",
    ):
        assert expected in script


def test_load_and_security_reports_exist() -> None:
    assert Path("tests/load/reports/load-test-report.md").exists()
    assert Path("tests/security/security-report.md").exists()
