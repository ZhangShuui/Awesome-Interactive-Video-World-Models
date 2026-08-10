# Awesome Interactive Video World Models [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)

A curated list of **interactive video world models** — generative models you can act inside, one step at a time.

Video generation stopped being a movie and became a place. This list tracks that shift: systems where a user or a policy issues an action, the model produces the next frames causally, and the world is still there when you look back — together with the work those systems are built out of, on action control, real-time generation, and long-horizon memory. General world-model lists cover robotics, driving, and 3D generation alongside this; here the narrow focus is the point.

<!-- BEGIN:STATS -->
<!-- END:STATS -->

Every entry is screened against the [scope](#scope) below. Those that clear the strict bar — a closed loop, causal generation, persistent state — are profiled on backbone, action space, frame rate, and memory mechanism where the paper has been read in depth; see [System Comparison](#system-comparison).

> ### Please read this first
>
> **This is a personal reading record, not an authoritative or community-curated list.** It is
> maintained by one person as working notes for a survey in progress. Inclusion, exclusion,
> section placement, and every value in the comparison table are one reader's judgement, made
> from the papers themselves and revised as that reading continues. Treat it as a starting point
> for your own reading, not as a citation-grade source.
>
> **New entries are screened by an [automated agent](docs/agent-review.md) before a human sees
> them.** The agent proposes; a person merges. Anything it placed without human confirmation is
> marked `"section_source": "agent"` in [`data/papers.jsonl`](data/papers.jsonl) and is listed by
> `python3 scripts/validate.py --review`, so you can always tell which entries have been read by
> a person and which have not. Papers it turned down are recorded, with reasons, in
> [`data/agent-rejected.jsonl`](data/agent-rejected.jsonl) rather than silently dropped.
>
> **It was initialized from [Awesome-World-Models](https://github.com/leofan90/Awesome-World-Models)**
> (BSD-3-Clause) by Leo Fan and contributors. That list seeded the initial paper pool — one of
> the collection channels parsed its README — and supplied the website and code links for entries
> that appear in both. The repository layout and the arXiv review-inbox workflow are adapted from
> it as well. If you want broad, actively maintained coverage of world models, go there; this list
> only narrows the same field to one slice of it.
>
> No affiliation with, or endorsement by, the authors of any listed paper or of the upstream lists
> is claimed. Mistakes here are the maintainer's, not the papers' authors'. Corrections are
> welcome — please [open an issue or a PR](how-to-contribute.md).

## Scope

Scope works at two levels: a wide one that decides whether a paper is in the list
at all, and a strict one that decides whether it counts as an interactive video
world model.

### What gets in

**Generated video, bearing on at least one of three axes.** The paper has to be
about generating video — an architecture, a component, an analysis, a benchmark,
a dataset — and it has to touch one of:

- **Action control** — how an action reaches the generator, including latent
  actions learned without labels.
- **Real-time and streaming generation** — meeting a per-frame latency budget:
  causal backbones, distillation, caching, sparse attention, serving.
- **Long-horizon consistency and memory** — staying coherent past the context
  window, and still being the same world when you come back to it.

Action conditioning is **not** required for membership. A training-free method
for minute-long video, or a sparse-attention kernel for video diffusion
transformers, is squarely in scope: interactive world models are built out of
exactly that work, and a list that admitted only closed-loop systems would omit
most of what makes them possible.

### What counts as an interactive video world model

The strict bar, which decides the `systems` designation and the rows of the
[System Comparison](#system-comparison) table. All three:

1. **Per-step action conditioning.** The model consumes an action at each step
   and the next observation depends on it. A single prompt or a fixed trajectory
   supplied up front does not count; the loop has to be closeable.
2. **Causal or streaming generation.** Frames are produced in causal order, so
   the user can react to what they just saw. Bidirectional denoising over a whole
   clip is out, however good the clip is.
3. **Persistent world state.** Something survives across steps — context, an
   explicit spatial store, a retrievable memory — so revisiting a place does not
   resample it from scratch.

Camera and navigation control counts as an action space: it closes the same loop
with a restricted set of actions.

### What stays out

Video work that touches none of the three axes — restoration, relighting, shadow
removal, portrait and face shaders, editing an existing clip — is out no matter
how good it is. So is work with no generated video at all: latent-only prediction
with no decoder, reinforcement-learning world models that never render, symbolic
or text-based world state, and static 3D asset and scene generation.

Several excellent lists cover the wider field — see [Related lists](#related-lists).

## Contents

<!-- BEGIN:CONTENTS -->
<!-- END:CONTENTS -->

Entries are newest first within each section. Venue tags show `arXiv YYMM` when a paper has no published venue recorded yet.

---

<!-- BEGIN:LIST -->
<!-- END:LIST -->

---

## System Comparison

What separates this list from a bibliography: for every system read in depth, the axes that decide whether you can actually act inside it. `Action` is a normalized summary of the paper's own action space; `Memory` is the mechanism that carries state across steps, not a quality judgement. `—` means the paper does not report the value.

These are notes taken while reading, not measurements. Frame rates are the numbers the authors claim on the hardware they claim them on, and are not comparable across rows without reading the setups. Check anything you intend to rely on against the paper.

<!-- BEGIN:TABLE -->
<!-- END:TABLE -->

## Contributing

Pull requests are welcome, including for entries already here — a wrong frame rate is worth a PR.

`README.md` is **generated**. Edit [`data/papers.jsonl`](data/papers.jsonl) instead and run `python3 scripts/build_readme.py`. See [how-to-contribute.md](how-to-contribute.md) for the record format and the review criteria.

Maintainers: the [arXiv candidate pipeline](docs/arxiv-pipeline.md) proposes recent papers in a review inbox every day, and a local [review agent](docs/agent-review.md) turns that inbox into a pull request for a human to merge.

## Related lists

This list is deliberately narrow. For the wider field:

- [Awesome-World-Models](https://github.com/leofan90/Awesome-World-Models) — world models for robotics, embodied AI, and autonomous driving. The daily-candidate pipeline here is adapted from theirs.
- [Awesome-World-Model](https://github.com/LMD0311/Awesome-World-Model) — world models with a strong autonomous-driving section.
- [Awesome-LLM-Robotics](https://github.com/GT-RIPL/Awesome-LLM-Robotics) — the template both lists descend from.
- [Awesome-Video-Diffusion](https://github.com/showlab/Awesome-Video-Diffusion) — video diffusion broadly, interactive or not.

## Citation

If this list helps your work, a star is plenty. If you want to cite it:

```bibtex
@misc{awesome_interactive_video_world_models,
  title        = {Awesome Interactive Video World Models},
  howpublished = {\url{https://github.com/ZhangShuui/Awesome-Interactive-Video-World-Models}},
  year         = {2026}
}
```

<!-- On survey release: add the survey bibtex here and point the opening
     paragraph at it. Keep the repo entry so the list stays citable on its own. -->

## License

[MIT](LICENSE) for the scripts and the collected metadata. Every linked paper belongs to its authors.

## Acknowledgements

This list would not exist without [Awesome-World-Models](https://github.com/leofan90/Awesome-World-Models) (BSD-3-Clause), which seeded it, and which in turn follows [Awesome-LLM-Robotics](https://github.com/GT-RIPL/Awesome-LLM-Robotics) — see [the notice above](#please-read-this-first) for what was taken from it. Paper metadata comes from the [arXiv API](https://info.arxiv.org/help/api/index.html); thank you to arXiv for its open access interoperability.

Above all, thanks to the authors of every paper listed here.
