#!/usr/bin/env python3
"""Regression tests for the deterministic public catalog."""

import json
import unittest

from tools import build_catalog


class TreatmentCatalogTest(unittest.TestCase):
    def test_catalog_matches_all_valid_treatments(self):
        catalog, serialized = build_catalog.build_catalog()
        paths = sorted(build_catalog.TREATMENTS.glob("*.yml"))
        self.assertEqual("design-treatment-catalog/v1", catalog["format"])
        self.assertEqual(len(paths), catalog["count"])
        self.assertEqual(len(paths), len(catalog["treatments"]))
        self.assertEqual(
            sorted(entry["id"] for entry in catalog["treatments"]),
            [entry["id"] for entry in catalog["treatments"]],
        )
        self.assertEqual(
            {path.relative_to(build_catalog.ROOT).as_posix() for path in paths},
            {entry["path"] for entry in catalog["treatments"]},
        )
        self.assertEqual(catalog, json.loads(serialized))

    def test_copyable_template_is_valid(self):
        template = build_catalog.ROOT / "templates" / "my_treatment.yml"
        failures, warnings, rows = build_catalog.checker.check(template)
        self.assertEqual([], failures)
        self.assertEqual([], warnings)
        self.assertGreater(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
