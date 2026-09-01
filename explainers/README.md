# Explainers

Long-form read-throughs of individual papers — the diagram you had to draw
before the method made sense, the ablation table read out loud — published as
sub-pages of the site.

## Adding one

Save the page as a file named for the paper's `id`, exactly as it appears in
[`data/papers.jsonl`](../data/papers.jsonl):

```bash
cp ~/notes/reworld.html explainers/2608.23565.html
python3 scripts/build_site.py     # then open site/index.html
```

That is the whole registration step. There is no list to append to: the build
walks this directory, and a file whose name matches a paper id becomes

- an `EXPLAINER` badge on that paper's row in the index,
- a page at `/explainers/<id>.html`, reachable by a link you can send someone.

A file naming an id no paper carries is reported as a warning rather than
skipped in silence, because a mistyped id would otherwise build nothing at all
for as long as nobody went looking for the badge.

## The one rule

**One file, standing on its own.** Unlike a demo, an explainer is not copied
into a directory of its own and not run in an iframe — it *is* the page the
reader lands on. So it may not reference a sibling file: inline the CSS and the
JavaScript, and embed images as `data:` URIs. Web fonts and other assets over
https are fine; a fetch from an origin that may disappear is not.

The build adds exactly one thing to what you wrote: an `← INDEX` link, fixed at
bottom left, that returns to the paper's row. It is inserted after `<body>` and
styled inline under `#site-back`, so keep that id and the bottom-left corner
free. Everything else — the theme, the header, the scroll behaviour, the
keyboard — is yours, and nothing in `web/style.css` reaches these pages.

## What an explainer is not

An explainer is written by whoever adds it. It is **not** the paper, and not
the authors' own account of it; where it disagrees with the paper, the paper is
right. Anything the authors published themselves belongs in the record's
`links`, where it is labelled as theirs.

Files starting with `_` are skipped, the same as directories under `demos/`.
