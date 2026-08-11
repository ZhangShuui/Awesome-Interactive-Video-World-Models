"""The inbox round trip: feed -> report -> ticks -> records."""
import contextlib
import email.message
import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_issue_selections as apply_mod  # noqa: E402
import arxiv_candidates as ac  # noqa: E402
import sources  # noqa: E402
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
        self.assertTrue(sources.OFF_TOPIC_RE.search(
            "A Systems Blueprint for Economic World Models"))

    def test_text_only_world_models_are_dropped(self):
        self.assertIsNone(sources.VISUAL_GATE_RE.search(
            "EnvACE: Internalizing Environment Dynamics for Agentic Reinforcement Learning"))

    def test_video_papers_pass_the_gate(self):
        self.assertIsNotNone(sources.VISUAL_GATE_RE.search(
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


class TestRateLimit(unittest.TestCase):
    """A 429 killed the scheduled run on 2026-08-11 after fifteen seconds of
    backoff. Rate limiting gets its own budget; a lost run is a lost day."""

    def _http_error(self, code, retry_after=None):
        headers = email.message.Message()
        if retry_after is not None:
            headers["Retry-After"] = retry_after
        return urllib.error.HTTPError("http://x", code, "nope", headers, None)

    def _fetch(self, responses):
        """Run fetch_page against a scripted sequence, returning the sleeps."""
        slept = []
        calls = iter(responses)

        def fake_urlopen(*_a, **_kw):
            outcome = next(calls)
            if isinstance(outcome, Exception):
                raise outcome
            return contextlib.nullcontext(SimpleNamespace(read=lambda: outcome))

        with mock.patch.object(ac.urllib.request, "urlopen", fake_urlopen), \
                mock.patch.object(ac.time, "sleep", slept.append):
            body = ac.fetch_page("q", 0, 10, 60.0, 2, 5.0)
        return body, slept

    def test_a_429_is_waited_out_not_given_up_on(self):
        body, slept = self._fetch([self._http_error(429), b"<feed/>"])
        self.assertEqual(body, b"<feed/>")
        self.assertEqual(slept, [ac.RATE_LIMIT_BACKOFF_S])

    def test_retry_after_is_honoured_when_the_server_sends_one(self):
        _, slept = self._fetch([self._http_error(429, "120"), b"<feed/>"])
        self.assertEqual(slept, [120.0])

    def test_a_hostile_retry_after_is_capped(self):
        _, slept = self._fetch([self._http_error(429, "999999"), b"<feed/>"])
        self.assertEqual(slept, [ac.RATE_LIMIT_MAX_WAIT_S])

    def test_backoff_grows_across_repeated_throttling(self):
        _, slept = self._fetch(
            [self._http_error(429), self._http_error(429), b"<feed/>"])
        self.assertEqual(slept, [ac.RATE_LIMIT_BACKOFF_S, 2 * ac.RATE_LIMIT_BACKOFF_S])

    def test_throttling_does_not_spend_the_transient_retry_budget(self):
        """Two 429s then a dropped socket: the socket still gets its retries."""
        _, slept = self._fetch([self._http_error(429), self._http_error(429),
                                urllib.error.URLError("reset"), b"<feed/>"])
        self.assertEqual(slept[-1], 5.0)

    def test_a_relentless_429_eventually_fails_loudly(self):
        with self.assertRaises(SystemExit):
            self._fetch([self._http_error(429)] * (ac.RATE_LIMIT_RETRIES + 1))

    def test_other_http_errors_keep_the_short_budget(self):
        """A 500 is not a rate limit and must not wait five minutes."""
        _, slept = self._fetch([self._http_error(500), b"<feed/>"])
        self.assertEqual(slept, [5.0])


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
        before = sources.checked_ids(self.report.read_text(encoding="utf-8"))
        refreshed = self.tmp / "inbox2.md"
        run_candidates("--papers", str(self.papers),
                       "--existing-issue-body", str(self.report), output=refreshed)
        self.assertEqual(sources.checked_ids(refreshed.read_text(encoding="utf-8")), before)

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
