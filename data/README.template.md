# Awesome Interactive Video World Models [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)

A curated list of **interactive video world models** — generative models you can act inside, one step at a time.

Video generation stopped being a movie and became a place. This list tracks that shift and only that shift: systems where a user or a policy issues an action, the model produces the next frames causally, and the world is still there when you look back. General world-model lists cover robotics, driving, and 3D generation alongside this; here the narrow scope is the point.

<!-- BEGIN:STATS -->
<!-- END:STATS -->

Every entry is screened against three criteria and, where the paper has been read in depth, profiled on backbone, action space, frame rate, and memory mechanism — see [System Comparison](#system-comparison).

> ### Please read this first
>
> **This is a personal reading record, not an authoritative or community-curated list.** It is
> maintained by one person as working notes for a survey in progress. Inclusion, exclusion,
> section placement, and every value in the comparison table are one reader's judgement, made
> from the papers themselves and revised as that reading continues. Treat it as a starting point
> for your own reading, not as a citation-grade source.
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

A paper belongs in **[Interactive Video World Models](#interactive-video-world-models)** when it satisfies all three:

1. **Per-step action conditioning.** The model consumes an action at each step and the next observation depends on it. A single prompt or a fixed trajectory supplied up front does not count; the loop has to be closeable.
2. **Causal or streaming generation.** Frames are produced in causal order, so the user can react to what they just saw. Bidirectional denoising over a whole clip is out, however good the clip is.
3. **Persistent world state.** Something survives across steps — context, an explicit spatial store, a retrievable memory — so revisiting a place does not resample it from scratch.

Camera and navigation control counts as an action space: it closes the same loop with a restricted set of actions.

The supporting sections are scoped more loosely on purpose. **Action Control**, **Real-Time & Streaming Generation**, **Long-Horizon Memory** and **Datasets** collect work that a system in the main list depends on, even when that work is a component or an analysis rather than a full interactive system. **Benchmarks** covers evaluation aimed at these systems.

Out of scope: text-to-video without a closed loop, robotics and driving world models that predict latents but never render an interactive stream, static 3D scene generation, and reinforcement-learning world models with no video decoder. Several excellent lists already cover those — see [Related lists](#related-lists).

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

Maintainers: the [arXiv candidate pipeline](docs/arxiv-pipeline.md) proposes recent papers in a review inbox every day.

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
