#!/bin/bash

pct="$(pmset -g batt 2>/dev/null | grep -Eo '[0-9]+%' | head -n1 || true)"
if [[ -n "${NAME:-}" ]]; then
  if [[ -n "$pct" ]]; then
    sketchybar --set "$NAME" drawing=on label="$pct"
  else
    sketchybar --set "$NAME" drawing=off
  fi
fi
