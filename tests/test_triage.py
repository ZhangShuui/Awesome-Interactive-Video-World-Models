"""Rules that have already been wrong once, pinned so they stay fixed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import triage  # noqa: E402


class TestSuggestSection(unittest.TestCase):
    def test_title_beats_abstract(self):
        # The abstract is all about memory; the title says the paper is a cache.
        section = triage.suggest_section(
            "WorldCache: Content-Aware Caching for Accelerated Video World Models",
            "We keep long-term memory consistent across revisits using retrieval.")
        self.assertEqual(section, "realtime")

    def test_memory_efficient_is_about_vram(self):
        section = triage.suggest_section(
            "Towards Memory-Efficient Autoregressive Video Generation", "")
        self.assertEqual(section, "realtime")

    def test_real_memory_paper_still_routes_to_memory(self):
        section = triage.suggest_section(
            "FadeMem: Distance-Aware Memory Consolidation for Video Diffusion", "")
        self.assertEqual(section, "memory")

    def test_dataset_needs_the_title(self):
        # Every method paper names its training data; that must not make it a dataset.
        method = triage.suggest_section(
            "CanvasMAR: Improving Masked Autoregressive Video Prediction",
            "We train on a large dataset of gameplay videos and a second dataset.")
        self.assertNotEqual(method, "datasets")
        real = triage.suggest_section(
            "EgoVid-5M: A Large-Scale Video-Action Dataset", "")
        self.assertEqual(real, "datasets")

    def test_serving_paper_is_not_memory(self):
        section = triage.suggest_section(
            "Stateful Worlds, Stateless Elasticity: Exact-State Serving for World Models", "")
        self.assertEqual(section, "realtime")


class TestTriage(unittest.TestCase):
    def test_all_three_criteria_reach_the_main_list(self):
        section, met, _ = triage.triage(
            "Matrix-Game 2.0: An Open-Source Real-Time Interactive World Model",
            "Frame-level keyboard and mouse actions drive an autoregressive causal "
            "diffusion model that streams at 25 FPS with long-term memory of the scene.")
        self.assertEqual(section, "systems")
        self.assertEqual(met, 3)

    def test_survey_wins_over_criteria(self):
        section, _, _ = triage.triage(
            "A Survey of Interactive Generative Video",
            "Real-time action-conditioned streaming with persistent memory.")
        self.assertEqual(section, "surveys")

    def test_benchmark_wins_over_criteria(self):
        section, _, _ = triage.triage(
            "WorldMark: A Unified Benchmark Suite for Interactive Video World Models",
            "Real-time action-conditioned streaming with persistent memory.")
        self.assertEqual(section, "benchmarks")

    def test_partial_evidence_lands_in_a_supporting_section(self):
        section, met, _ = triage.triage(
            "Rolling Diffusion Models", "A progressive noise schedule over frames.")
        self.assertNotEqual(section, "systems")
        self.assertLess(met, 3)


class TestEfficiencySubstrate(unittest.TestCase):
    """Real papers the criteria gate dropped at 0/3 while the realtime section
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
            section, _, _ = triage.triage(title, abstract)
            self.assertEqual(section, "realtime", title)

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


if __name__ == "__main__":
    unittest.main()
