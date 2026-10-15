# Scheduled weekly generation

The remote host runs `yearn-news-weekly.timer` every Thursday at **9:00 a.m.
America/New_York**. This follows Eastern daylight saving time: 13:00 UTC in
summer and 14:00 UTC in winter. It is not fixed UTC-5 year-round.

The timer launches Codex CLI in this checkout using its saved authentication and
configured model, with workspace-write permissions and network access. The host
must be running; your desktop app does not need to be open. User lingering is
enabled. A missed run starts when the timer becomes available again.

`automation/prompt.md` defines the editorial task. The runner backs up the current
content, TVL cache, and generated outputs before each run, checks required live
dependencies, researches and regenerates through Codex, then independently runs
all validation commands and verifies the output files were refreshed.

Draft generation does not publish to X, commit, push, or message anyone. Source
coverage and editorial cutoff limitations appear in the run report. An editor
must review the draft before publication. The runner edits the existing checkout;
avoid editing newsletter content while it is running.

Runtime files live under ignored `.automation/`: private logs and backups in
`runs/`, and the review page, report, and validated output copies in `review/`.
Only `review/` is exposed through a dedicated private Tailscale static route.
Private preview URLs stay out of tracked documentation and GitHub content.
Runs appear on the review page and in the systemd journal, not in the desktop
app's native Scheduled inbox. No email or push notification is configured.

## Operations

```bash
systemctl --user list-timers yearn-news-weekly.timer
systemctl --user status yearn-news-weekly.service
journalctl --user -u yearn-news-weekly.service -n 80 --no-pager
```

Test dependencies and unattended Codex execution without generating an issue:

```bash
python3 automation/run_weekly.py --check
```

Run a draft now or pause the schedule:

```bash
systemctl --user start yearn-news-weekly.service
systemctl --user disable --now yearn-news-weekly.timer
```

## Installation

On this host, copy the two unit files from `automation/` into
`~/.config/systemd/user/`, then run:

```bash
systemctl --user daemon-reload
systemctl --user enable --now yearn-news-weekly.timer
python3 automation/run_weekly.py --initialize
```

The units use this host's absolute checkout path. Reinstall them after changing
the schedule or moving the checkout. Keep Codex CLI authenticated on the host.
