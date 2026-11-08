"""Offline fixture tests; not a live endpoint verification."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from omix import accession, parse_record, url_is_official_download, size_gb, draft_request, OmixError

URL = "https://ngdc.cncb.ac.cn/omix/release/OMIX007792"
PUBLIC_HTML = """<html><body><h1>OMIX007792</h1>
<table><tr><th>Title</th><td>Expression atlas</td></tr>
<tr><th>Organism</th><td>Mus musculus</td></tr>
<tr><th>Data Accessibility</th><td>Open-access</td></tr>
<tr><th>BioProject</th><td>PRJCA123456</td></tr></table>
<table><thead><tr><th>File ID</th><th>File Title</th><th>Number/Samples</th><th>File Type</th><th>File Size</th><th>File Suffix</th><th>Download</th></tr></thead>
<tbody><tr><td>OMIX007792-03</td><td>matrix.mtx.gz</td><td>3</td><td>Expression Profiling</td><td>27.8 MB</td><td>gz</td>
<td><a href="ftp://download.cncb.ac.cn/OMIX/OMIX007792/OMIX007792-03.gz">FTP</a>
<a href="https://download.cncb.ac.cn/OMIX/OMIX007792/OMIX007792-03.gz">HTTPs</a></td></tr></tbody></table>
</body></html>"""
CONTROLLED_HTML = """<html><body><h1>OMIX010131</h1>
<table><tr><td>Title</td><td>Plasma metabolomics data</td></tr>
<tr><td>Data Accessibility</td><td>Controlled-access</td></tr></table>
<p>To request data access, please <a href="https://cbb.cncb.ac.cn/abb/">visit ABB and submit your application</a>.</p>
<table><tr><th>File ID</th><th>File Title</th><th>Number/Samples</th><th>File Type</th><th>File Size</th><th>File Suffix</th><th>Download</th></tr>
<tr><td>OMIX010131-01</td><td>Private data</td><td>10</td><td>Metabolome</td><td>23 GB</td><td>zip</td><td>Controlled</td></tr></table>
</body></html>"""

class TestOmix(unittest.TestCase):
    def test_public_file_discovery(self):
        r = parse_record(PUBLIC_HTML, URL, "OMIX007792")
        self.assertEqual(r["title"], "Expression atlas")
        self.assertEqual(r["access_type"], "Open-access")
        self.assertEqual(len(r["files"]), 1)
        self.assertEqual(r["files"][0]["file_id"], "OMIX007792-03")
        self.assertEqual(len(r["files"][0]["https_urls"]), 1)
        self.assertEqual(len(r["files"][0]["ftp_urls"]), 1)
    def test_controlled_application_no_file_url(self):
        r = parse_record(CONTROLLED_HTML, URL.replace("OMIX007792", "OMIX010131"), "OMIX010131")
        self.assertEqual(r["access_type"], "Controlled-access")
        self.assertEqual(r["files"][0]["https_urls"], [])
        self.assertEqual(r["access_request_links"][0]["url"], "https://cbb.cncb.ac.cn/abb/")
        self.assertIn("ethics approval", draft_request(r).lower())
    def test_bad_accession(self):
        for bad in ["../../OMIX1", "OMIXabcd", "OMIX", "OMIX1?x=y"]:
            with self.assertRaises(OmixError):
                accession(bad)
    def test_host_and_scheme_restrictions(self):
        self.assertTrue(url_is_official_download("https://download.cncb.ac.cn/OMIX/A/file.gz"))
        for bad in [
            "https://evil.example/OMIX/A/file.gz",
            "http://download.cncb.ac.cn/OMIX/A/file.gz",
            "https://download.cncb.ac.cn.evil.example/OMIX/A/file.gz",
            "https://download.cncb.ac.cn/other/A/file.gz",
        ]:
            self.assertFalse(url_is_official_download(bad))
    def test_size(self):
        self.assertAlmostEqual(size_gb("27.8 MB"), 0.0278)
        self.assertAlmostEqual(size_gb("1.5 TB"), 1500)
        self.assertIsNone(size_gb("unknown"))

if __name__ == "__main__":
    unittest.main()
