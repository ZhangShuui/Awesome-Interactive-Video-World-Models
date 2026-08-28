"""The site build: data in, static pages out."""
import json
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
        self.out = self.tmp / "site"

    def write(self, records):
        self.papers.write_text(
            "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

    def build(self):
        return bs.build(self.out, papers_path=self.papers,
                        tags_path=ROOT / "data" / "tags.json",
                        demos_dir=self.demos)

    def index(self):
        return (self.out / "index.html").read_text(encoding="utf-8")

    def add_demo(self, pid, entry="index.html", body="<p>hi</p>"):
        d = self.demos / pid
        d.mkdir(parents=True)
        (d / entry).write_text(body, encoding="utf-8")
        return d


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


class TestRealData(unittest.TestCase):
    def test_the_committed_data_builds(self):
        with tempfile.TemporaryDirectory() as tmp:
            stats = bs.build(Path(tmp) / "site")
            self.assertGreater(stats["papers"], 0)
            self.assertTrue((Path(tmp) / "site" / "assets" / "style.css").is_file())
            self.assertTrue((Path(tmp) / "site" / ".nojekyll").is_file())

    def test_every_tag_has_a_unique_site_code(self):
        tags = json.loads((ROOT / "data" / "tags.json").read_text(encoding="utf-8"))
        codes = [t["code"] for t in tags]
        self.assertEqual(len(set(codes)), len(codes))
        for tag in tags:
            self.assertRegex(tag["code"], r"^[A-Z]{3}$")
            self.assertIsInstance(tag["hue"], int)


if __name__ == "__main__":
    unittest.main()
