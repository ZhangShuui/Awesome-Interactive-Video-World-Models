"""The inbox round trip: feed -> report -> ticks -> records."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_issue_selections as apply_mod  # noqa: E402
import arxiv_candidates as ac  # noqa: E402
import triage  # noqa: E402

FEED = Path(__file__).resolve().parent / "data" / "sample-feed.xml"
SECTIONS = {s["key"] for s in json.loads((ROOT / "data" / "sections.json").read_text())}


def run_candidates(*extra, output):
    cmd = [sys.executable, str(ROOT / "scripts" / "arxiv_candidates.py"),
           "--feed-file", str(FEED), "--output", str(output), *extra]
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


class TestFeedParsing(unittest.TestCase):
    def test_parses_the_fixture(self):
        papers = ac.parse_feed(FEED.read_bytes())
        self.assertTrue(papers)
        for paper in papers:
            self.assertRegex(paper["id"], r"^\d{4}\.\d{4,5}$")
            self.assertTrue(paper["title"])
            self.assertRegex(paper["date"], r"^\d{4}-\d{2}-\d{2}$")


class TestFilters(unittest.TestCase):
    def test_off_topic_is_dropped(self):
        self.assertTrue(ac.OFF_TOPIC_RE.search(
            "A Systems Blueprint for Economic World Models"))

    def test_text_only_world_models_are_dropped(self):
        self.assertIsNone(ac.VISUAL_GATE_RE.search(
            "EnvACE: Internalizing Environment Dynamics for Agentic Reinforcement Learning"))

    def test_video_papers_pass_the_gate(self):
        self.assertIsNotNone(ac.VISUAL_GATE_RE.search(
            "Matrix-Game 2.0: streaming interactive video generation"))

    def test_zero_criteria_efficiency_papers_are_not_dropped(self):
        """The admission gate must consult the escape hatch, not just `met`."""
        title = "SPADE: An Input-Adaptive Sparse Attention Engine for Fast Video Diffusion Models"
        abstract = ("Video diffusion transformers pay quadratic self-attention cost, "
                    "making inference prohibitive at video-token scales.")
        section, met, _ = triage.triage(title, abstract)
        self.assertEqual(met, 0)
        admitted = (met > 0 or section in ("surveys", "benchmarks")
                    or triage.is_efficiency_substrate(title, abstract))
        self.assertTrue(admitted)


class TestRoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.papers = self.tmp / "papers.jsonl"
        self.papers.write_text("", encoding="utf-8")
        self.report = self.tmp / "inbox.md"

    def _tick_first(self, section=None):
        lines = self.report.read_text(encoding="utf-8").splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.startswith("- [ ]"):
                line = line.replace("- [ ]", "- [x]", 1)
                if section:
                    head, _, rest = line.partition("`")
                    _, _, tail = rest.partition("`")
                    line = f"{head}`{section}`{tail}"
                lines[i] = line
                break
        self.report.write_text("".join(lines), encoding="utf-8")

    def test_ticked_candidate_becomes_a_record(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._tick_first()
        body = self.report.read_text(encoding="utf-8")
        records, warnings = apply_mod.parse_selections(body, SECTIONS)
        self.assertEqual(len(records), 1)
        self.assertFalse(warnings)
        rec = records[0]
        self.assertIn(rec["id"], rec["links"]["paper"])
        self.assertIn(rec["section"], SECTIONS)
        self.assertEqual(rec["section_source"], "curated")

    def test_maintainer_section_edit_wins(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._tick_first(section="systems")
        records, warnings = apply_mod.parse_selections(
            self.report.read_text(encoding="utf-8"), SECTIONS)
        self.assertEqual(records[0]["section"], "systems")
        self.assertFalse(warnings)

    def test_unknown_section_falls_back_and_warns(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._tick_first(section="nonsense")
        records, warnings = apply_mod.parse_selections(
            self.report.read_text(encoding="utf-8"), SECTIONS)
        self.assertEqual(len(records), 1)
        self.assertIn(records[0]["section"], SECTIONS)
        self.assertTrue(warnings)

    def test_refresh_preserves_ticks(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._tick_first()
        before = ac.checked_ids(self.report.read_text(encoding="utf-8"))
        refreshed = self.tmp / "inbox2.md"
        run_candidates("--papers", str(self.papers),
                       "--existing-issue-body", str(self.report), output=refreshed)
        self.assertEqual(ac.checked_ids(refreshed.read_text(encoding="utf-8")), before)

    def test_known_papers_are_not_proposed_again(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        first = ac.parse_feed(FEED.read_bytes())[0]
        self.papers.write_text(json.dumps({
            "id": first["id"], "title": first["title"], "section": "systems",
            "links": {"paper": f"https://arxiv.org/abs/{first['id']}"}, "attrs": {},
        }) + "\n", encoding="utf-8")
        again = self.tmp / "inbox3.md"
        run_candidates("--papers", str(self.papers), output=again)
        self.assertNotIn(first["id"], again.read_text(encoding="utf-8"))

    def test_apply_is_idempotent(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._tick_first()
        args = [sys.executable, str(ROOT / "scripts" / "apply_issue_selections.py"),
                "--issue-body", str(self.report), "--papers", str(self.papers)]
        first = subprocess.run(args, capture_output=True, text=True, check=True)
        second = subprocess.run(args, capture_output=True, text=True, check=True)
        self.assertEqual(first.stdout.strip(), "1")
        self.assertEqual(second.stdout.strip(), "0")
        lines = [l for l in self.papers.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(lines), 1)


if __name__ == "__main__":
    unittest.main()
