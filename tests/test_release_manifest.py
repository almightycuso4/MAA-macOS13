#!/usr/bin/env python3
"""Prevent the workflow, build default, DMG name and checksum from drifting."""
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_manifest", ROOT / "scripts/release_manifest.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ReleaseManifestTests(unittest.TestCase):
    def test_v6213_is_the_current_stable_baseline(self):
        manifest = MODULE.load_manifest()
        self.assertEqual(manifest["stable_baseline"], "v6.21.3")
        self.assertEqual(manifest["default_tag"], "v6.21.3")
        self.assertEqual(MODULE.load_manifest()["default_tag"], "v6.21.3")


    def test_readme_marks_v6213_as_tested_stable_release(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("当前稳定版本为 **v6.21.3**", readme)
        self.assertIn("macOS 13.7.4 实机", readme)
        self.assertIn("非官方兼容构建", readme)

    def test_xcode_marketing_version_matches_manifest_default(self):
        version_config = (ROOT / "src/MaaMacGui/Version.xcconfig").read_text(encoding="utf-8")
        expected = MODULE.load_manifest()["default_tag"].removeprefix("v")
        self.assertRegex(version_config, rf"(?m)^MARKETING_VERSION = {re.escape(expected)}$")

    def test_workflow_default_matches_manifest(self):
        workflow = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        match = re.search(r"(?m)^\s*default:\s*(v[0-9]+\.[0-9]+\.[0-9]+)\s*$", workflow)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), MODULE.load_manifest()["default_tag"])

    def test_build_uses_manifest_default_and_sha_check(self):
        build = (ROOT / "scripts/build.sh").read_text(encoding="utf-8")
        self.assertIn("scripts/release_manifest.py --default", build)
        self.assertIn("shasum -a 256 -c -", build)
        self.assertIn('--repo "$RELEASE_REPOSITORY"', build)
        self.assertNotIn("MAA_CORE_TAG:=v6.21.1", build)

    def test_official_dmg_name_and_sha256_are_pinned(self):
        filename, digest, repository = MODULE.asset_for("v6.21.3")
        self.assertEqual(filename, "MAA-v6.21.3-macos-universal.dmg")
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertEqual(repository, "MaaAssistantArknights/MaaRelease")

    def test_release_binary_and_header_sources_are_separated(self):
        manifest = MODULE.load_manifest()
        self.assertEqual(manifest["release_repository"], "MaaAssistantArknights/MaaRelease")
        self.assertEqual(manifest["source_repository"], "MaaAssistantArknights/MaaAssistantArknights")
        fetcher = (ROOT / "scripts/fetch_core_headers.py").read_text(encoding="utf-8")
        self.assertIn('REPOSITORY = "MaaAssistantArknights/MaaAssistantArknights"', fetcher)

    def test_unpinned_tag_is_rejected_before_download(self):
        with self.assertRaisesRegex(SystemExit, "No pinned macOS DMG/checksum"):
            MODULE.asset_for("v6.21.4")


if __name__ == "__main__":
    unittest.main()
