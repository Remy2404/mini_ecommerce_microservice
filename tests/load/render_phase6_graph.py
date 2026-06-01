import json
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "docs" / "performance" / "phase6_results"
    summary_candidates = sorted(out_dir.glob("summary_v1_*.json"))
    if not summary_candidates:
        raise FileNotFoundError(out_dir / "summary_v1_*.json")

    summary_path = summary_candidates[-1]
    print(f"Using summary: {summary_path}")

    with summary_path.open("r", encoding="utf-8") as fh:
        summary = json.load(fh)

    metrics = summary["metrics"]
    row = {
        "vus": 1,
        "duration": "10s",
        "p95_ms": metrics["http_req_duration"]["p(95)"],
        "failed_rate": metrics["http_req_failed"]["value"],
        "rps": metrics["http_reqs"]["rate"],
    }
    df = pd.DataFrame([row])

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(df["vus"], df["p95_ms"], marker="o", color="tab:blue")
    ax1.set_xlabel("Virtual Users")
    ax1.set_ylabel("p95 response time (ms)", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.plot(df["vus"], df["failed_rate"], marker="x", color="tab:red")
    ax2.set_ylabel("Failed rate", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    plt.title("Phase 6: Response Time vs Load (Smoke Result)")
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    img = out_dir / "phase6_response_vs_load.png"
    plt.savefig(img, dpi=160)
    plt.close(fig)
    print(img)


if __name__ == "__main__":
    main()
