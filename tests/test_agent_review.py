"""Agent plumbing. Nothing here calls a model or the network."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import agent_review as ar  # noqa: E402
import arxiv_candidates as ac  # noqa: E402
import sources  # noqa: E402


class FakeProc:
    def __init__(self, stdout, returncode=0, stderr=""):
        self.stdout, self.returncode, self.stderr = stdout, returncode, stderr


def envelope(result, **extra):
    return json.dumps({"type": "result", "subtype": "success", "is_error": False,
                       "total_cost_usd": 0.5, "result": result, **extra})


class TestCallClaude(unittest.TestCase):
    def _run(self, stdout, **kw):
        with mock.patch("subprocess.run", return_value=FakeProc(stdout, **kw)):
            return ar.call_claude("p", "m", "", 60)

    def test_plain_json(self):
        parsed, cost = self._run(envelope('{"a": 1}'))
        self.assertEqual(parsed, {"a": 1})
        self.assertEqual(cost, 0.5)

    def test_code_fence_is_stripped(self):
        # Observed in practice: the model fences its JSON despite being told not to.
        parsed, _ = self._run(envelope('```json\n{"a": 1}\n```'))
        self.assertEqual(parsed, {"a": 1})

    def test_bare_fence_is_stripped(self):
        parsed, _ = self._run(envelope('```\n[{"id": "x"}]\n```'))
        self.assertEqual(parsed, [{"id": "x"}])

    def test_trailing_commentary_is_ignored(self):
        # Observed live: the attribute pass emitted valid JSON then kept talking,
        # json.loads rejected the lot, and the retry cost another $0.40.
        parsed, _ = self._run(envelope(
            '{"id": "2607.26037", "in_scope": true}\n\nNote: the paper is unclear '
            'about the frame rate.'))
        self.assertEqual(parsed["id"], "2607.26037")

    def test_preamble_before_the_json_is_ignored(self):
        parsed, _ = self._run(envelope('Here you go:\n{"a": 1}'))
        self.assertEqual(parsed, {"a": 1})

    def test_prose_with_no_json_is_an_error_not_a_guess(self):
        with self.assertRaises(ar.AgentError):
            self._run(envelope("I could not determine this."))

    def test_truncated_json_is_an_error(self):
        with self.assertRaises(ar.AgentError):
            self._run(envelope('{"id": "x", "attrs": {"backbone":'))

    def test_nonzero_exit(self):
        with self.assertRaises(ar.AgentError):
            self._run("", returncode=1, stderr="boom")

    def test_error_subtype(self):
        payload = json.dumps({"type": "result", "subtype": "error_max_turns",
                              "is_error": True, "result": "..."})
        with self.assertRaises(ar.AgentError):
            self._run(payload)

    def test_retry_then_succeed(self):
        procs = [FakeProc("not json"), FakeProc(envelope('{"ok": true}'))]
        with mock.patch("subprocess.run", side_effect=procs), \
             mock.patch("time.sleep"):
            parsed, _ = ar.call_with_retry("p", "m", "", 60)
        self.assertEqual(parsed, {"ok": True})


class TestToolPinning(unittest.TestCase):
    """An unrestricted headless agent goes exploring instead of answering, which
    turned a one-shot classification into a >10 minute session."""

    def _cmd(self, tools):
        with mock.patch("subprocess.run", return_value=FakeProc(envelope("{}"))) as run:
            ar.call_claude("p", "m", tools, 60)
        return run.call_args[0][0]

    def test_screening_denies_every_tool(self):
        cmd = self._cmd(ar.SCREEN_TOOLS)
        self.assertIn("--disallowed-tools", cmd)
        for tool in ("WebFetch", "Bash", "Read", "Task"):
            self.assertIn(tool, cmd)
        self.assertNotIn("--allowed-tools", cmd)

    def test_attribute_pass_gets_webfetch_only(self):
        cmd = ar.SCREEN_TOOLS and self._cmd(ar.ATTR_TOOLS)
        allowed = cmd[cmd.index("--allowed-tools") + 1:cmd.index("--disallowed-tools")]
        self.assertEqual(allowed, ["WebFetch"])
        self.assertNotIn("WebFetch", cmd[cmd.index("--disallowed-tools"):])
        self.assertIn("Bash", cmd)

    def test_no_tool_spec_passes_no_flag(self):
        cmd = self._cmd(None)
        self.assertNotIn("--allowed-tools", cmd)
        self.assertNotIn("--disallowed-tools", cmd)


class TestAwaitingMerge(unittest.TestCase):
    """Without this a second run re-judges everything the first run decided and
    pays for it twice: the run never ticks the inbox, and the records it wrote
    live on an unmerged branch."""

    BODY = ("## Accepted\n"
            "| [Wonder](https://arxiv.org/abs/2607.26037) | `systems` | ... |\n"
            "## Rejected\n"
            "- `2608.07420` Beyond Myopic World Models — one forward pass\n")

    def test_accepted_and_rejected_ids_are_both_found(self):
        with mock.patch.object(ar, "gh", return_value=json.dumps([{"body": self.BODY}])):
            self.assertEqual(ar.ids_awaiting_merge(), {"2607.26037", "2608.07420"})

    def test_no_open_prs(self):
        with mock.patch.object(ar, "gh", return_value="[]"):
            self.assertEqual(ar.ids_awaiting_merge(), set())

    def test_unreadable_pr_list_does_not_abort_the_run(self):
        with mock.patch.object(ar, "gh", return_value="not json"):
            self.assertEqual(ar.ids_awaiting_merge(), set())


class TestRejudge(unittest.TestCase):
    """Widening the scope makes past rejections wrong. They are recoverable only
    because they were logged rather than dropped."""

    def setUp(self):
        # ROOT is patched too, not just REJECTED: candidates_from_rejections
        # filters against ROOT/data/papers.jsonl, so without this the test
        # silently depends on whether the real list happens to contain the
        # fixture ids -- and starts failing the day someone adds one.
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "data").mkdir()
        (self.tmp / "data" / "papers.jsonl").write_text("", encoding="utf-8")
        (self.tmp / "data" / "arxiv-ignore.txt").write_text("", encoding="utf-8")
        self.log = self.tmp / "agent-rejected.jsonl"
        self.log.write_text(
            "# a comment survives\n"
            '{"id": "2608.05976", "title": "Diff-VF", "rejected_on": "2026-08-10", "reason": "no action conditioning"}\n'
            '{"id": "2607.26529", "title": "CineWeaver", "rejected_on": "2026-08-10", "reason": "no per-step action"}\n',
            encoding="utf-8")
        for target, value in (("REJECTED", self.log), ("ROOT", self.tmp)):
            patch = mock.patch.object(ar, target, value)
            patch.start()
            self.addCleanup(patch.stop)

    def test_rejection_date_is_not_used_as_the_paper_date(self):
        # The row records when the call was made. Reusing it would stamp every
        # recovered paper with the day it was re-judged.
        _, cands = ar.candidates_from_rejections()
        for cand in cands:
            self.assertNotIn("date", cand)

    def test_prior_reason_travels_with_the_candidate(self):
        _, cands = ar.candidates_from_rejections()
        self.assertEqual({c["id"] for c in cands}, {"2608.05976", "2607.26529"})
        self.assertTrue(all(c["prior_reason"] for c in cands))

    def test_papers_already_in_the_list_are_not_reproposed(self):
        (self.tmp / "data" / "papers.jsonl").write_text(
            json.dumps({"id": "2608.05976", "title": "Diff-VF"}) + "\n",
            encoding="utf-8")
        _, cands = ar.candidates_from_rejections()
        self.assertEqual([c["id"] for c in cands], ["2607.26529"])

    def test_recovered_papers_leave_the_log_and_the_rest_stay(self):
        ar.drop_rejections({"2608.05976"})
        text = self.log.read_text(encoding="utf-8")
        self.assertNotIn("2608.05976", text)
        self.assertIn("2607.26529", text)
        self.assertIn("# a comment survives", text)


class TestPrompts(unittest.TestCase):
    def test_scope_comes_from_the_published_readme(self):
        scope = ar.scope_text()
        self.assertTrue(scope.startswith("## Scope"))
        for phrase in ("Per-step action conditioning", "Causal or streaming",
                       "Persistent world state"):
            self.assertIn(phrase, scope)

    def test_sections_list_covers_every_section(self):
        keys = {s["key"] for s in json.loads(
            (ROOT / "data" / "sections.json").read_text(encoding="utf-8"))}
        text = ar.sections_text()
        for key in keys:
            self.assertIn(f"`{key}`", text)

    def test_render_fills_every_placeholder(self):
        out = ar.render("screen.md", SCOPE="S", SECTIONS="X", CANDIDATES="C")
        self.assertNotIn("{{", out)

    def test_unfilled_placeholder_is_fatal(self):
        with self.assertRaises(SystemExit):
            ar.render("screen.md", SCOPE="S")

    def test_attrs_prompt_carries_the_paper(self):
        out = ar.render("attrs.md", ID="2508.13009", TITLE="Matrix-Game 2.0")
        self.assertIn("arxiv.org/abs/2508.13009", out)
        self.assertIn("Matrix-Game 2.0", out)

    def test_candidates_block_flags_a_missing_abstract(self):
        block = ar.candidates_block([{"id": "1", "title": "T", "section": "systems"}])
        self.assertIn("say unsure", block)


class TestRejections(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "agent-rejected.jsonl"

    def test_ids_are_read_and_comments_skipped(self):
        self.path.write_text(
            "# a comment\n"
            '{"id": "2608.07463", "reason": "out of scope"}\n'
            "\n"
            '{"id": "2608.07420", "reason": "driving"}\n', encoding="utf-8")
        self.assertEqual(sources.rejected_ids(self.path),
                         {"2608.07463", "2608.07420"})

    def test_missing_file_is_empty(self):
        self.assertEqual(sources.rejected_ids(self.tmp / "nope.jsonl"), set())

    def test_rejected_papers_are_not_proposed_again(self):
        feed = Path(__file__).resolve().parent / "data" / "sample-feed.xml"
        first = ac.parse_feed(feed.read_bytes())[0]
        self.path.write_text(json.dumps({"id": first["id"], "reason": "x"}) + "\n",
                             encoding="utf-8")
        papers = self.tmp / "papers.jsonl"
        papers.write_text("", encoding="utf-8")
        report = self.tmp / "inbox.md"
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "scripts" / "arxiv_candidates.py"),
                        "--feed-file", str(feed), "--papers", str(papers),
                        "--rejected", str(self.path), "--output", str(report)],
                       check=True, capture_output=True)
        self.assertNotIn(first["id"], report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
