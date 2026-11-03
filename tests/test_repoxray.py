"""Tests for repoxray: scanner, graph, analysis, reports, CLI."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from repoxray.analysis import find_dead_code, hotspots, summarize  # noqa: E402
from repoxray.graph import (  # noqa: E402
    build_edges, entry_points, find_cycles, layers, orphans)
from repoxray.report import build_all  # noqa: E402
from repoxray.scanner import scan_project  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
SAMPLE = os.path.join(FIXTURES, "sample_project")
CYCLE = os.path.join(FIXTURES, "cycle_project")


def scan_sample():
    modules, counts = scan_project(SAMPLE)
    edges = build_edges(modules)
    return modules, counts, edges


class TestScanner(unittest.TestCase):
    def test_modules_and_edges(self):
        modules, counts, edges = scan_sample()
        self.assertEqual(counts["python_files"], 5)
        self.assertEqual(counts["parse_errors"], 0)
        self.assertIn("main", modules)
        self.assertIn("core.engine", modules)
        self.assertEqual(edges["main"], {"core.engine"})
        self.assertEqual(edges["core.engine"], {"core.utils"})
        # stdlib import is external, never an internal edge
        self.assertIn("sys", modules["main"].external_imports)

    def test_main_guard_detected(self):
        modules, _, _ = scan_sample()
        self.assertTrue(modules["main"].has_main_guard)

    def test_relative_import_resolved(self):
        modules, _, edges = scan_sample()
        self.assertIn("core.utils", edges["core.engine"])


class TestGraph(unittest.TestCase):
    def test_entry_points(self):
        modules, _, edges = scan_sample()
        entries = entry_points(modules, edges)
        self.assertIn("main", entries)
        self.assertNotIn("core.engine", entries)
        self.assertNotIn("core.utils", entries)

    def test_orphans(self):
        modules, _, edges = scan_sample()
        self.assertEqual(orphans(modules, edges), ["orphan"])

    def test_cycle_detected(self):
        modules, _ = scan_project(CYCLE)
        cycles = find_cycles(build_edges(modules))
        self.assertEqual(len(cycles), 1)
        self.assertEqual(sorted(cycles[0]), ["a", "b"])

    def test_layers_put_entry_first(self):
        modules, _, edges = scan_sample()
        depth = layers(modules, edges)
        self.assertEqual(depth["main"], 0)
        self.assertGreater(depth["core.utils"], depth["core.engine"])


class TestAnalysis(unittest.TestCase):
    def test_dead_code(self):
        modules, _, _ = scan_sample()
        dead = {(d.module, d.name) for d in find_dead_code(modules)}
        self.assertIn(("core.engine", "unused_engine_helper"), dead)
        self.assertIn(("orphan", "orphan_fn"), dead)
        # called functions and entry points are never dead
        self.assertNotIn(("core.engine", "run"), dead)
        self.assertNotIn(("main", "main"), dead)

    def test_hotspots(self):
        modules, _, _ = scan_sample()
        spots = hotspots(modules)
        self.assertTrue(any(h.name == "check_result" and h.complexity >= 5
                            for h in spots))

    def test_summary(self):
        modules, _, edges = scan_sample()
        summary = summarize(modules, edges)
        self.assertEqual(summary.modules, 5)
        self.assertEqual(summary.total_edges, 2)


class TestReports(unittest.TestCase):
    def _reports(self):
        modules, counts, edges = scan_sample()
        cycles = find_cycles(edges)
        entries = entry_points(modules, edges)
        orphan_list = orphans(modules, edges)
        dead = find_dead_code(modules)
        spots = hotspots(modules)
        summary = summarize(modules, edges)
        depth = layers(modules, edges)
        return build_all("sample", modules, counts, edges, cycles, entries,
                         orphan_list, dead, spots, summary, depth)

    def test_markdown_sections(self):
        md = self._reports()["md"]
        self.assertIn("## Start here (entry points)", md)
        self.assertIn("## Orphan modules", md)
        self.assertIn("## Possibly dead code", md)
        self.assertIn("unused_engine_helper", md)

    def test_json_round_trips(self):
        data = json.loads(self._reports()["json"])
        self.assertEqual(data["summary"]["modules"], 5)
        self.assertEqual(data["orphans"], ["orphan"])

    def test_html_has_svg(self):
        html_doc = self._reports()["html"]
        self.assertIn("<svg", html_doc)
        self.assertIn("core.engine", html_doc)


class TestCli(unittest.TestCase):
    def test_scan_all_formats_and_cycle_exit_code(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = os.path.join(os.path.dirname(__file__), "..", "src")
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, "-m", "repoxray", "scan", SAMPLE,
                 "--format", "all", "--quiet"],
                cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            for filename in ("ARCHITECTURE.md", "architecture.json",
                             "architecture-map.html"):
                self.assertTrue(os.path.exists(os.path.join(tmp, filename)),
                                filename)
            proc = subprocess.run(
                [sys.executable, "-m", "repoxray", "scan", CYCLE,
                 "--format", "md", "--quiet"],
                cwd=tmp, env=env, capture_output=True, text=True)
            # exit code 1 = cycles found (still a successful report)
            self.assertEqual(proc.returncode, 1, proc.stderr)
            self.assertIn("Import cycles", proc.stdout)

    def test_bad_path(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = os.path.join(os.path.dirname(__file__), "..", "src")
        proc = subprocess.run(
            [sys.executable, "-m", "repoxray", "scan", "/no/such/dir"],
            env=env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
