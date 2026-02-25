#!/bin/bash

ssid="$(networksetup -getairportnetwork en0 2>/dev/null | sed -E 's/^Current Wi-Fi Network: //' || true)"
if [[ -n "${NAME:-}" ]]; then
  if [[ -n "$ssid" && "$ssid" != *"not associated"* ]]; then
    sketchybar --set "$NAME" drawing=on label="$ssid"
  else
    sketchybar --set "$NAME" drawing=off
  fi
fi
