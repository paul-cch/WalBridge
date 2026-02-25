#!/bin/bash

# Use SketchyBar's front_app_switched event payload when available.
if [[ -n "${NAME:-}" ]]; then
  sketchybar --set "$NAME" label="${INFO:-App}"
fi
