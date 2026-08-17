"""Rules that have already been wrong once, pinned so they stay fixed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sources  # noqa: E402
import triage  # noqa: E402


class TestSuggestTags(unittest.TestCase):
    def test_title_beats_abstract(self):
        # The abstract is all about memory; the title says the paper is a cache.
        tags = triage.suggest_tags(
            "WorldCache: Content-Aware Caching for Accelerated Video World Models",
            "We keep long-term memory consistent across revisits using retrieval.")
        self.assertEqual(tags, ["realtime"])

    def test_memory_efficient_is_about_vram(self):
        tags = triage.suggest_tags(
            "Towards Memory-Efficient Autoregressive Video Generation", "")
        self.assertEqual(tags, ["realtime"])

    def test_real_memory_paper_still_routes_to_memory(self):
        tags = triage.suggest_tags(
            "FadeMem: Distance-Aware Memory Consolidation for Video Diffusion", "")
        self.assertEqual(tags, ["memory"])

    def test_dataset_needs_the_title(self):
        # Every method paper names its training data; that must not make it a dataset.
        method = triage.suggest_tags(
            "CanvasMAR: Improving Masked Autoregressive Video Prediction",
            "We train on a large dataset of gameplay videos and a second dataset.")
        self.assertNotIn("datasets", method)
        real = triage.suggest_tags(
            "EgoVid-5M: A Large-Scale Video-Action Dataset", "")
        self.assertIn("datasets", real)

    def test_serving_paper_is_not_memory(self):
        tags = triage.suggest_tags(
            "Stateful Worlds, Stateless Elasticity: Exact-State Serving for World Models", "")
        self.assertEqual(tags, ["realtime"])


class TestTriage(unittest.TestCase):
    def test_all_three_criteria_reach_the_main_list(self):
        tags, met, _ = triage.triage(
            "Matrix-Game 2.0: An Open-Source Real-Time Interactive World Model",
            "Frame-level keyboard and mouse actions drive an autoregressive causal "
            "diffusion model that streams at 25 FPS with long-term memory of the scene.")
        # `systems` first, then what the title says the paper is about. It is a
        # real-time paper as well, and under sections that was unsayable.
        self.assertEqual(tags, ["systems", "realtime"])
        self.assertEqual(met, 3)

    def test_survey_wins_over_criteria(self):
        tags, _, _ = triage.triage(
            "A Survey of Interactive Generative Video",
            "Real-time action-conditioned streaming with persistent memory.")
        self.assertEqual(tags, ["surveys"])

    def test_benchmark_wins_over_criteria(self):
        tags, _, _ = triage.triage(
            "WorldMark: A Unified Benchmark Suite for Interactive Video World Models",
            "Real-time action-conditioned streaming with persistent memory.")
        self.assertEqual(tags, ["benchmarks"])

    def test_partial_evidence_does_not_earn_the_systems_tag(self):
        tags, met, _ = triage.triage(
            "Rolling Diffusion Models", "A progressive noise schedule over frames.")
        self.assertNotIn("systems", tags)
        self.assertLess(met, 3)

    def test_a_title_that_claims_two_things_gets_two_tags(self):
        """The whole point of tags. Under sections this was a coin flip that
        emptied whichever list lost."""
        tags, _, _ = triage.triage(
            "Action-Conditioned Video World Models via Few-Step Distillation",
            "A progressive noise schedule over frames.")
        self.assertEqual(tags, ["control", "realtime"])

    def test_a_system_keeps_the_tags_for_what_it_is_about(self):
        tags, met, _ = triage.triage(
            "Incantation: Natural Language as the Action Interface for "
            "Multi-Entity Video World Models",
            "Per-entity free-form sentences drive an autoregressive causal model "
            "that streams in real time with persistent long-term memory.")
        self.assertEqual(met, 3)
        self.assertEqual(tags[0], "systems")
        self.assertIn("control", tags)


class TestEfficiencySubstrate(unittest.TestCase):
    """Real papers the criteria gate dropped at 0/3 while the realtime list
    already held a dozen of exactly their genre."""

    RECOVERED = [
        ("SPADE: An Input-Adaptive Sparse Attention Engine for Fast Video Diffusion Models",
         "Video diffusion transformers (vDiTs) generate high quality but pay quadratic "
         "self-attention cost, making inference prohibitive at video-token scales."),
        ("Token Radius Attention for Efficient Video Generation",
         "Video Diffusion Transformers enable high-fidelity generation but incur "
         "quadratic cost from dense 3D self-attention."),
        ("Adaptive-WAM: Quality-Guided Early-Exit Planning from Intermediate Video-Diffusion",
         "Large video diffusion models provide rich spatiotemporal priors, but existing "
         "world-action models inherit the cost of iterative future-video generation."),
    ]

    def test_they_still_meet_no_criterion(self):
        # If this ever starts failing the escape hatch is no longer what saves them.
        for title, abstract in self.RECOVERED:
            _, met, _ = triage.triage(title, abstract)
            self.assertEqual(met, 0, title)

    def test_the_escape_hatch_admits_them(self):
        for title, abstract in self.RECOVERED:
            self.assertTrue(triage.is_efficiency_substrate(title, abstract), title)

    def test_they_land_in_realtime(self):
        for title, abstract in self.RECOVERED:
            tags, _, _ = triage.triage(title, abstract)
            self.assertIn("realtime", tags, title)

    def test_efficiency_without_video_is_not_admitted(self):
        for title, abstract in [
            ("SnapFusion: Text-to-Image Diffusion on Mobile Devices in Two Seconds",
             "We accelerate image diffusion with step distillation and sparse attention."),
            ("Efficient KV-Cache Compression for Long-Context Language Models",
             "We halve the KV cache of a 70B model with negligible perplexity loss."),
        ]:
            self.assertFalse(triage.is_efficiency_substrate(title, abstract), title)

    def test_video_without_efficiency_is_not_admitted(self):
        self.assertFalse(triage.is_efficiency_substrate(
            "A Photorealistic Video Dataset of Kitchen Scenes",
            "We release 500 hours of annotated kitchen video."))


class TestExtractName(unittest.TestCase):
    def test_system_names(self):
        for title, expected in [
            ("Matrix-Game 2.0: An open-source world model", "Matrix-Game 2.0"),
            ("Genie: Generative Interactive Environments", "Genie"),
            ("INSPATIO-WORLD: A Real-Time 4D World Simulator", "INSPATIO-WORLD"),
            ("MBench: A Comprehensive Benchmark", "MBench"),
        ]:
            self.assertEqual(triage.extract_name(title), expected, title)

    def test_sentences_are_not_names(self):
        for title in [
            "Toward Stable World Models: Measuring and Addressing Instability",
            "Out of Sight, Out of Mind? Evaluating State Evolution",
            "Pre-Trained Video Generative Models as World Simulators",
            "Learning Latent Action World Models In The Wild",
        ]:
            self.assertIsNone(triage.extract_name(title), title)



class TestLanguageAsAnAction(unittest.TestCase):
    """Typing at a world is a way of acting in it.

    The action criterion was written around joysticks -- keyboard, mouse,
    camera trajectory, latent action -- and a paper whose interface is a
    sentence matched none of it. The systems in the list that work this way
    (Incantation, Pandora, LongLive) all scored on some *other* phrase in their
    abstracts, so the gap stayed invisible until someone asked why the control
    list had no prompt-controlled papers in it.
    """

    def test_a_language_interface_counts_as_an_action(self):
        evidence = triage.criteria_evidence(
            "Incantation: Natural Language as the Action Interface for "
            "Multi-Entity Video World Models",
            "Each entity is driven by its own free-form sentence at 0.25s "
            "granularity.")
        self.assertTrue(evidence["action"])

    def test_a_paper_that_is_only_an_interface_now_reaches_the_inbox(self):
        """0/3 is dropped before a human ever sees it -- see sources.proposal."""
        title = "In-Video Instructions: Visual Signals as Generative Control"
        abstract = ("We interpret visual signals embedded within the frames as "
                    "instructions, a paradigm we term In-Video Instruction. In "
                    "contrast to prompt-based control, which is global and coarse, "
                    "this encodes user guidance directly into the visual domain, "
                    "assigning distinct instructions to different objects.")
        propose, tags, met, _ = sources.proposal(title, abstract)
        self.assertTrue(propose)
        self.assertEqual(tags, ["control"])
        self.assertGreater(met, 0)

    def test_a_caption_is_not_an_action(self):
        """The guard on all of this.

        Text-to-video is an enormous literature and none of it belongs here. If
        a global prompt written before generation starts scored on the action
        criterion, every one of those papers would arrive in the inbox at 2/3.
        """
        evidence = triage.criteria_evidence(
            "Photorealistic Text-to-Video Generation with Cascaded Diffusion",
            "Given a text prompt, our text-guided model synthesises a "
            "high-resolution video clip conditioned on the caption.")
        self.assertFalse(evidence["action"])

    def test_a_control_paper_that_never_says_controllable_still_lands_there(self):
        """The title rules were a list of joysticks, so a paper about the
        conditioning channel itself fell through to whatever the abstract
        happened to score -- `memory` here, on "consistency" and "retrieval"."""
        tags, _, _ = triage.triage(
            "Video-As-Prompt: Unified Semantic Control for Video Generation",
            "We reframe the problem as in-context generation, using a reference "
            "video as a direct semantic prompt that guides a frozen video "
            "diffusion transformer, with position embeddings for robust context "
            "retrieval and consistency across conditions.")
        self.assertEqual(tags, ["control"])

if __name__ == "__main__":
    unittest.main()
