#!/usr/bin/env python3
"""Create a source-only release archive; exclude local builds and private caches."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from setup import bundle_files


def main():
    version = json.loads((ROOT / "manifest.json").read_text())["version"]
    name = f"omarchy-mouse-style-{version}"
    output = ROOT / "build/dist" / (name + ".tar.gz")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as archive:
        for relative in sorted(set(bundle_files(ROOT)) | {Path("AGENTS.md"), Path(".gitignore")}):
            archive.add(ROOT / relative, arcname=str(Path(name) / relative), recursive=False)
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name(output.name + ".sha256").write_text(f"{checksum}  {output.name}\n")
    print(output)


if __name__ == "__main__":
    main()
