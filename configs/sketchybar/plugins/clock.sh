#!/bin/bash

if [[ -n "${NAME:-}" ]]; then
  sketchybar --set "$NAME" label="$(date '+%a %H:%M')"
fi
