"""The inbox round trip: feed -> report -> ticks -> records."""
import contextlib
import email.message
import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
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
TAGS = {t["key"] for t in json.loads((ROOT / "data" / "tags.json").read_text())}


# The curated lists are inputs to the pipeline, so a test that leaves them at
# their defaults is really asserting against today's contents of data/. Ids the
# fixtures use are real ones, and adding one to the ignore list -- an ordinary
# act of curation -- would fail a test about carrying entries forward. Point
# every "already accounted for" source at an empty file and let each test
# supply the one it is actually about.
EMPTY = Path(tempfile.mkdtemp(prefix="pipeline-empty-")) / "empty"
EMPTY.write_text("", encoding="utf-8")

ISOLATED = ("--ignore", "--rejected", "--maintainer-rejected")


def run_candidates(*extra, output):
    cmd = [sys.executable, str(ROOT / "scripts" / "arxiv_candidates.py"),
           "--feed-file", str(FEED), "--output", str(output), *extra]
    for flag in ISOLATED:
        if flag not in extra:
            cmd += [flag, str(EMPTY)]
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
        tags, met, _ = triage.triage(title, abstract)
        self.assertEqual(met, 0)
        admitted = (met > 0 or {"surveys", "benchmarks"} & set(tags)
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


class TestSearchWindow(unittest.TestCase):
    """Where the window opens, which is the difference between a run that
    recovers from a failed one and a run that quietly writes off its papers."""

    NOW = datetime(2026, 8, 17, 4, 31, tzinfo=timezone.utc)

    def test_a_routine_run_reaches_back_the_usual_number_of_days(self):
        self.assertEqual(ac.window_start(self.NOW, 7, None),
                         self.NOW - timedelta(days=7))

    def test_a_recent_success_does_not_shorten_the_window(self):
        """Yesterday's run succeeding is no reason to stop covering the
        announcement lag -- arXiv posts a submission days after it arrives."""
        yesterday = self.NOW - timedelta(days=1)
        self.assertEqual(ac.window_start(self.NOW, 7, yesterday),
                         self.NOW - timedelta(days=7))

    def test_an_outage_widens_the_window_to_cover_it(self):
        last = self.NOW - timedelta(days=12)
        self.assertEqual(ac.window_start(self.NOW, 7, last), last)

    def test_the_august_gap_is_closed(self):
        """2608.14706 was submitted 08-11 00:02Z. Three runs died on a 429 and
        the next one opened its window at 08-11 02:17 -- 2h15m too late, and
        every later window opens later still. Anchored to the last success
        (08-10 05:57Z) the paper is inside the window again."""
        run = datetime(2026, 8, 14, 2, 17, tzinfo=timezone.utc)
        last_success = datetime(2026, 8, 10, 5, 57, tzinfo=timezone.utc)
        submitted = datetime(2026, 8, 11, 0, 2, 32, tzinfo=timezone.utc)
        self.assertGreater(ac.window_start(run, 3, None), submitted)
        self.assertLess(ac.window_start(run, 3, last_success), submitted)

    def test_a_naive_timestamp_is_read_as_utc(self):
        self.assertEqual(ac.parse_since("2026-08-14T04:31:00"),
                         datetime(2026, 8, 14, 4, 31, tzinfo=timezone.utc))

    def test_a_zulu_timestamp_is_understood(self):
        """gh run list hands back exactly this shape."""
        self.assertEqual(ac.parse_since("2026-08-14T04:31:00Z"),
                         datetime(2026, 8, 14, 4, 31, tzinfo=timezone.utc))

    def test_no_previous_run_is_not_an_error(self):
        """The first run ever, and every run whose lookup came back empty."""
        self.assertIsNone(ac.parse_since(""))
        self.assertIsNone(ac.parse_since(None))

    def test_a_malformed_timestamp_fails_loudly(self):
        """Silently falling back would look exactly like a healthy run."""
        with self.assertRaises(SystemExit):
            ac.parse_since("last tuesday")


class TestRoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.papers = self.tmp / "papers.jsonl"
        self.papers.write_text("", encoding="utf-8")
        self.rejects = self.tmp / "maintainer-rejected.jsonl"
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

    def _tick_first(self, tags=None):
        lines = self.report.read_text(encoding="utf-8").splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.startswith("- [ ]"):
                line = line.replace("- [ ]", "- [x]", 1)
                if tags:
                    head, _, rest = line.partition("`")
                    _, _, tail = rest.partition("`")
                    line = f"{head}`{tags}`{tail}"
                lines[i] = line
                break
        self.report.write_text("".join(lines), encoding="utf-8")

    def _select(self, body):
        order = [t["key"] for t in json.loads(
            (ROOT / "data" / "tags.json").read_text(encoding="utf-8"))]
        return apply_mod.parse_selections(body, set(order), order)

    def test_ticked_candidate_becomes_a_record(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._tick_first()
        body = self.report.read_text(encoding="utf-8")
        records, warnings = self._select(body)
        self.assertEqual(len(records), 1)
        self.assertFalse(warnings)
        rec = records[0]
        self.assertIn(rec["id"], rec["links"]["paper"])
        self.assertTrue(rec["tags"])
        self.assertTrue(set(rec["tags"]) <= TAGS)
        self.assertEqual(set(rec["tags_source"].values()), {"curated"})

    def test_maintainer_tag_edit_wins(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._tick_first(tags="systems")
        records, warnings = self._select(self.report.read_text(encoding="utf-8"))
        self.assertEqual(records[0]["tags"], ["systems"])
        self.assertFalse(warnings)

    def test_a_maintainer_can_type_a_second_tag(self):
        """The reason any of this exists: one box, two answers."""
        run_candidates("--papers", str(self.papers), output=self.report)
        self._tick_first(tags="systems, control")
        records, warnings = self._select(self.report.read_text(encoding="utf-8"))
        self.assertEqual(records[0]["tags"], ["systems", "control"])
        self.assertFalse(warnings)

    def test_an_unknown_tag_is_dropped_without_taking_the_paper_with_it(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._tick_first(tags="systems,nonsense")
        records, warnings = self._select(self.report.read_text(encoding="utf-8"))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["tags"], ["systems"])
        self.assertTrue(any("nonsense" in w for w in warnings))

    def test_all_tags_unknown_falls_back_and_warns(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._tick_first(tags="nonsense")
        records, warnings = self._select(self.report.read_text(encoding="utf-8"))
        self.assertEqual(len(records), 1)
        self.assertTrue(set(records[0]["tags"]) <= TAGS)
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
            "id": first["id"], "title": first["title"], "tags": ["systems"],
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
        self._tick_first(tags="systems")
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
             "tags": ["systems"], "met": 2,
             "evidence": {"action": True, "causal": False, "state": True}}
            for pid in (merged, kept)])) + "\n", encoding="utf-8")
        self.papers.write_text(json.dumps({
            "id": merged, "title": f"Paper {merged}", "tags": ["systems"],
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
             "tags": ["systems"], "met": 2, "evidence": {}}])) + "\n", encoding="utf-8")
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
                "tags": ["reports"], "met": 1, "evidence": {"state": True},
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

    def _cross_first(self):
        """Tick the nested drop box on the first candidate."""
        lines = self.report.read_text(encoding="utf-8").splitlines(keepends=True)
        for i, line in enumerate(lines):
            if sources.REJECT_RE.match(line):
                lines[i] = line.replace("- [ ]", "- [x]", 1)
                break
        self.report.write_text("".join(lines), encoding="utf-8")

    def _apply(self, *extra):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "apply_issue_selections.py"),
             "--issue-body", str(self.report), "--papers", str(self.papers),
             "--maintainer-rejected", str(self.rejects), *extra],
            capture_output=True, text=True, check=True)

    def test_every_candidate_offers_both_verdicts(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        body = self.report.read_text(encoding="utf-8")
        ids = self._ids(self.report)
        self.assertTrue(ids)
        offered = {m.group("id") for m in sources.REJECT_RE.finditer(body)}
        self.assertEqual(offered, ids)
        # Nothing is decided until someone clicks.
        self.assertFalse(sources.checked_ids(body))
        self.assertFalse(sources.rejected_in_issue(body))

    def test_a_crossed_box_is_recorded_and_stops_the_candidate_coming_back(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._cross_first()
        dropped = sources.rejected_in_issue(self.report.read_text(encoding="utf-8"))
        self.assertEqual(len(dropped), 1)
        self.assertEqual(self._apply().stdout.strip(), "1")
        recorded = [json.loads(l) for l in self.rejects.read_text(encoding="utf-8")
                    .splitlines() if l.strip()]
        self.assertEqual({r["id"] for r in recorded}, dropped)
        self.assertTrue(recorded[0]["title"])
        # Rejected, so not proposed again -- from the window or from the inbox.
        again = self.tmp / "inbox2.md"
        run_candidates("--papers", str(self.papers),
                       "--maintainer-rejected", str(self.rejects),
                       "--existing-issue-body", str(self.report), output=again)
        self.assertFalse(self._ids(again) & dropped)

    def test_a_cross_survives_a_refresh_before_it_is_recorded(self):
        """The click and the /create-pr that records it can be days apart, and
        the refresh in between rewrites the body."""
        run_candidates("--papers", str(self.papers), output=self.report)
        self._cross_first()
        dropped = sources.rejected_in_issue(self.report.read_text(encoding="utf-8"))
        refreshed = self.tmp / "inbox2.md"
        run_candidates("--papers", str(self.papers), "--feed-file", str(self._empty_feed()),
                       "--existing-issue-body", str(self.report), output=refreshed)
        body = refreshed.read_text(encoding="utf-8")
        self.assertEqual(sources.rejected_in_issue(body), dropped)
        self.assertTrue(dropped <= self._ids(refreshed))

    def test_ticked_and_crossed_at_once_keeps_the_tick_and_says_so(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._tick_first()
        self._cross_first()
        result = self._apply()
        self.assertEqual(result.stdout.strip(), "1")
        self.assertIn("ticked and crossed", result.stderr)
        # Nothing rejected, so the file is never even created.
        self.assertFalse(self.rejects.exists())
        self.assertEqual(len(self.papers.read_text(encoding="utf-8").splitlines()), 1)

    def test_recording_a_rejection_twice_does_not_duplicate_it(self):
        run_candidates("--papers", str(self.papers), output=self.report)
        self._cross_first()
        self.assertEqual(self._apply().stdout.strip(), "1")
        self.assertEqual(self._apply().stdout.strip(), "0")
        lines = [l for l in self.rejects.read_text(encoding="utf-8").splitlines()
                 if l.strip()]
        self.assertEqual(len(lines), 1)

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
