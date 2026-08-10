#!/usr/bin/env bash
# Install a systemd user timer that runs the review agent once a day.
#
# A user timer only fires while you are logged in. That is the right trade for
# this job: the inbox Issue is maintained in the cloud and keeps accumulating
# while the machine is off, so a missed run costs nothing but a longer queue.
#
#   ./agent/install-timer.sh            # install and start
#   ./agent/install-timer.sh --remove   # stop and uninstall
#
# Watch it:  journalctl --user -u awesome-ivwm-review -f
# Run it now: systemctl --user start awesome-ivwm-review.service
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
NAME="awesome-ivwm-review"

if [[ "${1:-}" == "--remove" ]]; then
  systemctl --user disable --now "$NAME.timer" 2>/dev/null || true
  rm -f "$UNIT_DIR/$NAME.service" "$UNIT_DIR/$NAME.timer"
  systemctl --user daemon-reload
  echo "removed $NAME"
  exit 0
fi

command -v claude >/dev/null || { echo "claude CLI not on PATH" >&2; exit 1; }
command -v gh >/dev/null || { echo "gh CLI not on PATH" >&2; exit 1; }

mkdir -p "$UNIT_DIR"

cat > "$UNIT_DIR/$NAME.service" <<EOF
[Unit]
Description=Review arXiv candidates for Awesome-Interactive-Video-World-Models
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$REPO
# A dirty tree aborts the run, so pull first and leave local edits committed.
ExecStartPre=/usr/bin/env git -C $REPO switch main
ExecStartPre=/usr/bin/env git -C $REPO pull --ff-only
ExecStart=/usr/bin/env python3 $REPO/scripts/agent_review.py
# Cost ceiling lives in the arguments, not in a budget the script cannot see:
# at most 25 papers screened and 5 read per run.
TimeoutStartSec=3600
EOF

cat > "$UNIT_DIR/$NAME.timer" <<EOF
[Unit]
Description=Daily review of arXiv candidates

[Timer]
# An hour after the cloud workflow refreshes the inbox (01:30 UTC).
OnCalendar=*-*-* 02:30:00 UTC
Persistent=true
RandomizedDelaySec=600

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now "$NAME.timer"
echo "installed. next run:"
systemctl --user list-timers "$NAME.timer" --no-pager
