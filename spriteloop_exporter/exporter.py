import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Optional

from krita import InfoObject


METADATA_FILE_NAME = "spriteloop.import.json"
FORMAT_NAME = "spriteloop.import"
FORMAT_VERSION = 1


class SpriteLoopExportError(Exception):
    pass


@dataclass
class ExportOptions:
    visible_only: bool = True
    export_groups_as_images: bool = True


@dataclass
class ExportResult:
    metadata_path: str
    part_count: int


@dataclass
class ExportNode:
    node: object
    id: str
    name: str
    node_type: str
    parent_id: Optional[str]


ProgressCallback = Callable[[int, int, str], None]


def export_document(
    document,
    export_dir: str,
    options: ExportOptions,
    progress_callback: Optional[ProgressCallback] = None,
) -> ExportResult:
    if not export_dir:
        raise SpriteLoopExportError("Choose an export folder.")

    export_dir = os.path.normpath(export_dir)
    os.makedirs(export_dir, exist_ok=True)
    images_dir = os.path.join(export_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    root = document.rootNode()
    if root is None:
        raise SpriteLoopExportError("The active document has no root node.")

    nodes = list(iter_export_nodes(root, options))
    if not nodes:
        raise SpriteLoopExportError("No exportable layers were found.")

    used_file_names: Dict[str, int] = {}
    node_ids = {id(item.node): item.id for item in nodes}
    parts = []
    hierarchy = []
    total_nodes = len(nodes)

    for index, item in enumerate(nodes, start=1):
        if item.node_type == "grouplayer":
            hierarchy.append(group_metadata(item, node_ids))
            if not options.export_groups_as_images:
                report_progress(progress_callback, index, total_nodes, item.name)
                continue

        rect = node_bounds(item.node)
        if rect["width"] <= 0 or rect["height"] <= 0:
            report_progress(progress_callback, index, total_nodes, item.name)
            continue

        file_name = unique_file_name(slugify(item.name), used_file_names)
        relative_path = "/".join(("images", file_name))
        absolute_path = os.path.join(images_dir, file_name)

        save_node_png(item.node, absolute_path, rect)

        part = {
            "id": item.id,
            "name": item.name,
            "image": relative_path,
            "x": rect["x"],
            "y": rect["y"],
            "width": rect["width"],
            "height": rect["height"],
            "opacity": node_opacity(item.node),
            "visible": node_visible(item.node),
        }
        if item.parent_id:
            part["parentId"] = item.parent_id
        parts.append(part)
        report_progress(progress_callback, index, total_nodes, item.name)

    if not parts:
        raise SpriteLoopExportError("No non-empty layers were exported.")

    metadata = {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "source": {
            "application": "Krita",
            "plugin": "spriteloop-krita-exporter",
            "documentName": document.fileName() or document.name(),
        },
        "canvas": {
            "width": int(document.width()),
            "height": int(document.height()),
        },
        "parts": parts,
    }
    if hierarchy:
        metadata["hierarchy"] = hierarchy

    metadata_path = os.path.join(export_dir, METADATA_FILE_NAME)
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")

    return ExportResult(metadata_path=metadata_path, part_count=len(parts))


def report_progress(
    progress_callback: Optional[ProgressCallback],
    current: int,
    total: int,
    node_name: str,
) -> None:
    if progress_callback:
        progress_callback(current, total, node_name)


def iter_export_nodes(root, options: ExportOptions) -> Iterable[ExportNode]:
    counters: Dict[str, int] = {}

    def walk(node, parent_id: Optional[str]) -> Iterable[ExportNode]:
        children = list(node.childNodes() or [])
        for child in children:
            if options.visible_only and not node_visible(child):
                continue

            child_type = child.type()
            child_name = child.name()
            child_id = unique_id(slugify(child_name), counters)

            if child_type == "grouplayer":
                group = ExportNode(child, child_id, child_name, child_type, parent_id)
                if options.export_groups_as_images:
                    yield group
                else:
                    yield group
                    yield from walk(child, child_id)
            elif child_type in ("paintlayer", "vectorlayer", "filelayer"):
                yield ExportNode(child, child_id, child_name, child_type, parent_id)

    yield from walk(root, None)


def group_metadata(item: ExportNode, node_ids: Dict[int, str]) -> dict:
    children = []
    for child in item.node.childNodes() or []:
        child_id = node_ids.get(id(child))
        if child_id:
            children.append(child_id)
    return {
        "id": item.id,
        "name": item.name,
        "type": "group",
        "children": children,
    }


def node_bounds(node) -> dict:
    bounds = node.bounds()
    return {
        "x": int(bounds.x()),
        "y": int(bounds.y()),
        "width": int(bounds.width()),
        "height": int(bounds.height()),
    }


def save_node_png(node, absolute_path: str, rect: dict) -> None:
    config = png_export_config()

    try:
        node.save(
            absolute_path,
            72,
            72,
            config,
            rect["x"],
            rect["y"],
            rect["width"],
            rect["height"],
        )
    except TypeError:
        try:
            node.save(absolute_path, 72, 72, config)
        except Exception as exc:
            raise SpriteLoopExportError("Could not export '{}': {}".format(node.name(), exc))
    except Exception as exc:
        raise SpriteLoopExportError("Could not export '{}': {}".format(node.name(), exc))

    if not os.path.exists(absolute_path):
        raise SpriteLoopExportError("Krita did not write image '{}'.".format(absolute_path))


def png_export_config() -> InfoObject:
    config = InfoObject()
    set_export_property(config, "alpha", True)
    set_export_property(config, "compression", 6)
    set_export_property(config, "forceSRGB", False)
    set_export_property(config, "indexed", False)
    set_export_property(config, "interlaced", False)
    set_export_property(config, "saveSRGBProfile", False)
    set_export_property(config, "transparencyFillcolor", [255, 255, 255])
    return config


def set_export_property(config: InfoObject, name: str, value) -> None:
    setter = getattr(config, "setProperty", None)
    if callable(setter):
        setter(name, value)


def node_visible(node) -> bool:
    visible = getattr(node, "visible", None)
    return bool(visible()) if callable(visible) else True


def node_opacity(node) -> float:
    opacity = getattr(node, "opacity", None)
    if not callable(opacity):
        return 1.0
    value = float(opacity())
    if value > 1:
        value = value / 255.0
    return max(0.0, min(1.0, value))


def unique_id(base: str, counters: Dict[str, int]) -> str:
    safe_base = base or "part"
    index = counters.get(safe_base, 0) + 1
    counters[safe_base] = index
    return safe_base if index == 1 else "{}_{}".format(safe_base, index)


def unique_file_name(base: str, counters: Dict[str, int]) -> str:
    return "{}.png".format(unique_id(base, counters))


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "part"
