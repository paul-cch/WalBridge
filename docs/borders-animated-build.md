# Building `borders-animated` From Source

This project can use a checked-in prebuilt `borders-animated` binary, but you
can also build your own binary from source for better supply-chain trust.

## Fast Path

Build upstream JankyBorders from a pinned ref:

```bash
bash tools/build-borders-animated.sh \
  --repo https://github.com/FelixKratz/JankyBorders.git \
  --ref v1.8.4 \
  --out ./borders-animated
```

## Gradient-Capable Build

The default upstream build does not include the custom gradient behavior used
by this project (`active_color=gradient(...)`). For parity with the included
binary, build from a gradient-enabled fork and pinned ref:

```bash
bash tools/build-borders-animated.sh \
  --repo <your-gradient-fork-url> \
  --ref <pinned-tag-or-commit> \
  --out ./borders-animated
```

If your fork keeps gradient changes as a patch, apply it at build time:

```bash
bash tools/build-borders-animated.sh \
  --repo https://github.com/FelixKratz/JankyBorders.git \
  --ref v1.8.4 \
  --patch-file ./gradient.patch \
  --out ./borders-animated
```

## Use Your Built Binary

Point wallpaper-theme-sync to your binary:

```bash
export WALLPAPER_BORDERS_BIN="$HOME/.local/bin/borders-animated"
```

Or copy it into place:

```bash
cp ./borders-animated "$HOME/.local/bin/borders-animated"
```

## Reproducibility Notes

- Pin both repository and ref (`--repo` + `--ref`).
- Record the output SHA256 shown by the script.
- Keep your gradient patch in version control.
- Avoid `main`/moving refs for release builds.
