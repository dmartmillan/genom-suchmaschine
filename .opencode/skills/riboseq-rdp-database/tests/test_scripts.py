"""Tests that never contact the live RDP website."""
from __future__ import annotations

import argparse
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


q = load("rdp_query", "rdp_query.py")
d = load("rdp_download", "rdp_download.py")


class QueryTests(unittest.TestCase):
    def test_fields_args(self):
        args = argparse.Namespace(action="fields")
        self.assertEqual(q.build_cli_args(args), ["RDP-Tools", "database", "sample-fields"])

    def test_samples_args_preserves_values_without_shell(self):
        args = argparse.Namespace(action="samples", query="TISSUE=Brain tissue", fields="TISSUE,CELL_LINE", limit=100)
        self.assertEqual(q.build_cli_args(args), ["RDP-Tools", "database", "samples",
                                                 "--query", "TISSUE=Brain tissue",
                                                 "--fields", "TISSUE,CELL_LINE", "--limit", "100"])

    def test_invalid_query(self):
        with self.assertRaises(ValueError):
            q.build_cli_args(argparse.Namespace(action="samples", query="TISSUE=", fields=None, limit=100))


class DownloadTests(unittest.TestCase):
    def test_safe_url(self):
        self.assertEqual(d.safe_url("https://rdp.ucc.ie/dataset", {"rdp.ucc.ie"}),
                         "https://rdp.ucc.ie/dataset")
        for url in ("http://rdp.ucc.ie/file", "https://localhost/file", "https://evil.test/file",
                    "https://rdp.ucc.ie:444/file", "https://user:pass@rdp.ucc.ie/file",
                    "file:///etc/passwd", "https://127.0.0.1/file"):
            with self.subTest(url=url), self.assertRaises(d.DownloadError):
                d.safe_url(url, {"rdp.ucc.ie"})

    def test_path_traversal(self):
        for name in ("../evil", "C:\\test", "", ".secret", "x/y"):
            with self.subTest(name=name), self.assertRaises(d.DownloadError):
                d.safe_filename(name)
        self.assertEqual(d.safe_filename("SRR12345.bam"), "SRR12345.bam")

    def test_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.csv"
            path.write_text("url,filename\nhttps://rdp.ucc.ie/a,S1.bam\n", encoding="utf-8")
            self.assertEqual(d.read_manifest(path), [("https://rdp.ucc.ie/a", "S1.bam")])
            path.write_text("url,filename\nhttps://rdp.ucc.ie/a,../bad\n", encoding="utf-8")
            with self.assertRaises(d.DownloadError):
                d.read_manifest(path)

    def test_empty_manifest_is_not_downloadable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.csv"
            path.write_text("url,filename\n", encoding="utf-8")
            with self.assertRaises(d.DownloadError):
                d.read_manifest(path)


if __name__ == "__main__":
    unittest.main()
