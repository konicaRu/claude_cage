#!/bin/sh
set -eu
lease=$(cat /run/cage-mic-bridge/lease 2>/dev/null || echo 0)
case "$lease" in ''|*[!0-9]*) lease=0;; esac
if test "$(( $(date +%s) - lease ))" -gt 90; then
  /bin/sh /run/cage-mic-bridge/cleanup.sh
fi
