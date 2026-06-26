# SpriteLoop Import Package Format

SpriteLoop import packages are folders containing one metadata file and referenced image assets.

## Metadata File

The root metadata file must be named:

```text
spriteloop.import.json
```

## Version 1

```json
{
  "format": "spriteloop.import",
  "version": 1,
  "source": {
    "application": "Krita",
    "plugin": "spriteloop-krita-exporter",
    "documentName": "character.kra"
  },
  "canvas": {
    "width": 1024,
    "height": 1024
  },
  "parts": [
    {
      "id": "head",
      "name": "Head",
      "image": "images/head.png",
      "x": 412,
      "y": 96,
      "width": 206,
      "height": 188,
      "opacity": 1,
      "visible": true,
      "parentId": "body"
    }
  ],
  "hierarchy": [
    {
      "id": "body",
      "name": "Body",
      "type": "group",
      "children": ["head"]
    }
  ]
}
```

## Importer Expectations

SpriteLoop should:

- accept only files named `spriteloop.import.json`
- resolve image paths relative to the metadata file
- validate that every referenced image exists
- create one part per `parts[]` entry
- place each part at `x`, `y`
- preserve `name` for display
- show readable errors for invalid JSON, unsupported versions, or missing images

The first SpriteLoop importer can ignore `hierarchy` and `parentId` while still reconstructing the artwork visually.

