#!/usr/bin/env python3
"""Compatibility entry point: install all required Mouse Style components."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
# Retained for callers of the old routing helpers.
sys.path.insert(0, str(ROOT))
from setup import input_config, startup_config
from mouse_style import ControlError

if __name__ == "__main__":
    os.execv("/usr/bin/bash", ["bash", str(ROOT / "install.sh"), *sys.argv[1:]])
