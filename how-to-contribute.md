# How to contribute

Corrections are as welcome as additions. A wrong frame rate in the comparison
table is worth a pull request.

## The one rule

**`README.md` is generated. Do not edit it.**

Everything lives in [`data/papers.jsonl`](data/papers.jsonl), one JSON object
per line. Edit that, then:

```bash
python3 scripts/build_readme.py     # rewrites README.md and docs/comparison.md
python3 scripts/validate.py         # catches malformed records before CI does
```

Both run on every pull request. A PR that edits `README.md` by hand fails the
build, because the next regeneration would silently discard the change.

## Adding a paper

Append a line like this. Only `id`, `title`, `section` and `links` are required:

```json
{"id": "2508.13009", "name": "Matrix-Game 2.0", "title": "Matrix-Game 2.0: An Open-Source Real-Time and Streaming Interactive World Model", "venue": null, "date": "2025-08-18", "section": "systems", "section_source": "curated", "links": {"paper": "https://arxiv.org/abs/2508.13009", "code": "https://github.com/SkyworkAI/Matrix-Game"}, "attrs": {}}
```

| field | meaning |
| --- | --- |
| `id` | arXiv id (`2508.13009`), or a prefixed slug for anything else (`blog:genie-3`) |
| `name` | short system name, shown in backticks. `null` when the paper has no system name |
| `title` | the paper's title, verbatim. A leading `Name:` is stripped at render time |
| `venue` | real venue only (`ICLR 2026`). Leave `null` and the arXiv month is derived from `date` |
| `date` | `YYYY-MM-DD`, or `YYYY` when only the year is known. Sorts the list |
| `section` | one of the keys in [`data/sections.json`](data/sections.json) |
| `section_source` | `curated` once a human has confirmed the section, `rule` if a keyword guessed it |
| `links` | any of `paper`, `website`, `code`, `blog` |
| `attrs` | comparison-table fields, see below. `{}` until someone reads the paper |

## Which section

The main list, `systems`, has a hard bar — all three criteria in the
[Scope](README.md#scope) section:

1. per-step action conditioning,
2. causal or streaming generation,
3. persistent world state.

If you are unsure whether a paper clears all three, put it in the supporting
section it fits best (`control`, `realtime`, `memory`, `datasets`) and say so in
the PR. Moving it up later is one field.

Papers that are out of scope entirely — driving world models, robot policies
without a rendered interactive stream, static 3D scene generation — belong in
one of the [related lists](README.md#related-lists), not here.

## Filling in the comparison table

`attrs` is what makes this list more than a bibliography, and it is the part
that cannot be automated. Only add a field you have read out of the paper:

```json
"attrs": {
  "backbone": "causal-diffusion",
  "action_space": "keyboard (multi-key) + continuous mouse (camera); Minecraft, Unreal Engine, GTA5",
  "fps": "25",
  "horizon": "~600 frames at 25fps (~24s) in the composite action-sequence eval",
  "memory": "implicit-context",
  "open_source": true
}
```

- `backbone` — one of `causal-diffusion`, `bidirectional-diffusion`,
  `hybrid-AR-diffusion`, `AR-transformer`, `SSM-hybrid`, or `other:<description>`.
- `memory` — `none`, `implicit-context`, `explicit-spatial-storage`,
  `explicit-spatial-reconstruction`, `retrieval`, `compression-ssm`,
  `other:<description>`, or `hybrid:<a>+<b>`.
- `fps` and `horizon` — the numbers the paper claims, with the caveat the paper
  attaches. Verbatim is better than tidy; the README shortens them for display
  and [`docs/comparison.md`](docs/comparison.md) keeps them in full.
- Leave a field out when the paper does not report it. A blank means "not
  reported", and that is useful information. Do not guess.

## Maintainers

The [arXiv pipeline](docs/arxiv-pipeline.md) opens a review inbox every day.
Nothing it finds enters the list without someone ticking a box.
