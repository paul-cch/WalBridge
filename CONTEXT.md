# WalBridge

WalBridge keeps macOS wallpaper-derived colors in sync across desktop and terminal apps.

## Language

**Target App**:
An external app WalBridge can generate color material for, regardless of whether that app supports hot reload.
_Avoid_: target, service, integration

**Color Material**:
The generated theme/configuration content WalBridge produces for a Target App from wallpaper-derived colors.
_Avoid_: config blob, writer output, theme file

**Sync Run**:
One wallpaper-to-Target-App pass: load wallpaper, derive color material, write enabled Target Apps, and hot reload what can reload.
_Avoid_: pipeline, workflow, job
