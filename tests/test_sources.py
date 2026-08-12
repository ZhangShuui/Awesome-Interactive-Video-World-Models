"""The four candidate sources and the scope rules they share.

Nothing here touches the network: every source is exercised against a saved
response in tests/data.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / "data"
sys.path.insert(0, str(ROOT / "scripts"))
import apply_issue_selections as apply_mod  # noqa: E402
import arxiv_candidates as ac  # noqa: E402
import blog_candidates as blog  # noqa: E402
import openreview_candidates as orv  # noqa: E402
import sources  # noqa: E402
import venue_candidates as venue  # noqa: E402

SECTIONS = {s["key"] for s in json.loads((ROOT / "data" / "sections.json").read_text())}


class TestIdentity(unittest.TestCase):
    def test_bare_ids_are_arxiv(self):
        self.assertEqual(sources.source_of("2608.07463"), "arxiv")

    def test_prefixes_name_their_source(self):
        for pid, want in (("openreview:wAuawx6o2e", "openreview"),
                          ("proc:cvpr2025-a1b2c3d4", "proc"),
                          ("blog:genie-3", "blog")):
            self.assertEqual(sources.source_of(pid), want)

    def test_a_colon_in_an_unknown_prefix_is_not_a_source(self):
        self.assertEqual(sources.source_of("weird:thing"), "arxiv")

    def test_urls_are_derived_or_carried(self):
        self.assertEqual(sources.url_for("2608.07463"),
                         "https://arxiv.org/abs/2608.07463")
        self.assertEqual(sources.url_for("openreview:abc"),
                         "https://openreview.net/forum?id=abc")
        # A blog slug maps to no URL, so the payload has to carry one.
        self.assertEqual(sources.url_for("blog:genie-3"), "")
        self.assertEqual(sources.url_for("blog:genie-3", "https://x.test/g"),
                         "https://x.test/g")

    def test_a_carried_url_beats_the_derived_one(self):
        self.assertEqual(sources.url_for("2608.07463", "https://x.test/p"),
                         "https://x.test/p")


class TestTitleDedup(unittest.TestCase):
    def test_punctuation_and_case_do_not_matter(self):
        """The same paper is titled differently on arXiv, OpenReview and CVF."""
        self.assertEqual(
            sources.norm_title("Matrix-Game 2.0: An Open-Source Model"),
            sources.norm_title("matrix game 2 0   an open source model"))

    def test_different_papers_stay_different(self):
        self.assertNotEqual(sources.norm_title("Genie 2"), sources.norm_title("Genie 3"))


class TestSharedScope(unittest.TestCase):
    def test_off_topic_is_dropped_whatever_the_source(self):
        propose, _, _, _ = sources.proposal(
            "A world model of protein folding",
            "We render molecular dynamics as video, causally, with memory.")
        self.assertFalse(propose)

    def test_a_world_model_with_no_pixels_is_dropped(self):
        propose, _, _, _ = sources.proposal(
            "EnvACE: internalizing environment dynamics for agentic RL",
            "A latent dynamics model over symbolic state, action-conditioned.")
        self.assertFalse(propose)

    def test_efficiency_substrate_survives_zero_criteria(self):
        propose, section, met, _ = sources.proposal(
            "SPADE: a sparse attention engine for fast video diffusion",
            "Video diffusion transformers pay quadratic self-attention cost.")
        self.assertEqual(met, 0)
        self.assertTrue(propose)
        self.assertEqual(section, "realtime")

    def test_all_three_criteria_suggest_the_main_list(self):
        propose, section, met, _ = sources.proposal(
            "PlayNet: a playable video world model",
            "Per-step keyboard actions drive causal streaming video generation "
            "with a persistent spatial memory across revisits.")
        self.assertTrue(propose)
        self.assertEqual(met, 3)
        self.assertEqual(section, "systems")


class TestQueryPhrases(unittest.TestCase):
    def test_no_phrase_contains_a_shorter_one(self):
        """A phrase is matched verbatim, so a longer one only ever narrows.

        "long video generation" cannot match anything "video generation" misses,
        and keeping both hides that the short one is doing all the work.
        """
        phrases = sources.QUERY_PHRASES
        for phrase in phrases:
            for other in phrases:
                if phrase != other:
                    self.assertNotIn(other, phrase,
                                     f"{phrase!r} is redundant: it contains {other!r}")

    def test_the_measured_dead_phrases_are_gone(self):
        """These returned zero arXiv results over a seven-day window."""
        for dead in ("action-conditioned video", "neural game engine",
                     "streaming video generation", "real-time video generation"):
            self.assertNotIn(dead, sources.QUERY_PHRASES)

    def test_arxiv_uses_the_shared_vocabulary(self):
        self.assertIs(ac.QUERY_PHRASES, sources.QUERY_PHRASES)


class TestArxivTruncation(unittest.TestCase):
    def test_total_results_is_read_from_the_feed(self):
        payload = (b'<feed><opensearch:totalResults xmlns:opensearch="x">'
                   b"812</opensearch:totalResults></feed>")
        self.assertEqual(ac.total_results(payload), 812)

    def test_a_feed_without_a_total_is_not_an_error(self):
        self.assertIsNone(ac.total_results(b"<feed></feed>"))


class TestBlogFeed(unittest.TestCase):
    def setUp(self):
        self.items = blog.parse_feed((DATA / "sample-blog-feed.xml").read_bytes())

    def test_the_post_link_wins_over_the_comment_feed(self):
        """An Atom entry carries several links; rel=replies is not the post."""
        self.assertEqual(self.items[0]["url"], "https://example.test/blog/genie-4/")

    def test_titles_dates_and_summaries_are_read(self):
        self.assertEqual(self.items[0]["title"], "Genie 4: a playable world model")
        self.assertEqual(self.items[0]["date"], "2026-08-01")
        self.assertIn("real time", self.items[0]["summary"])

    def test_the_watchlist_filter_keeps_releases_and_drops_funding(self):
        self.assertTrue(blog.WATCH_RE.search(self.items[0]["title"]))
        item = self.items[1]
        self.assertFalse(blog.WATCH_RE.search(f"{item['title']} {item['summary']}"))


class TestBlogPage(unittest.TestCase):
    def setUp(self):
        self.items = blog.parse_page(
            (DATA / "sample-blog-page.html").read_bytes(), "https://example.test/blog")

    def test_the_title_comes_from_structure_not_flattened_text(self):
        """Flattened anchor text runs the headline into the excerpt."""
        rtfm = next(i for i in self.items if i["url"].endswith("/rtfm"))
        self.assertEqual(rtfm["title"], "RTFM: A Real-Time Frame Model")

    def test_a_heading_is_preferred_when_there_is_one(self):
        atlas = next(i for i in self.items if i["url"].endswith("/atlas"))
        self.assertEqual(atlas["title"], "Atlas: an interactive world model")

    def test_a_leading_date_is_parsed(self):
        rtfm = next(i for i in self.items if i["url"].endswith("/rtfm"))
        self.assertEqual(rtfm["date"], "2025-10-16")

    def test_relative_links_are_absolute(self):
        self.assertTrue(all(i["url"].startswith("https://") for i in self.items))


class TestBlogSlugs(unittest.TestCase):
    def test_routing_segments_do_not_become_the_id(self):
        """'.../genie-3/feed/' must not collide with every other comment feed."""
        self.assertEqual(blog.slug_for("https://x.test/blog/genie-3/feed/"), "genie-3")

    def test_a_normal_post_keeps_its_slug(self):
        self.assertEqual(blog.slug_for("https://x.test/blog/rtfm"), "rtfm")

    def test_a_bare_domain_falls_back_to_the_host(self):
        self.assertEqual(blog.slug_for("https://oasis.test/"), "oasis-test")


class TestOpenReview(unittest.TestCase):
    def setUp(self):
        payload = json.loads((DATA / "sample-openreview.json").read_text())
        self.notes = {n["forum"]: n for n in payload["notes"]}
        self.found = orv.collect(self.notes, set(), set(), {}, orv.VENUE_RE, True)
        self.titles = [c["title"] for c in self.found]

    def test_the_accepted_conference_paper_is_proposed(self):
        self.assertIn("PlayNet: a playable video world model", self.titles)

    def test_one_candidate_per_title_preferring_the_conference(self):
        playnet = [c for c in self.found
                   if c["title"] == "PlayNet: a playable video world model"]
        self.assertEqual(len(playnet), 1)
        self.assertEqual(playnet[0]["origin"], "ICLR 2026 Poster")

    def test_withdrawn_submissions_are_not_proposed(self):
        self.assertNotIn("WithdrawnNet: streaming video generation", self.titles)

    def test_reindexed_records_outside_the_whitelist_are_dropped(self):
        self.assertNotIn("DblpNet: an interactive video model", self.titles)

    def test_notes_that_are_not_submissions_are_dropped(self):
        self.assertNotIn("A review comment", self.titles)

    def test_the_shared_scope_still_applies(self):
        self.assertNotIn("ProteinFold: a world model of molecular dynamics", self.titles)

    def test_a_title_already_in_the_list_is_not_reproposed(self):
        known = {sources.norm_title("PlayNet: a playable video world model")}
        again = orv.collect(self.notes, set(), known, {}, orv.VENUE_RE, True)
        self.assertEqual([c["title"] for c in again], [])

    def test_submissions_under_review_are_opt_in(self):
        withdrawn = orv.collect(self.notes, set(), set(), {}, orv.VENUE_RE, False)
        self.assertIn("WithdrawnNet: streaming video generation",
                      [c["title"] for c in withdrawn])

    def test_candidates_carry_a_forum_url(self):
        for cand in self.found:
            self.assertTrue(cand["url"].startswith("https://openreview.net/forum?id="))


class TestVenueListings(unittest.TestCase):
    CVF = ('<dt class="ptitle"><br><a href="/content/CVPR2025/html/A_Paper_CVPR_2025_paper.html">'
           'Playable World Models</a></dt>')
    ECVA = ('<dt class="ptitle"><br>\n<a href=papers/eccv_2024/papers_ECCV/html/4_ECCV_2024_paper.php>\n'
            'A Streaming Video Model</a>\n</dt>'
            '<dt class="ptitle"><br>\n<a href=papers/eccv_2022/papers_ECCV/html/9_ECCV_2022_paper.php>\n'
            'An Older Video Model</a>\n</dt>')
    NEURIPS = ('<a title="paper title" href="/paper_files/paper/2024/hash/abc-Abstract-Conference.html">'
               'Real-Time World Models</a>')

    def test_cvf_markup_parses(self):
        _, spec, _, year = venue.dialect_for("CVPR2025")
        got = venue.parse_listing(spec, self.CVF, "CVPR2025", year)
        self.assertEqual(got[0]["title"], "Playable World Models")
        self.assertTrue(got[0]["url"].startswith("https://openaccess.thecvf.com/content/"))

    def test_ecva_unquoted_hrefs_parse_and_the_year_is_honoured(self):
        """One ECVA page holds every ECCV; the year is only in the href."""
        _, spec, _, year = venue.dialect_for("ECCV2024")
        got = venue.parse_listing(spec, self.ECVA, "ECCV2024", year)
        self.assertEqual([p["title"] for p in got], ["A Streaming Video Model"])

    def test_neurips_markup_parses(self):
        _, spec, _, year = venue.dialect_for("NeurIPS2024")
        got = venue.parse_listing(spec, self.NEURIPS, "NeurIPS2024", year)
        self.assertEqual(got[0]["title"], "Real-Time World Models")

    def test_an_unknown_venue_is_refused_rather_than_guessed(self):
        with self.assertRaises(SystemExit):
            venue.dialect_for("SIGGRAPH2025")

    def test_ids_are_stable_for_a_url(self):
        self.assertEqual(venue.paper_id("CVPR2025", "https://x.test/p"),
                         venue.paper_id("CVPR2025", "https://x.test/p"))

    def test_the_title_prefilter_keeps_topical_titles(self):
        self.assertTrue(venue.TITLE_PREFILTER.search("Playable World Models"))
        self.assertFalse(venue.TITLE_PREFILTER.search("Source-Free Machine Unlearning"))

    def test_forcing_is_matched_literally_here_unlike_on_arxiv(self):
        """A regex does not stem, so this catches the genre without the physics.

        On arXiv the same word costs ~37 irrelevant candidates a month because
        the search backend expands it to force/forced. Nothing expands it here.
        """
        self.assertTrue(venue.TITLE_PREFILTER.search("Rolling Forcing: Autoregressive Video"))
        self.assertFalse(venue.TITLE_PREFILTER.search("Vision-Informed Grasp Force Prediction"))
        self.assertFalse(venue.TITLE_PREFILTER.search("Phonetic forced alignment"))


class TestNonArxivRecords(unittest.TestCase):
    """A ticked blog post must not become an arxiv.org/abs link."""

    def _issue_line(self, payload, section):
        return (f"- [x] `{section}` **{payload['id']}** — {payload['title']} "
                f"<!-- candidate:{sources.encode(payload)} -->\n")

    def test_a_blog_candidate_keeps_its_url_and_venue(self):
        body = self._issue_line({
            "id": "blog:genie-4", "title": "Genie 4", "name": "Genie 4",
            "date": "2026-08-01", "section": "reports",
            "url": "https://example.test/blog/genie-4/",
            "origin": "Google DeepMind"}, "reports")
        records, warnings = apply_mod.parse_selections(body, SECTIONS)
        self.assertFalse(warnings)
        self.assertEqual(records[0]["links"], {"blog": "https://example.test/blog/genie-4/"})
        self.assertEqual(records[0]["venue"], "Google DeepMind")

    def test_an_openreview_candidate_becomes_a_paper_link(self):
        body = self._issue_line({
            "id": "openreview:abc", "title": "PlayNet", "date": "2026-01-26",
            "section": "systems", "origin": "ICLR 2026 Poster"}, "systems")
        records, _ = apply_mod.parse_selections(body, SECTIONS)
        self.assertEqual(records[0]["links"],
                         {"paper": "https://openreview.net/forum?id=abc"})
        self.assertEqual(records[0]["venue"], "ICLR 2026 Poster")

    def test_an_arxiv_candidate_is_unchanged(self):
        body = self._issue_line({
            "id": "2608.07463", "title": "A paper", "date": "2026-08-07",
            "section": "realtime"}, "realtime")
        records, _ = apply_mod.parse_selections(body, SECTIONS)
        self.assertEqual(records[0]["links"],
                         {"paper": "https://arxiv.org/abs/2608.07463"})
        self.assertIsNone(records[0]["venue"])

    def test_a_candidate_with_no_usable_link_is_skipped_with_a_warning(self):
        body = self._issue_line({
            "id": "blog:mystery", "title": "No link", "section": "reports"}, "reports")
        records, warnings = apply_mod.parse_selections(body, SECTIONS)
        self.assertEqual(records, [])
        self.assertTrue(warnings)


class TestKnownState(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.papers = self.tmp / "papers.jsonl"
        self.papers.write_text(json.dumps({
            "id": "blog:genie-3", "title": "Genie 3: A new frontier",
            "links": {"blog": "https://deepmind.google/blog/genie-3/"},
        }) + "\n", encoding="utf-8")

    def test_urls_are_matched_regardless_of_scheme_www_or_slash(self):
        known = sources.known_urls(self.papers)
        for variant in ("http://deepmind.google/blog/genie-3",
                        "https://www.deepmind.google/blog/genie-3/",
                        "https://deepmind.google/blog/genie-3/"):
            self.assertIn(sources.norm_url(variant), known)

    def test_titles_are_normalised(self):
        self.assertIn(sources.norm_title("genie 3 a new frontier"),
                      sources.known_titles(self.papers))


if __name__ == "__main__":
    unittest.main()
