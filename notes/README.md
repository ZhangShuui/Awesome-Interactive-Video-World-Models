# Notes

Reports written *across* the index rather than down a single paper —
comparison tables, taxonomies, timelines, and the negative evidence that only
shows up once a dozen systems are read side by side.

The dividing line against [`explainers/`](../explainers/README.md) is simply
whether there is a row to hang the page on. An explainer is about one paper and
lives at that paper's id; a note is about a question, and no single row owns it.

## Adding one

```bash
cp ~/notes/rope-in-retrieval-kv.html notes/
python3 scripts/build_site.py     # then open site/notes/index.html
```

The filename becomes the URL and that is the whole registration step — but
unlike a paper id, a slug carries no title, so **a note has to name itself in
its own `<head>`**:

```html
<title>检索式 KV-cache 的 RoPE 处理 · 交互式视频世界模型 2025–2026</title>
<meta name="description" content="检索回来的 KV 该给什么时间索引？拆成三层正交决策……">
```

The listing at `/notes/` reads exactly those two tags — the `<title>` for the
entry and the description for the line under it. A page with no `<title>` is
reported rather than listed, because a blank entry is the one failure a reader
cannot tell apart from a styling bug. A missing description just leaves the
entry without a second line.

Notes are listed in filename order. With a handful of them, imposing a
chronology would mean maintaining a date nobody would remember to update.

The index links here from under its readout and again from its footer, and both
entrances appear only once this directory has something in it.

## The one rule

Same as an explainer: **one file, standing on its own.** It *is* the page the
reader lands on — no iframe, no wrapper — so it may not reference a sibling
file. Inline the CSS and the JavaScript, embed images as `data:` URIs. Web
fonts and other assets over https are fine.

The build adds exactly one thing: an `← NOTES` link, fixed at bottom left, back
to the listing. Keep the `#site-back` id and the bottom-left corner free.

## What a note is not

A note is not generated from `data/papers.jsonl`, and nothing checks it against
the data the way `scripts/validate.py` checks a record. The numbers in these
tables were read out of papers and repositories by hand, they carry the
opinions of whoever wrote them, and they date. Where a note disagrees with a
paper, the paper is right.

Files starting with `_` are skipped.
