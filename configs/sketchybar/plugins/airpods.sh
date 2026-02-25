#!/bin/bash

# Public default: disable AirPods widget unless user customizes this script.
if [[ -n "${NAME:-}" ]]; then
  sketchybar --set "$NAME" drawing=off
fi
