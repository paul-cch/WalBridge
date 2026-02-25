#!/bin/bash

# Public default: private integration disabled.
if [[ -n "${NAME:-}" ]]; then
  sketchybar --set "$NAME" drawing=off
fi
