"""The site build: data in, static pages out."""
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_site as bs  # noqa: E402


def record(pid, **over):
    rec = {
        "id": pid,
        "name": None,
        "title": f"Paper {pid}",
        "venue": None,
        "date": "2026-08-13",
        "tags": ["systems"],
        "tags_source": {"systems": "curated"},
        "links": {"paper": f"https://arxiv.org/abs/{pid}"},
        "attrs": {},
    }
    rec.update(over)
    return rec


class SiteCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.papers = self.tmp / "papers.jsonl"
        self.demos = self.tmp / "demos"
        self.demos.mkdir()
        self.explainers = self.tmp / "explainers"
        self.explainers.mkdir()
        self.out = self.tmp / "site"

    def write(self, records):
        self.papers.write_text(
            "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

    def build(self):
        return bs.build(self.out, papers_path=self.papers,
                        tags_path=ROOT / "data" / "tags.json",
                        demos_dir=self.demos,
                        explainers_dir=self.explainers)

    def index(self):
        return (self.out / "index.html").read_text(encoding="utf-8")

    def add_demo(self, pid, entry="index.html", body="<p>hi</p>"):
        d = self.demos / pid
        d.mkdir(parents=True)
        (d / entry).write_text(body, encoding="utf-8")
        return d

    def add_explainer(self, name, body=None):
        f = self.explainers / f"{name}.html"
        f.write_text(body if body is not None
                     else "<!DOCTYPE html>\n<html><body>\n<h1>read</h1>\n</body></html>",
                     encoding="utf-8")
        return f


class TestIndex(SiteCase):
    def test_every_paper_is_in_the_static_html(self):
        """The list is rendered server-side, not assembled by JavaScript. A
        bibliography that needs a script to show its entries is not one."""
        self.write([record("2608.00001"), record("2608.00002")])
        self.build()
        page = self.index()
        self.assertIn("2608.00001", page)
        self.assertIn("2608.00002", page)

    def test_newest_first(self):
        self.write([record("2401.00001", date="2024-01-01"),
                    record("2608.00002", date="2026-08-01")])
        self.build()
        page = self.index()
        self.assertLess(page.index("2608.00002"), page.index("2401.00001"))

    def test_a_name_prefix_is_not_printed_twice(self):
        self.write([record("2608.00001", name="MASS",
                           title="MASS: Multiplayer World Models")])
        self.build()
        self.assertNotIn("MASS: Multiplayer", self.index())
        self.assertIn("Multiplayer World Models", self.index())

    def test_the_paper_link_is_not_relabelled_on_every_row(self):
        """The id is the link to the paper, so a PAPER chip beside it names
        the same target twice -- on 381 of 451 rows it is the only link there
        is, and the label carries nothing."""
        self.write([record("2608.00001")])
        self.build()
        self.assertNotIn(">PAPER<", self.index())

    def test_a_second_link_is_still_named(self):
        self.write([record("2608.00001", links={
            "paper": "https://arxiv.org/abs/2608.00001",
            "code": "https://github.com/x/y"})])
        self.build()
        self.assertIn(">CODE<", self.index())

    def test_the_title_is_the_link_and_it_opens_beside_the_index(self):
        """The id is a 10px string in the margin; the title is what a reader
        points at. Leaving the index to read a paper must not cost the filter
        they built and the place they had scrolled to."""
        self.write([record("2608.00001")])
        self.build()
        page = self.index()
        self.assertIn('class="row__link" href="https://arxiv.org/abs/2608.00001"'
                      ' target="_blank" rel="noopener noreferrer"', page)

    def test_every_outbound_link_opens_in_a_new_tab(self):
        self.write([record("2608.00001", links={
            "paper": "https://arxiv.org/abs/2608.00001",
            "code": "https://github.com/x/y"})])
        self.build()
        page = self.index()
        for href in ("https://arxiv.org/abs/2608.00001", "https://github.com/x/y"):
            for match in re.finditer(rf'<a [^>]*href="{re.escape(href)}"[^>]*>', page):
                self.assertIn('target="_blank"', match.group(0))
                self.assertIn("noopener", match.group(0))

    def test_nothing_clickable_is_nested_inside_the_title_link(self):
        """A tag button or a disclosure inside the anchor is un-clickable --
        the anchor swallows the activation before the control sees it."""
        self.write([record("2608.00001", attrs={"backbone": "causal-diffusion"},
                           links={"paper": "https://arxiv.org/abs/2608.00001",
                                  "code": "https://github.com/x/y"})])
        self.build()
        inner = re.search(r'<a class="row__link"[^>]*>(.*?)</a>', self.index(), re.S)
        self.assertIsNotNone(inner)
        for forbidden in ("<button", "<details", "<summary", "<a ",
                          "demo-badge", "explainer-badge"):
            self.assertNotIn(forbidden, inner.group(1))

    def test_a_record_with_no_link_still_renders_its_title(self):
        self.write([record("2608.00001", links={})])
        self.build()
        page = self.index()
        self.assertIn("Paper 2608.00001", page)
        self.assertNotIn('class="row__link"', page)

    def test_titles_are_escaped(self):
        self.write([record("2608.00001", title="Attention <script>alert(1)</script>")])
        self.build()
        self.assertNotIn("<script>alert(1)</script>", self.index())

    def test_a_profile_is_only_offered_where_there_is_one(self):
        self.write([record("2608.00001", attrs={"backbone": "causal-diffusion"}),
                    record("2608.00002")])
        self.build()
        self.assertEqual(self.index().count("<summary>PROFILE</summary>"), 1)

    def test_empty_years_keep_their_column(self):
        """The axis is time. Dropping 2019 because nobody published silently
        rescales every other column against a shorter span."""
        self.write([record("2018.00001", date="2018-03-27"),
                    record("2020.00001", date="2020-06-01")])
        self.build()
        page = self.index()
        self.assertIn("year--empty", page)
        for short in ("18", "19", "20"):
            self.assertIn(f'class="year__k">{short}<', page)

    def test_search_blob_carries_the_tag_code(self):
        """Typing SYS should find the systems papers without reaching for a
        chip, so the code has to be in the haystack the filter reads."""
        self.write([record("2608.00001")])
        self.build()
        self.assertIn("sys", self.index())


class TestDemos(SiteCase):
    def test_a_demo_directory_becomes_a_page_and_a_badge(self):
        self.write([record("2608.00001")])
        self.add_demo("2608.00001")
        stats = self.build()
        self.assertEqual(stats["demos"], 1)
        self.assertTrue((self.out / "demos" / "2608.00001" / "index.html").is_file())
        self.assertTrue((self.out / "demos" / "2608.00001" / "app" / "index.html").is_file())
        self.assertIn("demo-badge", self.index())

    def test_the_demo_is_copied_verbatim(self):
        self.write([record("2608.00001")])
        self.add_demo("2608.00001", body="<canvas id=world></canvas>")
        self.build()
        copied = (self.out / "demos" / "2608.00001" / "app" / "index.html")
        self.assertEqual(copied.read_text(encoding="utf-8"), "<canvas id=world></canvas>")

    def test_underscore_directories_are_not_demos(self):
        """demos/_template is a template, not a demo for a paper called
        `_template`."""
        self.write([record("2608.00001")])
        self.add_demo("_template")
        stats = self.build()
        self.assertEqual(stats["demos"], 0)
        self.assertNotIn("demo-badge", self.index())

    def test_a_demo_for_an_unknown_id_is_reported_not_ignored(self):
        """A mistyped id would otherwise build nothing at all, silently, for
        as long as nobody went looking for the badge."""
        self.write([record("2608.00001")])
        self.add_demo("9999.99999")
        _, orphans = bs.find_demos(self.demos, {"2608.00001"})
        self.assertTrue(any("9999.99999" in o for o in orphans))

    def test_a_demo_directory_with_no_entry_point_is_reported(self):
        d = self.demos / "2608.00001"
        d.mkdir()
        (d / "notes.txt").write_text("wip", encoding="utf-8")
        _, orphans = bs.find_demos(self.demos, {"2608.00001"})
        self.assertTrue(any("no index.html" in o for o in orphans))

    def test_no_demos_is_not_an_error(self):
        self.write([record("2608.00001")])
        stats = self.build()
        self.assertEqual(stats["demos"], 0)
        self.assertNotIn("data-flag=\"demo\"", self.index())


class TestExplainers(SiteCase):
    def test_an_explainer_file_becomes_a_page_and_a_badge(self):
        self.write([record("2608.00001")])
        self.add_explainer("2608.00001")
        stats = self.build()
        self.assertEqual(stats["explainers"], 1)
        self.assertTrue((self.out / "explainers" / "2608.00001.html").is_file())
        self.assertIn('href="explainers/2608.00001.html"', self.index())

    def test_the_explainer_is_published_as_itself(self):
        """A demo is wrapped in site chrome because it runs in an iframe. An
        explainer is a long document carrying its own header, theme toggle and
        progress bar, and every one of those measures a viewport an iframe
        would take away from it. Nothing but the link home is added."""
        page = ("<!DOCTYPE html>\n<html lang=\"zh-CN\"><head><title>t</title></head>"
                "<body class=\"x\">\n<h1>\u7cbe\u8bfb</h1>\n</body></html>")
        self.write([record("2608.00001")])
        self.add_explainer("2608.00001", body=page)
        self.build()
        built = (self.out / "explainers" / "2608.00001.html").read_text(encoding="utf-8")
        self.assertNotIn("<iframe", built)
        self.assertIn('<body class="x">', built)
        self.assertIn("\u7cbe\u8bfb", built)
        # Everything the source said, still said, in order.
        self.assertEqual([line for line in page.splitlines() if line.strip()],
                         [line for line in built.splitlines()
                          if line.strip() and line in page])

    def test_the_link_home_lands_on_the_paper_row(self):
        """An explainer is reached by a shared link as often as from the index,
        and a page with no way back is a dead end."""
        self.write([record("2608.00001")])
        self.add_explainer("2608.00001")
        self.build()
        built = (self.out / "explainers" / "2608.00001.html").read_text(encoding="utf-8")
        self.assertIn('href="../index.html#p-2608.00001"', built)

    def test_the_link_home_goes_after_body_not_into_head(self):
        """Inserted at the top of the file it would sit inside <head>, where
        browsers move it anyway -- but only after the CSS beside it has been
        dropped on the floor."""
        self.write([record("2608.00001")])
        self.add_explainer("2608.00001")
        self.build()
        built = (self.out / "explainers" / "2608.00001.html").read_text(encoding="utf-8")
        self.assertLess(built.index("<body>"), built.index('id="site-back"'))

    def test_the_link_home_is_added_once(self):
        """`<body>` appears in the prose of a page about HTML too."""
        self.write([record("2608.00001")])
        self.add_explainer(
            "2608.00001",
            body="<html><body>\n<code>&lt;body&gt;</code>\n<body>\n</html>")
        self.build()
        built = (self.out / "explainers" / "2608.00001.html").read_text(encoding="utf-8")
        self.assertEqual(built.count('id="site-back"'), 1)

    def test_an_explainer_for_an_unknown_id_is_reported_not_ignored(self):
        self.add_explainer("9999.99999")
        found, orphans = bs.find_explainers(self.explainers, {"2608.00001"})
        self.assertEqual(found, {})
        self.assertTrue(any("9999.99999" in o for o in orphans))

    def test_underscore_files_are_not_explainers(self):
        """Even where a paper is somehow called `_template`, the leading
        underscore means "not published", the same as it does under demos/."""
        self.add_explainer("_template")
        found, orphans = bs.find_explainers(self.explainers, {"_template"})
        self.assertEqual(found, {})
        self.assertEqual(orphans, [])

    def test_the_row_is_filterable_and_findable(self):
        """The chip is the obvious way in; 解读 is what the reader of a
        Chinese-language explainer would actually type."""
        self.write([record("2608.00001"), record("2608.00002")])
        self.add_explainer("2608.00001")
        self.build()
        page = self.index()
        self.assertIn('data-flag="explainer"', page)
        self.assertEqual(page.count(' data-explainer="1"'), 1)
        row = re.search(r'<li class="row" id="p-2608\.00001".*?data-search="([^"]*)"',
                        page).group(1)
        self.assertIn("explainer", row)
        self.assertIn("\u89e3\u8bfb", row)

    def test_no_explainers_is_not_an_error(self):
        self.write([record("2608.00001")])
        stats = self.build()
        self.assertEqual(stats["explainers"], 0)
        self.assertNotIn('data-flag="explainer"', self.index())
        self.assertFalse((self.out / "explainers").exists())

    def test_a_paper_can_carry_both(self):
        self.write([record("2608.00001")])
        self.add_demo("2608.00001")
        self.add_explainer("2608.00001")
        stats = self.build()
        self.assertEqual((stats["demos"], stats["explainers"]), (1, 1))
        page = self.index()
        self.assertIn("demo-badge", page)
        self.assertIn("explainer-badge", page)


class TestRealData(unittest.TestCase):
    def test_the_committed_data_builds(self):
        with tempfile.TemporaryDirectory() as tmp:
            stats = bs.build(Path(tmp) / "site")
            self.assertGreater(stats["papers"], 0)
            self.assertTrue((Path(tmp) / "site" / "assets" / "style.css").is_file())
            self.assertTrue((Path(tmp) / "site" / ".nojekyll").is_file())

    def test_no_outbound_link_anywhere_opens_in_the_same_tab(self):
        """Covers the template's own links too, not just the generated rows --
        the footer is where an inconsistency survives longest, because nothing
        regenerates it when a paper is added."""
        with tempfile.TemporaryDirectory() as tmp:
            bs.build(Path(tmp) / "site")
            page = (Path(tmp) / "site" / "index.html").read_text(encoding="utf-8")
        offenders = [a for a in re.findall(r'<a [^>]*href="https?://[^"]*"[^>]*>', page)
                     if 'target="_blank"' not in a or "noopener" not in a]
        self.assertEqual(offenders, [])

    def test_every_tag_has_a_unique_site_code(self):
        tags = json.loads((ROOT / "data" / "tags.json").read_text(encoding="utf-8"))
        codes = [t["code"] for t in tags]
        self.assertEqual(len(set(codes)), len(codes))
        for tag in tags:
            self.assertRegex(tag["code"], r"^[A-Z]{3}$")
            self.assertIsInstance(tag["hue"], int)


if __name__ == "__main__":
    unittest.main()
