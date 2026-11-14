"""Verify package installation and single-entry config edits using owned fixtures."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("install_runtime", ROOT / "tools/install_runtime.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

CONFIG = '''# Owned config; never the real user config.
model = "selected-model"
[mcp_servers.other]
command = "other-command"
args = ["keep-other-args"]
[mcp_servers.other.env]
PRIVATE_VALUE = "owned-placeholder"
[mcp_servers.large-text-searcher]
command = "python"
args = ["old/server.py"]
startup_timeout_sec = 120
[mcp_servers.large-text-searcher.env]
LARGE_TEXT_VIEWER_BIN = "D:/owned-absent/runtime.exe"
KEEP_ME = "owned-private-placeholder"
'''


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="owned-install-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.config = self.root / "owned-config.toml"
        self.config.write_text(CONFIG, encoding="utf-8")
        self.entry = self.root / "搬迁 package" / "large_text_viewer_mcp.py"

    def assert_selected_change(self, before):
        expected = copy.deepcopy(before)
        selected = expected["mcp_servers"]["large-text-searcher"]
        selected["command"] = str(Path(sys.executable).resolve()).replace("\\", "/")
        selected["args"] = ["-B", "-X", "utf8", str(self.entry).replace("\\", "/")]
        selected["env"].pop("LARGE_TEXT_VIEWER_BIN")
        self.assertEqual(tomllib.loads(self.config.read_text(encoding="utf-8")), expected)

    def test_preserves_other_servers_and_selected_environment(self):
        before = tomllib.loads(CONFIG)
        result = installer.update_config(self.config, "large-text-searcher", self.entry)
        self.assertTrue(result["changed"])
        self.assertEqual(Path(result["backup"]).read_text(encoding="utf-8"), CONFIG)
        self.assert_selected_change(before)
        original = self.config.read_bytes()
        result = installer.update_config(self.config, "large-text-searcher", self.entry)
        self.assertFalse(result["changed"])
        self.assertEqual(self.config.read_bytes(), original)

    def test_retries_from_fresh_concurrent_config(self):
        original_read = Path.read_bytes
        reads = 0
        concurrent = CONFIG.replace('keep-other-args', 'concurrent-new-args')

        def racing_read(path):
            nonlocal reads
            if path == self.config.resolve():
                reads += 1
                if reads == 2:
                    self.config.write_text(concurrent, encoding="utf-8")
            return original_read(path)

        with patch.object(Path, "read_bytes", racing_read):
            result = installer.update_config(self.config, "large-text-searcher", self.entry)
        self.assertEqual(result["concurrent_update_retries"], 1)
        self.assert_selected_change(tomllib.loads(concurrent))

    def test_repeated_concurrent_updates_leave_latest_file_intact(self):
        original_read = Path.read_bytes
        reads = 0

        def racing_read(path):
            nonlocal reads
            if path == self.config.resolve():
                reads += 1
                if reads in (2, 4):
                    self.config.write_text(CONFIG + f"\n# concurrent-{reads}\n", encoding="utf-8")
            return original_read(path)

        with patch.object(Path, "read_bytes", racing_read):
            with self.assertRaisesRegex(ValueError, "changed concurrently"):
                installer.update_config(self.config, "large-text-searcher", self.entry)
        self.assertEqual(self.config.read_text(encoding="utf-8"), CONFIG + "\n# concurrent-4\n")

    def make_package(self):
        package = self.root / "package"
        package.mkdir()
        for name in ("large_text_viewer_mcp.py", "runtime_support.py", "crypto_magic_search.py", "requirements.txt", "THIRD-PARTY-NOTICES.txt"):
            (package / name).write_text("owned fixture\n", encoding="utf-8")
        (package / "bin").mkdir()
        (package / "bin/runtime.exe").write_bytes(b"owned fixture, never executed")
        manifest = {"schema": 1, "protocol": "large-text-cli-v1", "executable": "bin/runtime.exe", "sha256": hashlib.sha256(b"owned fixture, never executed").hexdigest()}
        (package / "runtime.json").write_text(json.dumps(manifest), encoding="utf-8")
        return package

    def run_install(self, package, version="0.1.0-owned"):
        arguments = ["install_runtime.py", "--package", str(package), "--install-root", str(self.root / "install"), "--version", version, "--codex-config", str(self.config), "--receipt", str(self.root / "receipt.json")]
        with patch.object(sys, "argv", arguments), contextlib.redirect_stdout(io.StringIO()):
            installer.main()
        return json.loads((self.root / "receipt.json").read_text(encoding="utf-8"))

    def test_idempotent_install_ignores_bytecode_only(self):
        package = self.make_package()
        (package / "__pycache__").mkdir()
        (package / "__pycache__/source.pyc").write_bytes(b"source cache")
        first = self.run_install(package)
        destination = Path(first["package_path"])
        self.assertFalse((destination / "__pycache__").exists())
        (destination / "__pycache__").mkdir()
        (destination / "__pycache__/runtime.pyc").write_bytes(b"generated cache")
        self.assertTrue(self.run_install(package)["installed"])
        (destination / "runtime_support.py").write_text("changed runtime", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "differs"):
            self.run_install(package)

    def test_rejects_version_path_escape(self):
        package = self.make_package()
        for version in ("..", ".", "../escape", "C:/escape", "..\\escape"):
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, "Invalid package version"):
                self.run_install(package, version)
        self.assertFalse((self.root / "install").exists())
        self.assertEqual(self.config.read_text(encoding="utf-8"), CONFIG)

    def test_rejects_tampered_or_escaping_runtime_before_install(self):
        package = self.make_package()
        manifest_path = package / "runtime.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["executable"] = "../runtime.exe"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "bin directory"):
            self.run_install(package)
        manifest["executable"] = "bin/runtime.exe"
        manifest["sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "integrity"):
            self.run_install(package)
        self.assertFalse((self.root / "install").exists())
        self.assertEqual(self.config.read_text(encoding="utf-8"), CONFIG)


if __name__ == "__main__":
    unittest.main()
