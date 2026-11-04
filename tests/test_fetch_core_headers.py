#!/usr/bin/env python3
"""Offline regression tests for downloading exact-tag MaaCore public headers."""
import base64
import hashlib
import importlib.util
import io
from urllib.error import HTTPError, URLError
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

script = Path(__file__).resolve().parents[1] / "scripts/fetch_core_headers.py"
spec = importlib.util.spec_from_file_location("fetch_core_headers", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def file_entry(path, data):
    sha = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    listing = {"path": path, "type": "file", "size": len(data), "sha": sha}
    content = {"path": path, "type": "file", "encoding": "base64", "content": base64.b64encode(data).decode(), "sha": sha}
    return listing, content


class HeaderDownloadTests(unittest.TestCase):
    def make_data(self):
        a, a_content = file_entry("include/AsstCaller.h", b"#pragma once\n")
        b, b_content = file_entry("include/AsstCallerExtra.h", b"#pragma once\n")
        c, c_content = file_entry("include/subdir/AsstDef.h", b"#define A 1\n")
        data = {
            "include": [a, b, {"path": "include/subdir", "type": "dir"}],
            "include/AsstCaller.h": a_content,
            "include/AsstCallerExtra.h": b_content,
            "include/subdir": [c],
            "include/subdir/AsstDef.h": c_content,
        }
        return data

    def test_download_validates_tag_sha_and_recursive_content(self):
        data = self.make_data()
        with tempfile.TemporaryDirectory() as d:
            with patch.object(module, "request_json", side_effect=lambda path, tag, token: data[path]) as fn:
                files = module.download("v6.21.3", Path(d), "mock-token")
            self.assertEqual(len(files), 3)
            self.assertEqual((Path(d) / "subdir/AsstDef.h").read_text(), "#define A 1\n")
            self.assertTrue(all(call.args[1] == "v6.21.3" for call in fn.call_args_list))

    def test_bad_sha_is_rejected(self):
        data = self.make_data()
        data["include/AsstCaller.h"]["sha"] = "0" * 40
        with tempfile.TemporaryDirectory() as d:
            with patch.object(module, "request_json", side_effect=lambda path, tag, token: data[path]):
                with self.assertRaisesRegex(module.HeaderDownloadError, "SHA mismatch"):
                    module.download("v6.21.3", Path(d), "mock-token")

    def test_bad_size_is_rejected(self):
        data = self.make_data()
        data["include/AsstCaller.h"]["content"] = base64.b64encode(b"wrong").decode()
        with tempfile.TemporaryDirectory() as d:
            with patch.object(module, "request_json", side_effect=lambda path, tag, token: data[path]):
                with self.assertRaisesRegex(module.HeaderDownloadError, "size mismatch"):
                    module.download("v6.21.3", Path(d), "mock-token")

    def test_unsafe_path_is_rejected(self):
        data = self.make_data()
        data["include"].append({"path": "include/../steal", "type": "file", "size": 0})
        with tempfile.TemporaryDirectory() as d:
            with patch.object(module, "request_json", side_effect=lambda path, tag, token: data[path]):
                with self.assertRaisesRegex(module.HeaderDownloadError, "Unsafe"):
                    module.download("v6.21.3", Path(d), "mock-token")

    def test_temporary_http_error_retries(self):
        err = HTTPError("https://api.github.com/example", 503, "busy", {}, None)
        with patch.object(module, "urlopen", side_effect=[err, io.BytesIO(b"[]")]) as remote:
            with patch.object(module.time, "sleep") as pause:
                result = module.request_json("include", "v6.21.3", "test")
        self.assertEqual(result, [])
        self.assertEqual(remote.call_count, 2)
        pause.assert_called_once()

    def test_permanent_http_error_does_not_retry(self):
        err = HTTPError("https://api.github.com/example", 404, "not found", {}, None)
        with patch.object(module, "urlopen", side_effect=err) as remote:
            with self.assertRaisesRegex(module.HeaderDownloadError, "HTTP 404"):
                module.request_json("include", "v6.21.3", "test")
        remote.assert_called_once()

    def test_incorrect_tag_fails_before_network(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(module, "request_json") as fn:
                with self.assertRaisesRegex(module.HeaderDownloadError, "Invalid MAA release tag"):
                    module.download("v6.21.3; rm -rf ./", Path(d), "mock-token")
            fn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
