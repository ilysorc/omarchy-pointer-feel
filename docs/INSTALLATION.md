# Installation contract and validation

Date: 2026-09-22. Version: 1.0.0. Current target: Omarchy / Hyprland 0.56.2.

`./install.sh` owns one complete setup: consent, package preflight, installing
missing packages, building both native modules, transactional activation,
readback, preference preservation and bar integration. First-use QML calls that
same entry point; no second Quickshell process or separate terminal is required.

The setup worker is independent of the panel's 25-second pointer-command timeout.
It reports progress through a state file and captures its background log. Closing
the panel does not cancel a package-manager transaction. Authentication refusal,
package failure, compile failure, incompatible headers, unsupported compositor,
and active pointer trials never report a successful installation.

The updater preserves the active profile, all saved per-profile settings and the
bar label. Native module replacement is atomic and happens only while unloaded.
Rollback covers the generated configuration, integration routes, launchers,
native modules, receipt and files deployed into a development copy. A persistent
journal permits recovery after process interruption. Shared packages and user
preferences/backups are retained on full removal.

## Verification record: 0.4.0 on 2026-09-21

- 68 Python tests pass. Isolated-home tests drive the full installer transaction
  with fake system commands: fresh install, missing packages, authentication
  cancellation, build/load failure, rollback, interruption recovery, repeated
  setup, ABI repair restoring the saved style, headers without an includedir
  variable, competing workers, and complete removal preserving unrelated edits.
- Both native modules compile from the bundled sources with GCC 16.2.1 against
  the running Hyprland 0.56.2. All 24 native tests and 1,280 table samples pass.
- Actual SetupState/SetupPanel QML is exercised offscreen with a fake installer.
  The button starts installation, progress disables duplicate clicks, and closing
  the panel does not terminate the worker. Existing pointer-panel and queued
  polling regression tests still pass.
- A regression test reproduces the false Setup screen by polling between native
  module unload/load and between Keep removing the trial and saving preferences.
  Before the fix, ten checkpoints reported an incomplete installation. Readiness
  now remains true across profile switches, trial replacement, Keep and Revert.
  Source/ABI changes, missing/corrupt binaries and removed integration still
  require setup. Runtime-only repair restores the saved profile without a build.
- On the live desktop after deployment, six trial switches (Omarchy, Win, Mac,
  Win, Omarchy, Win) ran alongside 74 readiness samples: zero false Setup results
  or read errors. Revert restored the original Win profile; saved preferences,
  bar label and absence of a pending trial were verified unchanged.
- The real unified installer ran successfully on the working desktop. Win 10/20
  with EPP, Mac tracking 7 and its scroll/button preferences, Omarchy preferences,
  Letter display and no active trial were preserved. Each engine was loaded and
  read back during activation; native configuration validation remained clean.
- A second identical installation did not rebuild or install packages. Both the
  source and installed bundle report readiness. The installed bar opens with no
  QML runtime errors in the journal.
- Extracted distribution sources match the repository's runtime-source digest;
  the archive's installer plan validates. Windows source/patch checksums match.
- Bootstrap status with missing Python remains read-only regardless of flag order.

Package installation and cancellation branches use controlled fake commands in
isolated tests because the live desktop already has the dependencies. No system
packages were removed to manufacture a missing-dependency case. A separate clean
OS/VM installation remains untested. This publication check does not repeat a
live destructive uninstall; removal coverage comes from isolated transactions.

For the 2026-09-22 publication check, the suite now has 70 Python tests, including
Git-managed checkout boundaries. Fresh native compilation, all 24 native tests,
1,280 reference samples and the actual QML panel/polling/setup tests pass. See
[publication readiness](PUBLISHING.md) for packaging, CI and marketplace status.

## Identity migration verified on 2026-09-22

The active installation was moved to `ilysorc.pointer-feel`, `pointer-feel`,
`pointer_feel.py`, `~/.config/pointer-feel`, `~/.local/state/pointer-feel`,
`~/.config/hypr/pointer-feel.lua` and `pointer-feel-mac.so`. The source and private
GitHub repository are named `omarchy-pointer-feel`.

Before cutover, 70 Python tests, all three actual QML checks, 24 native tests and
1,280 Mac reference samples passed with the renamed paths. Both modules were
built against the running ABI. The prior full uninstaller and the renamed
installer's normal activation/rollback transaction performed the cutover.
Saved profile and UI values, active Windows behavior and the bar position were
preserved. Installation readiness and Hyprland configuration checks passed.
Retired files and recovery copies are archived outside the active source and
plugin trees. The rename adds no trackpad functionality or OS-parity claims.

## Version 1.0.0 preparation on 2026-09-22

The real installer rebuilt both native modules and verified profile activation
for 1.0.0. The owned Mac module now reports the CMake project version rather than
a separate stale literal. Saved profile/UI files remained byte-for-byte identical,
the active Windows profile was restored, no trial remained, and both source and
installed bundles reported ready with no Hyprland configuration errors. The
source archive and its extracted runtime identity passed release validation.
This version change adds no device support or algorithm-parity claim.

## Boundaries

The package manager itself is not rolled back after a later compile/load error.
An unsupported Hyprland ABI may need a source compatibility update, not merely
recompilation. Setup does not upgrade the whole OS or bypass native ABI checks.
The current compatibility target is the tested 0.56.2 source API; it is not a
promise of compatibility with every future compositor release.

Omarchy's plain `plugin remove` only removes its repository/widget; full removal
must use `pointer-feel uninstall` first. Preferences and system packages remain
intentionally. No automatic deletion of unrelated packages or backup history is
performed.
