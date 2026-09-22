# Mac Sequoia reference (0.3)

This is an experimental **measured reference**, not a port of Apple's private
runtime or a claim of bit-for-bit macOS equivalence.

## Source and reproducibility

Pinned source: [INRIA/libpointing](https://github.com/INRIA/libpointing/tree/ecb67da58145343c9fa64211d629730134fe74ae/pointing-echomouse/darwin-24).
The dataset identifies macOS Sequoia 15.3.2 (Darwin 24.3.0), a 400-CPI/125-Hz input,
and a 1728×1117 display at 120 Hz. It has ten tracking levels, aliases
0, 0.125, 0.5, 0.6875, 0.875, 1, 1.5, 2, 2.5, and 3; level 4 is its default.
We preserve all ten tables without modification.

[UPSTREAM.json](../vendor/libpointing-sequoia/UPSTREAM.json) records the revision,
original paths, and SHA-256 hashes. The build checks every hash and generates a
header from the data offline. `tests/check_mac_reference.py` checks the compiled
replay tool against all 1,280 published axis samples, not against another copy of
the engine formula.

## Transfer convention

The adapter follows the table convention of libpointing's
[Interpolation::applyd with normalization disabled](https://github.com/INRIA/libpointing/blob/ecb67da58145343c9fa64211d629730134fe74ae/pointing/transferfunctions/Interpolation.cpp):

- Each physical relative report supplies both axes together.
- Its index is `floor(hypot(dx, dy))`.
- The gain is the selected level's measured output divided by the index.
- Apply the same gain to both axes; preserve fractional output for the compositor.
- Past the last measured point (127 counts), hold the endpoint gain as libpointing
  does. This is defined extrapolation, not an additional macOS measurement.

There is no guessed timestamp correction, sensor-DPI inference, or monitor-PPI
normalization. This preserves the published reference semantics. It also means
that other device resolutions, rates, and display scales can feel different.
High-rate behavior, macOS temporal behavior, diagonals on a real Mac, and physical
latency have not been independently validated. Matching a measured axis table is
not equivalent to reproducing every internal macOS state transition.

The Mac reference includes pointer acceleration; this release has no verified
acceleration-off reference and does not expose a fabricated one. Natural scrolling
and primary-button choice use Hyprland's native options while Mac is active.
Wheel momentum, Apple scroll acceleration, gestures, and double-click timing are
not implemented by this pointer module.

## Integration

The optional `pointer-feel-mac.so` module uses the same inspected Hyprland motion
entry point as the existing Windows module, with the compositor ABI check intact.
The controller unloads the current engine before loading the selected one. Mac
initialization additionally refuses to load over Windows. Only one hook is active;
the existing Windows binary and engine remain unchanged. Do not load these modules
manually on top of each other or add competing startup loaders.

Omarchy unloads both. Raw relative events are preserved. Touchpads, virtual devices,
non-mouse events, and fractional/rotated raw reports bypass the Mac transformation.
The profile's global scroll/button choices remain subject to device overrides.
No kernel module, root service, event grabber, or second desktop shell is required.

Tracking 1–10, natural scrolling, and primary-button choice are saved independently
under `mac` in schema version 3. Versions 1/2 are migrated with existing preferences
intact. Trial tokens, the 15-second watchdog, backend readback, Keep, Revert, and
login restore use the existing controller.

## License and provenance

The tables and their accompanying license declaration are GPL-2.0-or-later.
The Mac engine/replay/module sources use GPL-2.0-or-later; retain their corresponding
source and [license files](../vendor/libpointing-sequoia/LICENSE.md) when distributing
binaries. [COPYING](../vendor/libpointing-sequoia/COPYING) is included.

The Hyprland hook/config integration is adapted from the pinned
windows-pointer-linux adapter and the existing local 0.56 compatibility changes;
its [BSD-3-Clause notice](../vendor/windows-pointer-linux/LICENSE) is retained.
The Windows reference engine remains under its original BSD license. The unlicensed
Apple research-cache implementation files are neither copied into this module nor
compiled. This does not resolve the separate licensing/reproduction work for a
future direct Apple engine port.

## Local validation on 2026-09-20

- Six Mac engine tests and 18 unchanged Windows engine tests passed.
- All 1,280 measured samples matched the compiled Mac engine.
- 39 controller/installer tests and the queued-action QML test passed.
- The matching 0.56.2 module loaded; actual mouse reports increased its processed
  counter (1,293 observed in the first captured trial).
- Tracking/scroll/button values, save/restore, Mac↔Omarchy/Windows transitions,
  and rollback were read back; at most one engine was loaded at each check.
- The Mac panel was visually inspected. Original saved preferences were restored
  after tests. `hyprctl configerrors` was empty.

Mac-specific feel approval, real logout/reboot, multiple hardware models, and independent
Mac comparison remain pending.

## Tracking control investigation (0.3.1)

The 0.3 panel only updated a local draft until **Try Mac settings** was clicked.
Moving the slider alone therefore had no engine effect. All profile controls now
apply directly; sliders apply on release and active trials remain adjustable.
The original Mac engine and published tables are unchanged.

Compiled replay outputs for a horizontal raw packet (not physical distances):

| Tracking | Raw 1 | Raw 10 | Raw 50 |
|---|---:|---:|---:|
| 1 | 0.242253 | 2.43841 | 12.196 |
| 4 | 0.230339 | 6.28665 | 60.8906 |
| 7 | 0.258138 | 10.0436 | 103.891 |
| 8 | 0.309766 | 12.0531 | 124.668 |
| 10 | 0.413021 | 16.0721 | 166.227 |

Levels differ substantially for larger packets; some slow-movement values are
close and not monotonically ordered across measured levels. For example, 4→7
changes raw-1 output by about 12%, versus about 71% at raw-50. These are properties
of this measured reference, not proof of present macOS behavior or perceived
movement on another device. Do not rescale the engine merely to make the slider
appear stronger.

Live readback also confirmed tracking 1, 10, 4, and 7 in sequence through the
installed module. Repeated edits/style switches expired back to the original
Windows state; Keep/restore saved the final adjusted value. Pre-test preferences
(including the user's saved Mac level 7) were restored afterward.
