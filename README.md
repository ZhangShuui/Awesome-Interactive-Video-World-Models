# Awesome Interactive Video World Models [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)

A curated list of **interactive video world models** — generative models you can act inside, one step at a time.

Video generation stopped being a movie and became a place. This list tracks that shift and only that shift: systems where a user or a policy issues an action, the model produces the next frames causally, and the world is still there when you look back. General world-model lists cover robotics, driving, and 3D generation alongside this; here the narrow scope is the point.

<!-- BEGIN:STATS -->
**387 papers** across 9 sections &nbsp;·&nbsp; **130** read in depth and profiled in the comparison table &nbsp;·&nbsp; **34** with released weights or code &nbsp;·&nbsp; **50** reporting ≥10 FPS &nbsp;·&nbsp; newest entry 2026-08-06
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

A paper belongs in **[Interactive Video World Models](#interactive-video-world-models)** when it satisfies all three:

1. **Per-step action conditioning.** The model consumes an action at each step and the next observation depends on it. A single prompt or a fixed trajectory supplied up front does not count; the loop has to be closeable.
2. **Causal or streaming generation.** Frames are produced in causal order, so the user can react to what they just saw. Bidirectional denoising over a whole clip is out, however good the clip is.
3. **Persistent world state.** Something survives across steps — context, an explicit spatial store, a retrievable memory — so revisiting a place does not resample it from scratch.

Camera and navigation control counts as an action space: it closes the same loop with a restricted set of actions.

The supporting sections are scoped more loosely on purpose. **Action Control**, **Real-Time & Streaming Generation**, **Long-Horizon Memory** and **Datasets** collect work that a system in the main list depends on, even when that work is a component or an analysis rather than a full interactive system. **Benchmarks** covers evaluation aimed at these systems.

Out of scope: text-to-video without a closed loop, robotics and driving world models that predict latents but never render an interactive stream, static 3D scene generation, and reinforcement-learning world models with no video decoder. Several excellent lists already cover those — see [Related lists](#related-lists).

## Contents

<!-- BEGIN:CONTENTS -->
- [Surveys & Related Lists](#surveys--related-lists) (24)
- [Foundations & Prehistory](#foundations--prehistory) (5)
- [Blogs & Technical Reports](#blogs--technical-reports) (6)
- [Interactive Video World Models](#interactive-video-world-models) (105)
- [Action Control & Interfaces](#action-control--interfaces) (27)
- [Real-Time & Streaming Generation](#real-time--streaming-generation) (104)
- [Long-Horizon Memory & Consistency](#long-horizon-memory--consistency) (91)
- [Benchmarks & Evaluation](#benchmarks--evaluation) (21)
- [Datasets & Environments](#datasets--environments) (4)
- [System Comparison](#system-comparison)
- [Contributing](#contributing)
- [Citation](#citation)
<!-- END:CONTENTS -->

Entries are newest first within each section. Venue tags show `arXiv YYMM` when a paper has no published venue recorded yet.

---

<!-- BEGIN:LIST -->
## Surveys & Related Lists

_Surveys that cover world models, video generation, or interactive generation. Read these first to place a paper in context._ &nbsp;·&nbsp; **24 entries**

* World Action Models: A Survey. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.20781)]
* World Models for Robotic Manipulation: A Survey. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2606.00113)]
* World Model for Robot Learning: A Comprehensive Survey. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2605.00080)] [[Website](https://ntumars.github.io/wm-robot-survey/)] [[Code](https://github.com/NTUMARS/Awesome-World-Model-for-Robotics-Policy)]
* Simulating the Visual World with Artificial Intelligence: A Roadmap. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.08585)] [[Website](https://world-model-roadmap.github.io/)] [[Code](https://github.com/ziqihuangg/Awesome-From-Video-Generation-to-World-Model)]
* A Step Toward World Models: A Survey on Robotic Manipulation. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2511.02097)]
* A Survey on Cache Methods in Diffusion Models: Toward Efficient Multi-Modal Generation. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.19755)]
* A Comprehensive Survey on World Models for Embodied AI. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.16732)] [[Website](https://github.com/Li-Zn-H/AwesomeWorldModels)]
* 3D and 4D World Modeling: A Survey. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.07996)]
* A Survey on Long-Video Storytelling Generation: Architectures, Consistency, and Cinematic Quality. **`arXiv 2025.07`** [[Paper](https://arxiv.org/abs/2507.07202)]
* A Survey: Learning Embodied Intelligence from Physical Simulators and World Models. **`arXiv 2025.07`** [[Paper](https://arxiv.org/abs/2507.00917)] [[Code](https://github.com/NJU3DV-LoongGroup/Embodied-World-Models-Survey)]
* From 2D to 3D Cognition: A Brief Survey of General World Models. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.20134)]
* A Survey of Interactive Generative Video. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.21853)]
* Exploring the Evolution of Physics Cognition in Video Generation: A Survey. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.21765)] [[Code](https://github.com/minnie-lin/Awesome-Physics-Cognition-based-Video-Generation)]
* Simulating the Real World: A Unified Survey of Multimodal Generative Models. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.04641)] [[Code](https://github.com/ALEEEHU/World-Simulator)]
* Generative Physical AI in Vision: A Survey. **`arXiv 2025.01`** [[Paper](https://arxiv.org/abs/2501.10928)]
* Understanding World or Predicting Future? A Comprehensive Survey of World Models. **`arXiv 2024.11`** [[Paper](https://arxiv.org/abs/2411.14499)]
* From Efficient Multimodal Models to World Models: A Survey. **`arXiv 2024.06`** [[Paper](https://arxiv.org/abs/2407.00118)]
* From Sora What We Can See: A Survey of Text-to-Video Generation. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.10674)]
* Is Sora a World Simulator? A Comprehensive Survey on General World Models and Beyond. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.03520)] [[Code](https://github.com/GigaAI-research/General-World-Models-Survey)]
* Video Diffusion Models: A Survey. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.03150)]
* A Survey on Long Video Generation: Challenges, Methods, and Prospects. **`arXiv 2024.03`** [[Paper](https://arxiv.org/abs/2403.16407)]
* Sora as a World Model? A Complete Survey on Text-to-Video Generation. **`arXiv 2024.03`** [[Paper](https://arxiv.org/abs/2403.05131)]
* **`Sora`**, A Review on Background, Technology, Limitations, and Opportunities of Large Vision Models. **`arXiv 2024.02`** [[Paper](https://arxiv.org/abs/2402.17177)]
* A Survey on Future Frame Synthesis: Bridging Deterministic and Generative Approaches. **`arXiv 2024.01`** [[Paper](https://arxiv.org/abs/2401.14718)]

## Foundations & Prehistory

_Work that defined the problem before interactive video world models became a category of their own: latent world models, neural game engines, and playable video generation._ &nbsp;·&nbsp; **5 entries**

* **`Genie`**, Generative Interactive Environments. **`DeepMind`** [[Paper](https://arxiv.org/abs/2402.15391)] [[Blog](https://sites.google.com/view/genie-2024/home)]
* Playable Environments: Video Manipulation in Space and Time. **`arXiv 2022.03`** [[Paper](https://arxiv.org/abs/2203.01914)]
* Playable Video Generation. **`arXiv 2021.01`** [[Paper](https://arxiv.org/abs/2101.12195)]
* Learning to Simulate Dynamic Environments With GameGAN. **`arXiv 2020.05`** [[Paper](https://arxiv.org/abs/2005.12126)]
* World Models. **`NIPS 2018 Oral`** [[Paper](https://arxiv.org/abs/1803.10122)] [[Website](https://worldmodels.github.io/)]

## Blogs & Technical Reports

_Systems that would sit in the main list if they had a paper. Announced through a blog post or technical report, documented well enough to place, and too important to leave out — every URL here has been checked by hand._ &nbsp;·&nbsp; **6 entries**

* **`PixVerse R1`**, A Real-Time World Model That Redefines AI Video Generation. **`PixVerse 2026`** [[Blog](https://pixverse.ai/en/blog/pixverse-launches-r1-real-time-world-model)]
* **`Happy Oyster`**, Happy Oyster (Kuaile Shenghao): Real-Time Interactive Open-World Model. **`Alibaba 2026`** [[Blog](https://happyoyster.cn/)]
* **`Genie 3`**, A new frontier for world models. **`DeepMind 2025`** [[Blog](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/)]
* **`Genie 2`**, A large-scale foundation world model. **`DeepMind 2024`** [[Blog](https://deepmind.google/discover/blog/genie-2-a-large-scale-foundation-world-model/)]
* **`Oasis`**, A Universe in a Transformer. **`Decart & Etched 2024`** [[Blog](https://oasis-model.github.io/)]
* **`Sora`**, Video generation models as world simulators. **`OpenAI 2024`** [[Blog](https://openai.com/index/video-generation-models-as-world-simulators/)]

## Interactive Video World Models

_The main list: systems that meet all three criteria. Newest first._ &nbsp;·&nbsp; **105 entries**

* **`Wonder`**, Video World Model Done Better. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.26037)]
* **`ABot-World-0`**, Infinite Interactive World Rollout on a Single Desktop GPU. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.19191)]
* **`WanToFight`**, Real-Time Generative Game Engine for Multi-Player Combat Interaction. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.12592)]
* Infinite Worlds with Versatile Interactions. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.07534)]
* **`AlayaWorld`**, Long-Horizon and Playable Video World Generation. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.06291)]
* **`MoWorld`**, A Flash World Model. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.06216)]
* Multiplayer Interactive World Models with Representation Autoencoders. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.05352)]
* **`Worldscape-MoE`**, A Unified Mixture-of-Experts World Model for Scalable Heterogeneous Action Control. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.03964)]
* **`WorldDirector`**, Building Controllable World Simulators with Persistent Dynamic Memory. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.02517)]
* **`DreamForge-World 0.1`**, DreamForge-World 0.1 Preview: A Low-Compute Real-Time Controllable World Model. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.30292)]
* Walking in the Implicit: Interactive World Exploration via Neural Scene Representation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.30045)]
* Directing the World: Fast Autoregressive Video Generation with Compositional Human-Camera Control. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.27964)]
* **`MaineCoon`**, Pursuing A Real-Time Audio-Visual Social World Model. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.17800)]
* **`ActWorld`**, From Explorable to Interactive World Model via Action-Aware Memory. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.17730)]
* **`DreamX-World 1.0`**, A General-Purpose Interactive World Model. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.16993)]
* **`GeoStream`**, Toward Precise Camera Controlled Streaming Video Generation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.15162)]
* **`MoVerse`**, Real-Time Video World Modeling with Panoramic Gaussian Scaffold. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.13376)]
* **`BiWM`**, Advancing Open-Source Interactive Video World Models with Bidirectional Autoregression. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.10135)]
* **`Prisma-World`**, Camera-Controllable Multi-Agent Video World Model. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.09507)]
* **`DisCo`**, World Models with Discrete Camera Motion Control. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.07967)]
* Streaming Video Generation with Streaming Force Control. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.07508)]
* **`AnchorWorld`**, Embodied Egocentric World Simulation with View-based Evolution Customization. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.07326)]
* **`MetaWorld`**, Scaling Multi-Agent Video World Model from Single-view Video Data. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.02753)]
* From Zero to Hero: Training-Free Custom Concept Spawning in World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.02575)]
* **`Gamma-World`**, Generative Multi-Agent World Modeling Beyond Two Players. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.28816)] [[Website](https://research.nvidia.com/labs/sil/projects/gamma-world)]
* **`WorldCraft`**, From Camera Navigation to Object Manipulation in Interactive Video World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.25077)] [[Website](https://nevsdev.github.io/WorldCraft/)]
* **`SCOPE`**, Simulating Cross-game Operations in Playable Environments for FPS World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.23345)] [[Website](https://z2tong.github.io/SCOPE/)] [[Code](https://github.com/z2tong/SCOPE)]
* **`Incantation`**, Natural Language as the Action Interface for Multi-Entity Video World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.18601)]
* **`ReactiveGWM`**, Steering NPC in Reactive Game World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.15256)] [[Website](https://inv-wzq.github.io/ReactiveGWM/)]
* **`SANA-WM`**, Efficient Minute-Scale World Modeling with Hybrid Linear Diffusion Transformer. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.15178)] [[Website](https://nvlabs.github.io/Sana/WM/)]
* **`CausalCine`**, Real-Time Autoregressive Generation for Multi-Shot Video Narratives. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.12496)]
* **`PROWL`**, Prioritized Regret-Driven Optimization for World Model Learning. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.18803)]
* **`MultiWorld`**, Scalable Multi-Agent Multi-View Video World Models. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.18564)] [[Website](https://multi-world.github.io/)]
* **`Matrix-Game 3.0`**, Real-Time and Streaming Interactive World Model with Long-Horizon Memory. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.08995)] [[Website](https://matrix-game-v3.github.io/)]
* **`INSPATIO-WORLD`**, A Real-Time 4D World Simulator via Spatiotemporal Autoregressive Modeling. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.07209)]
* **`ActionParty`**, Multi-Subject Action Binding in Generative Video Games. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.02330)]
* **`EgoSim`**, Egocentric World Simulator for Embodied Interaction Generation. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.01001)] [[Website](http://egosimulator.github.io/)]
* **`MemCam`**, Memory-Augmented Camera Control for Consistent Video Generation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.26193)]
* **`ShotStream`**, Streaming Multi-Shot Video Generation for Interactive Storytelling. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.25746)]
* **`WorldCam`**, Interactive Autoregressive 3D Gaming Worlds with Camera Pose as a Unifying Geometric Representation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.16871)] [[Website](https://cvlab-kaist.github.io/WorldCam/)]
* **`InSpatio-WorldFM`**, An Open-Source Real-Time Generative Frame Model. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.11911)]
* **`RealWonder`**, Real-Time Physical Action-Conditioned Video Generation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.05449)]
* **`MultiGen`**, Level-Design for Editable Multiplayer Worlds in Diffusion Game Engines. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.06679)]
* Beyond Pixel Histories: World Models with Persistent 3D State. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.03482)] [[Website](https://francelico.github.io/persist.github.io)]
* **`COMBAT`**, Conditional World Models for Behavioral Agent Training. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2603.00825)]
* **`UCM`**, Unifying Camera Control and Memory with Time-aware Positional Encoding Warping for World Models. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.22960)] [[Website](https://humanaigc.github.io/ucm-webpage/)]
* **`Solaris`**, Building a Multiplayer Video World Model in Minecraft. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.22208)] [[Website](https://solaris-wm.github.io/)]
* **`Generated Reality`**, Human-centric World Simulation using Interactive Video Generation with Hand and Camera Control. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.18422)]
* **`Hand2World`**, Autoregressive Egocentric Interaction Generation via Free-Space Hand Gestures. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.09600)] [[Website](https://hand2world.github.io/)]
* **`LIVE`**, Long-horizon Interactive Video World Modeling. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.03747)] [[Website](https://junchao-cs.github.io/LIVE-demo/)]
* **`Infinite-World`**, Scaling Interactive World Models to 1000-Frame Horizons via Pose-Free Hierarchical Memory. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.02393)]
* Scalable Generative Game Engine: Breaking the Resolution Wall via Hardware-Algorithm Co-Design. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2602.00608)]
* **`lingbot-world`**, Advancing Open-source World Models. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.20540)] [[Website](https://technology.robbyant.com/lingbot-world)] [[Code](https://github.com/robbyant/lingbot-world)]
* **`TeleWorld`**, Towards Dynamic Multimodal Synthesis with a 4D World Model. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2601.00051)]
* **`Yume-1.5`**, A Text-Controlled Interactive World Generation Model. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.22096)] [[Website](https://stdstu12.github.io/YUME-Project)] [[Code](https://github.com/stdstu12/YUME)]
* **`CustomX`**, Unified Character, Action, and Scene Customization in Video World Models. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.17796)]
* **`Spatia`**, Video Generation with Updatable Spatial Memory. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.15716)]
* **`WorldPlay`**, Towards Long-Term Geometric Consistency for Real-Time Interactive World Modeling. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.14614)] [[Website](https://3d-models.hunyuan.tencent.com/world/)]
* **`Astra`**, General Interactive World Model with Autoregressive Denoising. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.08931)] [[Website](https://eternalevan.github.io/Astra-project/)] [[Code](https://github.com/EternalEvan/Astra)]
* **`RELIC`**, Interactive Video World Model with Long-Horizon Memory. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.04040)] [[Website](https://relic-worldmodel.github.io/)]
* **`WorldPack`**, Compressed Memory Improves Spatial Consistency in Video World Modeling. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.02473)]
* **`SpriteHand`**, Real-Time Versatile Hand-Object Interaction with Autoregressive Video Generation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.01960)]
* **`AVWM`**, Audio-Visual World Models: Towards Multisensory Imagination in Sight and Sound. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2512.00883)]
* **`Hunyuan-GameCraft-2`**, Instruction-following Interactive Game World Model. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.23429)] [[Website](https://hunyuan-gamecraft-2.github.io/)]
* **`Captain Safari`**, A World Engine. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.22815)] [[Website](https://johnson111788.github.io/open-safari/)]
* **`MagicWorld`**, Towards Long-Horizon Stability for Interactive Video World Exploration. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.18886)] [[Website](https://vivocameraresearch.github.io/magicworld/)] [[Code](https://github.com/vivoCameraResearch/Magic-World)]
* **`PAN`**, A World Model for General, Interactable, and Long-Horizon World Simulation. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.09057)]
* Co-Evolving Latent Action World Models. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.26433)]
* Memory Forcing: Spatio-Temporal Memory for Consistent Scene Generation on Minecraft. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.03198)]
* **`EvoWorld`**, Evolving Panoramic World Generation with Explicit 3D Memory. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.01183)] [[Code](https://github.com/JiahaoPlus/EvoWorld)]
* **`Dreamer4`**, Training Agents Inside of Scalable World Models. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.24527)] [[Website](https://danijar.com/dreamer4/)]
* **`LongLive`**, Real-time Interactive Long Video Generation. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.22622)]
* **`Matrix-Game 2.0`**, An open-source real-time and streaming interactive world model. **`arXiv 2025.08`** [[Paper](https://arxiv.org/abs/2508.13009)] [[Website](https://matrix-game-v2.github.io/)]
* **`Yan`**, Foundational Interactive Video Generation. **`arXiv 2025.08`** [[Paper](https://arxiv.org/abs/2508.08601)]
* **`Yume`**, An Interactive World Generation Model. **`arXiv 2025.07`** [[Paper](https://arxiv.org/abs/2507.17744)] [[Website](https://stdstu12.github.io/YUME-Project/)] [[Code](https://github.com/stdstu12/YUME)]
* From Virtual Games to Real-World Play. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.18901)]
* **`Matrix-Game`**, Interactive World Foundation Model. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.18701)] [[Code](https://github.com/SkyworkAI/Matrix-Game)]
* **`Hunyuan-GameCraft`**, High-dynamic Interactive Game Video Generation with Hybrid History Condition. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.17201)]
* **`PlayerOne`**, Egocentric World Simulator. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.09995)]
* Autoregressive Adversarial Post-Training for Real-Time Interactive Video Generation. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.09350)]
* Video World Models with Long-term Spatial Memory. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.05284)] [[Website](https://spmem.github.io/)]
* Context as Memory: Scene-Consistent Interactive Long Video Generation with Memory Retrieval. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.03141)]
* **`DeepVerse`**, 4D Autoregressive Video Generation as a World Model. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.01103)]
* **`VRAG`**, Learning World Models for Interactive Video Generation. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.21996)]
* Long-Context State-Space Video World Models. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.20171)] [[Website](https://ryanpo.com/ssm_wm)]
* **`Vid2World`**, Crafting Video Diffusion Models to Interactive World Models. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.14357)] [[Website](http://knightnemo.github.io/vid2world/)]
* Learning 3D Persistent Embodied World Models. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.05495)]
* **`WorldMem`**, Long-term Consistent World Simulation with Memory. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.12369)]
* **`MineWorld`**, a Real-Time and Open-Source Interactive World Model on Minecraft. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.08388)]
* Exploration-Driven Generative Interactive Environments. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.02515)]
* **`AnimeGamer`**, Infinite Anime Life Simulation with Next Game State Prediction. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.01014)]
* Model as a Game: On Numerical and Spatial Consistency for Generative Games. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.21172)]
* **`AdaWorld`**, Learning Adaptable World Models with Latent Actions. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.18938)] [[Website](https://adaptable-world-model.github.io/)]
* Pre-Trained Video Generative Models as World Simulators. **`arXiv 2025.02`** [[Paper](https://arxiv.org/abs/2502.07825)]
* **`GameFactorly`**, Creating New Games with Generative Interactive Videos. **`arXiv 2025.01`** [[Paper](https://arxiv.org/abs/2501.08325)]
* **`GenEx`**, Generating an Explorable World. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.09624)]
* The Matrix: Infinite-Horizon World Generation with Real-Time Moving Control. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.03568)]
* Playable Game Generation. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.00887)]
* **`GameGen-X`**, Interactive Open-world Game Video Generation. **`arXiv 2024.11`** [[Paper](https://arxiv.org/abs/2411.00769)]
* **`SlowFast-VGen`**, Slow-Fast Learning for Action-Driven Long Video Generation. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2410.23277)]
* Learning Generative Interactive Environments By Trained Agent Exploration. **`arXiv 2024.09`** [[Paper](https://arxiv.org/abs/2409.06445)]
* Diffusion Models Are Real-Time Game Engines. **`arXiv 2024.08`** [[Paper](https://arxiv.org/abs/2408.14837)]
* **`Pandora`**, Towards General World Model with Natural Language Actions and Video States. **`arXiv 2024.06`** [[Paper](https://arxiv.org/abs/2406.09455)] [[Code](https://github.com/maitrix-org/Pandora)]
* iVideoGPT: Interactive VideoGPTs are Scalable World Models. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.15223)]
* Learning Interactive Real-World Simulators. **`arXiv 2023.10`** [[Paper](https://arxiv.org/abs/2310.06114)]

## Action Control & Interfaces

_How an action reaches the generator: action spaces, injection mechanisms, latent actions learned without labels, and control-fidelity analysis._ &nbsp;·&nbsp; **27 entries**

* **`GeniWorld`**, A Generalizable Interactive World Model for Robotic Manipulation via Visual Actions. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.06332)]
* **`LAWM-3D`**, Learning 3D-Aware Latent Actions from Human Videos for Generalizable Robot World Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.05706)]
* **`UniWorld-View`**, Large-Baseline View Synthesis via Video Diffusion Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.04701)]
* Overcoming Statistical Bias in Action-Controllable World Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.04653)]
* Causally Debiased Latent Action Model for Embodied Action Conditioned World Models. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.09185)]
* **`CLAW`**, Learning Continuous Latent Action World Models via Adversarial Latent Regularization. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.04130)]
* World Models as Group Actions. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.24578)]
* **`Nano World Models`**, A Minimalist Implementation of Future Video Prediction. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.23993)] [[Website](https://simchowitzlabpublic.github.io/nano-world-model/)]
* **`DiLA`**, Disentangled Latent Action World Models. **`ICML 2026`** [[Paper](https://arxiv.org/abs/2605.15725)] [[Website](http://disentangled-latent-action-world-models.github.io)]
* Render, Don't Decode: Weight-Space World Models with Latent Structural Disentanglement. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.06298)]
* **`DCARL`**, A Divide-and-Conquer Framework for Autoregressive Long-Trajectory Video Generation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.24835)]
* **`MosaicMem`**, Hybrid Spatial Memory for Controllable Video World Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.17117)] [[Website](https://mosaicmem.github.io/mosaicmem/)]
* Hierarchical Latent Action Model. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.05815)]
* Factored Latent Action World Models. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.16229)]
* **`Olaf-World`**, Orienting Latent Actions for Video World Modeling. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.10104)] [[Website](https://showlab.github.io/Olaf-World/)] [[Code](https://github.com/showlab/Olaf-World)]
* Learning Latent Action World Models In The Wild. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.05230)]
* **`LongVie 2`**, Multimodal Controllable Ultra-Long Video World Model. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.13604)] [[Website](https://vchitect.github.io/LongVie2-project/)]
* **`Infinity-RoPE`**, Action-Controllable Infinite Video Generation Emerges From Autoregressive Self-Rollout. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.20649)]
* Real-Time Motion-Controllable Autoregressive Video Diffusion. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.08131)]
* Reinforcement Learning with Inverse Rewards for World Model Post-training. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.23958)]
* **`CausNVS`**, Autoregressive Multi-view Diffusion for Flexible 3D Novel View Synthesis. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.06579)]
* Inter-environmental world modeling for continuous and compositional dynamics. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.09911)]
* **`Gen3C`**, 3D-Informed World-Consistent Video Generation with Precise Camera Control. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.03751)]
* **`PlaySlot`**, Learning Inverse Latent Dynamics for Controllable Object-Centric Video Prediction and Planning. **`arXiv 2025.02`** [[Paper](https://arxiv.org/abs/2502.07600)]
* **`IGOR`**, Image-GOal Representations are the Atomic Control Units for Foundation Models in Embodied AI. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2411.00785)]
* Learning to Act without Actions. **`arXiv 2023.12`** [[Paper](https://arxiv.org/abs/2312.10812)]
* Learning what you can do before doing anything. **`arXiv 2018.06`** [[Paper](https://arxiv.org/abs/1806.09655)]

## Real-Time & Streaming Generation

_Meeting the per-frame latency budget: causal and autoregressive backbones, few-step distillation, KV caching, and inference systems._ &nbsp;·&nbsp; **104 entries**

* **`In-Context Forcing`**, Uncovering Context Effects in Autoregressive Video Diffusion. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.05237)]
* **`MiniWorld`**, Democratizing the Training of Video World Models from Scratch. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.01127)]
* **`FlashDecoder`**, Real-Time Latent-to-Pixel Streaming Decoder with Transformers. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.14898)]
* Stateful Worlds, Stateless Elasticity: Exact-State Serving for Interactive World Models. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.10389)]
* **`OPSD-V`**, On-Policy Self-Distillation for Post-Training Few-Step Autoregressive Video Generators. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.08766)]
* **`SAGA`**, Stable Acceleration Guidance for Autoregressive Video Generation. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.08020)]
* **`Flex-Forcing`**, Towards a Unified Autoregressive and Bidirectional Video Diffusion Model. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.03509)]
* Towards Memory-Efficient Autoregressive Video Generation via Instance-Specific Parametric Absorption. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.00712)]
* **`TempAct`**, Advancing Temporal Plausibility in Autoregressive Video Generation via Planner-Executor RL. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.28016)]
* **`LiveEdit`**, Towards Real-Time Diffusion-Based Streaming Video Editing. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.26740)]
* **`Causal-rCM`**, A Unified Teacher-Forcing and Self-Forcing Open Recipe for Autoregressive Diffusion Distillation in Streaming Video Generation and Interactive World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.25473)]
* **`TurboServe`**, Serving Streaming Video Generation Efficiently and Economically. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.19271)]
* **`UniTemp`**, Unlocking Video Generation in Any Temporal Order via Bidirectional Distillation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.18702)]
* Adaptive Resource Management and Quality Control for Streaming Video Generation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.15319)]
* **`Next Forcing`**, Causal World Modeling with Multi-Chunk Prediction. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.11187)]
* **`SwiftVR`**, Real-Time One-Step Generative Video Restoration. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.09516)]
* Ultra Flash: Scaling Real-Time Streaming Video Generation to High Resolutions. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.09150)]
* **`DSA`**, Dynamic Step Allocation for Fast Autoregressive Video Generation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.04432)]
* **`AAD-1`**, Asymmetric Adversarial Distillation for One-Step Autoregressive Video Generation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.03972)]
* **`Video-Mirai`**, Autoregressive Video Diffusion Models Need Foresight. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.03971)]
* Light Interaction: Training-Free Inference Acceleration for Interactive Video World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.31158)]
* **`SANA-Streaming`**, Real-time Streaming Video Editing with Hybrid Diffusion Transformer. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30409)]
* **`VideoMLA`**, Low-Rank Latent KV Cache for Minute-Scale Autoregressive Video Diffusion. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30351)]
* **`AdaState`**, Self-Evolving Anchors for Streaming Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30349)]
* **`minWM`**, A Full-Stack Open-Source Framework for Real-Time Interactive Video World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30263)] [[Website](https://github.com/shengshu-ai/minWM)]
* **`SGMD`**, Score Gradient Matching Distillation for Few-Step Video Diffusion Distillation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30116)]
* Quantized Keys Steal Attention: Bias Correction for KV-Cache Compression in Video Diffusion. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.26266)]
* On-Policy Adversarial Flow Distillation for Autoregressive Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.26105)]
* **`One-Forcing`**, Towards Stable One-Step Autoregressive Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.23458)]
* **`Q-ARVD`**, Quantizing Autoregressive Video Diffusion Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.21072)]
* **`LongLive-2.0`**, An NVFP4 Parallel Infrastructure for Long Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.18739)]
* Focused Forcing: Content-Aware Per-Frame KV Selection for Efficient Autoregressive Video Diffusion. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.18346)]
* Causal Forcing++: Scalable Few-Step Autoregressive Diffusion Distillation for Real-Time Interactive Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.15141)]
* Delta Forcing: Trust Region Steering for Interactive Autoregressive Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.14382)]
* **`KVPO`**, ODE-Native GRPO for Autoregressive Video Alignment via KV Semantic Exploration. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.14278)]
* Pyramid Forcing: Head-Aware Pyramid KV Cache Policy for High-Quality Long Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.13111)]
* **`Forcing-KV`**, Hybrid KV Cache Compression for Efficient Autoregressive Video Diffusion Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.09681)]
* **`Stream-T1`**, Test-Time Scaling for Streaming Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.04461)]
* **`Stream-R1`**, Reliability-Perplexity Aware Reward Distillation for Streaming Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.03849)]
* Sparse Forcing: Native Trainable Sparse Attention for Real-time Autoregressive Diffusion Video Generation. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.21221)]
* **`X-Cache`**, Cross-Chunk Block Caching for Few-Step Autoregressive World Models Inference. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.20289)]
* Speculative Decoding for Autoregressive Video Generation. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.17397)]
* **`DiT as Real-Time Rerenderer`**, Streaming Video Stylization with Autoregressive Diffusion Transformer. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.13509)]
* Long-Horizon Streaming Video Generation via Hybrid Attention with Decoupled Distillation. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.10103)]
* **`WorldCache`**, Content-Aware Caching for Accelerated Video World Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.22286)] [[Website](https://umair1221.github.io/World-Cache/)]
* **`Astrolabe`**, Steering Forward-Process Reinforcement Learning for Distilled Autoregressive Video Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.17051)]
* **`OmniForcing`**, Unleashing Real-time Joint Audio-Visual Generation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.11647)]
* Streaming Autoregressive Video Generation via Diagonal Distillation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.09488)]
* **`WorldCache`**, Accelerating World Models for Free via Heterogeneous Token Caching. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.06331)] [[Website](https://github.com/FofGofx/WorldCache)]
* **`Helios`**, Real Real-Time Long Video Generation Model. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.04379)] [[Website](https://pku-yuangroup.github.io/Helios-Page/)] [[Code](https://github.com/PKU-YuanGroup/Helios)]
* Accelerating Video Generation Inference with Sequential-Parallel 3D Positional Encoding Using a Global Time Index. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.06664)]
* Adapting VACE for Real-Time Autoregressive Video Diffusion. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.14381)]
* A Causal Diffusion Model for Video Reconstruction from Ultra-Low-Bitrate Representations. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.13837)]
* **`MonarchRT`**, Efficient Attention for Real-Time Video Generation. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.12271)]
* Causality in Video Diffusers is Separable from Denoising. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.10095)]
* Light Forcing: Accelerating Autoregressive Video Diffusion via Sparse Attention. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.04789)]
* **`Quant VideoGen`**, Auto-Regressive Long Video Generation via 2-Bit KV-Cache Quantization. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.02958)]
* Causal Forcing: Autoregressive Diffusion Distillation Done Right for High-Quality Real-Time Interactive Video Generation. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.02214)]
* Fast Autoregressive Video Diffusion and World Models with Temporal Cache Compression and Sparse Attention. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.01801)]
* Past- and Future-Informed KV Cache Policy with Salience Estimation in Autoregressive Video Diffusion. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.21896)]
* **`Reward-Forcing`**, Autoregressive Video Generation with Reward Feedback. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.16933)]
* **`LoL`**, Longer than Longer, Scaling Video Generation to Hour. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.16914)]
* **`S2DiT`**, Sandwich Diffusion Transformer for Mobile Streaming Video Generation. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.12719)]
* Transition Matching Distillation for Fast Video Generation. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.09881)]
* **`LiveTalk`**, Real-Time Multimodal Interactive Video Diffusion via Improved On-Policy Distillation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.23576)]
* **`SneakPeek`**, Future-Guided Instructional Streaming Video Generation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.13019)]
* Endless World: Real-Time 3D-Aware Long Video Generation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.12430)]
* **`AutoRefiner`**, Improving Autoregressive Video Diffusion Models via Reflective Refinement Over the Stochastic Sampling Path. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.11203)]
* Deep Forcing: Training-Free Long Video Generation with Deep Sink and Participative Compression. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.05081)]
* Reward Forcing: Efficient Streaming Video Generation with Rewarded Distribution Matching Distillation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.04678)]
* **`Inferix`**, A Block-Diffusion based Next-Generation Inference Engine for World Simulation. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.20714)] [[Code](https://github.com/alibaba-damo-academy/Inferix)]
* Block Cascading: Training Free Acceleration of Block-Causal Video Models. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.20426)]
* **`StreamDiffusionV2`**, A Streaming System for Dynamic and Interactive Video Generation. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.07399)]
* Towards One-step Causal Video Generation via Adversarial Self-Distillation. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.01419)]
* **`MotionStream`**, Real-Time Video Generation with Interactive Motion Controls. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.01266)]
* **`CanvasMAR`**, Improving Masked Autoregressive Video Prediction With Canvas. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.13669)]
* Streaming Drag-Oriented Interactive Video Manipulation: Drag Anything, Anytime!. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.03550)]
* Rolling Forcing: Autoregressive Long Video Diffusion in Real Time. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.25161)]
* **`SANA-Video`**, Efficient Video Generation with Block Linear Diffusion Transformer. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.24695)]
* **`StreamDiT`**, Real-Time Streaming Text-to-Video Generation. **`arXiv 2025.07`** [[Paper](https://arxiv.org/abs/2507.03745)]
* Self Forcing: Bridging the Train-Test Gap in Autoregressive Video Diffusion. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.08009)]
* Playing with Transformer at 30+ FPS via Next-Frame Diffusion. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.01380)]
* **`MAGI-1`**, Autoregressive Video Generation at Scale. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.13211)]
* **`SkyReels-V2`**, Infinite-length Film Generative Model. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.13074)]
* One-Minute Video Generation with Test-Time Training. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.05298)]
* **`AR-Diffusion`**, Asynchronous Video Generation with Auto-Regressive Diffusion. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.07418)]
* Next Block Prediction: Video Generation via Semi-Autoregressive Modeling. **`arXiv 2025.02`** [[Paper](https://arxiv.org/abs/2502.07737)]
* Taming Teacher Forcing for Masked Autoregressive Video Generation. **`arXiv 2025.01`** [[Paper](https://arxiv.org/abs/2501.12389)]
* Diffusion Adversarial Post-Training for One-Step Video Generation. **`arXiv 2025.01`** [[Paper](https://arxiv.org/abs/2501.08316)]
* **`MSC`**, Multi-Scale Spatio-Temporal Causal Attention for Autoregressive Video Diffusion. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.09828)]
* Video Creation by Demonstration. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.09551)]
* From Slow Bidirectional to Fast Autoregressive Video Diffusion Models. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.07772)]
* **`Ca2-VDM`**, Efficient Autoregressive Video Diffusion Model with Causal Generation and Cache Sharing. **`arXiv 2024.11`** [[Paper](https://arxiv.org/abs/2411.16375)]
* Pyramidal Flow Matching for Efficient Video Generative Modeling. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2410.05954)]
* **`Loong`**, Generating Minute-level Long Videos with Autoregressive Language Models. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2410.02757)]
* Real-Time Video Generation with Pyramid Attention Broadcast. **`arXiv 2024.08`** [[Paper](https://arxiv.org/abs/2408.12588)]
* Diffusion Forcing: Next-token Prediction Meets Full-Sequence Diffusion. **`arXiv 2024.07`** [[Paper](https://arxiv.org/abs/2407.01392)]
* Motion Consistency Model: Accelerating Video Diffusion with Disentangled Motion-Appearance Distillation. **`arXiv 2024.06`** [[Paper](https://arxiv.org/abs/2406.06890)]
* Lifelong Learning of Video Diffusion Models From a Single Video Stream. **`arXiv 2024.06`** [[Paper](https://arxiv.org/abs/2406.04814)]
* **`SF-V`**, Single Forward Video Generation Model. **`arXiv 2024.06`** [[Paper](https://arxiv.org/abs/2406.04324)]
* Streaming Video Diffusion: Online Video Editing with Diffusion Models. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.19726)]
* Looking Backward: Streaming Video-to-Video Translation with Feature Banks. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.15757)]
* Rolling Diffusion Models. **`arXiv 2024.02`** [[Paper](https://arxiv.org/abs/2402.09470)]
* Language Model Beats Diffusion -- Tokenizer is Key to Visual Generation. **`arXiv 2023.10`** [[Paper](https://arxiv.org/abs/2310.05737)]

## Long-Horizon Memory & Consistency

_Keeping the world stable when the camera comes back: long context, explicit spatial and 3D memory, retrieval, and state persistence._ &nbsp;·&nbsp; **91 entries**

* **`Vorch-Director`**, Interactive World Story Model via Noise-Aware Error Rectification. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.05776)]
* **`Cycle-World`**, Mitigating Error Accumulation in Long-term Video World Models via Reverse-Prediction Cycle Consistency. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.11836)]
* **`MemLearner`**, Learning to Query Context memory for Video World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.31734)]
* Compression and Retrieval: Implicit Memory Retrieval for Video World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.23105)]
* **`PermaVid`**, Consistent Video Generation Across Edits via Disentangled Context Memory. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.16449)]
* **`TetherCache`**, Stabilizing Autoregressive Long-Form Video Generation with Gated Recall and Trusted Alignment. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.13035)]
* **`FadeMem`**, Distance-Aware Memory Consolidation for Autoregressive Video Diffusion. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.10671)]
* Latent Spatial Memory for Video World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.09828)]
* **`Echo-Memory`**, A Controlled Study of Memory in Action World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.09803)]
* What Makes Video World Model Latents Action-Relevant: Prediction over Reconstruction. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.07687)]
* **`Steady-Forcing`**, Balancing Spatial Persistence and Motion Continuity in Long-Horizon Nature Video Diffusion. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.14732)]
* **`LongLive-RAG`**, A General Retrieval-Augmented Framework for Long Video Generation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.02553)]
* Retrieve What's Missing: Coverage-Maximizing Retrieval for Consistent Long Video Generation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.02479)]
* Geometry-Aware Implicit Memory for Video World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.02436)] [[Website](https://gim-world.github.io/)]
* **`DecMem`**, Towards Minute-Long Consistent World Generation with Decoupled Memory. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.31336)]
* **`SlotMemory`**, Object-Centric KV Memory for Streaming Long-Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.31033)]
* Robust Dreamer: Deviation-Aware Latent Gaussian Memory for Action-Controlled AR Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30855)]
* **`OmniMem`**, Scalable and Adaptive Memory Retrieval for Long Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30519)]
* Teaching Video Generators to Remember: Eliciting Dynamic Memory for Out-of-Sight State Evolution. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.25333)]
* **`WorldKV`**, Efficient World Memory with World Retrieval and Compression. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.22718)] [[Website](https://cvlab-kaist.github.io/WorldKV/)]
* **`DySink`**, Dynamic Frame Sinks for Autoregressive Long Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.21028)]
* Advancing Narrative Long Video Generation via Training-Free Identity-Aware Memory. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.18733)]
* Attend Locally, Remember Linearly: Linear Attention as Cross-Frame Memory for Autoregressive Video Diffusion. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.16579)]
* Identifiable Token Correspondence for World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.16457)] [[Code](https://github.com/snu-mllab/Identifiable-Token-Correspondence)]
* **`Echo-Forcing`**, A Scene Memory Framework for Interactive Long Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.16003)]
* **`RAVEN`**, Real-time Autoregressive Video Extrapolation with Consistency-model GRPO. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.15190)]
* Head Forcing: Long Autoregressive Video Generation via Head Heterogeneity. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.14487)]
* Composition of Memory Experts for Diffusion World Models. **`ICLR 2026`** [[Paper](https://arxiv.org/abs/2605.18813)]
* **`SWIFT`**, Prompt-Adaptive Memory for Efficient Interactive Long Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.09442)]
* Memorize When Needed: Decoupled Memory Control for Spatially Consistent Long-Horizon Video Generation. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.18215)]
* **`Lyra 2.0`**, Explorable Generative 3D Worlds. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.13036)]
* Grounded Forcing: Bridging Time-Independent Semantics and Proximal Dynamics in Autoregressive Video Synthesis. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.06939)]
* **`PackForcing`**, Short Video Training Suffices for Long Video Sampling and Long Context Inference. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.25730)]
* Out of Sight but Not Out of Mind: Hybrid Memory for Dynamic Video World Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.25716)]
* **`I3DM`**, Implicit 3D-aware Memory Retrieval and Injection for Consistent Video Scene Generation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.23413)]
* Relax Forcing: Relaxed KV-Memory for Consistent Long Video Generation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.21366)]
* Anchor Forcing: Anchor Memory and Tri-Region RoPE for Interactive Streaming Video Diffusion. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.13405)]
* **`MemRoPE`**, Training-Free Infinite Video Generation via Evolving Memory Tokens. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.12513)]
* **`LiveWorld`**, Simulating Out-of-Sight Dynamics in Generative Video World Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.07145)] [[Website](https://zichengduan.github.io/LiveWorld/index.html)]
* **`AnchorWeave`**, World-Consistent Video Generation with Retrieved Local Spatial Memories. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.14941)]
* Train Short, Inference Long: Training-free Horizon Extension for Autoregressive Video Generation. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.14027)]
* **`WorldCompass`**, Reinforcement Learning for Long-Horizon World Models. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.09022)] [[Website](https://3d-models.hunyuan.tencent.com/world/)]
* Geometry-Aware Rotary Position Embedding for Consistent Video World Model. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.07854)]
* Rolling Sink: Bridging Limited-Horizon Training and Open-Ended Testing in Autoregressive Video Diffusion. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.07775)]
* Context Forcing: Consistent Autoregressive Video Generation with Long Context. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.06028)]
* **`TokenTrim`**, Inference-Time Token Pruning for Autoregressive Long Video Generation. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2602.00268)]
* Efficient Autoregressive Video Diffusion with Dummy Head. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.20499)]
* Entropy-Guided k-Guard Sampling for Long-Horizon Autoregressive Video Generation. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.19488)]
* **`StableWorld`**, Towards Stable and Consistent Long Interactive Video Generation. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.15281)]
* Plenoptic Video Generation. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.05239)]
* **`TinyHistory`**, Lightweight Video History Embeddings via Two-Stage Context Learning. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.23851)]
* **`Memorize-and-Generate`**, Towards Long-Term Consistency in Real-Time Video Generation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.18741)]
* **`FrameDiffuser`**, G-Buffer-Conditioned Diffusion for Neural Forward Frame Rendering. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.16670)]
* End-to-End Training for Autoregressive Video Diffusion via Self-Resampling. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.15702)]
* **`MemFlow`**, Flowing Adaptive Memory for Consistent and Efficient Long Video Narratives. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.14699)]
* **`BAgger`**, Backwards Aggregation for Mitigating Drift in Autoregressive Video Diffusion Models. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.12080)]
* **`On Memory`**, A comparison of memory mechanisms in world models. **`World Modeling Workshop 2026`** [[Paper](https://arxiv.org/abs/2512.06983)]
* **`VideoSSM`**, Autoregressive Long Video Generation with Hybrid State-Space Memory. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.04519)]
* **`EgoLCD`**, Egocentric Video Generation with Long Context Diffusion. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.04515)]
* **`GrndCtrl`**, Grounding World Models via Self-Supervised Reward Alignment. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.01952)]
* **`BIFE`**, Better Interaction, Fewer Errors for Minute-Long Video Generation. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.22973)]
* **`UltraViCo`**, Breaking Extrapolation Limits in Video Diffusion Transformers. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.20123)]
* Recurrent Autoregressive Diffusion: Global Memory Meets Local Attention. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.12940)]
* Adaptive Begin-of-Video Tokens for Autoregressive Video Diffusion Models. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.12099)]
* Generative View Stitching. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.24718)]
* Stable Video Infinity: Infinite-Length Video Generation with Error Recycling. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.09212)]
* **`Self-Forcing++`**, Towards Minute-Scale High-Quality Video Generation. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.02283)]
* **`FantasyWorld`**, Geometry-Consistent World Modeling via Unified Video and 3D Prediction. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.21657)]
* **`SAMPO`**, Scale-wise Autoregression with Motion PrOmpt for generative world models. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.15536)]
* Mixture of Contexts for Long Video Generation. **`arXiv 2025.08`** [[Paper](https://arxiv.org/abs/2508.21058)]
* **`HERO`**, Hierarchical Extrapolation and Refresh for Efficient World Models. **`arXiv 2025.08`** [[Paper](https://arxiv.org/abs/2508.17588)]
* **`WorldWeaver`**, Generating Long-Horizon Video Worlds via Rich Perception. **`arXiv 2025.08`** [[Paper](https://arxiv.org/abs/2508.15720)]
* **`Geometry Forcing`**, Marrying Video Diffusion and 3D Representation for Consistent World Modeling. **`arXiv 2025.07`** [[Paper](https://arxiv.org/abs/2507.07982)] [[Website](https://GeometryForcing.github.io)]
* **`VMem`**, Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.18903)]
* **`StateSpaceDiffuser`**, Bringing Long Context to Diffusion World Models. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.22246)]
* Generative Pre-trained Autoregressive Diffusion Transformer. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.07344)]
* Frame Context Packing and Drift Prevention in Next-Frame-Prediction Video Diffusion Models. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.12626)]
* Long-Context Autoregressive Video Modeling with Next-Frame Prediction. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.19325)] [[Website](https://farlongctx.github.io/)] [[Code](https://github.com/showlab/FAR)]
* Long Context Tuning for Video Generation. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.10589)]
* Error Analyses of Auto-Regressive Video Diffusion Models: A Unified Framework. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.10704)]
* History-Guided Video Diffusion. **`arXiv 2025.02`** [[Paper](https://arxiv.org/abs/2502.06764)]
* **`Owl-1`**, Omni World Model for Consistent Long Video Generation. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.09600)]
* **`ACDiT`**, Interpolating Autoregressive Conditional Modeling and Diffusion Transformer. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.07720)]
* **`ARLON`**, Boosting Diffusion Transformers with Autoregressive Models for Long Video Generation. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2410.20502)]
* Progressive Autoregressive Video Diffusion Models. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2410.08151)]
* **`ACDC`**, Autoregressive Coherent Multimodal Generation using Diffusion Correction. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2410.04721)]
* **`MovieDreamer`**, Hierarchical Generation for Coherent Long Visual Sequence. **`arXiv 2024.07`** [[Paper](https://arxiv.org/abs/2407.16655)]
* **`Streetscapes`**, Large-scale Consistent Street View Generation Using Autoregressive Video Diffusion. **`arXiv 2024.07`** [[Paper](https://arxiv.org/abs/2407.13759)]
* **`FIFO-Diffusion`**, Generating Infinite Videos from Text without Training. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.11473)]
* **`StreamingT2V`**, Consistent, Dynamic, and Extendable Long Video Generation from Text. **`arXiv 2024.03`** [[Paper](https://arxiv.org/abs/2403.14773)]
* Temporally Consistent Transformers for Video Generation. **`arXiv 2022.10`** [[Paper](https://arxiv.org/abs/2210.02396)]

## Benchmarks & Evaluation

_Benchmarks and evaluation protocols aimed at interactive world models, including memory, control-following, and long-horizon stability._ &nbsp;·&nbsp; **21 entries**

* **`WorldExam`**, Benchmarking World Models from Apparent Appearance to Inherent Reactivity. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.02603)]
* **`WorldRoamBench`**, An Open-World Benchmark for Long-Horizon Stability of Interactive World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.31672)]
* **`MemoBench`**, Benchmarking World Modeling in Dynamically Changing Environments. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.27537)]
* Hallucination in World Models is Predictable and Preventable. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.27326)]
* Current World Models Lack a Persistent State Core. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.20545)]
* **`WorldOlympiad`**, Can Your World Model Survive a Triathlon?. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.11129)]
* **`MBench`**, A Comprehensive Benchmark on Memory Capability for Video World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2606.00793)] [[Website](https://peanutup.github.io/MBench-project/)] [[Code](https://github.com/study-overflow/MBench)]
* **`WBench`**, A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.25874)] [[Website](https://meituan-longcat.github.io/WBench/)]
* Quantitative Video World Model Evaluation for Geometric-Consistency. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.15185)] [[Website](https://pdi-bench.github.io/)]
* **`WorldReasonBench`**, Human-Aligned Stress Testing of Video Generators as Future World-State Predictors. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.10434)]
* **`ACWM-Phys`**, Investigating Generalized Physical Interaction in Action-Conditioned Video World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.08567)] [[Website](https://xavihart.github.io/ACWM-Phys)] [[Code](https://github.com/xavihart/ACWM-Phys-dev)]
* **`iWorld-Bench`**, A Benchmark for Interactive World Models with a Unified Action Generation Framework. **`ICML 2026`** [[Paper](https://arxiv.org/abs/2605.03941)]
* **`WorldMark`**, A Unified Benchmark Suite for Interactive Video World Models. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.21686)]
* World Reasoning Arena. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.25887)] [[Code](https://github.com/MBZUAI-IFM/WR-Arena)]
* **`Omni-WorldBench`**, Towards a Comprehensive Interaction-Centric Evaluation for World Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.22212)]
* Out of Sight, Out of Mind? Evaluating State Evolution in Video World Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.13215)] [[Website](https://glab-caltech.github.io/STEVOBench/)]
* **`MIND`**, Benchmarking Memory Consistency and Action Control in World Models. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.08025)] [[Code](https://github.com/CSU-JPG/MIND)]
* **`World-in-World`**, World Models in a Closed-Loop World. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.18135)] [[Website](https://github.com/World-In-World/world-in-world)]
* **`UNIVERSE`**, Adapting Vision-Language Models for Evaluating World Models. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.17967)]
* Toward Memory-Aided World Models: Benchmarking via Spatial Consistency. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.22976)] [[Code](https://github.com/Kevin-lkw/LoopNav)]
* Toward Stable World Models: Measuring and Addressing World Instability in Generative Environments. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.08122)]

