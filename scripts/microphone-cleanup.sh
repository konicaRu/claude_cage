#!/bin/sh
set -eu
rm -f /run/systemd/system/cage-audio.service.d/90-mic-bridge.conf
systemctl daemon-reload
systemctl restart cage-audio.service
# PulseAudio needs a moment after systemctl reports the service started.
i=0
until runuser -u cage -- pactl --server=unix:/run/cage-audio/native info >/dev/null 2>&1; do
  i=$((i+1)); test "$i" -lt 40; sleep .1
done
systemctl stop cage-mic-bridge-watchdog.timer || true
rm -f /run/cage-mic-bridge/data/audio.fifo
rmdir /run/cage-mic-bridge/data
rm -f /run/cage-mic-bridge/audio.pa /run/cage-mic-bridge/lease /run/cage-mic-bridge/lease.new /run/cage-mic-bridge/owner /run/cage-mic-bridge/watchdog.sh /run/cage-mic-bridge/cleanup.sh
rmdir /run/cage-mic-bridge
