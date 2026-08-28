# Interactive demos

Hand-written pages that let someone try the idea a paper describes, published
as sub-pages of the site.

## Adding one

Copy the template to a directory named for the paper's `id`, exactly as it
appears in [`data/papers.jsonl`](../data/papers.jsonl):

```bash
cp -r demos/_template demos/2608.06257
python3 scripts/build_site.py     # then open site/index.html
```

That is the whole registration step. There is no list to append to: the build
walks this directory, and a directory whose name matches a paper id becomes

- a `DEMO` badge on that paper's row in the index,
- a page at `/demos/<id>/` carrying the site's chrome — back link, paper title,
  tags, and the link to the paper itself.

The build looks for `index.html`, then `demo.html`, then `main.html`.

## The two rules

**Every path must be relative and must stay inside your directory.** The build
copies the directory wholesale into `site/demos/<id>/app/`, so `../../assets/`
resolves somewhere different once it has moved. Inline what you can; commit
what you cannot.

**Your page owns its whole document.** It runs in an iframe, so its CSS and its
key handlers cannot reach the page around it — reset what you like, capture the
arrow keys, take over the pointer. Nothing you do leaks out.

Third-party libraries are fine from a CDN. A demo that fetches from an origin
that may disappear is not; vendor it instead.

## What a demo is not

A demo is written by whoever adds it. It is **not** the paper's released code,
and the wrapper page says so under every one. If a paper ships a runnable
artefact, that belongs in the record's `links.code`, where it is labelled as
the authors' own.

Directories starting with `_` are skipped, which is how `_template` stays a
template.
