import subprocess
import json
import argparse
from pathlib import Path
from pathlib import PurePosixPath
import datetime
import sys 
import shutil
import os
import urllib.error
import urllib.request

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import tabulate  # noqa: F401
except Exception:
    print("Missing Python dependencies. Run: uv sync")
    raise


DEFAULT_STAGES = [
    (1, "2m"),
    (10, "5m"),
    (25, "5m"),
    (50, "10m"),
    (75, "5m"),
    (100, "5m"),
]

DEFAULT_AUTH_SCOPE = "openid profile email"
DEFAULT_LOGIN_PATH = "/api/v1/auth/login"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _container_path(path: Path) -> str:
    repo_root = _repo_root()
    candidate = path if path.is_absolute() else (repo_root / path)
    try:
        rel = candidate.resolve().relative_to(repo_root)
    except ValueError:
        rel = candidate.name
    return str(PurePosixPath("/work") / PurePosixPath(rel.as_posix()))


def _login_url(base_url: str) -> str:
    return base_url.rstrip("/") + DEFAULT_LOGIN_PATH


def _fetch_auth_token(base_url: str, username: str, password: str, scope: str) -> str:
    payload = {
        "username": username,
        "password": password,
        "scope": scope,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        _login_url(base_url),
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Failed to login at {request.full_url}: {exc.code} {exc.reason}: {error_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to reach login endpoint {request.full_url}: {exc}") from exc

    token = body.get("access_token") or body.get("accessToken")
    if not token:
        raise RuntimeError(f"Login response did not contain access_token: {body}")
    return str(token)


def _candidate_login_base_urls(base_url: str) -> list[str]:
    candidates: list[str] = []

    override = os.environ.get("LOGIN_BASE_URL")
    if override:
        candidates.append(override)

    candidates.append(base_url)

    if "host.docker.internal" in base_url:
        candidates.append(base_url.replace("host.docker.internal", "localhost"))
        candidates.append(base_url.replace("host.docker.internal", "127.0.0.1"))

    deduped: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return deduped


def _resolve_auth_token(base_url: str) -> str:
    existing = os.environ.get("AUTH_TOKEN")
    if existing:
        return existing

    username = os.environ.get("AUTH_USERNAME")
    password = os.environ.get("AUTH_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "AUTH_TOKEN is missing. Set AUTH_TOKEN or provide AUTH_USERNAME and AUTH_PASSWORD."
        )

    scope = os.environ.get("AUTH_SCOPE", DEFAULT_AUTH_SCOPE)
    last_error: Exception | None = None

    for login_base_url in _candidate_login_base_urls(base_url):
        try:
            token = _fetch_auth_token(login_base_url, username, password, scope)
            os.environ["AUTH_TOKEN"] = token
            return token
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    if last_error is not None:
        raise last_error

    raise RuntimeError("Unable to resolve an authentication token")


def run_stage(k6_script: Path, vus: int, duration: str, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
    summary_file = out_dir / f"summary_v{vus}_{timestamp}.json"

    stage_env = {
        "K6_PRODUCT_VUS": str(vus),
        "K6_PRODUCT_DURATION": duration,
        "K6_ORDER_RATE": str(max(1, vus // 5)),
        "K6_ORDER_DURATION": duration,
    }
    auth_token = _resolve_auth_token(os.environ.get("BASE_URL", "http://localhost:8000"))
    stage_env["AUTH_TOKEN"] = auth_token

    # Try local k6 first, fall back to dockerized grafana/k6 if binary not found
    def _run_local_k6():
        cmd = [
            "k6",
            "run",
            "--summary-export",
            str(summary_file),
            str(k6_script),
        ]
        print("Running (local k6):", " ".join(cmd))
        env = os.environ.copy()
        env.update(stage_env)
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)

    def _run_docker_k6():
        repo_root = _repo_root()
        # Ensure Windows paths are handled for docker mount
        host_path = str(repo_root).replace('\\', '/')
        container_script = _container_path(k6_script)
        container_summary = _container_path(summary_file)
        docker_env = []
        for key, value in stage_env.items():
            docker_env += ["-e", f"{key}={value}"]

        # Propagate common env vars to the container if present.
        for e in ("BASE_URL", "AUTH_TOKEN", "USER_ID", "PRODUCT_ID"):
            val = os.environ.get(e)
            if val is not None:
                docker_env += ["-e", f"{e}={val}"]

        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{host_path}:/work",
            "-w",
            "/work",
        ] + docker_env + [
            "grafana/k6:latest",
            "run",
            "--summary-export",
            container_summary,
            container_script,
        ]
        print("Running (docker k6):", " ".join(cmd))
        env = os.environ.copy()
        env.update(stage_env)
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)

    proc = None
    try:
        if shutil.which("k6"):
            proc = _run_local_k6()
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        proc = _run_docker_k6()

    if proc is None or proc.returncode != 0:
        if proc is not None:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"k6 failed for vus={vus}")

    with summary_file.open("r", encoding="utf-8") as fh:
        summary = json.load(fh)

    metrics = summary.get("metrics", {})

    result = {"vus": vus, "duration": duration, "summary_file": str(summary_file)}

    # HTTP request duration p95
    http_req_duration = metrics.get("http_req_duration", {})
    p95 = None
    if http_req_duration:
        values = http_req_duration.get("values", {})
        p95 = values.get("p(95)") or values.get("p95") or http_req_duration.get("p(95)")

    result["p95_ms"] = p95

    # Failed request rate
    http_req_failed = metrics.get("http_req_failed", {})
    failed_rate = None
    if http_req_failed:
        failed_rate = http_req_failed.get("values", {}).get("rate")
        if failed_rate is None:
            failed_rate = http_req_failed.get("rate")
        if failed_rate is None:
            failed_rate = http_req_failed.get("value")

    result["failed_rate"] = failed_rate

    # Requests per second (throughput)
    rps = None
    http_reqs = metrics.get("http_reqs", {})
    if http_reqs:
        rps = http_reqs.get("values", {}).get("rate") or http_reqs.get("rate")
    result["rps"] = rps

    return result


def run_all(k6_script: Path, stages, out_dir: Path):
    results = []
    for vus, duration in stages:
        print(f"=== Stage: {vus} VUs for {duration} ===")
        r = run_stage(k6_script, vus, duration, out_dir)
        results.append(r)
    return results


def plot_results(results, out_dir: Path):
    df = pd.DataFrame(results)
    df_sorted = df.sort_values("vus")

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(df_sorted["vus"], df_sorted["p95_ms"], marker="o", color="tab:blue", label="p95 (ms)")
    ax1.set_xlabel("Virtual Users")
    ax1.set_ylabel("p95 response time (ms)", color="tab:blue")
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.plot(df_sorted["vus"], df_sorted["failed_rate"], marker="x", color="tab:red", label="failed rate")
    ax2.set_ylabel("Failed rate", color="tab:red")
    ax2.tick_params(axis='y', labelcolor='tab:red')

    plt.title("Phase 6: Response Time vs Load")
    fig.tight_layout()
    img = out_dir / "phase6_response_vs_load.png"
    plt.savefig(img)
    plt.close(fig)
    return img


def write_report(results, img_path: Path, out_dir: Path):
    now = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
    report_md = out_dir / "phase6-sovann-report.md"
    df = pd.DataFrame(results).sort_values("vus")

    with report_md.open("w", encoding="utf-8") as fh:
        fh.write("# Phase 6 — Performance Report\n\n")
        fh.write(f"Generated: {now}\n\n")
        fh.write("## Summary Table\n\n")
        fh.write(df.to_markdown(index=False))
        fh.write("\n\n")
        fh.write("## Graph: Response Time vs Load\n\n")
        fh.write(f"![response vs load]({img_path.name})\n\n")
        fh.write("## Bottleneck Notes\n\n- Fill in observed bottlenecks and operational limits here.\n")

    return report_md


def main():
    p = argparse.ArgumentParser(description="Phase 6 runner for load tests and reporting")
    p.add_argument("--k6-script", default="tests/load/k6_ecommerce.js", help="Path to k6 script")
    p.add_argument("--out-dir", default="docs/performance/phase6_results", help="Output directory for summaries and reports")
    p.add_argument("--stages", nargs="*", help="Optional stages as vus:duration e.g. 10:5m 25:5m")
    args = p.parse_args()

    k6_script = Path(args.k6_script)
    if not k6_script.exists():
        print(f"k6 script not found: {k6_script}")
        sys.exit(2)

    out_dir = Path(args.out_dir)
    if args.stages:
        stages = []
        for item in args.stages:
            vus_s, duration = item.split(":")
            stages.append((int(vus_s), duration))
    else:
        stages = DEFAULT_STAGES

    results = run_all(k6_script, stages, out_dir)
    img = plot_results(results, out_dir)
    report = write_report(results, img, out_dir)

    print("Results saved to:")
    print(out_dir)
    print(report)


if __name__ == "__main__":
    main()
