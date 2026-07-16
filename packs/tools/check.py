#!/usr/bin/env python3
"""Validate treatment-pack structure, colors, and contrast.

Usage: python3 packs/tools/check.py [--details] [pack.yml ...]

With no pack paths, checks every ``packs/*.yml`` file. The command exits 1
when a file cannot be read or parsed, its contract is malformed, or a required
contrast floor is missed. ``--details`` also prints the contrast matrix and
the informational primary/accent text ratings.
"""

import argparse
import re
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on the local runtime.
    raise SystemExit("PyYAML is required: pip3 install pyyaml") from exc


ROOT = Path(__file__).resolve().parent.parent
FORMAT = "design-treatment-pack/v1"
CONTRAST_FLOOR = (
    "ink >= 7:1 on background, surface, and surface_alt; ink_muted >= 4.5:1 on "
    "background, surface, and surface_alt; on_primary >= 4.5:1 on primary; inverse_ink "
    ">= 4.5:1 on inverse_background; focus roles >= 3:1 on their surfaces; colors below "
    "4.5:1 as text are decorative-only"
)

TOP_KEYS = {
    "format",
    "id",
    "name",
    "category",
    "summary",
    "fit",
    "formula",
    "color",
    "type",
    "shape",
    "motion",
    "rhythm",
    "imagery",
    "voice",
    "apply",
}
COLOR_ROLES = {
    "background",
    "surface",
    "surface_alt",
    "ink",
    "ink_muted",
    "line",
    "primary",
    "on_primary",
    "accent",
    "inverse_background",
    "inverse_ink",
    "focus",
    "focus_inverse",
}
TYPE_KEYS = {"display", "body", "meta", "source", "scale_px", "kicker"}
DISPLAY_KEYS = {"family", "stack", "weight", "tracking"}
BODY_KEYS = {"family", "stack", "weight", "bold_weight"}
META_KEYS = {"family", "stack"}
SCALE_KEYS = {"display", "h1", "h2", "h3", "body", "meta"}
KICKER_KEYS = {"case", "tracking"}
SHAPE_KEYS = {
    "radius_px",
    "button_radius_px",
    "border_width_px",
    "card_shadow",
    "button_shadow",
    "note",
}
MOTION_KEYS = {"duration_ms", "easing", "hover", "reduced_motion", "note"}
RHYTHM_KEYS = {"base_unit_px", "content_width_px", "section_gap_px", "note"}
APPLY_KEYS = {"contrast_floor", "rules"}

ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
HEX_RGB_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
HEX_RGBA_RE = re.compile(r"^#[0-9A-Fa-f]{8}$")
TRACKING_RE = re.compile(r"^(?:0|[+-]?(?:\d+(?:\.\d+)?|\.\d+)em)$")
CUBIC_BEZIER_RE = re.compile(
    r"^cubic-bezier\(\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*,\s*"
    r"([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*,\s*"
    r"([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*,\s*"
    r"([+-]?(?:\d+(?:\.\d+)?|\.\d+))\s*\)$"
)
SAFE_FONT_STACK_RE = re.compile(r"^[A-Za-z0-9'\", .-]{1,255}$")
SAFE_SHADOW_RE = re.compile(r"^[A-Za-z0-9#().,%\s-]{1,128}$")
MAX_PACK_BYTES = 64 * 1024
UNSAFE_TEMPLATE_DELIMITERS = ("{{", "{%", "{#")


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def lum(hex_str):
    """Return WCAG relative luminance for a validated #RRGGBB color."""
    if not isinstance(hex_str, str) or not HEX_RGB_RE.fullmatch(hex_str):
        return None
    chans = [int(hex_str[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [
        channel / 12.92
        if channel <= 0.03928
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in chans
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def ratio(foreground, background):
    """Return a WCAG contrast ratio, or None for an invalid color."""
    foreground_lum = lum(foreground)
    background_lum = lum(background)
    if foreground_lum is None or background_lum is None:
        return None
    return (max(foreground_lum, background_lum) + 0.05) / (
        min(foreground_lum, background_lum) + 0.05
    )


def fmt(value):
    return "invalid" if value is None else f"{value:.1f}:1"


def _validate_mapping(value, label, required, failures):
    if not isinstance(value, dict):
        failures.append(f"{label} must be a mapping")
        return False
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    for key in missing:
        failures.append(f"missing key: {label}.{key}")
    for key in unknown:
        failures.append(f"unknown key: {label}.{key}")
    return not missing


def _validate_string(value, label, failures):
    if not isinstance(value, str) or not value.strip():
        failures.append(f"{label} must be a non-empty string")


def _validate_int(value, label, failures, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        failures.append(f"{label} must be an integer from {minimum} to {maximum}")


def _validate_font_role(value, label, required, failures):
    if not _validate_mapping(value, label, required, failures):
        return
    _validate_string(value.get("family"), f"{label}.family", failures)
    _validate_string(value.get("stack"), f"{label}.stack", failures)
    if "weight" in required:
        _validate_int(value.get("weight"), f"{label}.weight", failures, 1, 1000)
    if "bold_weight" in required:
        _validate_int(
            value.get("bold_weight"), f"{label}.bold_weight", failures, 1, 1000
        )
    if "tracking" in required:
        _validate_string(value.get("tracking"), f"{label}.tracking", failures)
        if isinstance(value.get("tracking"), str) and not TRACKING_RE.fullmatch(
            value["tracking"]
        ):
            failures.append(f"{label}.tracking must be 0 or an em value")


def _validate_easing(value, failures):
    _validate_string(value, "motion.easing", failures)
    if not isinstance(value, str):
        return
    if value in {"linear", "ease", "ease-in", "ease-out", "ease-in-out"}:
        return
    match = CUBIC_BEZIER_RE.fullmatch(value)
    if not match:
        failures.append("motion.easing must be a CSS easing keyword or cubic-bezier()")
        return
    x1, _y1, x2, _y2 = (float(part) for part in match.groups())
    if not 0 <= x1 <= 1 or not 0 <= x2 <= 1:
        failures.append("motion.easing cubic-bezier x values must be from 0 to 1")


def _validate_contract(doc, path, failures):
    if not _validate_mapping(doc, "pack", TOP_KEYS, failures):
        return

    if doc.get("format") != FORMAT:
        failures.append(f"format must be {FORMAT!r}")

    pack_id = doc.get("id")
    if (
        not isinstance(pack_id, str)
        or not ID_RE.fullmatch(pack_id)
        or len(pack_id) > 64
    ):
        failures.append("id must be lower snake_case and at most 64 characters")
    if pack_id != path.stem:
        failures.append(f"id {pack_id!r} does not match filename {path.stem!r}")

    for key in ("name", "category", "summary", "fit", "formula", "imagery", "voice"):
        _validate_string(doc.get(key), key, failures)

    colors = doc.get("color")
    if _validate_mapping(colors, "color", COLOR_ROLES, failures):
        for role in sorted(COLOR_ROLES):
            value = colors.get(role)
            valid = isinstance(value, str) and bool(HEX_RGB_RE.fullmatch(value))
            if role == "line":
                valid = isinstance(value, str) and bool(
                    HEX_RGB_RE.fullmatch(value) or HEX_RGBA_RE.fullmatch(value)
                )
            if not valid:
                allowed = "#RRGGBB or #RRGGBBAA" if role == "line" else "#RRGGBB"
                failures.append(f"color.{role} must be {allowed}")

    typography = doc.get("type")
    if _validate_mapping(typography, "type", TYPE_KEYS, failures):
        _validate_font_role(
            typography.get("display"), "type.display", DISPLAY_KEYS, failures
        )
        _validate_font_role(typography.get("body"), "type.body", BODY_KEYS, failures)
        body = typography.get("body")
        if isinstance(body, dict):
            weight = body.get("weight")
            bold_weight = body.get("bold_weight")
            if type(weight) is int and type(bold_weight) is int and bold_weight <= weight:
                failures.append("type.body.bold_weight must be greater than type.body.weight")
        meta = typography.get("meta")
        if meta is not None:
            _validate_font_role(meta, "type.meta", META_KEYS, failures)
        if typography.get("source") != "google-fonts":
            failures.append("type.source must be 'google-fonts'")
        for role in ("display", "body", "meta"):
            definition = typography.get(role)
            if definition is not None and isinstance(definition, dict):
                stack = definition.get("stack")
                if not isinstance(stack, str) or not SAFE_FONT_STACK_RE.fullmatch(stack):
                    failures.append(
                        f"type.{role}.stack contains unsupported CSS characters or is too long"
                    )

        scale = typography.get("scale_px")
        if _validate_mapping(scale, "type.scale_px", SCALE_KEYS, failures):
            for key in sorted(SCALE_KEYS):
                _validate_int(scale.get(key), f"type.scale_px.{key}", failures, 8, 240)
            ordered_keys = ("display", "h1", "h2", "h3", "body", "meta")
            if all(type(scale.get(key)) is int for key in ordered_keys):
                for larger, smaller in zip(ordered_keys, ordered_keys[1:]):
                    if scale[larger] <= scale[smaller]:
                        failures.append(
                            f"type.scale_px.{larger} must be greater than "
                            f"type.scale_px.{smaller}"
                        )

        kicker = typography.get("kicker")
        if _validate_mapping(kicker, "type.kicker", KICKER_KEYS, failures):
            if kicker.get("case") not in {"none", "upper", "lower", "title"}:
                failures.append(
                    "type.kicker.case must be one of: none, upper, lower, title"
                )
            _validate_string(kicker.get("tracking"), "type.kicker.tracking", failures)
            if isinstance(kicker.get("tracking"), str) and not TRACKING_RE.fullmatch(
                kicker["tracking"]
            ):
                failures.append("type.kicker.tracking must be 0 or an em value")

    shape = doc.get("shape")
    if _validate_mapping(shape, "shape", SHAPE_KEYS, failures):
        _validate_int(shape.get("radius_px"), "shape.radius_px", failures, 0, 999)
        _validate_int(
            shape.get("button_radius_px"),
            "shape.button_radius_px",
            failures,
            0,
            999,
        )
        _validate_int(
            shape.get("border_width_px"),
            "shape.border_width_px",
            failures,
            0,
            20,
        )
        for key in ("card_shadow", "button_shadow", "note"):
            _validate_string(shape.get(key), f"shape.{key}", failures)
        for key in ("card_shadow", "button_shadow"):
            value = shape.get(key)
            if not isinstance(value, str) or not SAFE_SHADOW_RE.fullmatch(value):
                failures.append(
                    f"shape.{key} contains unsupported CSS characters or is too long"
                )

    motion = doc.get("motion")
    if _validate_mapping(motion, "motion", MOTION_KEYS, failures):
        _validate_int(
            motion.get("duration_ms"), "motion.duration_ms", failures, 0, 5000
        )
        _validate_easing(motion.get("easing"), failures)
        if motion.get("hover") not in {"none", "lift", "push", "invert"}:
            failures.append("motion.hover must be one of: none, lift, push, invert")
        if motion.get("reduced_motion") != "honor":
            failures.append("motion.reduced_motion must be 'honor'")
        _validate_string(motion.get("note"), "motion.note", failures)

    rhythm = doc.get("rhythm")
    if _validate_mapping(rhythm, "rhythm", RHYTHM_KEYS, failures):
        _validate_int(
            rhythm.get("base_unit_px"), "rhythm.base_unit_px", failures, 1, 64
        )
        _validate_int(
            rhythm.get("content_width_px"),
            "rhythm.content_width_px",
            failures,
            320,
            2560,
        )
        _validate_int(
            rhythm.get("section_gap_px"),
            "rhythm.section_gap_px",
            failures,
            0,
            512,
        )
        _validate_string(rhythm.get("note"), "rhythm.note", failures)

    apply = doc.get("apply")
    if _validate_mapping(apply, "apply", APPLY_KEYS, failures):
        if apply.get("contrast_floor") != CONTRAST_FLOOR:
            failures.append("apply.contrast_floor must match the v1 canonical floor")
        rules = apply.get("rules")
        if not isinstance(rules, list) or not rules:
            failures.append("apply.rules must be a non-empty list")
        else:
            for index, rule in enumerate(rules):
                _validate_string(rule, f"apply.rules[{index}]", failures)


def _contrast_rows(colors, failures):
    floors = [
        ("ink on background", "ink", "background", 7.0),
        ("ink on surface", "ink", "surface", 7.0),
        ("ink on surface_alt", "ink", "surface_alt", 7.0),
        ("ink_muted on background", "ink_muted", "background", 4.5),
        ("ink_muted on surface", "ink_muted", "surface", 4.5),
        ("ink_muted on surface_alt", "ink_muted", "surface_alt", 4.5),
        ("on_primary on primary", "on_primary", "primary", 4.5),
        (
            "inverse_ink on inverse_background",
            "inverse_ink",
            "inverse_background",
            4.5,
        ),
        ("focus on background", "focus", "background", 3.0),
        ("focus on surface", "focus", "surface", 3.0),
        ("focus on surface_alt", "focus", "surface_alt", 3.0),
        (
            "focus_inverse on inverse_background",
            "focus_inverse",
            "inverse_background",
            3.0,
        ),
    ]
    rows = []
    for name, foreground_role, background_role, floor in floors:
        value = ratio(colors[foreground_role], colors[background_role])
        rows.append((name, fmt(value)))
        if value is None:
            failures.append(f"{name} could not be calculated")
        elif value < floor:
            failures.append(f"{name} = {fmt(value)} (floor {floor:g}:1)")

    for name, role in (("primary", "primary"), ("accent", "accent")):
        value = ratio(colors[role], colors["background"])
        if value is None:
            rating = "invalid"
        elif value >= 7:
            rating = "AAA"
        elif value >= 4.5:
            rating = "AA"
        elif value >= 3:
            rating = "AA large"
        else:
            rating = "decorative-only"
        rows.append((f"{name} as text on background", f"{fmt(value)} - {rating}"))
    return rows


def check(path):
    """Return ``(failures, warnings, contrast_rows)`` for one pack path."""
    failures = []
    warnings = []
    if path.is_symlink():
        return ["pack path must not be a symbolic link"], warnings, []
    if not path.is_file():
        return ["pack path must be a regular file"], warnings, []
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return [f"cannot read file: {exc}"], warnings, []
    if len(raw) > MAX_PACK_BYTES:
        failures.append(f"pack exceeds the {MAX_PACK_BYTES}-byte limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"pack must be valid UTF-8: {exc}"], warnings, []
    if not text.endswith("\n"):
        failures.append("pack must end with a newline")
    if any(delimiter in text for delimiter in UNSAFE_TEMPLATE_DELIMITERS):
        failures.append("pack contains an unsafe template delimiter")

    try:
        doc = yaml.load(text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        problem = getattr(exc, "problem", None) or str(exc).splitlines()[0]
        return [f"invalid YAML: {problem}"], warnings, []

    _validate_contract(doc, path, failures)
    rows = []
    colors = doc.get("color") if isinstance(doc, dict) else None
    if not failures and isinstance(colors, dict):
        rows = _contrast_rows(colors, failures)
    return failures, warnings, rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--details",
        action="store_true",
        help="print the contrast matrix for every pack",
    )
    parser.add_argument("packs", nargs="*", type=Path, help="pack YAML files to check")
    args = parser.parse_args(argv)

    paths = args.packs or sorted(ROOT.glob("*.yml"))
    any_fail = False
    for path in paths:
        failures, warnings, rows = check(path)
        status = "FAIL" if failures else "ok"
        any_fail = any_fail or bool(failures)
        print(f"{status:4}  {path.stem}")
        for failure in failures:
            print(f"      FAIL  {failure}")
        for warning in warnings:
            print(f"      WARN  {warning}")
        if args.details:
            for name, value in rows:
                print(f"      {name}: {value}")

    print(f"\n{len(paths)} packs checked")
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
