"""Offline safety and completeness checks for downloaded research evidence."""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from colab.import_results import extract, verify_session
from protocol import write_json


class ImportTests(unittest.TestCase):
    def test_archive_rejects_traversal_and_nonresult_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("../outside.json", "model.safetensors", "credentials.env"):
                archive = root / "bad.zip"
                with zipfile.ZipFile(archive, "w") as output:
                    output.writestr(name, "test")
                with self.subTest(name=name), self.assertRaises(ValueError):
                    extract(archive, root / "results")

    def test_missing_baselines_never_become_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "execution-profile.json", {"source_sha256": {}, "gpu": "test GPU"})
            with patch("colab.import_results.source_hashes", return_value={}):
                report = verify_session(root)
            self.assertEqual(report["status"], "incomplete")
            self.assertEqual(report["baselines"], [])

    def test_import_checks_frozen_source_before_reading_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "execution-profile.json", {"source_sha256": {"changed": "source"}})
            with self.assertRaisesRegex(RuntimeError, "Archived source differs"):
                verify_session(root)


if __name__ == "__main__":
    unittest.main()