## Datasets & Environments

_Action-annotated video corpora and simulators used to train and probe interactive world models._ &nbsp;·&nbsp; **4 entries**

* **`PhysEditWorld`**, A Large-Scale Dataset Toward Physics-Editable World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.26694)]
* **`EgoCS-400K`**, An Egocentric Gameplay Dataset for World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.18180)]
* **`WildWorld`**, A Large-Scale Dataset for Dynamic World Modeling with Actions and Explicit State toward Generative ARPG. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.23497)] [[Website](https://shandaai.github.io/wildworld-project/)] [[Code](https://github.com/ShandaAI/WildWorld)]
* **`EgoVid-5M`**, A Large-Scale Video-Action Dataset for Egocentric Video Generation. **`arXiv 2024.11`** [[Paper](https://arxiv.org/abs/2411.08380)]
<!-- END:LIST -->

---

## System Comparison

What separates this list from a bibliography: for every system read in depth, the axes that decide whether you can actually act inside it. `Action` is a normalized summary of the paper's own action space; `Memory` is the mechanism that carries state across steps, not a quality judgement. `—` means the paper does not report the value.

These are notes taken while reading, not measurements. Frame rates are the numbers the authors claim on the hardware they claim them on, and are not comparable across rows without reading the setups. Check anything you intend to rely on against the paper.

<!-- BEGIN:TABLE -->
| System | Date | Backbone | Action | FPS | Memory | Open |
| --- | --- | --- | --- | --- | --- | --- |
| [Wonder](https://arxiv.org/abs/2607.26037) | 2026-07 | causal diffusion | keyboard + camera | 16 | hybrid: retrieval+implicit-context — sparse full-fidelity attention+recent chunks always retained, plus top-k content-similar middle-history chunks). Retrieval is content-based, not geometric | no |
| [WanToFight](https://arxiv.org/abs/2607.12592) | 2026-07 | causal diffusion | keyboard | 30 | context | no |
| [Infinite Worlds with Versatile Interactions](https://arxiv.org/abs/2607.07534) | 2026-07 | AR + diffusion | camera + language + embodied | 60 | context | yes |
| [AlayaWorld](https://arxiv.org/abs/2607.06291) | 2026-07 | bidir. diffusion | camera + language | 24 | hybrid: spatial (recon)+compressive | no |
| [MoWorld](https://arxiv.org/abs/2607.06216) | 2026-07 | bidir. diffusion | camera | 50 | hybrid: context+retrieval | no |
| [Multiplayer Interactive World Models with R…](https://arxiv.org/abs/2607.05352) | 2026-07 | causal diffusion | keyboard | 20 | context | no |
| [Worldscape-MoE](https://arxiv.org/abs/2607.03964) | 2026-07 | other | camera + embodied | — | context | no |
| [WorldDirector](https://arxiv.org/abs/2607.02517) | 2026-07 | causal diffusion | camera + language | — | hybrid: spatial (store)+retrieval | no |
| [DreamForge-World 0.1](https://arxiv.org/abs/2606.30292) | 2026-06 | causal diffusion | keyboard + mouse | 14.5 | context | no |
| [Walking in the Implicit](https://arxiv.org/abs/2606.30045) | 2026-06 | other | camera | — | hybrid: spatial (recon)+retrieval | no |
| [Directing the World](https://arxiv.org/abs/2606.27964) | 2026-06 | AR + diffusion | camera | — | context | no |
| [MaineCoon](https://arxiv.org/abs/2606.17800) | 2026-06 | causal diffusion | language + embodied | 47.5 | context | no |
| [ActWorld](https://arxiv.org/abs/2606.17730) | 2026-06 | bidir. diffusion | keyboard + mouse + camera | 3.5 | hybrid: context+retrieval | no |
| [DreamX-World 1.0](https://arxiv.org/abs/2606.16993) | 2026-06 | bidir. diffusion | camera + language | 16 | retrieval | no |
| [GeoStream](https://arxiv.org/abs/2606.15162) | 2026-06 | causal diffusion | camera | 4.05 | spatial (recon) | no |
| [MoVerse](https://arxiv.org/abs/2606.13376) | 2026-06 | bidir. diffusion | camera | 8 | hybrid: spatial (recon)+context | no |
| [BiWM](https://arxiv.org/abs/2606.10135) | 2026-06 | AR + diffusion | camera + language | — | hybrid: context+compressive | yes |
| [Prisma-World](https://arxiv.org/abs/2606.09507) | 2026-06 | bidir. diffusion | camera | — | hybrid: context+spatial (store) | no |
| [DisCo](https://arxiv.org/abs/2606.07967) | 2026-06 | causal diffusion | camera | — | context | no |
| [Streaming Video Generation with Streaming F…](https://arxiv.org/abs/2606.07508) | 2026-06 | causal diffusion | other | 16.6 | context | no |
| [AnchorWorld](https://arxiv.org/abs/2606.07326) | 2026-06 | bidir. diffusion | other | — | spatial (store) | no |
| [MetaWorld](https://arxiv.org/abs/2606.02753) | 2026-06 | bidir. diffusion | camera | — | none | no |
| [From Zero to Hero](https://arxiv.org/abs/2606.02575) | 2026-06 | causal diffusion | camera | — | hybrid: context+retrieval | yes |
| [Gamma-World](https://arxiv.org/abs/2605.28816) | 2026-05 | causal diffusion | keyboard + mouse + embodied | 24 | context | no |
| [WorldCraft](https://arxiv.org/abs/2605.25077) | 2026-05 | causal diffusion | camera | — | hybrid: context+spatial (store) | no |
| [SCOPE](https://arxiv.org/abs/2605.23345) | 2026-05 | bidir. diffusion | keyboard + camera | — | none | yes |
| [Incantation](https://arxiv.org/abs/2605.18601) | 2026-05 | causal diffusion | language | 19.7 | context | no |
| [ReactiveGWM](https://arxiv.org/abs/2605.15256) | 2026-05 | bidir. diffusion | keyboard | — | context | no |
| [SANA-WM](https://arxiv.org/abs/2605.15178) | 2026-05 | SSM hybrid | camera | 16 | hybrid: compressive+context | yes |
| [CausalCine](https://arxiv.org/abs/2605.12496) | 2026-05 | causal diffusion | language | 16 | retrieval | no |
| [PROWL](https://arxiv.org/abs/2605.18803) | 2026-05 | causal diffusion | camera | 20 | context | no |
| [MultiWorld](https://arxiv.org/abs/2604.18564) | 2026-04 | causal diffusion | keyboard + mouse + embodied | — | hybrid: context+spatial (recon) | no |
| [Matrix-Game 3.0](https://arxiv.org/abs/2604.08995) | 2026-04 | bidir. diffusion | keyboard + mouse | 40 | hybrid: retrieval+context | yes |
| [INSPATIO-WORLD](https://arxiv.org/abs/2604.07209) | 2026-04 | causal diffusion | camera | 24 | hybrid: spatial (recon)+context | yes |
| [ActionParty](https://arxiv.org/abs/2604.02330) | 2026-04 | causal diffusion | keyboard | — | hybrid: context+spatial (store) | no |
| [EgoSim](https://arxiv.org/abs/2604.01001) | 2026-04 | bidir. diffusion | embodied | 16 | spatial (recon) | no |
| [MemCam](https://arxiv.org/abs/2603.26193) | 2026-03 | bidir. diffusion | camera | — | retrieval | yes |
| [ShotStream](https://arxiv.org/abs/2603.25746) | 2026-03 | causal diffusion | language | 16 | context | yes |
| [WorldCam](https://arxiv.org/abs/2603.16871) | 2026-03 | AR + diffusion | keyboard + mouse + camera | — | retrieval | no |
| [InSpatio-WorldFM](https://arxiv.org/abs/2603.11911) | 2026-03 | other | camera | 25 | hybrid: spatial (recon)+context | yes |

_Showing the 40 most recent of 104 profiled systems. Full table with horizons and verbatim action spaces: [docs/comparison.md](docs/comparison.md)._
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
