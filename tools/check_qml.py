#!/usr/bin/env python3
"""Lint against installed Omarchy imports; report the known Quickshell metadata gap."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
# Quickshell's installed qmltypes declares this C++ parameter but not its type.
# Runtime panel/process checks still exercise the actual exited signal.
EXIT_STATUS_WARNING = "Type QProcess::ExitStatus of parameter exitStatus in signal called exited was not found, but is required to compile onExited. Did you add all imports and dependencies?"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shell", type=Path, default=Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")) / "shell")
    args = parser.parse_args()
    compiler = shutil.which("qmllint") or "/usr/lib/qt6/bin/qmllint"
    if not args.shell.is_dir() or not Path(compiler).is_file():
        parser.error("Install Omarchy and Qt's qmllint, or pass --shell to an installed shell tree.")
    with tempfile.TemporaryDirectory(prefix="mouse-style-qml-") as temp:
        directory = Path(temp)
        (directory / "qs").symlink_to(args.shell.resolve(), target_is_directory=True)
        report = directory / "report.json"
        result = subprocess.run([compiler, "-I", str(directory), "--json", str(report),
                                 *map(str, sorted(ROOT.glob("*.qml")))], capture_output=True, text=True)
        if not report.exists():
            print(result.stdout + result.stderr)
            return 1
        unexpected, known = [], []
        data = json.loads(report.read_text())
        for file in data["files"]:
            name = Path(file["filename"]).name
            for item in file.get("warnings", []):
                if item.get("type") not in ("warning", "error", "critical", "fatal"):
                    continue
                message = f"{name}:{item.get('line', 0)}: {item['message']}"
                if (name in ("PointerState.qml", "SetupState.qml")
                        and item.get("type") == "warning" and item["message"] == EXIT_STATUS_WARNING):
                    known.append(message)
                else:
                    unexpected.append(message)
        if result.returncode or unexpected:
            print("\n".join(unexpected) or result.stdout + result.stderr)
            return 1
        print(f"PASS: {len(data['files'])} QML files; no project warnings or errors.")
        if known:
            print(f"NOTE: {len(known)} known upstream QProcess::ExitStatus metadata warnings; not a warning-free lint run.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
