"""Resolve and verify the packaged text runtime without developer-tree fallbacks."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading

PROTOCOL = "large-text-cli-v1"
CAPABILITIES = ("file_info", "extract_lines", "search_text", "search_crypto_magic")

class RuntimeFailure(Exception):
    def __init__(self, code: str, message: str, *, next_action: str | None = None):
        super().__init__(message)
        self.payload = {"code": code, "message": message}
        if next_action:
            self.payload["next_action"] = next_action

def _number(name: str, default: int, minimum: int = 0, maximum: int | None = None) -> int:
    try:
        result = int(os.environ.get(name, str(default)))
    except ValueError:
        raise RuntimeFailure("runtime_configuration_invalid", f"{name} must be an integer") from None
    if result < minimum or maximum is not None and result > maximum:
        raise RuntimeFailure("runtime_configuration_invalid", f"{name} is outside its supported range")
    return result

class TextRuntime:
    def __init__(self, base: Path | None = None):
        self.base = (base or Path(__file__).resolve().parent).resolve()
        self.path: Path | None = None
        self.source = "override" if os.environ.get("LARGE_TEXT_VIEWER_BIN") else "bundled"
        self.failure: RuntimeFailure | None = None
        self.info: dict = {}
        self.identity = None
        self.expected_hash: str | None = None
        self.lock = threading.RLock()
        self.probe()

    def _resolve(self) -> Path:
        override = os.environ.get("LARGE_TEXT_VIEWER_BIN")
        if override:
            candidate = Path(override)
            if not candidate.is_absolute():
                raise RuntimeFailure("runtime_configuration_invalid", "LARGE_TEXT_VIEWER_BIN must be an absolute path")
            return candidate.resolve()
        manifest_path = self.base / "runtime.json"
        if not manifest_path.is_file():
            raise RuntimeFailure("runtime_missing", "The packaged text runtime is not installed", next_action="Install a complete package or set LARGE_TEXT_VIEWER_BIN")
        try:
            if manifest_path.stat().st_size > 65536:
                raise ValueError()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            candidate = (self.base / manifest["executable"]).resolve()
            expected = manifest["sha256"]
            if manifest["schema"] != 1 or manifest["protocol"] != PROTOCOL or not candidate.is_relative_to(self.base):
                raise ValueError()
            if not isinstance(expected, str) or len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
                raise ValueError()
        except (OSError, KeyError, TypeError, ValueError):
            raise RuntimeFailure("runtime_manifest_invalid", "The packaged runtime manifest is invalid") from None
        self.expected_hash = expected
        return candidate

    @staticmethod
    def _identity(path: Path):
        st = path.stat()
        return st.st_size, st.st_mtime_ns, st.st_ino

    def probe(self) -> dict:
        with self.lock:
            self.failure = None
            self.info = {}
            self.identity = None
            try:
                self.path = self._resolve()
                if not self.path.is_file() or os.name != "nt" and not os.access(self.path, os.X_OK):
                    raise RuntimeFailure("runtime_missing", "The selected text runtime is unavailable", next_action="Install a complete package or correct LARGE_TEXT_VIEWER_BIN")
                if self.expected_hash:
                    with self.path.open("rb") as binary:
                        actual_hash = hashlib.file_digest(binary, "sha256").hexdigest()
                    if actual_hash != self.expected_hash:
                        raise RuntimeFailure("runtime_integrity_mismatch", "Packaged runtime identity differs from its manifest")
                deadline = _number("LARGE_TEXT_STARTUP_TIMEOUT_MS", 5000)
                completed = subprocess.run([str(self.path), "--capabilities"], capture_output=True,
                    timeout=None if deadline == 0 else deadline / 1000,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                if completed.returncode != 0 or len(completed.stdout) > 65536:
                    raise RuntimeFailure("runtime_incompatible", "The selected runtime does not implement the packaged text protocol")
                try:
                    info = json.loads(completed.stdout.decode("utf-8"))
                    if not isinstance(info, dict) or not isinstance(info.get("commands"), list) or not all(isinstance(command, str) for command in info["commands"]) or info.get("protocol") != PROTOCOL or not {"info", "lines", "search"}.issubset(info["commands"]) or info.get("output_limit") is not True:
                        raise ValueError()
                except (UnicodeError, ValueError, TypeError):
                    raise RuntimeFailure("runtime_incompatible", "The selected runtime does not implement the packaged text protocol") from None
                _number("LARGE_TEXT_TOOL_TIMEOUT_MS", 0)
                _number("LARGE_TEXT_MAX_OUTPUT_BYTES", 262144, 1024, 8 * 1024 * 1024)
                self.info = info
                self.identity = self._identity(self.path)
            except RuntimeFailure as failure:
                self.failure = failure
            except subprocess.TimeoutExpired:
                self.failure = RuntimeFailure("runtime_probe_timeout", "Text runtime startup probe exceeded the configured deadline")
            except OSError:
                self.failure = RuntimeFailure("runtime_unavailable", "The selected runtime could not be inspected or started")
            return self.health()

    def health(self, include_paths: bool = False) -> dict:
        result = {"ready": self.failure is None, "source": self.source, "startup_checked": True,
            "protocol": self.info.get("protocol"), "version": self.info.get("version"),
            "integrity_verified": self.failure is None and self.expected_hash is not None,
            "capabilities": {name: self.failure is None for name in CAPABILITIES}}
        if self.failure:
            result["error"] = self.failure.payload
        if include_paths and self.path is not None:
            result["executable_path"] = str(self.path)
        return result

    def execute(self, arguments: list[str]) -> str:
        with self.lock:
            try:
                if self.path is None or self.identity != self._identity(self.path):
                    self.probe()
            except OSError:
                self.probe()
            if self.failure:
                raise self.failure
            output_limit = _number("LARGE_TEXT_MAX_OUTPUT_BYTES", 262144, 1024, 8 * 1024 * 1024)
            deadline = _number("LARGE_TEXT_TOOL_TIMEOUT_MS", 0)
            executable = str(self.path)
        try:
            completed = subprocess.run([executable, *arguments, "--max-output-bytes", str(output_limit)], capture_output=True,
                timeout=None if deadline == 0 else deadline / 1000,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except subprocess.TimeoutExpired:
            raise RuntimeFailure("request_timeout", "Text request exceeded the configured deadline", next_action="Increase LARGE_TEXT_TOOL_TIMEOUT_MS or set it to 0") from None
        except OSError:
            raise RuntimeFailure("runtime_unavailable", "The text runtime could not be started") from None
        if completed.returncode:
            code = "output_limit_exceeded" if b"output_limit_exceeded" in completed.stderr else "native_command_failed"
            raise RuntimeFailure(code, "Text request did not complete", next_action="Use a smaller line/count/context window" if code == "output_limit_exceeded" else "Check the file and search arguments")
        if len(completed.stdout) > output_limit:
            raise RuntimeFailure("output_limit_exceeded", "Text request exceeded the configured output budget")
        try:
            return completed.stdout.decode("utf-8")
        except UnicodeError:
            raise RuntimeFailure("runtime_protocol_error", "Text runtime returned invalid UTF-8") from None

_runtime: TextRuntime | None = None

def get_runtime() -> TextRuntime:
    global _runtime
    if _runtime is None:
        _runtime = TextRuntime()
    return _runtime
