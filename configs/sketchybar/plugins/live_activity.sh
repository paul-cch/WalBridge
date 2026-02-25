#!/bin/bash

# Public default: hide live activity widget unless user customizes this script.
if [[ -n "${NAME:-}" ]]; then
  sketchybar --set "$NAME" drawing=off
fi
