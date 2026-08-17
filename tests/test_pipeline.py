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


class TestCategoryGate(unittest.TestCase):
    """The list is about generated video, not about robots or renderers."""

    def test_robotics_and_graphics_are_not_admitted_on_their_own(self):
        self.assertNotIn("cs.RO", ac.ALLOWED_CATEGORIES)
        self.assertNotIn("cs.GR", ac.ALLOWED_CATEGORIES)

    def test_vision_and_learning_still_are(self):
        for category in ("cs.CV", "cs.LG", "cs.AI", "cs.MM", "eess.IV"):
            self.assertIn(category, ac.ALLOWED_CATEGORIES)

    def test_a_cross_listed_robotics_paper_still_arrives(self):
        """Dropping cs.RO excludes only work that never reached vision at all.

        A paper passes on any of its categories, so the robot world models this
        list wants -- which cross-list cs.CV or cs.LG as a matter of course --
        are unaffected. Losing that distinction is the way this change could
        quietly go wrong.
        """
        cross_listed = {"cs.RO", "cs.CV"}
        pure_robotics = {"cs.RO", "eess.SY"}
        self.assertTrue(cross_listed & ac.ALLOWED_CATEGORIES)
        self.assertFalse(pure_robotics & ac.ALLOWED_CATEGORIES)


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

        # Jitter off, so a wait can be asserted exactly; it has its own tests.
        with mock.patch.object(ac.urllib.request, "urlopen", fake_urlopen), \
                mock.patch.object(ac.random, "random", lambda: 0.0), \
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

    def _backoffs(self, rand):
        with mock.patch.object(ac.random, "random", lambda: rand):
            return [ac.backoff_for(n)
                    for n in range(1, ac.RATE_LIMIT_RETRIES + 1)]

    def test_backoff_holds_at_the_cap_rather_than_growing_without_bound(self):
        self.assertEqual(self._backoffs(0.0)[-1], ac.RATE_LIMIT_MAX_WAIT_S)

    def test_jitter_only_ever_shortens_a_wait(self):
        """Never longer than the cap says, never so short it stops helping."""
        for jittered, base in zip(self._backoffs(1.0), self._backoffs(0.0)):
            self.assertLessEqual(jittered, base)
            self.assertGreater(jittered, base * 0.5)

    def test_the_budget_outlasts_a_quarter_hour_of_throttling(self):
        """08-16 was still being refused six minutes in and the run was lost.
        Worst-case jitter, so this is the floor the schedule can count on."""
        self.assertGreaterEqual(sum(self._backoffs(1.0)), 15 * 60)


class TestRoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.papers = self.tmp / "papers.jsonl"
        self.papers.write_text("", encoding="utf-8")
        self.report = self.tmp / "inbox.md"

    def _empty_feed(self):
        """A window that has moved past everything the inbox holds."""
        path = self.tmp / "empty-feed.xml"
        path.write_text('<feed xmlns="http://www.w3.org/2005/Atom"></feed>',
                        encoding="utf-8")
        return path

    def _ids(self, path):
        return {c["id"]
                for c in sources.carried_candidates(path.read_text(encoding="utf-8"))}

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

    def test_a_candidate_outlives_the_window_it_arrived_in(self):
        """The bug this guards: on 08-17 a 3-day refresh silently dropped 18 of
        the 23 papers a 4-day run had put in the inbox hours earlier. They were
        not judged, they were just older than the new window."""
        run_candidates("--papers", str(self.papers), output=self.report)
        before = self._ids(self.report)
        self.assertTrue(before)
        refreshed = self.tmp / "inbox2.md"
        run_candidates("--papers", str(self.papers), "--feed-file", str(self._empty_feed()),
                       "--existing-issue-body", str(self.report), output=refreshed)
        self.assertEqual(self._ids(refreshed), before)

    def test_a_carried_candidate_keeps_its_tick_and_its_criteria(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._tick_first(section="systems")
        body = self.report.read_text(encoding="utf-8")
        ticked = sources.checked_ids(body)
        detail = {c["id"]: (c["met"], c["evidence"])
                  for c in sources.carried_candidates(body)}
        refreshed = self.tmp / "inbox2.md"
        run_candidates("--papers", str(self.papers), "--feed-file", str(self._empty_feed()),
                       "--existing-issue-body", str(self.report), output=refreshed)
        after = refreshed.read_text(encoding="utf-8")
        self.assertEqual(sources.checked_ids(after), ticked)
        self.assertEqual({c["id"]: (c["met"], c["evidence"])
                          for c in sources.carried_candidates(after)}, detail)
        self.assertIn("`systems`", after)

    def test_carrying_forward_is_not_never_forgetting(self):
        """An entry retires the moment something else accounts for it --
        otherwise the inbox only ever grows. Written against a hand-built body
        rather than the fixture, which yields a single candidate and so cannot
        tell 'retired the merged one' from 'dropped everything'."""
        merged, kept = "2608.06257", "2608.06332"
        self.report.write_text("\n".join(sources.render_candidates([
            {"id": pid, "title": f"Paper {pid}", "date": "2026-08-13",
             "section": "systems", "met": 2,
             "evidence": {"action": True, "causal": False, "state": True}}
            for pid in (merged, kept)])) + "\n", encoding="utf-8")
        self.papers.write_text(json.dumps({
            "id": merged, "title": f"Paper {merged}", "section": "systems",
            "links": {"paper": f"https://arxiv.org/abs/{merged}"}, "attrs": {},
        }) + "\n", encoding="utf-8")
        refreshed = self.tmp / "inbox2.md"
        run_candidates("--papers", str(self.papers), "--feed-file", str(self._empty_feed()),
                       "--existing-issue-body", str(self.report), output=refreshed)
        self.assertEqual(self._ids(refreshed), {kept})

    def test_an_open_pr_also_retires_a_carried_entry(self):
        """Ticked papers sit in an open PR for as long as review takes, and the
        inbox must not re-propose them the whole time."""
        pid = "2608.06257"
        self.report.write_text("\n".join(sources.render_candidates([
            {"id": pid, "title": f"Paper {pid}", "date": "2026-08-13",
             "section": "systems", "met": 2, "evidence": {}}])) + "\n", encoding="utf-8")
        pr_bodies = self.tmp / "open-prs.md"
        pr_bodies.write_text(f"adds https://arxiv.org/abs/{pid}\n", encoding="utf-8")
        refreshed = self.tmp / "inbox2.md"
        run_candidates("--papers", str(self.papers), "--feed-file", str(self._empty_feed()),
                       "--existing-issue-body", str(self.report),
                       "--known-file", str(pr_bodies), output=refreshed)
        self.assertEqual(self._ids(refreshed), set())

    def test_a_paper_still_in_the_window_is_not_listed_twice(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        before = self._ids(self.report)
        refreshed = self.tmp / "inbox2.md"
        run_candidates("--papers", str(self.papers),
                       "--existing-issue-body", str(self.report), output=refreshed)
        body = refreshed.read_text(encoding="utf-8")
        self.assertEqual(self._ids(refreshed), before)
        self.assertEqual(len(sources.carried_candidates(body)), len(before))

    def test_the_watchlist_carries_its_own_candidates_forward(self):
        """Feeds are incremental and listing pages are short, so a post that
        scrolls off is never announced again. Polled with an empty watchlist,
        which is also the shape of every source being unreachable at once."""
        post = {"id": "blog:runway-gwm-1", "title": "GWM-1", "date": "2026-07-02",
                "section": "reports", "met": 1, "evidence": {"state": True},
                "url": "https://runwayml.com/research/introducing-runway-gwm-1",
                "origin": "Runway research"}
        self.report.write_text(
            "\n".join(sources.render_candidates([post])) + "\n", encoding="utf-8")
        watchlist = self.tmp / "watchlist.json"
        watchlist.write_text("[]", encoding="utf-8")
        refreshed = self.tmp / "inbox2.md"
        subprocess.run([sys.executable, str(ROOT / "scripts" / "blog_candidates.py"),
                        "--watchlist", str(watchlist), "--papers", str(self.papers),
                        "--existing-issue-body", str(self.report),
                        "--output", str(refreshed)],
                       capture_output=True, text=True, check=True)
        carried = sources.carried_candidates(refreshed.read_text(encoding="utf-8"))
        self.assertEqual([c["id"] for c in carried], [post["id"]])
        self.assertEqual(carried[0]["url"], post["url"])
        self.assertEqual(carried[0]["origin"], post["origin"])

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
