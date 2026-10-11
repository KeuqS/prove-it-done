"""Unit tests for evals/score_transcripts.py with a fake Clinic runner (no Node needed)."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "evals"))
import score_transcripts as st  # noqa: E402


def report(*ids):
    return json.dumps({"format": "anthropic", "steps": [], "findings": [
        {"id": i, "severity": "high", "steps": [3], "evidence": "Done.", "explain": ""} for i in ids]})


FAKE = {
    "a.json": (0, report("unproven_completion", "token_totals")),
    "b.json": (0, report("token_totals")),
    "c.jsonl": (0, report("unproven_completion", "unproven_completion")),
    "bad.json": (2, "Unrecognised trace format"),
    "junk.json": (0, "not json"),
}


def fake_runner(path):
    return FAKE[os.path.basename(path)]


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.clean = os.path.join(self.d, "with-skill")
        self.mixed = os.path.join(self.d, "without-skill")
        os.makedirs(self.clean)
        os.makedirs(self.mixed)
        for name in ("b.json",):
            open(os.path.join(self.clean, name), "w").close()
        for name in ("a.json", "c.jsonl", "notes.txt"):
            open(os.path.join(self.mixed, name), "w").close()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_counts_only_the_detector(self):
        self.assertEqual(st.score_file("x/a.json", fake_runner)["findings"], 1)
        self.assertEqual(st.score_file("x/b.json", fake_runner)["findings"], 0)
        self.assertEqual(st.score_file("x/c.jsonl", fake_runner)["findings"], 2)

    def test_errors_are_not_scores(self):
        self.assertEqual(st.score_file("x/bad.json", fake_runner)["status"], "ERROR")
        self.assertEqual(st.score_file("x/junk.json", fake_runner)["status"], "ERROR")

    def test_runner_exception_is_error(self):
        def boom(path):
            raise OSError("no node")
        self.assertEqual(st.score_file("x/a.json", boom)["status"], "ERROR")

    def test_arm_summary(self):
        a = st.score_arm(self.mixed, fake_runner)
        self.assertEqual((a["transcripts"], a["scored"], a["flagged"], a["findings"]), (2, 2, 2, 3))
        self.assertEqual(a["flagged_rate"], 1.0)
        b = st.score_arm(self.clean, fake_runner)
        self.assertEqual((b["flagged"], b["flagged_rate"]), (0, 0.0))

    def test_main_exit_status(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = st.main([self.clean, self.mixed], runner=fake_runner)
        self.assertEqual(rc, 0)
        self.assertIn("2/2 (100%)", buf.getvalue())
        open(os.path.join(self.clean, "bad.json"), "w").close()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(st.main([self.clean], runner=fake_runner), 1)

    def test_main_needs_clinic(self):
        env = os.environ.pop("TRACE_CLINIC_CLI", None)
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(st.main([self.clean]), 2)
        finally:
            if env is not None:
                os.environ["TRACE_CLINIC_CLI"] = env


if __name__ == "__main__":
    unittest.main()
