# SpriteLoop Krita Exporter

Krita Python plugin for exporting layered artwork as a SpriteLoop import package.

The exporter creates:

- cropped PNG files for exported parts
- `spriteloop.import.json` metadata
- position and hierarchy data so SpriteLoop can reconstruct the artwork layout

## Status

Initial project scaffold. The package format is intended to be consumed by the future SpriteLoop app feature: **Import Data Package**.

## Krita Install

### Recommended: Import From File

Use Krita's built-in importer:

`Tools -> Scripts -> Import Python Plugin from File`

Create the install zip with Windows Explorer:

1. Open `dist/spriteloop_exporter`.
2. Select `spriteloop_exporter.desktop` and `spriteloop_exporter/`.
3. Right-click and choose `Compress to ZIP file`.
4. Import that zip in Krita.

The archive contains `spriteloop_exporter.desktop` and `spriteloop_exporter/` at the top level.

Restart Krita, then enable **SpriteLoop Exporter** in:

`Settings -> Configure Krita -> Python Plugin Manager`

The action appears under:

`Tools -> Scripts -> Export SpriteLoop Package`

The plugin also adds a **SpriteLoop** docker with an **Export Package** button. Enable it from Krita's docker list if it is not visible.

The exporter opens an options dialog before writing files. By default it exports groups as image parts. Uncheck **Export groups as images** to export individual layers instead.

### Manual Install

If you want to install manually, copy these into Krita's `pykrita` resource folder:

- `spriteloop_exporter.desktop`
- `spriteloop_exporter/`

## Exported Package

```text
my-character/
  spriteloop.import.json
  images/
    head.png
    torso.png
    arm_left.png
```

See [docs/import-package-format.md](docs/import-package-format.md) for the metadata contract.

## Development Notes

The plugin targets Krita's built-in Python API and avoids third-party runtime dependencies.

The initial exporter favors a conservative format that SpriteLoop can import later without knowing about Krita internals:

- `canvas` stores the original document size
- `parts[]` stores image file paths and original top-left placement
- `hierarchy` is optional and can be ignored by early importers
