"""Rendering rules that are easy to break and hard to notice."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_readme as br  # noqa: E402


def rec(**kw):
    base = {"id": "2508.13009", "title": "A Title", "tags": ["systems"],
            "links": {"paper": "https://arxiv.org/abs/2508.13009"}, "attrs": {}}
    base.update(kw)
    return base


class TestOneList(unittest.TestCase):
    """No sections. One list, each paper once, tags on the line."""

    def test_every_paper_appears_exactly_once(self):
        records = [rec(id="1", date="2026-01-01", tags=["systems", "control"]),
                   rec(id="2", date="2026-02-01", tags=["control"])]
        self.assertEqual(len(br.render_list(records).splitlines()), 2)

    def test_newest_first_across_the_whole_list(self):
        records = [rec(id="1", date="2025-01-01", title="Older"),
                   rec(id="2", date="2026-01-01", title="Newer")]
        body = br.render_list(records)
        self.assertLess(body.index("Newer"), body.index("Older"))

    def test_a_line_carries_all_of_its_tags(self):
        line = br.entry_line(rec(tags=["systems", "control", "realtime"]))
        self.assertTrue(line.endswith("· `systems` `control` `realtime`"), line)

    def test_each_tag_is_rendered_with_its_glyph(self):
        line = br.entry_line(rec(tags=["systems", "control"]),
                             {"systems": "🌍", "control": "🕹️"})
        self.assertTrue(line.endswith("· 🌍`systems` 🕹️`control`"), line)

    def test_every_tag_has_a_glyph(self):
        """The glyph is how a tag is found -- searching for `control` also
        matches every title containing the word. A tag without one is
        unsearchable, and renders as a bare backtick run with no colour."""
        tags = json.loads((ROOT / "data" / "tags.json").read_text(encoding="utf-8"))
        for tag in tags:
            self.assertTrue(tag.get("icon"), tag["key"])
        glyphs = [t["icon"] for t in tags]
        self.assertEqual(len(set(glyphs)), len(glyphs), "two tags share a glyph")

    def test_nothing_generated_is_a_heading(self):
        """Heading-per-section rendering is what this replaced. If it comes
        back the list is categorised again, whatever the data says."""
        body = br.render_list([rec(id="1"), rec(id="2")])
        self.assertNotIn("#", body)


class TestEntryLine(unittest.TestCase):
    def test_name_prefix_is_not_repeated(self):
        line = br.entry_line(rec(name="AlayaWorld",
                                 title="AlayaWorld: Long-Horizon Video World Generation",
                                 date="2026-07-06"))
        self.assertIn("**`AlayaWorld`**, Long-Horizon Video World Generation.", line)
        self.assertNotIn("AlayaWorld: Long-Horizon", line)

    def test_title_without_the_prefix_is_untouched(self):
        line = br.entry_line(rec(name="Genie", title="Generative Interactive Environments",
                                 date="2024-02-23"))
        self.assertIn("**`Genie`**, Generative Interactive Environments.", line)

    def test_links_render_in_a_stable_order(self):
        line = br.entry_line(rec(date="2026-01-01", links={
            "code": "https://example.com/code", "paper": "https://example.com/paper",
            "website": "https://example.com/site"}))
        self.assertLess(line.index("[Paper]"), line.index("[Website]"))
        self.assertLess(line.index("[Website]"), line.index("[Code]"))


class TestVenue(unittest.TestCase):
    def test_inherited_arxiv_tags_are_restyled(self):
        self.assertEqual(br.venue_of(rec(venue="arxiv 2026.06", date="2026-06-11")),
                         "arXiv 2026.06")

    def test_real_venues_survive(self):
        self.assertEqual(br.venue_of(rec(venue="ICLR 2026", date="2025-09-01")),
                         "ICLR 2026")

    def test_derived_from_date_when_absent(self):
        self.assertEqual(br.venue_of(rec(date="2026-07-21")), "arXiv 2026.07")

    def test_year_only_date_has_no_derived_venue(self):
        self.assertIsNone(br.venue_of(rec(date="2026")))


class TestAttributeNormalisation(unittest.TestCase):
    def test_hybrid_memory_parts_are_all_shortened(self):
        self.assertEqual(
            br.norm_memory("hybrid:implicit-context+other:closed-form-weight-absorption"),
            "hybrid: context+other")

    def test_plain_memory(self):
        self.assertEqual(br.norm_memory("explicit-spatial-reconstruction"), "spatial (recon)")

    def test_backbone_drops_the_free_text_tail(self):
        self.assertEqual(br.norm_backbone("other:pure-Transformer frame-causal decoder"),
                         "other")

    def test_explanation_after_the_token_stays_out_of_the_table(self):
        # Verbatim from a live agent run: the vocabulary token, then an essay.
        self.assertEqual(br.norm_memory(
            "retrieval — sparse attention over a growing, full-fidelity historical "
            "KV-cache: an initial 'sink' chunk plus top-k retrieved chunks"),
            "retrieval")

    def test_explanation_after_a_hybrid_pair(self):
        self.assertEqual(br.norm_memory(
            "hybrid:retrieval+implicit-context — sparse full-fidelity attention: the "
            "entire history KV cache is kept and a subset selected per step"),
            "hybrid: retrieval+context")

    def test_explanation_after_a_backbone(self):
        self.assertEqual(br.norm_backbone(
            "causal-diffusion — distilled from a bidirectional teacher"),
            "causal diffusion")

    def test_unknown_value_still_collapses_to_one_cell(self):
        cell = br.norm_memory("something-new — with a long explanation that follows")
        self.assertEqual(cell, "something-new")

    def test_action_space_is_summarised(self):
        self.assertEqual(
            br.norm_action("keyboard (multi-key) + continuous mouse (camera)"),
            "keyboard + mouse + camera")


class TestTable(unittest.TestCase):
    def test_only_the_main_list_is_compared(self):
        records = [
            rec(id="1", tags=["systems"], attrs={"backbone": "causal-diffusion"}),
            rec(id="2", tags=["realtime"], attrs={"backbone": "causal-diffusion"}),
        ]
        self.assertEqual([r["id"] for r in br.table_rows(records)], ["1"])

    def test_a_system_that_is_also_a_component_is_still_a_system(self):
        """Tags overlap, so "the supporting lists" has to be said by exclusion.
        Listing the other tags would put every system in both halves of
        comparison.md, once as a system and once as its own component."""
        records = [
            rec(id="1", tags=["systems", "realtime"],
                attrs={"backbone": "causal-diffusion"}),
            rec(id="2", tags=["realtime"], attrs={"backbone": "causal-diffusion"}),
        ]
        self.assertEqual([r["id"] for r in br.table_rows(records)], ["1"])
        others = br.table_rows(records, ("realtime",), without=("systems",))
        self.assertEqual([r["id"] for r in others], ["2"])

    def test_long_titles_are_truncated(self):
        label = br.short_label(rec(name=None, title="A " + "very " * 20 + "long title"))
        self.assertLessEqual(len(label), 44)
        self.assertTrue(label.endswith("…"))


class TestNoTallies(unittest.TestCase):
    """The generated files report papers, not counts of papers.

    A tally is noise that goes stale on every merge and tells a reader nothing
    they came for. These crept in one at a time -- a stats banner, a number
    beside each table-of-contents line, an entry count under each heading, a
    "showing 40 of 107" footer -- so they are pinned out.
    """

    TAGS = json.loads((ROOT / "data" / "tags.json").read_text())

    def test_the_tag_key_is_definitions_only(self):
        key = br.render_tag_key(self.TAGS)
        self.assertNotRegex(key, r"\(\d+\)")

    def test_the_list_carries_no_entry_count(self):
        body = br.render_list([rec(id="1")])
        self.assertNotIn("entries", body)

    def test_no_stats_banner_is_rendered(self):
        self.assertFalse(hasattr(br, "render_stats"))

    def test_the_readme_states_no_totals(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        head = readme.split("<!-- BEGIN:LIST -->")[0]
        for pattern in (r"\d+ papers", r"\d+ entries", r"Showing the \d+"):
            self.assertNotRegex(head, pattern)


class TestGeneratedFilesAreCurrent(unittest.TestCase):
    def test_readme_matches_the_data(self):
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_readme.py"),
                        "--check"], check=True)


if __name__ == "__main__":
    unittest.main()
