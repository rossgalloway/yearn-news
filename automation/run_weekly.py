"""Run the unattended newsletter workflow and maintain a private review page."""

import fcntl
import html
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".automation"
REVIEW = STATE / "review"
OUTPUTS = (
    "output.md",
    "output-x-article.html",
    "output-x-article-fragment.html",
    "output-x-article.txt",
    "output-yearn-glance-banner.svg",
    "output-yearn-glance-banner-review.html",
)
CHECKS = (
    ["uv", "run", "ruff", "format", ".", "--check"],
    ["uv", "run", "python", "-m", "unittest", "discover", "-s", "tests", "-v"],
    ["uv", "run", "python", "-m", "mypy", "src", "tests", "automation"],
    ["uv", "run", "ruff", "check", ".", "--no-fix"],
)


def update_review(status: str, detail: str, ready: bool = False) -> None:
    REVIEW.mkdir(parents=True, exist_ok=True)
    links = '<a href="report.txt">Latest run report</a>' if (REVIEW / "report.txt").exists() else ""
    if ready:
        links += (
            '<p><a href="output-x-article.html">Review article</a> · '
            '<a href="output-yearn-glance-banner-review.html">Review banner</a> · '
            '<a href="output.md">Markdown</a></p>'
        )
    page = (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Yearn News weekly run</title><style>"
        "body{font:18px/1.6 system-ui;max-width:760px;margin:64px auto;padding:0 24px}"
        "a{color:inherit}small{color:#666}</style><h1>Yearn News weekly run</h1>"
        "<p>Every Thursday at 9:00 a.m. America/New_York. Drafts for editor review.</p>"
        f"<h2>{html.escape(status)}</h2><p>{html.escape(detail)}</p>{links}"
        f"<p><small>Updated {datetime.now(timezone.utc).isoformat()}</small></p></html>"
    )
    temporary = REVIEW / "index.html.tmp"
    temporary.write_text(page)
    temporary.replace(REVIEW / "index.html")


def command(args: list[str], log: TextIO, timeout: int = 600) -> None:
    print("Running:", " ".join(args), flush=True)
    log.write("\nRunning: " + " ".join(args) + "\n")
    log.flush()
    subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=timeout)


def main() -> int:
    os.environ.setdefault("UV_CACHE_DIR", "/tmp/yearn-news-uv-cache")
    STATE.mkdir(exist_ok=True)
    if sys.argv[1:] == ["--initialize"]:
        if not (REVIEW / "index.html").exists():
            update_review("Scheduled", "No scheduled draft has run yet. The next run will appear here.")
        return 0
    with (STATE / "run.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Another newsletter run is active; skipping.")
            return 0
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        run_dir = STATE / "runs" / run_id
        run_dir.mkdir(parents=True)
        with (run_dir / "run.log").open("w") as log:
            if sys.argv[1:] == ["--check"]:
                command(["codex", "login", "status"], log)
                command(["uv", "run", "python", "src/preflight.py"], log)
                command(
                    [
                        "codex",
                        "exec",
                        "--sandbox",
                        "read-only",
                        "-c",
                        'approval_policy="never"',
                        "--color",
                        "never",
                        "-o",
                        str(run_dir / "smoke.txt"),
                        "Read automation/prompt.md without editing any files. Reply with exactly NEWS_TIMER_READY.",
                    ],
                    log,
                    timeout=180,
                )
                if (run_dir / "smoke.txt").read_text().strip() != "NEWS_TIMER_READY":
                    raise RuntimeError("Codex smoke check did not return its readiness marker")
                print("Codex authentication, preflight, and unattended execution passed.")
                return 0
            if sys.argv[1:]:
                raise ValueError("Supported arguments: --check, --initialize")
            for name in ("src/content.py", "data/tvl_cache.json", *OUTPUTS):
                source = ROOT / name
                if source.exists():
                    target = run_dir / "before" / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
            started = datetime.now(timezone.utc).timestamp()
            update_review("Running", f"Run {run_id}: researching and generating a fresh draft.")
            try:
                command(["uv", "run", "python", "src/preflight.py"], log)
                prompt = (ROOT / "automation/prompt.md").read_text()
                command(
                    [
                        "codex",
                        "exec",
                        "--sandbox",
                        "workspace-write",
                        "-c",
                        'approval_policy="never"',
                        "-c",
                        "sandbox_workspace_write.network_access=true",
                        "--color",
                        "never",
                        "-o",
                        str(run_dir / "report.txt"),
                        prompt,
                    ],
                    log,
                    timeout=5400,
                )
                for args in CHECKS:
                    command(args, log)
                for name in OUTPUTS:
                    source = ROOT / name
                    if not source.is_file() or source.stat().st_mtime < started:
                        raise RuntimeError(f"Generation did not refresh {name}")
                for name in OUTPUTS:
                    shutil.copy2(ROOT / name, REVIEW / name)
                shutil.copy2(run_dir / "report.txt", REVIEW / "report.txt")
                update_review(
                    "Draft ready for editor review", f"Run {run_id}. Read the report for source limitations.", True
                )
                return 0
            except Exception as exc:
                detail = f"Run {run_id} failed: {exc}. Earlier preview files have not been refreshed."
                report = run_dir / "report.txt"
                text = report.read_text() if report.exists() else "No editorial report was produced."
                (REVIEW / "report.txt").write_text(detail + "\n\n" + text)
                update_review("Run failed — action needed", detail)
                print(detail, file=sys.stderr)
                return 1


if __name__ == "__main__":
    sys.exit(main())
