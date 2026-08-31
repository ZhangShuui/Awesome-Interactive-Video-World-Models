# Awesome Interactive Video World Models [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)

A curated list of **interactive video world models** — generative models you can act inside, one step at a time.

**[Browse it as a filterable index →](https://zhangshuui.github.io/Awesome-Interactive-Video-World-Models/)**
The same list, filterable by tag, with each paper's comparison record folded into its row.

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

There are no sections. Every paper sits in one list, newest first, carrying one to three tags that say what it is about — a system whose contribution is its action interface is 🌍`systems` 🕹️`control`, and it is one entry, not two.

To read everything on a topic, search the page for its **glyph**. Searching for `control` also hits every title with the word in it; searching for 🕹️ hits exactly the papers tagged with it and nothing else.

<!-- BEGIN:TAGKEY -->
- 📚 **`surveys`** — A survey, review or related list. Read one first to place the rest in context.
- 🌱 **`foundations`** — Work that defined the problem before interactive video world models were a category of their own: latent world models, neural game engines, playable video generation.
- 📰 **`reports`** — No paper — announced through a blog post or technical report, documented well enough to place. Every URL carrying this tag has been checked by hand.
- 🌍 **`systems`** — Meets all three scope criteria: per-step action conditioning, causal or streaming generation, persistent world state. The strict bar, and the only tag that feeds the comparison table.
- 🕹️ **`control`** — How an action reaches the generator: action spaces, injection mechanisms, latent actions learned without labels, control-fidelity analysis. A prompt issued per step, per entity or mid-rollout is an action too, so language interfaces carry this tag alongside the ones about buttons.
- ⚡ **`realtime`** — Meeting the per-frame latency budget: causal and autoregressive backbones, few-step distillation, KV caching, inference systems.
- 🧠 **`memory`** — Keeping the world stable when the camera comes back: long context, explicit spatial and 3D memory, retrieval, state persistence.
- 📊 **`benchmarks`** — A benchmark or evaluation protocol aimed at interactive world models — memory, control-following, long-horizon stability.
- 🗂️ **`datasets`** — An action-annotated video corpus or a simulator used to train and probe interactive world models.
<!-- END:TAGKEY -->

Venue labels show `arXiv YYMM` when a paper has no published venue recorded yet.

---

<!-- BEGIN:LIST -->
* **`LayerRecall`**, A State-Conditioned Memory Router for Long-Horizon Consistency in Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.28460)] · 🧠`memory`
* How Far Can 5,500 Hours of Driving Take You? A Scaling Law Analysis of Video Diffusion Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.28404)] · 🧠`memory`
* **`DensityKV`**, Density-Guided KV Cache Compression for Long Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.27922)] · ⚡`realtime`
* **`PAWBench`**, How Far Are We from Probabilistically Aligned World Modeling?. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.27345)] · 🧠`memory`
* **`R2M-Bench`**, Evaluating Revisit Memory via Relative Consistency in Interactive Video World Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.27328)] · 🧠`memory` 📊`benchmarks`
* **`Magpie`**, Real-Time World Renderer for Interactive Games. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.27168)] · ⚡`realtime`
* Tether the Subject, Release the Scene: Query-Aware Memory Routing for Long-Horizon Autoregressive Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.26902)] · 🧠`memory`
* Ring Forcing: Towards Precise Long-Term Memory for Autoregressive Video Diffusion. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.26794)] · 🧠`memory`
* **`RECAP-Forcing`**, Retaining Content Appearances for Long Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.26671)] · 🧠`memory`
* **`StreamAV-Bench`**, A Comprehensive Benchmark for Streaming Audio-Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.26336)] · ⚡`realtime` 📊`benchmarks`
* Code World Model: Coding Agent as World Brain. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.25927)] · 🧠`memory`
* Scaling Reinforcement Learning for Diffusion Models via Velocity Matching. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.23664)] · ⚡`realtime`
* **`ReWorld`**, An Interactive World Model with Long-Horizon Memory. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.23565)] · 🧠`memory`
* **`EchoWM`**, Open and Enterable Omnimodal World Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.23189)] · 🧠`memory`
* From Generation to Simulation: How Far Are World Models from Being True Simulators?. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.23070)] · 🕹️`control`
* **`StocBench`**, A Benchmark for Generative Modeling of Stochastic Dynamics. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.22309)] · 📊`benchmarks`
* **`FIRM-Video`**, Check Before You Score for Reliable Text-to-Video Reward Modeling. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.21839)] · 🕹️`control`
* 4DAnyone: Create Anyone in 4D from a Casual Monocular Video. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.20335)] · 🧠`memory`
* **`BeyondMasks`**, Evaluating Causal and Physical Consistency in Video Object Removal. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.20107)] · 🧠`memory` 📊`benchmarks`
* **`Stream4D`**, 4D-Consistency for Streaming Autoregressive Diffusion Video Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.19556)] · ⚡`realtime` 🧠`memory`
* **`CamWorldQA`**, Perceptual Quality Assessment of Camera-Controlled World Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.18710)] · 🧠`memory`
* Partition the Support, Reconstruct the Residual: Training-Free Sparse Attention for Video Generation and World Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.18484)] · ⚡`realtime`
* **`LinCa`**, Accelerating Diffusion Models via Learnable Decomposed Feature Caching. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.17973)] · ⚡`realtime`
* **`DynaForcing`**, Overcoming Dynamic Collapse in Self-Forcing Distillation for Streaming Avatar Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.17707)] · ⚡`realtime`
* Magnitude-Direction Decoupling for Fast Video Generation with Flow Matching Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.17695)] · ⚡`realtime`
* **`SemComp-Bench`**, Benchmarking Semantic Task Completion in Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.17426)] · 📊`benchmarks`
* **`HarnessEval-W`**, Agentifying the Evaluation of Visual Worlds. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.16859)] · 📊`benchmarks`
* **`CaliBench`**, Are the Stochastic Dynamics of Video World Models Physically Calibrated?. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.16829)] · 🧠`memory`
* **`SQuad`**, Sub-Quadratic Attention Distillation for Efficient Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.16585)] · ⚡`realtime`
* MLLM-Guided Semantic Correction for Text-to-Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.16513)] · 🕹️`control`
* **`Marionette`**, Predicting World States, Rendering Geometry, Painting Appearance. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.14530)] · 🧠`memory`
* **`ForgeWM`**, Progressive Causal Training for Few-Step Action-Conditioned Video World Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.14022)] · 🌍`systems` 🕹️`control` ⚡`realtime`
* **`PlayWorld`**, Benchmarking World Models with Agent Players over Long-Horizon Objectives. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.13552)] · 🧠`memory` 📊`benchmarks`
* **`Alaya-EVOKE`**, From Linear-Scaling Supervision to Endless World. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.13546)] · 🧠`memory`
* **`AlayaWorld`**, Interactive Long-Horizon World Modeling - Full Technical Report (v1.1). **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.13492)] · 🧠`memory`
* **`Context-Matched Distillation`**, Teacher Causality for Autoregressive Video Distillation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.13391)] · 🌍`systems` ⚡`realtime`
* **`HPSD`**, Hybrid-Policy Self-Distillation for Text-Image-to-Video Diffusion Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.13205)] · ⚡`realtime`
* From Local Mismatch to Global Impact: Optimizing Cache Reuse Policy for Efficient Diffusion. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.13043)] · ⚡`realtime`
* Spatially-Grounded Text-to-Video Generation via Inference-Time Gradient-Free Optimization. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.13037)] · 🕹️`control`
* **`Avatar-Forever`**, Decoupled Parallel Training for High-Quality Real-Time Infinite Avatars. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.12107)] · ⚡`realtime`
* **`LoSA`**, Near-Lossless Sparse Attention for Training-Free Video Diffusion Acceleration. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.12032)] · ⚡`realtime`
* **`LiveAnimate`**, Stable Long-Form Streaming Human Animation in Real-Time. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.11745)] · ⚡`realtime`
* From Synthesis to Removal: Physics-Grounded Reflection Simulation and Diffusion-Based Video Dereflection. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.11562)] · ⚡`realtime`
* Equilibrium Forcing: Adaptive Video Generation Without Noise Conditioning. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.14706)] · 🧠`memory`
* **`SparSTAR`**, Sparse Attention for SpaceTime AutoRegressive Video Synthesis. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.10519)] · 🧠`memory`
* Bridging Event Streams and DiT: Event-Guided Video Frame Interpolation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.10479)] · 🧠`memory`
* Stream Forcing: Constructing Unified Training Trajectory for Robust Streaming Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.10439)] · ⚡`realtime`
* **`DUET`**, A Diversity-Quality Duet of Distillation Experts for Two-Step Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.09637)] · ⚡`realtime`
* **`Sekai2`**, From World Exploration to Interactive World Modeling. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.09449)] · 🧠`memory`
* Alpha as an Efficiency Signal: Visibility-Routed RGBA Image-to-Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.09355)] · ⚡`realtime`
* Addressable Memory for Video World Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.07408)] · 🧠`memory`
* **`MASS`**, Multiplayer World Models with Authoritative Shared State. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.06257)] · 🌍`systems`
* **`Diff-VF`**, Training-free High-quality Long Video Generation via Diffusion Model. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.05976)] · 🧠`memory`
* **`GAUGE`**, A Measurement-Grounded Benchmark for Physical Fidelity in Simulation Engines and Video World Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.05948)] · 📊`benchmarks`
* **`Vorch-Director`**, Interactive World Story Model via Noise-Aware Error Rectification. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.05776)] · 🧠`memory`
* **`In-Context Forcing`**, Uncovering Context Effects in Autoregressive Video Diffusion. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.05237)] · ⚡`realtime`
* **`HelloWorld`**, Enabling Socially Interactive Characters in Video World Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.05070)] · 🌍`systems` 🕹️`control`
* **`WorldCycle`**, Self-Verifiable Reinforcement Learning for Long-Horizon Video World Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.04964)] · 🧠`memory`
* **`UniWorld-View`**, Large-Baseline View Synthesis via Video Diffusion Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.04701)] · 🕹️`control`
* Overcoming Statistical Bias in Action-Controllable World Models. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.04653)] · 🕹️`control`
* **`SPADE`**, An Input-Adaptive Sparse Attention Engine for Fast Video Diffusion Models Inference. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.03335)] · ⚡`realtime`
* **`WorldExam`**, Benchmarking World Models from Apparent Appearance to Inherent Reactivity. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.02603)] · 📊`benchmarks`
* Token Radius Attention for Efficient Video Generation. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.02504)] · ⚡`realtime`
* **`WorldDynCache`**, Risk-Controlled Latent Dynamics Approximation for Diffusion World Model. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.01845)] · ⚡`realtime`
* **`MiniWorld`**, Democratizing the Training of Video World Models from Scratch. **`arXiv 2026.08`** [[Paper](https://arxiv.org/abs/2608.01127)] · ⚡`realtime`
* Video Models as Native 4D Renderers: World-Grounded Conditioning from Animated Mesh. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2608.00094)] · 🕹️`control`
* **`ShadowDancer`**, Teaching Video World Models Any Action by Learning Unified Dynamics Representations from a Video and Its Shadow. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.28362)] · 🕹️`control`
* **`ODEWorld`**, A Continuous Predictive Architecture via Physical-Time Flow. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.27924)] · 🧠`memory`
* **`FreqForcing`**, Autoregressive Long Video Generation via Spectral Self-Anchoring. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.27110)] · 🧠`memory`
* Mitigating Compounding Error via Video Representation Regularization. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.27036)] · 🧠`memory`
* **`StatePlay`**, State-Aware Game World Models for Mechanics-Consistent Generation. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.26754)] · 🌍`systems` 🧠`memory`
* **`Visko Orbis 1.0`**, A Live Model for Real-Time Interactive Long Video Generation. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.26694)] · 🌍`systems` ⚡`realtime`
* **`CineWeaver`**, Training-Free Reference-Controllable Multi-Shot Long Video Generation for Cinematic Storytelling. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.26529)] · 🕹️`control` 🧠`memory`
* **`Wonder`**, Video World Model Done Better. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.26037)] · 🌍`systems`
* Parallel Decoding Distillation for Fast Image and Video Generation. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.26004)] · ⚡`realtime`
* **`ABot-World-0`**, Infinite Interactive World Rollout on a Single Desktop GPU. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.19191)] · 🌍`systems`
* **`FlashDecoder`**, Real-Time Latent-to-Pixel Streaming Decoder with Transformers. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.14898)] · ⚡`realtime`
* **`WanToFight`**, Real-Time Generative Game Engine for Multi-Player Combat Interaction. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.12592)] · 🌍`systems` ⚡`realtime`
* **`Cycle-World`**, Mitigating Error Accumulation in Long-term Video World Models via Reverse-Prediction Cycle Consistency. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.11836)] · 🧠`memory`
* Stateful Worlds, Stateless Elasticity: Exact-State Serving for Interactive World Models. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.10389)] · ⚡`realtime`
* **`OPSD-V`**, On-Policy Self-Distillation for Post-Training Few-Step Autoregressive Video Generators. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.08766)] · ⚡`realtime`
* **`SAGA`**, Stable Acceleration Guidance for Autoregressive Video Generation. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.08020)] · ⚡`realtime`
* Infinite Worlds with Versatile Interactions. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.07534)] · 🌍`systems` 🕹️`control`
* **`AlayaWorld`**, Long-Horizon and Playable Video World Generation. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.06291)] · 🌍`systems` 🕹️`control` 🧠`memory`
* **`MoWorld`**, A Flash World Model. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.06216)] · 🌍`systems`
* Multiplayer Interactive World Models with Representation Autoencoders. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.05352)] · 🌍`systems`
* **`Worldscape-MoE`**, A Unified Mixture-of-Experts World Model for Scalable Heterogeneous Action Control. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.03964)] · 🌍`systems`
* **`Flex-Forcing`**, Towards a Unified Autoregressive and Bidirectional Video Diffusion Model. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.03509)] · ⚡`realtime`
* **`WorldDirector`**, Building Controllable World Simulators with Persistent Dynamic Memory. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.02517)] · 🌍`systems` 🕹️`control` 🧠`memory`
* Towards Memory-Efficient Autoregressive Video Generation via Instance-Specific Parametric Absorption. **`arXiv 2026.07`** [[Paper](https://arxiv.org/abs/2607.00712)] · ⚡`realtime`
* World Narrative Model for Highly Controllable Video Generation: A Paradigm Shift from Pixel Sampling to Physical World Orchestration. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.31946)] · 🕹️`control`
* **`MemLearner`**, Learning to Query Context memory for Video World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.31734)] · 🧠`memory`
* **`WorldRoamBench`**, An Open-World Benchmark for Long-Horizon Stability of Interactive World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.31672)] · 🧠`memory` 📊`benchmarks`
* **`DreamForge-World 0.1`**, DreamForge-World 0.1 Preview: A Low-Compute Real-Time Controllable World Model. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.30292)] · 🌍`systems` 🕹️`control` ⚡`realtime`
* Walking in the Implicit: Interactive World Exploration via Neural Scene Representation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.30045)] · 🌍`systems`
* **`TempAct`**, Advancing Temporal Plausibility in Autoregressive Video Generation via Planner-Executor RL. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.28016)] · 🕹️`control` ⚡`realtime`
* Directing the World: Fast Autoregressive Video Generation with Compositional Human-Camera Control. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.27964)] · 🌍`systems` 🕹️`control`
* **`MemoBench`**, Benchmarking World Modeling in Dynamically Changing Environments. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.27537)] · 📊`benchmarks`
* Hallucination in World Models is Predictable and Preventable. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.27326)] · 📊`benchmarks`
* **`LiveEdit`**, Towards Real-Time Diffusion-Based Streaming Video Editing. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.26740)] · 🕹️`control` ⚡`realtime`
* **`PhysEditWorld`**, A Large-Scale Dataset Toward Physics-Editable World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.26694)] · 🗂️`datasets`
* **`Causal-rCM`**, A Unified Teacher-Forcing and Self-Forcing Open Recipe for Autoregressive Diffusion Distillation in Streaming Video Generation and Interactive World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.25473)] · ⚡`realtime`
* Compression and Retrieval: Implicit Memory Retrieval for Video World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.23105)] · 🧠`memory`
* World Action Models: A Survey. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.20781)] · 📚`surveys`
* Current World Models Lack a Persistent State Core. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.20545)] · 🧠`memory` 📊`benchmarks`
* **`TurboServe`**, Serving Streaming Video Generation Efficiently and Economically. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.19271)] · ⚡`realtime`
* **`UniTemp`**, Unlocking Video Generation in Any Temporal Order via Bidirectional Distillation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.18702)] · ⚡`realtime`
* **`EgoCS-400K`**, An Egocentric Gameplay Dataset for World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.18180)] · 🗂️`datasets`
* **`MaineCoon`**, Pursuing A Real-Time Audio-Visual Social World Model. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.17800)] · 🌍`systems` 🕹️`control` ⚡`realtime`
* **`ActWorld`**, From Explorable to Interactive World Model via Action-Aware Memory. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.17730)] · 🌍`systems` 🧠`memory`
* **`DreamX-World 1.0`**, A General-Purpose Interactive World Model. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.16993)] · 🌍`systems` 🕹️`control`
* **`PermaVid`**, Consistent Video Generation Across Edits via Disentangled Context Memory. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.16449)] · 🧠`memory`
* Adaptive Resource Management and Quality Control for Streaming Video Generation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.15319)] · ⚡`realtime`
* **`GeoStream`**, Toward Precise Camera Controlled Streaming Video Generation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.15162)] · 🌍`systems` ⚡`realtime`
* **`MoVerse`**, Real-Time Video World Modeling with Panoramic Gaussian Scaffold. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.13376)] · 🌍`systems` ⚡`realtime`
* **`TetherCache`**, Stabilizing Autoregressive Long-Form Video Generation with Gated Recall and Trusted Alignment. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.13035)] · 🧠`memory`
* **`Next Forcing`**, Causal World Modeling with Multi-Chunk Prediction. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.11187)] · 🕹️`control` ⚡`realtime`
* **`WorldOlympiad`**, Can Your World Model Survive a Triathlon?. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.11129)] · 📊`benchmarks`
* **`FadeMem`**, Distance-Aware Memory Consolidation for Autoregressive Video Diffusion. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.10671)] · 🧠`memory`
* **`BiWM`**, Advancing Open-Source Interactive Video World Models with Bidirectional Autoregression. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.10135)] · 🌍`systems` 🕹️`control`
* Latent Spatial Memory for Video World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.09828)] · 🧠`memory`
* **`Echo-Memory`**, A Controlled Study of Memory in Action World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.09803)] · 🧠`memory`
* **`SwiftVR`**, Real-Time One-Step Generative Video Restoration. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.09516)] · ⚡`realtime`
* **`Prisma-World`**, Camera-Controllable Multi-Agent Video World Model. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.09507)] · 🌍`systems` 🕹️`control`
* Ultra Flash: Scaling Real-Time Streaming Video Generation to High Resolutions. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.09150)] · ⚡`realtime`
* **`DisCo`**, World Models with Discrete Camera Motion Control. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.07967)] · 🌍`systems`
* What Makes Video World Model Latents Action-Relevant: Prediction over Reconstruction. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.07687)] · 🧠`memory`
* Streaming Video Generation with Streaming Force Control. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.07508)] · 🌍`systems` ⚡`realtime`
* **`DSA`**, Dynamic Step Allocation for Fast Autoregressive Video Generation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.04432)] · ⚡`realtime`
* **`Steady-Forcing`**, Balancing Spatial Persistence and Motion Continuity in Long-Horizon Nature Video Diffusion. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.14732)] · 🧠`memory`
* **`CLAW`**, Learning Continuous Latent Action World Models via Adversarial Latent Regularization. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.04130)] · 🕹️`control`
* **`AAD-1`**, Asymmetric Adversarial Distillation for One-Step Autoregressive Video Generation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.03972)] · ⚡`realtime`
* **`Video-Mirai`**, Autoregressive Video Diffusion Models Need Foresight. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.03971)] · ⚡`realtime`
* **`MetaWorld`**, Scaling Multi-Agent Video World Model from Single-view Video Data. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.02753)] · 🌍`systems`
* From Zero to Hero: Training-Free Custom Concept Spawning in World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.02575)] · 🌍`systems`
* **`LongLive-RAG`**, A General Retrieval-Augmented Framework for Long Video Generation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.02553)] · 🧠`memory`
* Retrieve What's Missing: Coverage-Maximizing Retrieval for Consistent Long Video Generation. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.02479)] · 🧠`memory`
* Geometry-Aware Implicit Memory for Video World Models. **`arXiv 2026.06`** [[Paper](https://arxiv.org/abs/2606.02436)] [[Website](https://gim-world.github.io/)] · 🧠`memory`
* **`MBench`**, A Comprehensive Benchmark on Memory Capability for Video World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2606.00793)] [[Website](https://peanutup.github.io/MBench-project/)] [[Code](https://github.com/study-overflow/MBench)] · 🧠`memory` 📊`benchmarks`
* **`DecMem`**, Towards Minute-Long Consistent World Generation with Decoupled Memory. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.31336)] · 🧠`memory`
* Light Interaction: Training-Free Inference Acceleration for Interactive Video World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.31158)] · ⚡`realtime`
* **`SlotMemory`**, Object-Centric KV Memory for Streaming Long-Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.31033)] · ⚡`realtime` 🧠`memory`
* Robust Dreamer: Deviation-Aware Latent Gaussian Memory for Action-Controlled AR Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30855)] · 🧠`memory`
* **`OmniMem`**, Scalable and Adaptive Memory Retrieval for Long Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30519)] · 🧠`memory`
* **`SANA-Streaming`**, Real-time Streaming Video Editing with Hybrid Diffusion Transformer. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30409)] · ⚡`realtime`
* **`VideoMLA`**, Low-Rank Latent KV Cache for Minute-Scale Autoregressive Video Diffusion. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30351)] · ⚡`realtime`
* **`AdaState`**, Self-Evolving Anchors for Streaming Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30349)] · ⚡`realtime`
* **`minWM`**, A Full-Stack Open-Source Framework for Real-Time Interactive Video World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30263)] [[Website](https://github.com/shengshu-ai/minWM)] · ⚡`realtime`
* **`SGMD`**, Score Gradient Matching Distillation for Few-Step Video Diffusion Distillation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.30116)] · ⚡`realtime`
* **`Gamma-World`**, Generative Multi-Agent World Modeling Beyond Two Players. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.28816)] [[Website](https://research.nvidia.com/labs/sil/projects/gamma-world)] · 🌍`systems`
* Quantized Keys Steal Attention: Bias Correction for KV-Cache Compression in Video Diffusion. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.26266)] · ⚡`realtime`
* On-Policy Adversarial Flow Distillation for Autoregressive Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.26105)] · ⚡`realtime`
* **`WBench`**, A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.25874)] [[Website](https://meituan-longcat.github.io/WBench/)] · 📊`benchmarks`
* Teaching Video Generators to Remember: Eliciting Dynamic Memory for Out-of-Sight State Evolution. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.25333)] · 🧠`memory`
* **`WorldCraft`**, From Camera Navigation to Object Manipulation in Interactive Video World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.25077)] [[Website](https://nevsdev.github.io/WorldCraft/)] · 🌍`systems`
* World Models as Group Actions. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.24578)] · 🕹️`control`
* **`One-Forcing`**, Towards Stable One-Step Autoregressive Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.23458)] · ⚡`realtime`
* **`SCOPE`**, Simulating Cross-game Operations in Playable Environments for FPS World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.23345)] [[Website](https://z2tong.github.io/SCOPE/)] [[Code](https://github.com/z2tong/SCOPE)] · 🌍`systems`
* **`WorldKV`**, Efficient World Memory with World Retrieval and Compression. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.22718)] [[Website](https://cvlab-kaist.github.io/WorldKV/)] · 🧠`memory`
* **`Q-ARVD`**, Quantizing Autoregressive Video Diffusion Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.21072)] · ⚡`realtime`
* **`DySink`**, Dynamic Frame Sinks for Autoregressive Long Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.21028)] · 🧠`memory`
* **`LongLive-2.0`**, An NVFP4 Parallel Infrastructure for Long Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.18739)] · ⚡`realtime`
* Advancing Narrative Long Video Generation via Training-Free Identity-Aware Memory. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.18733)] · 🧠`memory`
* **`Incantation`**, Natural Language as the Action Interface for Multi-Entity Video World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.18601)] · 🌍`systems` 🕹️`control`
* Focused Forcing: Content-Aware Per-Frame KV Selection for Efficient Autoregressive Video Diffusion. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.18346)] · ⚡`realtime`
* **`Nano World Models`**, A Minimalist Implementation of Future Video Prediction. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.23993)] [[Website](https://simchowitzlabpublic.github.io/nano-world-model/)] · 🕹️`control`
* Attend Locally, Remember Linearly: Linear Attention as Cross-Frame Memory for Autoregressive Video Diffusion. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.16579)] · 🧠`memory`
* Identifiable Token Correspondence for World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.16457)] [[Code](https://github.com/snu-mllab/Identifiable-Token-Correspondence)] · 🧠`memory`
* **`Echo-Forcing`**, A Scene Memory Framework for Interactive Long Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.16003)] · 🧠`memory`
* **`DiLA`**, Disentangled Latent Action World Models. **`ICML 2026`** [[Paper](https://arxiv.org/abs/2605.15725)] [[Website](http://disentangled-latent-action-world-models.github.io)] · 🕹️`control`
* **`ReactiveGWM`**, Steering NPC in Reactive Game World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.15256)] [[Website](https://inv-wzq.github.io/ReactiveGWM/)] · 🌍`systems`
* **`RAVEN`**, Real-time Autoregressive Video Extrapolation with Consistency-model GRPO. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.15190)] · ⚡`realtime` 🧠`memory`
* Quantitative Video World Model Evaluation for Geometric-Consistency. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.15185)] [[Website](https://pdi-bench.github.io/)] · 🧠`memory` 📊`benchmarks`
* **`SANA-WM`**, Efficient Minute-Scale World Modeling with Hybrid Linear Diffusion Transformer. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.15178)] [[Website](https://nvlabs.github.io/Sana/WM/)] · 🌍`systems`
* Causal Forcing++: Scalable Few-Step Autoregressive Diffusion Distillation for Real-Time Interactive Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.15141)] · ⚡`realtime`
* Head Forcing: Long Autoregressive Video Generation via Head Heterogeneity. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.14487)] · 🧠`memory`
* Delta Forcing: Trust Region Steering for Interactive Autoregressive Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.14382)] · ⚡`realtime`
* **`KVPO`**, ODE-Native GRPO for Autoregressive Video Alignment via KV Semantic Exploration. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.14278)] · ⚡`realtime`
* Pyramid Forcing: Head-Aware Pyramid KV Cache Policy for High-Quality Long Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.13111)] · ⚡`realtime`
* Composition of Memory Experts for Diffusion World Models. **`ICLR 2026`** [[Paper](https://arxiv.org/abs/2605.18813)] · 🧠`memory`
* **`CausalCine`**, Real-Time Autoregressive Generation for Multi-Shot Video Narratives. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.12496)] · 🌍`systems` 🕹️`control` ⚡`realtime`
* **`PROWL`**, Prioritized Regret-Driven Optimization for World Model Learning. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.18803)] · 🌍`systems`
* **`WorldReasonBench`**, Human-Aligned Stress Testing of Video Generators as Future World-State Predictors. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.10434)] · 📊`benchmarks`
* **`Forcing-KV`**, Hybrid KV Cache Compression for Efficient Autoregressive Video Diffusion Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.09681)] · ⚡`realtime`
* **`SWIFT`**, Prompt-Adaptive Memory for Efficient Interactive Long Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.09442)] · 🧠`memory`
* **`ACWM-Phys`**, Investigating Generalized Physical Interaction in Action-Conditioned Video World Models. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.08567)] [[Website](https://xavihart.github.io/ACWM-Phys)] [[Code](https://github.com/xavihart/ACWM-Phys-dev)] · 🕹️`control` 📊`benchmarks`
* Render, Don't Decode: Weight-Space World Models with Latent Structural Disentanglement. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.06298)] · 🕹️`control`
* **`Stream-T1`**, Test-Time Scaling for Streaming Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.04461)] · ⚡`realtime`
* **`iWorld-Bench`**, A Benchmark for Interactive World Models with a Unified Action Generation Framework. **`ICML 2026`** [[Paper](https://arxiv.org/abs/2605.03941)] · 📊`benchmarks`
* **`Stream-R1`**, Reliability-Perplexity Aware Reward Distillation for Streaming Video Generation. **`arXiv 2026.05`** [[Paper](https://arxiv.org/abs/2605.03849)] · ⚡`realtime`
* **`WorldMark`**, A Unified Benchmark Suite for Interactive Video World Models. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.21686)] · 📊`benchmarks`
* Sparse Forcing: Native Trainable Sparse Attention for Real-time Autoregressive Diffusion Video Generation. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.21221)] · ⚡`realtime`
* **`X-Cache`**, Cross-Chunk Block Caching for Few-Step Autoregressive World Models Inference. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.20289)] · ⚡`realtime`
* **`MultiWorld`**, Scalable Multi-Agent Multi-View Video World Models. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.18564)] [[Website](https://multi-world.github.io/)] · 🌍`systems`
* Memorize When Needed: Decoupled Memory Control for Spatially Consistent Long-Horizon Video Generation. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.18215)] · 🧠`memory`
* Speculative Decoding for Autoregressive Video Generation. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.17397)] · ⚡`realtime`
* **`DiT as Real-Time Rerenderer`**, Streaming Video Stylization with Autoregressive Diffusion Transformer. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.13509)] · ⚡`realtime`
* **`Lyra 2.0`**, Explorable Generative 3D Worlds. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.13036)] · 🧠`memory`
* Long-Horizon Streaming Video Generation via Hybrid Attention with Decoupled Distillation. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.10103)] · ⚡`realtime` 🧠`memory`
* **`Matrix-Game 3.0`**, Real-Time and Streaming Interactive World Model with Long-Horizon Memory. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.08995)] [[Website](https://matrix-game-v3.github.io/)] · 🌍`systems` ⚡`realtime` 🧠`memory`
* **`INSPATIO-WORLD`**, A Real-Time 4D World Simulator via Spatiotemporal Autoregressive Modeling. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.07209)] · 🌍`systems` ⚡`realtime`
* Grounded Forcing: Bridging Time-Independent Semantics and Proximal Dynamics in Autoregressive Video Synthesis. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.06939)] · 🧠`memory`
* **`ActionParty`**, Multi-Subject Action Binding in Generative Video Games. **`arXiv 2026.04`** [[Paper](https://arxiv.org/abs/2604.02330)] · 🌍`systems`
* **`MemCam`**, Memory-Augmented Camera Control for Consistent Video Generation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.26193)] · 🌍`systems` 🕹️`control` 🧠`memory`
* World Reasoning Arena. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.25887)] [[Code](https://github.com/MBZUAI-IFM/WR-Arena)] · 📊`benchmarks`
* **`ShotStream`**, Streaming Multi-Shot Video Generation for Interactive Storytelling. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.25746)] · 🌍`systems` 🕹️`control` ⚡`realtime`
* **`PackForcing`**, Short Video Training Suffices for Long Video Sampling and Long Context Inference. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.25730)] · 🧠`memory`
* Out of Sight but Not Out of Mind: Hybrid Memory for Dynamic Video World Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.25716)] · 🧠`memory`
* **`DCARL`**, A Divide-and-Conquer Framework for Autoregressive Long-Trajectory Video Generation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.24835)] · 🕹️`control`
* **`WildWorld`**, A Large-Scale Dataset for Dynamic World Modeling with Actions and Explicit State toward Generative ARPG. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.23497)] [[Website](https://shandaai.github.io/wildworld-project/)] [[Code](https://github.com/ShandaAI/WildWorld)] · 🗂️`datasets`
* **`I3DM`**, Implicit 3D-aware Memory Retrieval and Injection for Consistent Video Scene Generation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.23413)] · 🧠`memory`
* **`WorldCache`**, Content-Aware Caching for Accelerated Video World Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.22286)] [[Website](https://umair1221.github.io/World-Cache/)] · ⚡`realtime`
* **`Omni-WorldBench`**, Towards a Comprehensive Interaction-Centric Evaluation for World Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.22212)] · 📊`benchmarks`
* Relax Forcing: Relaxed KV-Memory for Consistent Long Video Generation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.21366)] · 🧠`memory`
* **`MosaicMem`**, Hybrid Spatial Memory for Controllable Video World Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.17117)] [[Website](https://mosaicmem.github.io/mosaicmem/)] · 🕹️`control` 🧠`memory`
* **`Astrolabe`**, Steering Forward-Process Reinforcement Learning for Distilled Autoregressive Video Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.17051)] · ⚡`realtime`
* **`WorldCam`**, Interactive Autoregressive 3D Gaming Worlds with Camera Pose as a Unifying Geometric Representation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.16871)] [[Website](https://cvlab-kaist.github.io/WorldCam/)] · 🌍`systems`
* Out of Sight, Out of Mind? Evaluating State Evolution in Video World Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.13215)] [[Website](https://glab-caltech.github.io/STEVOBench/)] · 🧠`memory` 📊`benchmarks`
* Anchor Forcing: Anchor Memory and Tri-Region RoPE for Interactive Streaming Video Diffusion. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.13405)] · ⚡`realtime` 🧠`memory`
* **`MemRoPE`**, Training-Free Infinite Video Generation via Evolving Memory Tokens. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.12513)] · 🧠`memory`
* **`InSpatio-WorldFM`**, An Open-Source Real-Time Generative Frame Model. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.11911)] · 🌍`systems` ⚡`realtime`
* **`OmniForcing`**, Unleashing Real-time Joint Audio-Visual Generation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.11647)] · ⚡`realtime`
* Streaming Autoregressive Video Generation via Diagonal Distillation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.09488)] · ⚡`realtime`
* **`LiveWorld`**, Simulating Out-of-Sight Dynamics in Generative Video World Models. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.07145)] [[Website](https://zichengduan.github.io/LiveWorld/index.html)] · 🧠`memory`
* **`WorldCache`**, Accelerating World Models for Free via Heterogeneous Token Caching. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.06331)] [[Website](https://github.com/FofGofx/WorldCache)] · ⚡`realtime`
* Hierarchical Latent Action Model. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.05815)] · 🕹️`control`
* **`RealWonder`**, Real-Time Physical Action-Conditioned Video Generation. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.05449)] · 🌍`systems` 🕹️`control` ⚡`realtime`
* **`Helios`**, Real Real-Time Long Video Generation Model. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.04379)] [[Website](https://pku-yuangroup.github.io/Helios-Page/)] [[Code](https://github.com/PKU-YuanGroup/Helios)] · ⚡`realtime`
* **`MultiGen`**, Level-Design for Editable Multiplayer Worlds in Diffusion Game Engines. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.06679)] · 🌍`systems`
* Beyond Pixel Histories: World Models with Persistent 3D State. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.03482)] [[Website](https://francelico.github.io/persist.github.io)] · 🌍`systems` 🧠`memory`
* Accelerating Video Generation Inference with Sequential-Parallel 3D Positional Encoding Using a Global Time Index. **`arXiv 2026.03`** [[Paper](https://arxiv.org/abs/2603.06664)] · ⚡`realtime`
* **`COMBAT`**, Conditional World Models for Behavioral Agent Training. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2603.00825)] · 🌍`systems`
* **`UCM`**, Unifying Camera Control and Memory with Time-aware Positional Encoding Warping for World Models. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.22960)] [[Website](https://humanaigc.github.io/ucm-webpage/)] · 🌍`systems` 🕹️`control` 🧠`memory`
* **`Solaris`**, Building a Multiplayer Video World Model in Minecraft. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.22208)] [[Website](https://solaris-wm.github.io/)] · 🌍`systems`
* **`Generated Reality`**, Human-centric World Simulation using Interactive Video Generation with Hand and Camera Control. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.18422)] · 🌍`systems` 🕹️`control`
* Factored Latent Action World Models. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.16229)] · 🕹️`control`
* **`AnchorWeave`**, World-Consistent Video Generation with Retrieved Local Spatial Memories. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.14941)] · 🧠`memory`
* Adapting VACE for Real-Time Autoregressive Video Diffusion. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.14381)] · ⚡`realtime`
* Train Short, Inference Long: Training-free Horizon Extension for Autoregressive Video Generation. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.14027)] · 🧠`memory`
* A Causal Diffusion Model for Video Reconstruction from Ultra-Low-Bitrate Representations. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.13837)] · ⚡`realtime`
* **`MonarchRT`**, Efficient Attention for Real-Time Video Generation. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.12271)] · ⚡`realtime`
* **`Olaf-World`**, Orienting Latent Actions for Video World Modeling. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.10104)] [[Website](https://showlab.github.io/Olaf-World/)] [[Code](https://github.com/showlab/Olaf-World)] · 🕹️`control`
* Causality in Video Diffusers is Separable from Denoising. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.10095)] · ⚡`realtime`
* **`Hand2World`**, Autoregressive Egocentric Interaction Generation via Free-Space Hand Gestures. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.09600)] [[Website](https://hand2world.github.io/)] · 🌍`systems`
* Rethinking Global Text Conditioning in Diffusion Transformers. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.09268)] · 🕹️`control`
* **`WorldCompass`**, Reinforcement Learning for Long-Horizon World Models. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.09022)] [[Website](https://3d-models.hunyuan.tencent.com/world/)] · 🧠`memory`
* **`MIND`**, Benchmarking Memory Consistency and Action Control in World Models. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.08025)] [[Code](https://github.com/CSU-JPG/MIND)] · 🧠`memory` 📊`benchmarks`
* Geometry-Aware Rotary Position Embedding for Consistent Video World Model. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.07854)] · 🧠`memory`
* Rolling Sink: Bridging Limited-Horizon Training and Open-Ended Testing in Autoregressive Video Diffusion. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.07775)] · 🧠`memory`
* Context Forcing: Consistent Autoregressive Video Generation with Long Context. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.06028)] · 🧠`memory`
* Light Forcing: Accelerating Autoregressive Video Diffusion via Sparse Attention. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.04789)] · ⚡`realtime`
* **`LIVE`**, Long-horizon Interactive Video World Modeling. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.03747)] [[Website](https://junchao-cs.github.io/LIVE-demo/)] · 🌍`systems` 🧠`memory`
* **`Quant VideoGen`**, Auto-Regressive Long Video Generation via 2-Bit KV-Cache Quantization. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.02958)] · ⚡`realtime`
* **`Infinite-World`**, Scaling Interactive World Models to 1000-Frame Horizons via Pose-Free Hierarchical Memory. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.02393)] · 🌍`systems` 🧠`memory`
* Causal Forcing: Autoregressive Diffusion Distillation Done Right for High-Quality Real-Time Interactive Video Generation. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.02214)] · ⚡`realtime`
* Fast Autoregressive Video Diffusion and World Models with Temporal Cache Compression and Sparse Attention. **`arXiv 2026.02`** [[Paper](https://arxiv.org/abs/2602.01801)] · ⚡`realtime`
* Scalable Generative Game Engine: Breaking the Resolution Wall via Hardware-Algorithm Co-Design. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2602.00608)] · 🌍`systems`
* **`TokenTrim`**, Inference-Time Token Pruning for Autoregressive Long Video Generation. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2602.00268)] · 🧠`memory`
* Past- and Future-Informed KV Cache Policy with Salience Estimation in Autoregressive Video Diffusion. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.21896)] · ⚡`realtime`
* **`lingbot-world`**, Advancing Open-source World Models. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.20540)] [[Website](https://technology.robbyant.com/lingbot-world)] [[Code](https://github.com/robbyant/lingbot-world)] · 🌍`systems`
* Efficient Autoregressive Video Diffusion with Dummy Head. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.20499)] · 🧠`memory`
* Entropy-Guided k-Guard Sampling for Long-Horizon Autoregressive Video Generation. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.19488)] · 🧠`memory`
* **`Reward-Forcing`**, Autoregressive Video Generation with Reward Feedback. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.16933)] · ⚡`realtime`
* **`LoL`**, Longer than Longer, Scaling Video Generation to Hour. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.16914)] · ⚡`realtime`
* **`StableWorld`**, Towards Stable and Consistent Long Interactive Video Generation. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.15281)] · 🧠`memory`
* **`S2DiT`**, Sandwich Diffusion Transformer for Mobile Streaming Video Generation. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.12719)] · ⚡`realtime`
* Transition Matching Distillation for Fast Video Generation. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.09881)] · ⚡`realtime`
* Plenoptic Video Generation. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.05239)] · 🧠`memory`
* Learning Latent Action World Models In The Wild. **`arXiv 2026.01`** [[Paper](https://arxiv.org/abs/2601.05230)] · 🕹️`control`
* **`PixVerse R1`**, A Real-Time World Model That Redefines AI Video Generation. **`PixVerse 2026`** [[Blog](https://pixverse.ai/en/blog/pixverse-launches-r1-real-time-world-model)] · 📰`reports` ⚡`realtime`
* **`Happy Oyster`**, Happy Oyster (Kuaile Shenghao): Real-Time Interactive Open-World Model. **`Alibaba 2026`** [[Blog](https://happyoyster.cn/)] · 📰`reports` ⚡`realtime`
* **`TeleWorld`**, Towards Dynamic Multimodal Synthesis with a 4D World Model. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2601.00051)] · 🌍`systems`
* **`TinyHistory`**, Lightweight Video History Embeddings via Two-Stage Context Learning. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.23851)] · 🧠`memory`
* **`LiveTalk`**, Real-Time Multimodal Interactive Video Diffusion via Improved On-Policy Distillation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.23576)] · ⚡`realtime`
* **`Yume-1.5`**, A Text-Controlled Interactive World Generation Model. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.22096)] [[Website](https://stdstu12.github.io/YUME-Project)] [[Code](https://github.com/stdstu12/YUME)] · 🌍`systems` 🕹️`control`
* **`Memorize-and-Generate`**, Towards Long-Term Consistency in Real-Time Video Generation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.18741)] · ⚡`realtime` 🧠`memory`
* **`CustomX`**, Unified Character, Action, and Scene Customization in Video World Models. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.17796)] · 🌍`systems` 🕹️`control`
* **`FrameDiffuser`**, G-Buffer-Conditioned Diffusion for Neural Forward Frame Rendering. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.16670)] · 🧠`memory`
* **`Spatia`**, Video Generation with Updatable Spatial Memory. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.15716)] · 🌍`systems` 🕹️`control` 🧠`memory`
* End-to-End Training for Autoregressive Video Diffusion via Self-Resampling. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.15702)] · 🧠`memory`
* **`MemFlow`**, Flowing Adaptive Memory for Consistent and Efficient Long Video Narratives. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.14699)] · 🧠`memory`
* **`WorldPlay`**, Towards Long-Term Geometric Consistency for Real-Time Interactive World Modeling. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.14614)] [[Website](https://3d-models.hunyuan.tencent.com/world/)] · 🌍`systems` 🕹️`control` ⚡`realtime` 🧠`memory`
* **`LongVie 2`**, Multimodal Controllable Ultra-Long Video World Model. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.13604)] [[Website](https://vchitect.github.io/LongVie2-project/)] · 🕹️`control`
* **`SneakPeek`**, Future-Guided Instructional Streaming Video Generation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.13019)] · ⚡`realtime`
* Endless World: Real-Time 3D-Aware Long Video Generation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.12430)] · ⚡`realtime`
* **`BAgger`**, Backwards Aggregation for Mitigating Drift in Autoregressive Video Diffusion Models. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.12080)] · 🧠`memory`
* **`AutoRefiner`**, Improving Autoregressive Video Diffusion Models via Reflective Refinement Over the Stochastic Sampling Path. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.11203)] · ⚡`realtime`
* **`Astra`**, General Interactive World Model with Autoregressive Denoising. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.08931)] [[Website](https://eternalevan.github.io/Astra-project/)] [[Code](https://github.com/EternalEvan/Astra)] · 🌍`systems`
* **`On Memory`**, A comparison of memory mechanisms in world models. **`World Modeling Workshop 2026`** [[Paper](https://arxiv.org/abs/2512.06983)] · 🧠`memory`
* **`TV2TV`**, A Unified Framework for Interleaved Language and Video Generation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.05103)] · 🕹️`control`
* Deep Forcing: Training-Free Long Video Generation with Deep Sink and Participative Compression. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.05081)] · ⚡`realtime`
* Reward Forcing: Efficient Streaming Video Generation with Rewarded Distribution Matching Distillation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.04678)] · ⚡`realtime`
* **`VideoSSM`**, Autoregressive Long Video Generation with Hybrid State-Space Memory. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.04519)] · 🧠`memory`
* **`EgoLCD`**, Egocentric Video Generation with Long Context Diffusion. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.04515)] · 🧠`memory`
* **`RELIC`**, Interactive Video World Model with Long-Horizon Memory. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.04040)] [[Website](https://relic-worldmodel.github.io/)] · 🌍`systems` 🧠`memory`
* **`WorldPack`**, Compressed Memory Improves Spatial Consistency in Video World Modeling. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.02473)] · 🌍`systems` 🧠`memory`
* **`SpriteHand`**, Real-Time Versatile Hand-Object Interaction with Autoregressive Video Generation. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.01960)] · 🌍`systems` ⚡`realtime`
* **`GrndCtrl`**, Grounding World Models via Self-Supervised Reward Alignment. **`arXiv 2025.12`** [[Paper](https://arxiv.org/abs/2512.01952)] · 🧠`memory`
* **`AVWM`**, Audio-Visual World Models: Towards Multisensory Imagination in Sight and Sound. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2512.00883)] · 🌍`systems`
* **`Hunyuan-GameCraft-2`**, Instruction-following Interactive Game World Model. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.23429)] [[Website](https://hunyuan-gamecraft-2.github.io/)] · 🌍`systems` 🕹️`control`
* **`BIFE`**, Better Interaction, Fewer Errors for Minute-Long Video Generation. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.22973)] · 🧠`memory`
* **`Captain Safari`**, A World Engine. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.22815)] [[Website](https://johnson111788.github.io/open-safari/)] · 🌍`systems`
* **`Inferix`**, A Block-Diffusion based Next-Generation Inference Engine for World Simulation. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.20714)] [[Code](https://github.com/alibaba-damo-academy/Inferix)] · ⚡`realtime`
* **`Infinity-RoPE`**, Action-Controllable Infinite Video Generation Emerges From Autoregressive Self-Rollout. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.20649)] · 🕹️`control`
* Block Cascading: Training Free Acceleration of Block-Causal Video Models. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.20426)] · ⚡`realtime`
* **`UltraViCo`**, Breaking Extrapolation Limits in Video Diffusion Transformers. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.20123)] · 🧠`memory`
* **`In-Video Instructions`**, Visual Signals as Generative Control. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.19401)] · 🕹️`control`
* **`MagicWorld`**, Towards Long-Horizon Stability for Interactive Video World Exploration. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.18886)] [[Website](https://vivocameraresearch.github.io/magicworld/)] [[Code](https://github.com/vivoCameraResearch/Magic-World)] · 🌍`systems` 🧠`memory`
* **`Plan-X`**, Instruct Video Generation via Semantic Planning. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.17986)] · 🕹️`control`
* Recurrent Autoregressive Diffusion: Global Memory Meets Local Attention. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.12940)] · 🧠`memory`
* Adaptive Begin-of-Video Tokens for Autoregressive Video Diffusion Models. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.12099)] · 🧠`memory`
* **`PAN`**, A World Model for General, Interactable, and Long-Horizon World Simulation. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.09057)] · 🌍`systems` 🕹️`control` 🧠`memory`
* Simulating the Visual World with Artificial Intelligence: A Roadmap. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.08585)] [[Website](https://world-model-roadmap.github.io/)] [[Code](https://github.com/ziqihuangg/Awesome-From-Video-Generation-to-World-Model)] · 📚`surveys`
* **`StreamDiffusionV2`**, A Streaming System for Dynamic and Interactive Video Generation. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.07399)] · ⚡`realtime`
* Towards One-step Causal Video Generation via Adversarial Self-Distillation. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.01419)] · ⚡`realtime`
* **`MotionStream`**, Real-Time Video Generation with Interactive Motion Controls. **`arXiv 2025.11`** [[Paper](https://arxiv.org/abs/2511.01266)] · ⚡`realtime`
* Co-Evolving Latent Action World Models. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.26433)] · 🌍`systems` 🕹️`control`
* Generative View Stitching. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.24718)] · 🧠`memory`
* **`Video-As-Prompt`**, Unified Semantic Control for Video Generation. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.20888)] · 🕹️`control`
* A Survey on Cache Methods in Diffusion Models: Toward Efficient Multi-Modal Generation. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.19755)] · 📚`surveys` ⚡`realtime`
* **`World-in-World`**, World Models in a Closed-Loop World. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.18135)] [[Website](https://github.com/World-In-World/world-in-world)] · 📊`benchmarks`
* **`TGT`**, Text-Grounded Trajectories for Locally Controlled Video Generation. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.15104)] · 🕹️`control`
* **`CanvasMAR`**, Improving Masked Autoregressive Video Prediction With Canvas. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.13669)] · ⚡`realtime`
* Stable Video Infinity: Infinite-Length Video Generation with Error Recycling. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.09212)] · 🧠`memory`
* Real-Time Motion-Controllable Autoregressive Video Diffusion. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.08131)] · 🕹️`control` ⚡`realtime`
* **`MorphoSim`**, An Interactive, Controllable, and Editable Language-guided 4D World Simulator. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.04390)] · 🕹️`control`
* Streaming Drag-Oriented Interactive Video Manipulation: Drag Anything, Anytime!. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.03550)] · ⚡`realtime`
* Memory Forcing: Spatio-Temporal Memory for Consistent Scene Generation on Minecraft. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.03198)] · 🌍`systems` 🧠`memory`
* When and Where do Events Switch in Multi-Event Video Generation?. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.03049)] · 🕹️`control`
* **`Self-Forcing++`**, Towards Minute-Scale High-Quality Video Generation. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.02283)] · 🧠`memory`
* **`EvoWorld`**, Evolving Panoramic World Generation with Explicit 3D Memory. **`arXiv 2025.10`** [[Paper](https://arxiv.org/abs/2510.01183)] [[Code](https://github.com/JiahaoPlus/EvoWorld)] · 🌍`systems` 🧠`memory`
* Rolling Forcing: Autoregressive Long Video Diffusion in Real Time. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.25161)] · ⚡`realtime`
* **`SANA-Video`**, Efficient Video Generation with Block Linear Diffusion Transformer. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.24695)] · ⚡`realtime`
* **`Dreamer4`**, Training Agents Inside of Scalable World Models. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.24527)] [[Website](https://danijar.com/dreamer4/)] · 🌍`systems`
* Reinforcement Learning with Inverse Rewards for World Model Post-training. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.23958)] · 🕹️`control`
* **`LongLive`**, Real-time Interactive Long Video Generation. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.22622)] · 🌍`systems` 🕹️`control` ⚡`realtime`
* **`FantasyWorld`**, Geometry-Consistent World Modeling via Unified Video and 3D Prediction. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.21657)] · 🧠`memory`
* **`SAMPO`**, Scale-wise Autoregression with Motion PrOmpt for generative world models. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.15536)] · 🧠`memory`
* **`CausNVS`**, Autoregressive Multi-view Diffusion for Flexible 3D Novel View Synthesis. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.06579)] · 🕹️`control`
* 3D and 4D World Modeling: A Survey. **`arXiv 2025.09`** [[Paper](https://arxiv.org/abs/2509.07996)] · 📚`surveys`
* Mixture of Contexts for Long Video Generation. **`arXiv 2025.08`** [[Paper](https://arxiv.org/abs/2508.21058)] · 🧠`memory`
* **`HERO`**, Hierarchical Extrapolation and Refresh for Efficient World Models. **`arXiv 2025.08`** [[Paper](https://arxiv.org/abs/2508.17588)] · 🧠`memory`
* **`WorldWeaver`**, Generating Long-Horizon Video Worlds via Rich Perception. **`arXiv 2025.08`** [[Paper](https://arxiv.org/abs/2508.15720)] · 🧠`memory`
* **`Matrix-Game 2.0`**, An open-source real-time and streaming interactive world model. **`arXiv 2025.08`** [[Paper](https://arxiv.org/abs/2508.13009)] [[Website](https://matrix-game-v2.github.io/)] · 🌍`systems` ⚡`realtime`
* **`Yan`**, Foundational Interactive Video Generation. **`arXiv 2025.08`** [[Paper](https://arxiv.org/abs/2508.08601)] · 🌍`systems`
* **`Genie 3`**, A new frontier for world models. **`DeepMind 2025`** [[Blog](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/)] · 📰`reports`
* **`Yume`**, An Interactive World Generation Model. **`arXiv 2025.07`** [[Paper](https://arxiv.org/abs/2507.17744)] [[Website](https://stdstu12.github.io/YUME-Project/)] [[Code](https://github.com/stdstu12/YUME)] · 🌍`systems`
* Controllable Video Generation: A Survey. **`arXiv 2025.07`** [[Paper](https://arxiv.org/abs/2507.16869)] · 📚`surveys` 🕹️`control`
* **`Geometry Forcing`**, Marrying Video Diffusion and 3D Representation for Consistent World Modeling. **`arXiv 2025.07`** [[Paper](https://arxiv.org/abs/2507.07982)] [[Website](https://GeometryForcing.github.io)] · 🧠`memory`
* A Survey on Long-Video Storytelling Generation: Architectures, Consistency, and Cinematic Quality. **`arXiv 2025.07`** [[Paper](https://arxiv.org/abs/2507.07202)] · 📚`surveys` 🧠`memory`
* **`StreamDiT`**, Real-Time Streaming Text-to-Video Generation. **`arXiv 2025.07`** [[Paper](https://arxiv.org/abs/2507.03745)] · ⚡`realtime`
* From 2D to 3D Cognition: A Brief Survey of General World Models. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.20134)] · 📚`surveys`
* **`VMem`**, Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.18903)] · 🧠`memory`
* From Virtual Games to Real-World Play. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.18901)] · 🌍`systems`
* **`Matrix-Game`**, Interactive World Foundation Model. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.18701)] [[Code](https://github.com/SkyworkAI/Matrix-Game)] · 🌍`systems`
* **`UNIVERSE`**, Adapting Vision-Language Models for Evaluating World Models. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.17967)] · 📊`benchmarks`
* **`Hunyuan-GameCraft`**, High-dynamic Interactive Game Video Generation with Hybrid History Condition. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.17201)] · 🌍`systems`
* **`PlayerOne`**, Egocentric World Simulator. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.09995)] · 🌍`systems`
* Autoregressive Adversarial Post-Training for Real-Time Interactive Video Generation. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.09350)] · 🌍`systems` ⚡`realtime`
* Self Forcing: Bridging the Train-Test Gap in Autoregressive Video Diffusion. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.08009)] · ⚡`realtime`
* Video World Models with Long-term Spatial Memory. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.05284)] [[Website](https://spmem.github.io/)] · 🌍`systems` 🕹️`control` 🧠`memory`
* Context as Memory: Scene-Consistent Interactive Long Video Generation with Memory Retrieval. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.03141)] · 🌍`systems` 🧠`memory`
* Playing with Transformer at 30+ FPS via Next-Frame Diffusion. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.01380)] · ⚡`realtime`
* **`DeepVerse`**, 4D Autoregressive Video Generation as a World Model. **`arXiv 2025.06`** [[Paper](https://arxiv.org/abs/2506.01103)] · 🌍`systems` 🕹️`control`
* Toward Memory-Aided World Models: Benchmarking via Spatial Consistency. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.22976)] [[Code](https://github.com/Kevin-lkw/LoopNav)] · 🧠`memory` 📊`benchmarks`
* **`StateSpaceDiffuser`**, Bringing Long Context to Diffusion World Models. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.22246)] · 🧠`memory`
* **`VRAG`**, Learning World Models for Interactive Video Generation. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.21996)] · 🌍`systems`
* Long-Context State-Space Video World Models. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.20171)] [[Website](https://ryanpo.com/ssm_wm)] · 🌍`systems`
* **`Vid2World`**, Crafting Video Diffusion Models to Interactive World Models. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.14357)] [[Website](http://knightnemo.github.io/vid2world/)] · 🌍`systems`
* **`MAGI-1`**, Autoregressive Video Generation at Scale. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.13211)] · ⚡`realtime`
* Generative Pre-trained Autoregressive Diffusion Transformer. **`arXiv 2025.05`** [[Paper](https://arxiv.org/abs/2505.07344)] · 🧠`memory`
* A Survey of Interactive Generative Video. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.21853)] · 📚`surveys`
* **`SkyReels-V2`**, Infinite-length Film Generative Model. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.13074)] · ⚡`realtime`
* Frame Context Packing and Drift Prevention in Next-Frame-Prediction Video Diffusion Models. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.12626)] · 🧠`memory`
* **`WorldMem`**, Long-term Consistent World Simulation with Memory. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.12369)] · 🌍`systems` 🧠`memory`
* **`MineWorld`**, a Real-Time and Open-Source Interactive World Model on Minecraft. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.08388)] · 🌍`systems` ⚡`realtime`
* One-Minute Video Generation with Test-Time Training. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.05298)] · ⚡`realtime`
* Exploration-Driven Generative Interactive Environments. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.02515)] · 🌍`systems`
* **`AnimeGamer`**, Infinite Anime Life Simulation with Next Game State Prediction. **`arXiv 2025.04`** [[Paper](https://arxiv.org/abs/2504.01014)] · 🌍`systems` 🕹️`control`
* Exploring the Evolution of Physics Cognition in Video Generation: A Survey. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.21765)] [[Code](https://github.com/minnie-lin/Awesome-Physics-Cognition-based-Video-Generation)] · 📚`surveys`
* Model as a Game: On Numerical and Spatial Consistency for Generative Games. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.21172)] · 🌍`systems` 🧠`memory`
* Long-Context Autoregressive Video Modeling with Next-Frame Prediction. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.19325)] [[Website](https://farlongctx.github.io/)] [[Code](https://github.com/showlab/FAR)] · 🧠`memory`
* **`AdaWorld`**, Learning Adaptable World Models with Latent Actions. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.18938)] [[Website](https://adaptable-world-model.github.io/)] · 🌍`systems` 🕹️`control`
* Long Context Tuning for Video Generation. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.10589)] · 🧠`memory`
* Inter-environmental world modeling for continuous and compositional dynamics. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.09911)] · 🕹️`control`
* Error Analyses of Auto-Regressive Video Diffusion Models: A Unified Framework. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.10704)] · 🧠`memory`
* Toward Stable World Models: Measuring and Addressing World Instability in Generative Environments. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.08122)] · 📊`benchmarks`
* **`AR-Diffusion`**, Asynchronous Video Generation with Auto-Regressive Diffusion. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.07418)] · ⚡`realtime`
* Simulating the Real World: A Unified Survey of Multimodal Generative Models. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.04641)] [[Code](https://github.com/ALEEEHU/World-Simulator)] · 📚`surveys`
* **`Gen3C`**, 3D-Informed World-Consistent Video Generation with Precise Camera Control. **`arXiv 2025.03`** [[Paper](https://arxiv.org/abs/2503.03751)] · 🕹️`control` 🧠`memory`
* Next Block Prediction: Video Generation via Semi-Autoregressive Modeling. **`arXiv 2025.02`** [[Paper](https://arxiv.org/abs/2502.07737)] · ⚡`realtime`
* **`PlaySlot`**, Learning Inverse Latent Dynamics for Controllable Object-Centric Video Prediction and Planning. **`arXiv 2025.02`** [[Paper](https://arxiv.org/abs/2502.07600)] · 🕹️`control`
* Pre-Trained Video Generative Models as World Simulators. **`arXiv 2025.02`** [[Paper](https://arxiv.org/abs/2502.07825)] · 🌍`systems`
* History-Guided Video Diffusion. **`arXiv 2025.02`** [[Paper](https://arxiv.org/abs/2502.06764)] · 🧠`memory`
* Taming Teacher Forcing for Masked Autoregressive Video Generation. **`arXiv 2025.01`** [[Paper](https://arxiv.org/abs/2501.12389)] · ⚡`realtime`
* Generative Physical AI in Vision: A Survey. **`arXiv 2025.01`** [[Paper](https://arxiv.org/abs/2501.10928)] · 📚`surveys`
* **`GameFactorly`**, Creating New Games with Generative Interactive Videos. **`arXiv 2025.01`** [[Paper](https://arxiv.org/abs/2501.08325)] · 🌍`systems`
* Diffusion Adversarial Post-Training for One-Step Video Generation. **`arXiv 2025.01`** [[Paper](https://arxiv.org/abs/2501.08316)] · ⚡`realtime`
* **`MSC`**, Multi-Scale Spatio-Temporal Causal Attention for Autoregressive Video Diffusion. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.09828)] · ⚡`realtime`
* **`GenEx`**, Generating an Explorable World. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.09624)] · 🌍`systems`
* **`Owl-1`**, Omni World Model for Consistent Long Video Generation. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.09600)] · 🧠`memory`
* Video Creation by Demonstration. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.09551)] · ⚡`realtime`
* From Slow Bidirectional to Fast Autoregressive Video Diffusion Models. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.07772)] · ⚡`realtime`
* **`ACDiT`**, Interpolating Autoregressive Conditional Modeling and Diffusion Transformer. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.07720)] · 🧠`memory`
* **`Genie 2`**, A large-scale foundation world model. **`DeepMind 2024`** [[Blog](https://deepmind.google/discover/blog/genie-2-a-large-scale-foundation-world-model/)] · 📰`reports`
* The Matrix: Infinite-Horizon World Generation with Real-Time Moving Control. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.03568)] · 🌍`systems` 🕹️`control` ⚡`realtime`
* Playable Game Generation. **`arXiv 2024.12`** [[Paper](https://arxiv.org/abs/2412.00887)] · 🌍`systems`
* **`Ca2-VDM`**, Efficient Autoregressive Video Diffusion Model with Causal Generation and Cache Sharing. **`arXiv 2024.11`** [[Paper](https://arxiv.org/abs/2411.16375)] · ⚡`realtime`
* Understanding World or Predicting Future? A Comprehensive Survey of World Models. **`arXiv 2024.11`** [[Paper](https://arxiv.org/abs/2411.14499)] · 📚`surveys`
* **`EgoVid-5M`**, A Large-Scale Video-Action Dataset for Egocentric Video Generation. **`arXiv 2024.11`** [[Paper](https://arxiv.org/abs/2411.08380)] · 🗂️`datasets`
* **`GameGen-X`**, Interactive Open-world Game Video Generation. **`arXiv 2024.11`** [[Paper](https://arxiv.org/abs/2411.00769)] · 🌍`systems` 🕹️`control`
* **`Oasis`**, A Universe in a Transformer. **`Decart & Etched 2024`** [[Blog](https://oasis-model.github.io/)] · 📰`reports`
* **`SlowFast-VGen`**, Slow-Fast Learning for Action-Driven Long Video Generation. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2410.23277)] · 🌍`systems` 🕹️`control`
* **`ARLON`**, Boosting Diffusion Transformers with Autoregressive Models for Long Video Generation. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2410.20502)] · 🧠`memory`
* Progressive Autoregressive Video Diffusion Models. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2410.08151)] · 🧠`memory`
* Pyramidal Flow Matching for Efficient Video Generative Modeling. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2410.05954)] · ⚡`realtime`
* **`ACDC`**, Autoregressive Coherent Multimodal Generation using Diffusion Correction. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2410.04721)] · 🧠`memory`
* **`Loong`**, Generating Minute-level Long Videos with Autoregressive Language Models. **`arXiv 2024.10`** [[Paper](https://arxiv.org/abs/2410.02757)] · ⚡`realtime`
* Learning Generative Interactive Environments By Trained Agent Exploration. **`arXiv 2024.09`** [[Paper](https://arxiv.org/abs/2409.06445)] · 🌍`systems`
* Diffusion Models Are Real-Time Game Engines. **`arXiv 2024.08`** [[Paper](https://arxiv.org/abs/2408.14837)] · 🌍`systems` ⚡`realtime`
* Real-Time Video Generation with Pyramid Attention Broadcast. **`arXiv 2024.08`** [[Paper](https://arxiv.org/abs/2408.12588)] · ⚡`realtime`
* **`MovieDreamer`**, Hierarchical Generation for Coherent Long Visual Sequence. **`arXiv 2024.07`** [[Paper](https://arxiv.org/abs/2407.16655)] · 🧠`memory`
* **`Streetscapes`**, Large-scale Consistent Street View Generation Using Autoregressive Video Diffusion. **`arXiv 2024.07`** [[Paper](https://arxiv.org/abs/2407.13759)] · 🧠`memory`
* Diffusion Forcing: Next-token Prediction Meets Full-Sequence Diffusion. **`arXiv 2024.07`** [[Paper](https://arxiv.org/abs/2407.01392)] · ⚡`realtime`
* From Efficient Multimodal Models to World Models: A Survey. **`arXiv 2024.06`** [[Paper](https://arxiv.org/abs/2407.00118)] · 📚`surveys`
* **`Pandora`**, Towards General World Model with Natural Language Actions and Video States. **`arXiv 2024.06`** [[Paper](https://arxiv.org/abs/2406.09455)] [[Code](https://github.com/maitrix-org/Pandora)] · 🌍`systems` 🕹️`control`
* Motion Consistency Model: Accelerating Video Diffusion with Disentangled Motion-Appearance Distillation. **`arXiv 2024.06`** [[Paper](https://arxiv.org/abs/2406.06890)] · ⚡`realtime` 🧠`memory`
* Lifelong Learning of Video Diffusion Models From a Single Video Stream. **`arXiv 2024.06`** [[Paper](https://arxiv.org/abs/2406.04814)] · ⚡`realtime`
* **`SF-V`**, Single Forward Video Generation Model. **`arXiv 2024.06`** [[Paper](https://arxiv.org/abs/2406.04324)] · ⚡`realtime`
* Streaming Video Diffusion: Online Video Editing with Diffusion Models. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.19726)] · ⚡`realtime`
* Looking Backward: Streaming Video-to-Video Translation with Feature Banks. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.15757)] · ⚡`realtime`
* iVideoGPT: Interactive VideoGPTs are Scalable World Models. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.15223)] · 🌍`systems`
* **`FIFO-Diffusion`**, Generating Infinite Videos from Text without Training. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.11473)] · 🧠`memory`
* From Sora What We Can See: A Survey of Text-to-Video Generation. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.10674)] · 📚`surveys`
* Is Sora a World Simulator? A Comprehensive Survey on General World Models and Beyond. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.03520)] [[Code](https://github.com/GigaAI-research/General-World-Models-Survey)] · 📚`surveys`
* Video Diffusion Models: A Survey. **`arXiv 2024.05`** [[Paper](https://arxiv.org/abs/2405.03150)] · 📚`surveys`
* A Survey on Long Video Generation: Challenges, Methods, and Prospects. **`arXiv 2024.03`** [[Paper](https://arxiv.org/abs/2403.16407)] · 📚`surveys`
* **`StreamingT2V`**, Consistent, Dynamic, and Extendable Long Video Generation from Text. **`arXiv 2024.03`** [[Paper](https://arxiv.org/abs/2403.14773)] · 🧠`memory`
* Sora as a World Model? A Complete Survey on Text-to-Video Generation. **`arXiv 2024.03`** [[Paper](https://arxiv.org/abs/2403.05131)] · 📚`surveys`
* **`Sora`**, A Review on Background, Technology, Limitations, and Opportunities of Large Vision Models. **`arXiv 2024.02`** [[Paper](https://arxiv.org/abs/2402.17177)] · 📚`surveys`
* **`Genie`**, Generative Interactive Environments. **`DeepMind`** [[Paper](https://arxiv.org/abs/2402.15391)] [[Blog](https://sites.google.com/view/genie-2024/home)] · 🌱`foundations`
* **`Sora`**, Video generation models as world simulators. **`OpenAI 2024`** [[Blog](https://openai.com/index/video-generation-models-as-world-simulators/)] · 📰`reports`
* Rolling Diffusion Models. **`arXiv 2024.02`** [[Paper](https://arxiv.org/abs/2402.09470)] · ⚡`realtime`
* **`InteractiveVideo`**, User-Centric Controllable Video Generation with Synergistic Multimodal Instructions. **`arXiv 2024.02`** [[Paper](https://arxiv.org/abs/2402.03040)] · 🕹️`control`
* A Survey on Future Frame Synthesis: Bridging Deterministic and Generative Approaches. **`arXiv 2024.01`** [[Paper](https://arxiv.org/abs/2401.14718)] · 📚`surveys`
* Learning to Act without Actions. **`arXiv 2023.12`** [[Paper](https://arxiv.org/abs/2312.10812)] · 🕹️`control`
* Learning Interactive Real-World Simulators. **`arXiv 2023.10`** [[Paper](https://arxiv.org/abs/2310.06114)] · 🌍`systems` 🕹️`control`
* Language Model Beats Diffusion -- Tokenizer is Key to Visual Generation. **`arXiv 2023.10`** [[Paper](https://arxiv.org/abs/2310.05737)] · ⚡`realtime`
* Temporally Consistent Transformers for Video Generation. **`arXiv 2022.10`** [[Paper](https://arxiv.org/abs/2210.02396)] · 🧠`memory`
* Playable Environments: Video Manipulation in Space and Time. **`arXiv 2022.03`** [[Paper](https://arxiv.org/abs/2203.01914)] · 🌱`foundations`
* Playable Video Generation. **`arXiv 2021.01`** [[Paper](https://arxiv.org/abs/2101.12195)] · 🌱`foundations`
* Learning to Simulate Dynamic Environments With GameGAN. **`arXiv 2020.05`** [[Paper](https://arxiv.org/abs/2005.12126)] · 🌱`foundations`
* Learning what you can do before doing anything. **`arXiv 2018.06`** [[Paper](https://arxiv.org/abs/1806.09655)] · 🕹️`control`
* World Models. **`NIPS 2018 Oral`** [[Paper](https://arxiv.org/abs/1803.10122)] [[Website](https://worldmodels.github.io/)] · 🌱`foundations`
<!-- END:LIST -->

---

## System Comparison

What separates this list from a bibliography: for every system read in depth, the axes that decide whether you can actually act inside it. `Action` is a normalized summary of the paper's own action space; `Memory` is the mechanism that carries state across steps, not a quality judgement. `—` means the paper does not report the value.

These are notes taken while reading, not measurements. Frame rates are the numbers the authors claim on the hardware they claim them on, and are not comparable across rows without reading the setups. Check anything you intend to rely on against the paper.

<!-- BEGIN:TABLE -->
| System | Date | Backbone | Action | FPS | Memory | Open |
| --- | --- | --- | --- | --- | --- | --- |
| [MASS](https://arxiv.org/abs/2608.06257) | 2026-08 | other | embodied | — | other | no |
| [HelloWorld](https://arxiv.org/abs/2608.05070) | 2026-08 | bidir. diffusion | keyboard + camera + language | 24 | spatial (recon) | no |
| [StatePlay](https://arxiv.org/abs/2607.26754) | 2026-07 | bidir. diffusion | other | — | other | no |
| [Wonder](https://arxiv.org/abs/2607.26037) | 2026-07 | causal diffusion | keyboard + camera | 16 | hybrid: retrieval+context | no |
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
| [MemCam](https://arxiv.org/abs/2603.26193) | 2026-03 | bidir. diffusion | camera | — | retrieval | yes |
| [ShotStream](https://arxiv.org/abs/2603.25746) | 2026-03 | causal diffusion | language | 16 | context | yes |
| [WorldCam](https://arxiv.org/abs/2603.16871) | 2026-03 | AR + diffusion | keyboard + mouse + camera | — | retrieval | no |

_Most recent systems only. Full table, with horizons and verbatim action spaces: [docs/comparison.md](docs/comparison.md)._
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
