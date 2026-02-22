#!/bin/bash

source "$CONFIG_DIR/colors.sh"

if [ "$SELECTED" = "true" ]; then
  # Same dark as BAR_COLOR but at ~60% opacity so wallpaper shows through
  SELECTED_BG=$(echo $BAR_COLOR | sed 's/0x../0x99/')
  sketchybar --animate tanh 15 --set "$NAME" \
    icon.color=$BLUE_VIVID \
    icon.padding_left=8 \
    icon.padding_right=8 \
    label.drawing=on \
    label.color=$BLUE_VIVID \
    background.drawing=on \
    background.color=$SELECTED_BG \
    background.border_color=$BLUE \
    background.border_width=1 \
    background.corner_radius=6 \
    background.height=28
else
  sketchybar --animate tanh 15 --set "$NAME" \
    icon.color=$GREY \
    icon.padding_left=8 \
    icon.padding_right=8 \
    label.drawing=off \
    background.drawing=on \
    background.color=$BAR_COLOR \
    background.border_color=$GREY \
    background.border_width=1 \
    background.corner_radius=6 \
    background.height=28
fi
