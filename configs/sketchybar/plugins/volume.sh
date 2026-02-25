#!/bin/bash

vol="$(osascript -e 'output volume of (get volume settings)' 2>/dev/null || true)"
if [[ -n "${NAME:-}" ]]; then
  if [[ -n "$vol" ]]; then
    sketchybar --set "$NAME" drawing=on label="${vol}%"
  else
    sketchybar --set "$NAME" drawing=off
  fi
fi
