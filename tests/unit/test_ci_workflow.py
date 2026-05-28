from pathlib import Path


def test_ci_workflow_contains_required_quality_gates() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text()

    for required_command in (
        "uv sync --all-extras --dev",
        "uv run ruff check .",
        "uv run pytest",
        "docker compose -f infra/docker-compose.yml config --quiet",
        "uv run pytest tests/smoke tests/e2e",
    ):
        assert required_command in workflow


def test_ci_workflow_uses_uv_cache_and_python_matrix() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text()

    assert "astral-sh/setup-uv@v5" in workflow
    assert "enable-cache: true" in workflow
    assert "matrix:" in workflow
    assert "python-version: ['3.12']" in workflow
