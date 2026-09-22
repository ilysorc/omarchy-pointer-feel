#!/usr/bin/env python3
"""Check release completeness, pinned vendor hashes and extracted source identity."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from setup import bundle_files, source_revision


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    version = manifest["version"]
    cmake = (ROOT / "CMakeLists.txt").read_text()
    assert re.search(r"project\(omarchy_mouse_style VERSION " + re.escape(version) + r"\b", cmake)
    assert manifest["license"] == "GPL-2.0-or-later"
    for path in manifest["entryPoints"].values():
        assert (ROOT / path).is_file(), path
    checked = 0
    for directory in (ROOT / "vendor").iterdir():
        if not directory.is_dir():
            continue
        record = json.loads((directory / "UPSTREAM.json").read_text())
        for file in record["files"]:
            actual = hashlib.sha256((directory / file["path"]).read_bytes()).hexdigest()
            assert actual == file["sha256"], f"Vendor checksum mismatch: {directory.name}/{file['path']}"
            checked += 1
    preview = (ROOT / "preview.png").read_bytes()
    assert preview[:8] == b"\x89PNG\r\n\x1a\n", "Invalid PNG preview"
    width, height = struct.unpack(">II", preview[16:24])
    assert 0 < width * height <= 40_000_000 and len(preview) <= 50_000_000
    subprocess.run([sys.executable, str(ROOT / "tools/package.py")], check=True)
    archive = ROOT / "build/dist" / f"omarchy-mouse-style-{version}.tar.gz"
    expected = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert archive.with_name(archive.name + ".sha256").read_text().split()[0] == expected
    with tempfile.TemporaryDirectory(prefix="mouse-style-release-") as temp:
        with tarfile.open(archive) as package:
            package.extractall(temp, filter="data")
        extracted = Path(temp) / f"omarchy-mouse-style-{version}"
        assert source_revision(extracted) == source_revision(ROOT)
        for relative in bundle_files(ROOT):
            assert (extracted / relative).read_bytes() == (ROOT / relative).read_bytes(), relative
        assert (extracted / "install.sh").stat().st_mode & 0o111, "Installer is not executable"
        assert not list(extracted.rglob("*.so")), "Source archive contains a compiled module"
        assert not (extracted / "build").exists() and not (extracted / ".research").exists()
    print(f"PASS: v{version} source archive, {checked} vendor checksums, preview and extracted source identity.")


if __name__ == "__main__":
    main()
