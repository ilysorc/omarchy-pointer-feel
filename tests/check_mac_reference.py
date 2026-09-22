#!/usr/bin/env python3
"""Compare all 1,280 published axis samples with the compiled Mac replay tool."""
from pathlib import Path
import argparse
import math
import re
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--binary', type=Path, default=root / 'build/mouse-style-mac-replay')
binary = parser.parse_args().binary.resolve()
checked = 0
for tracking in range(1, 11):
    table = (root / f'vendor/libpointing-sequoia/f{tracking}.dat').read_text()
    samples = dict((int(x), float(y)) for x, y in re.findall(r'^(\d+): ([\d.]+)$', table, re.M))
    output = subprocess.check_output([str(binary), str(tracking)],
                                     input=''.join(f'{x} 0\n' for x in range(128)), text=True)
    rows = output.splitlines()
    assert len(rows) == 128
    for x, row in enumerate(rows):
        dx, dy = map(float, row.split())
        assert math.isclose(dx, samples[x], abs_tol=1e-8) and dy == 0, (tracking, x, row, samples[x])
        checked += 1
print(f'PASS: {checked} published Sequoia samples match the compiled engine.')
