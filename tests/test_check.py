#!/usr/bin/env python3
"""Focused regression tests for the treatment-pack checker."""

import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from packs.tools import check as checker


PACKS = Path(__file__).resolve().parent.parent / "packs"
BASELINE_PACK_IDS = {
    "acid_mono",
    "atelier",
    "basel",
    "blush",
    "broadsheet",
    "cherry_soda",
    "civic",
    "cobalt",
    "executive",
    "gilded_noir",
    "hearth",
    "heritage_navy",
    "hot_circuit",
    "meridian",
    "midnight_terminal",
    "neo_pop",
    "newsprint",
    "pastille",
    "retro_pop",
    "riso",
    "seafoam",
    "sherbet",
    "slate",
    "soft_serve",
    "soft_studio",
    "southwestern",
    "stark",
    "swiss_classic",
    "terra_sage",
    "trust_blue",
    "understory",
    "voltage",
}


class TreatmentPackCheckerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = yaml.safe_load((PACKS / "slate.yml").read_text(encoding="utf-8"))

    def write_pack(self, directory, mutate=None, stem="fixture"):
        doc = copy.deepcopy(self.base)
        doc["id"] = stem
        if mutate:
            mutate(doc)
        path = Path(directory) / f"{stem}.yml"
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
        return path

    def assert_has_failure(self, path, expected):
        failures, _warnings, _rows = checker.check(path)
        self.assertTrue(
            any(expected in failure for failure in failures),
            f"Expected {expected!r} in {failures!r}",
        )

    def test_shipped_catalog_passes_and_reports_text_ratings(self):
        paths = sorted(PACKS.glob("*.yml"))
        self.assertTrue(BASELINE_PACK_IDS.issubset({path.stem for path in paths}))
        for path in paths:
            with self.subTest(pack=path.stem):
                failures, warnings, rows = checker.check(path)
                self.assertEqual([], failures)
                self.assertEqual([], warnings)
                names = {name for name, _value in rows}
                self.assertIn("primary as text on background", names)
                self.assertIn("accent as text on background", names)

    def test_invalid_critical_color_fails_instead_of_skipping(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_pack(
                directory, lambda doc: doc["color"].update({"ink": "not-a-color"})
            )
            failures, _warnings, rows = checker.check(path)
            self.assertIn("color.ink must be #RRGGBB", failures)
            self.assertEqual([], rows)
            self.assertNotIn("skip", " ".join(failures))

    def test_wrong_format_and_scalar_types_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            def mutate(doc):
                doc["format"] = "design-treatment-pack/v0"
                doc["summary"] = 42

            path = self.write_pack(directory, mutate)
            self.assert_has_failure(path, "format must be")
            self.assert_has_failure(path, "summary must be a non-empty string")

    def test_missing_nested_key_unknown_key_enum_and_range_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            def mutate(doc):
                del doc["type"]["display"]["family"]
                doc["shape"]["mystery"] = True
                doc["motion"]["hover"] = "spin"
                doc["motion"]["easing"] = "very-smooth"
                doc["rhythm"]["base_unit_px"] = 0

            path = self.write_pack(directory, mutate)
            failures, _warnings, _rows = checker.check(path)
            for expected in (
                "missing key: type.display.family",
                "unknown key: shape.mystery",
                "motion.hover must be one of",
                "motion.easing must be a CSS easing keyword or cubic-bezier()",
                "rhythm.base_unit_px must be an integer from 1 to 64",
            ):
                self.assertTrue(
                    any(expected in failure for failure in failures),
                    f"Expected {expected!r} in {failures!r}",
                )

    def test_semantic_type_and_canonical_floor_rules_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            def mutate(doc):
                doc["type"]["body"]["bold_weight"] = doc["type"]["body"]["weight"]
                doc["type"]["scale_px"]["h2"] = doc["type"]["scale_px"]["h1"]
                doc["type"]["display"]["tracking"] = "tight"
                doc["apply"]["contrast_floor"] = "close enough"

            path = self.write_pack(directory, mutate)
            failures, _warnings, _rows = checker.check(path)
            for expected in (
                "bold_weight must be greater",
                "type.scale_px.h1 must be greater than type.scale_px.h2",
                "type.display.tracking must be 0 or an em value",
                "apply.contrast_floor must match the v1 canonical floor",
            ):
                self.assertTrue(
                    any(expected in failure for failure in failures),
                    f"Expected {expected!r} in {failures!r}",
                )

    def test_alpha_is_allowed_only_for_line(self):
        with tempfile.TemporaryDirectory() as directory:
            line_path = self.write_pack(
                directory,
                lambda doc: doc["color"].update({"line": "#0000001F"}),
                stem="alpha_line",
            )
            self.assertEqual([], checker.check(line_path)[0])

            focus_path = self.write_pack(
                directory,
                lambda doc: doc["color"].update({"focus": "#000000FF"}),
                stem="alpha_focus",
            )
            self.assert_has_failure(focus_path, "color.focus must be #RRGGBB")

    def test_surface_alt_and_inverse_focus_contrast_are_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            def mutate(doc):
                doc["color"]["ink_muted"] = doc["color"]["surface_alt"]
                doc["color"]["focus_inverse"] = doc["color"]["inverse_background"]

            path = self.write_pack(directory, mutate)
            self.assert_has_failure(path, "ink_muted on surface_alt")
            self.assert_has_failure(path, "focus_inverse on inverse_background")

    def test_missing_focus_inverse_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_pack(
                directory, lambda doc: doc["color"].pop("focus_inverse")
            )
            self.assert_has_failure(path, "missing key: color.focus_inverse")

    def test_duplicate_yaml_keys_fail_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            source = (PACKS / "slate.yml").read_text(encoding="utf-8")
            path = Path(directory) / "slate.yml"
            path.write_text(f"{source}\nid: slate\n", encoding="utf-8")
            self.assert_has_failure(path, "invalid YAML: found duplicate key 'id'")

    def test_id_must_match_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_pack(directory, stem="matching_name")
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            doc["id"] = "different_name"
            path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
            self.assert_has_failure(path, "does not match filename")

    def test_pack_must_be_portable_prompt_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source = (PACKS / "slate.yml").read_text(encoding="utf-8")

            no_newline = Path(directory) / "slate.yml"
            no_newline.write_text(source.rstrip("\n"), encoding="utf-8")
            self.assert_has_failure(no_newline, "must end with a newline")

            unsafe = Path(directory) / "slate.yml"
            unsafe.write_text(source + "# {{ unsafe }}\n", encoding="utf-8")
            self.assert_has_failure(unsafe, "unsafe template delimiter")

    def test_pack_path_must_not_be_a_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "slate.yml"
            target.write_bytes((PACKS / "slate.yml").read_bytes())
            link = Path(directory) / "linked.yml"
            link.symlink_to(target)
            self.assert_has_failure(link, "must not be a symbolic link")

    def test_css_tokens_reject_unsafe_characters(self):
        with tempfile.TemporaryDirectory() as directory:
            def mutate(doc):
                doc["type"]["display"]["stack"] = "Inter; color: red"
                doc["shape"]["card_shadow"] = "url(javascript:alert(1))"

            path = self.write_pack(directory, mutate)
            self.assert_has_failure(path, "type.display.stack contains unsupported")
            self.assert_has_failure(path, "shape.card_shadow contains unsupported")

    def test_details_cli_prints_primary_and_accent_rows(self):
        result = subprocess.run(
            [sys.executable, str(checker.__file__), "--details", str(PACKS / "slate.yml")],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("primary as text on background", result.stdout)
        self.assertIn("accent as text on background", result.stdout)


if __name__ == "__main__":
    unittest.main()
