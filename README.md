# Drupal Design Lab Treatments

Reusable visual-treatment packs for Drupal site templates. Each treatment is one self-contained YAML file carrying color roles, typography, shape, motion, rhythm, imagery, voice, and rules for applying the direction without replacing Drupal-owned content or functionality.

The catalog launches with **32 treatments** and welcomes additions through pull requests. The
current, complete list is always available in [`catalog.json`](catalog.json).

## Use a treatment

A generated build combines:

1. Drupal CMS and its required capabilities;
2. a site template or base Look;
3. optional Recipes; and
4. one treatment from this repository.

The treatment may strongly redirect color, typography, spacing, density, layout, section composition, component styling, imagery treatment, and non-essential motion. The site template remains authoritative for routes, information architecture, structured data, functionality, accessibility, permissions, workflows, and editor outcomes.

Treatment YAML is intended to be included byte-for-byte in a generated build prompt. Consumers should pin the treatment's SHA-256 from [`catalog.json`](catalog.json), rather than silently following a moving branch.

## Add your own

Copy the provided, valid template and run the checker:

```bash
git clone https://github.com/scottfalconer/drupal-design-lab-treatments.git
cd drupal-design-lab-treatments
python3 -m pip install -r requirements-dev.txt
cp templates/my_treatment.yml packs/your_treatment.yml
# Edit the file and make id match the filename.
python3 packs/tools/check.py --details packs/your_treatment.yml
python3 tools/build_catalog.py
```

Then open a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contract, review criteria, licensing requirements, and validation workflow.

## Machine-readable catalog

[`catalog.json`](catalog.json) is generated deterministically from the validated YAML files. Each entry includes its stable ID, display metadata, repository path, and exact SHA-256. Downstream sites can compare a pinned catalog commit and treatment hashes before importing changes.

The supported synchronization model is pull-based and reviewable:

- fetch a selected Git commit or release;
- validate every treatment locally;
- compare IDs and hashes against the currently pinned catalog;
- generate a change plan;
- materialize approved additions or corrections; and
- deploy code, configuration, content, and media through the site's normal release process.

Production sites should not fetch this repository at request time.

## Treatment roles

Every treatment defines thirteen color roles:

| Role | Purpose |
| --- | --- |
| `background` | Page field |
| `surface` | Cards and panels |
| `surface_alt` | Alternating or tinted sections |
| `ink` / `ink_muted` | Primary and secondary text |
| `line` | Borders, dividers, and rules |
| `primary` / `on_primary` | Main action fill and its foreground |
| `accent` | Secondary, usually decorative emphasis |
| `inverse_background` / `inverse_ink` | Reversed bands such as footers and CTA strips |
| `focus` / `focus_inverse` | Focus rings on regular and inverse surfaces |

The validator enforces these minimums:

- `ink` at least 7:1 on background and surfaces;
- `ink_muted` at least 4.5:1 on background and surfaces;
- action and inverse foregrounds at least 4.5:1 on their fills; and
- focus roles at least 3:1 on the surfaces where they appear.

Run `python3 packs/tools/check.py --details` to see every enforced pair and informational ratings for primary and accent text.

## The initial 32 treatments

| ID | Direction |
| --- | --- |
| [`acid_mono`](packs/acid_mono.yml) | Black, white, one acid accent, and mono display type |
| [`atelier`](packs/atelier.yml) | Ivory, ink actions, tracked caps, and restrained bronze |
| [`basel`](packs/basel.yml) | Swiss structure with black actions and rationed red |
| [`blush`](packs/blush.yml) | Cream, dusty rose, and gray-blue actions |
| [`broadsheet`](packs/broadsheet.yml) | Editorial serif hierarchy with rules instead of boxes |
| [`cherry_soda`](packs/cherry_soda.yml) | Cream, cherry red, retro teal, and poster serif |
| [`civic`](packs/civic.yml) | Color-safe public-service utility with Public Sans |
| [`cobalt`](packs/cobalt.yml) | Quiet product design pushed toward royal cobalt |
| [`executive`](packs/executive.yml) | Ice gray, trust navy, and plaque-gold details |
| [`gilded_noir`](packs/gilded_noir.yml) | Black, gold, and Deco luxury after dark |
| [`hearth`](packs/hearth.yml) | Espresso, cream, paprika, olive, and Fraunces |
| [`heritage_navy`](packs/heritage_navy.yml) | Navy, ivory, brass, and Garamond |
| [`hot_circuit`](packs/hot_circuit.yml) | Zinc black, acid-green actions, decorative hot pink |
| [`meridian`](packs/meridian.yml) | Source Serif, Libre Franklin, navy, and gold |
| [`midnight_terminal`](packs/midnight_terminal.yml) | Near-black, phosphor green, grotesque, and mono details |
| [`neo_pop`](packs/neo_pop.yml) | Cream paper, black borders, hard shadows, loud yellow |
| [`newsprint`](packs/newsprint.yml) | Flat newsprint, red pencil, Newsreader, and Oswald |
| [`pastille`](packs/pastille.yml) | Lavender mist, feather shadows, and Plus Jakarta Sans |
| [`retro_pop`](packs/retro_pop.yml) | Yellow field, white cards, black shadows, royal purple |
| [`riso`](packs/riso.yml) | Screen-print blocks, acid chartreuse, and zero radius |
| [`seafoam`](packs/seafoam.yml) | Pale mint, forest teal, and patient-facing calm |
| [`sherbet`](packs/sherbet.yml) | Warm milk, plum outlines, cobalt pills, candy tints |
| [`slate`](packs/slate.yml) | Disciplined gray ramp, one working blue, and Inter |
| [`soft_serve`](packs/soft_serve.yml) | Lavender pastels, deep indigo, and friendly Nunito |
| [`soft_studio`](packs/soft_studio.yml) | Oat surfaces, light Garamond, and tiny tracked caps |
| [`southwestern`](packs/southwestern.yml) | Warm sand, forest teal, and terracotta action |
| [`stark`](packs/stark.yml) | Monochrome with one acid highlight |
| [`swiss_classic`](packs/swiss_classic.yml) | Black, white, true red, neo-grotesque, visible grid |
| [`terra_sage`](packs/terra_sage.yml) | Terracotta, sage, cream, DM Serif, and DM Sans |
| [`trust_blue`](packs/trust_blue.yml) | Dependable blue, cool gray, Montserrat, and Open Sans |
| [`understory`](packs/understory.yml) | Moss, stone, unbleached paper, Lora, and Karla |
| [`voltage`](packs/voltage.yml) | Dark technical cyan with a violet second |

## Versioning and license

The file format is `design-treatment-pack/v1`. Treatment IDs are stable public API; materially different directions should receive a new ID instead of silently replacing an existing one.

Code, documentation, and treatment data are available under the [MIT License](LICENSE). Named Google Fonts remain subject to their SIL Open Font License terms.
