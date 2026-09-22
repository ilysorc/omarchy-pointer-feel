#!/usr/bin/env python3
"""Build a header from pinned, hash-verified Sequoia measurements (offline)."""
import hashlib
import json
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
vendor = root / 'vendor/libpointing-sequoia'
metadata = json.loads((vendor / 'UPSTREAM.json').read_text())
for record in metadata['files']:
    assert hashlib.sha256((vendor / record['path']).read_bytes()).hexdigest() == record['sha256'], record['path']
curves = []
for index in range(1, 11):
    entries = dict((int(x), float(y)) for x, y in re.findall(r'^(\d+): ([\d.]+)$', (vendor / f'f{index}.dat').read_text(), re.M))
    assert sorted(entries) == list(range(128))
    assert entries[0] == 0 and all(entries[x] > 0 for x in range(1,128))
    curves.append('    {{' + ', '.join(str(entries[x]) for x in range(128)) + '}}')
output = '''// Generated from libpointing darwin-24. Do not hand-edit.
// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright Inria. Provenance: vendor/libpointing-sequoia/UPSTREAM.json.
#pragma once
#include <array>
namespace mac_reference {
inline constexpr std::array<std::array<double, 128>, 10> samples = {{
''' + ',\n'.join(curves) + '\n}};\n}\n'
Path(sys.argv[1]).write_text(output)
