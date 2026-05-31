import subprocess
import json
import argparse
from pathlib import Path
import datetime
import sys

try:
    import pandas as pd
    import matplotlib.pyplot as plt
except Exception:
    print("Missing Python dependencies. Install from tests/load/requirements.txt")
    raise


DEFAULT_STAGES = [
    (1, "2m"),
    (10, "5m"),
    (25, "5m"),
    (50, "10m"),
    (75, "5m"),
    (100, "5m"),
]


def run_stage(k6_script: Path, vus: int, duration: str, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    summary_file = out_dir / f"summary_v{vus}_{timestamp}.json"

    cmd = [
        "k6",
        "run",
        "--vus",
        str(vus),
        "--duration",
        duration,
        "--summary-export",
        str(summary_file),
        str(k6_script),
    ]

    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
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
        failed_rate = http_req_failed.get("values", {}).get("rate") or http_req_failed.get("rate")

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
    now = datetime.datetime.utcnow().isoformat() + "Z"
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
