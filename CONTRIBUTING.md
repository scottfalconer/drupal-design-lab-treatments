# Contributing a treatment

Thank you for helping expand the Drupal Design Lab treatment catalog. A treatment is a self-contained visual direction that can be combined with a Drupal site template. It controls visual expression while the selected template continues to own routes, content structure, functionality, accessibility, permissions, and editor outcomes.

## Add a treatment

1. Fork this repository and create a branch.
2. Copy the valid example:

   ```bash
   cp templates/my_treatment.yml packs/your_treatment.yml
   ```

3. Set `id: your_treatment`. The ID must use lower snake_case and exactly match the filename.
4. Replace every example value. In particular, make `summary`, `fit`, and `formula` specific enough that reviewers can understand what makes the treatment distinct.
5. Run validation:

   ```bash
   python3 -m pip install -r requirements-dev.txt
   python3 packs/tools/check.py --details packs/your_treatment.yml
   python3 tools/build_catalog.py
   python3 -m unittest discover -s tests
   ```

6. Commit the new treatment and the regenerated `catalog.json`, then open a pull request using the provided template. New treatments do not require test-code changes.

## Design contract

Every treatment must:

- use `format: design-treatment-pack/v1`;
- provide all required color, typography, shape, motion, rhythm, imagery, voice, and application fields;
- use only `#RRGGBB` colors, except the `line` role may also use `#RRGGBBAA`;
- meet the enforced WCAG contrast floor;
- preserve the canonical `apply.contrast_floor` statement and application precedence;
- use Google Fonts and list only the weights the treatment needs;
- honor reduced-motion preferences; and
- be meaningful without relying on a screenshot or proprietary design asset;
- remain under 64 KiB, end with a newline, and contain no Twig-style template delimiters; and
- use only the portable CSS characters accepted for font stacks and shadow values.

The checker rejects missing or unknown keys, duplicate YAML keys, invalid types, unsafe ranges, filename/ID mismatches, and contrast failures. `catalog.json` is deterministic and is the machine-readable integration surface for downstream consumers.

## Stable IDs and changes

Treatment IDs are public API. Once merged, do not repurpose an existing ID for a materially different visual direction. Create a new treatment by cloning the closest starting point and giving it a new ID. Corrections that preserve the same direction may update an existing treatment, but downstream consumers will detect the changed SHA-256 and must explicitly sync it.

Merged treatments are not removed through ordinary cleanup. If a legal, security, or contract issue requires withdrawal, open a maintainer issue first; downstream consumers must treat the missing ID as an explicit withdrawal, not an automatic delete.

## Originality and licensing

Do not include logos, photographs, illustrations, screenshots, proprietary design-system tokens, or other third-party assets. Font families must be available from Google Fonts under the SIL Open Font License. By opening a pull request, you agree that your contribution may be distributed under this repository's MIT license.

## Review criteria

Reviewers consider:

- contract and contrast validation;
- distinctness from existing treatments;
- clarity of the formula and role relationships;
- practical fit across real Drupal components and editor-owned content;
- accessible focus, motion, and interaction guidance; and
- rights and licensing safety.

Passing automation is required, but it does not guarantee acceptance. Maintainers may ask for a stronger formula, fewer decorative colors, safer contrast, or a clearer distinction from an existing treatment.
