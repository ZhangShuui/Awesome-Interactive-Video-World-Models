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

Append a line like this. Only `id`, `title`, `tags` and `links` are required:

```json
{"id": "2508.13009", "name": "Matrix-Game 2.0", "title": "Matrix-Game 2.0: An Open-Source Real-Time and Streaming Interactive World Model", "venue": null, "date": "2025-08-18", "tags": ["systems", "realtime"], "tags_source": {"systems": "curated", "realtime": "curated"}, "links": {"paper": "https://arxiv.org/abs/2508.13009", "code": "https://github.com/SkyworkAI/Matrix-Game"}, "attrs": {}}
```

| field | meaning |
| --- | --- |
| `id` | arXiv id (`2508.13009`), or a prefixed slug for anything else (`blog:genie-3`) |
| `name` | short system name, shown in backticks. `null` when the paper has no system name |
| `title` | the paper's title, verbatim. A leading `Name:` is stripped at render time |
| `venue` | real venue only (`ICLR 2026`). Leave `null` and the arXiv month is derived from `date` |
| `date` | `YYYY-MM-DD`, or `YYYY` when only the year is known. Sorts the list |
| `tags` | one or more keys from [`data/tags.json`](data/tags.json), in that file's order. A new tag needs a `key`, an `icon` nobody else uses, a `title` and a `blurb` |
| `tags_source` | per tag: `curated` once a human has confirmed it, `rule` if a keyword guessed it |
| `links` | any of `paper`, `website`, `code`, `blog` |
| `attrs` | comparison-table fields, see below. `{}` until someone reads the paper |

## Which tags

The main list, `systems`, has a hard bar — all three criteria in the
[Scope](README.md#scope) section:

1. per-step action conditioning,
2. causal or streaming generation,
3. persistent world state.

Tags are not exclusive, so this is not a choice. A paper that clears the bar
gets `systems` **and** a tag for each thing it contributes — `control` for an
action interface, `realtime` for a latency result, `memory` for a persistence
mechanism. If you are unsure whether it clears all three, leave `systems` off
and tag the rest; adding it later is one entry in a list.

Tag what the paper contributes, not what it mentions. Every video model has an
action space and a frame rate; two or three tags is a lot, five is wrong.

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

## The site

The same data renders a second way, at
[zhangshuui.github.io/Awesome-Interactive-Video-World-Models](https://zhangshuui.github.io/Awesome-Interactive-Video-World-Models/):
the whole list, filterable by tag, with the comparison record folded into each
row. Nothing there is a separate source of truth — it is built from
`data/papers.jsonl` by `scripts/build_site.py`.

```bash
python3 scripts/build_site.py           # -> site/
python3 -m http.server -d site 8000
```

`site/` is not committed. The Pages workflow rebuilds it on every push to main,
which is the reason it cannot fall behind the data the way `README.md` could.
Edit `data/papers.jsonl` for content and `web/` for how it looks.

A paper can also carry an interactive demo as a sub-page — see
[`demos/README.md`](demos/README.md). Copy `demos/_template` to
`demos/<paper-id>/` and the next build picks it up.

It can carry a written explainer the same way — see
[`explainers/README.md`](explainers/README.md). Drop a self-contained page at
`explainers/<paper-id>.html` and the next build publishes it and badges the
row. Neither needs registering anywhere; the filename is the whole of it.

A report that spans the index rather than a single paper has no row to hang
off, so it goes to [`notes/`](notes/README.md) instead and is published under
`/notes/` behind a listing of its own. A note names itself in its `<head>`;
see that README.

## Maintainers

The [candidate pipeline](docs/candidate-pipeline.md) opens a review inbox every day.
Nothing it finds enters the list without someone ticking a box.
