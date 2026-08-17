# Awesome Interactive Video World Models [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)

A curated list of **interactive video world models** — generative models you can act inside, one step at a time.

Video generation stopped being a movie and became a place. This list tracks that shift: systems where a user or a policy issues an action, the model produces the next frames causally, and the world is still there when you look back — together with the work those systems are built out of, on action control, real-time generation, and long-horizon memory. General world-model lists cover robotics, driving, and 3D generation alongside this; here the narrow focus is the point.

> A personal reading record, not an authoritative or community-curated list: every inclusion,
> tagging, and comparison-table value is one reader's judgement, revised as that reading
> continues. New entries are screened by an [automated agent](docs/agent-review.md) and carry
> `"tags_source": {"...": "agent"}` until a person confirms them; what it turned down is kept, with
> reasons, in [`data/agent-rejected.jsonl`](data/agent-rejected.jsonl).

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

## Tags

There are no sections. Every paper sits in one list, newest first, carrying one to three tags that say what it is about — a system whose contribution is its action interface is `systems` `control`, and it is one entry, not two. To read everything on a topic, search the page for its tag.

<!-- BEGIN:TAGKEY -->
<!-- END:TAGKEY -->

Venue labels show `arXiv YYMM` when a paper has no published venue recorded yet.

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

Maintainers: the [candidate pipeline](docs/candidate-pipeline.md) proposes papers in a review inbox every day — from arXiv and a watchlist of lab blogs, with OpenReview and conference proceedings swept on demand — and a local [review agent](docs/agent-review.md) turns that inbox into a pull request for a human to merge.

## Related lists

This list is deliberately narrow. For the wider field:

- [Awesome-World-Models](https://github.com/leofan90/Awesome-World-Models) — world models for robotics, embodied AI, and autonomous driving.
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

Initialized from [Awesome-World-Models](https://github.com/leofan90/Awesome-World-Models) (BSD-3-Clause) by Leo Fan and contributors. That list seeded the initial paper pool — one of the collection channels parsed its README — and supplied the website and code links for entries that appear in both; the repository layout and the review-inbox workflow are adapted from it as well. It in turn follows [Awesome-LLM-Robotics](https://github.com/GT-RIPL/Awesome-LLM-Robotics). If you want broad, actively maintained coverage of world models, go there — this list only narrows the same field to one slice of it.

Paper metadata comes from the [arXiv API](https://info.arxiv.org/help/api/index.html); thank you to arXiv for its open access interoperability.

No affiliation with, or endorsement by, the authors of any listed paper or of the upstream lists is claimed. Mistakes here are the maintainer's, not the papers' authors'. Corrections are welcome — please [open an issue or a PR](how-to-contribute.md).

Above all, thanks to the authors of every paper listed here.
