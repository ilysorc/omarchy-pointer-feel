# Roadmap and acceptance criteria

Current state on 2026-09-22: Pointer Feel 1.0.0 is locally validated and the GitHub
repository is private. The initial hosted CI passed; release and marketplace
submission remain paused until the owner approves public distribution.
The owner waived the recommended clean OS/VM installation test for 1.0.0 on
2026-09-22; that environment remains unverified and is not a release gate.
See [publication readiness](PUBLISHING.md) and its submission draft. The owner approved
the current overall experience after the profile, reset, and bar-label changes.
That feedback is separate from independent algorithm equivalence, hardware
coverage, and the Mac-specific feel evaluation described below.

## Completed: research and reference harness

- Defined Win / Mac / Default / Custom semantics.
- Inspected the current Windows backend and native Omarchy settings.
- Checked Apple sources, libpointing data provenance, and licensing records.
- Pinned an unmodified Windows engine/replay/test subset with hashes and license.
- Built and passed all 18 upstream engine tests.
- Added vendor-neutral, read-only system diagnostics.

## Completed: 0.1 bar frontend and controller

- English bar widget and panel with real Win / Default transitions.
- Windows speed and EPP draft editing and backend readback.
- Persistent preferences and startup migration.
- 15-second trial, Keep/Revert, independent rollback worker, unique trial tokens.
- 16 controller/installer tests, including failure and idempotency cases.
- Live speed/EPP changes, profile switching, saved-state restore, and closed-panel
  expiry tested. Original Win 10/20 + EPP restored after agent testing.
- QML panel visually inspected and keyboard activation exercised.

This uses the existing native binary. A shared native dispatcher is not yet
implemented. Mac has since gained the separate experimental reference below;
The initial Custom placeholder was removed in 0.3.2.

## Completed: 0.2 operating-system settings

- Renamed Default to Omarchy; each active profile shows only its own settings.
- Added actual native System/Adaptive/Flat, sensitivity, scroll speed, natural
  scrolling, and left-handed buttons, with complete readback and rollback.
- Kept independent Windows/Omarchy preferences, migrating v1 with a backup.
- Fixed background polling so controls keep focus and clicks are not dropped.
- 24 controller/installer tests and the headless QML polling/queued-action test pass.
- Live native settings, save/restore, cross-profile rollback, and both panels
  verified; pre-test preferences restored.

## Completed: 0.3 experimental Mac reference

- Found and pinned libpointing's Sequoia 15.3.2 dataset (not the older Sierra data).
- Matched all 1,280 measured samples and passed six Mac engine tests.
- Added an ABI-checked Mac module with mutually exclusive Win/Mac loading.
- Added tracking 1–10, natural scrolling, primary button, and independent preferences.
- Migrated v1/v2 preferences to v3; retained original Win/Omarchy values.
- 31 controller tests and QML queued-action tests pass; live Mac reports, settings,
  restore/rollback, and the panel were verified. Mac-specific feel approval is pending.
- Retained data/source license files and documented the experimental limits.

## Completed: 0.3.1 direct settings

- Removed redundant Try/draft-reset actions from all three profile panels.
- Sliders apply on release; toggles and keyboard/wheel changes apply directly.
- Trials stay editable, renew the timer, and preserve their original rollback anchor.
- Revisions use new tokens/workers; stale actions and failures cannot save a partial trial.
- 39 controller/installer tests plus polling and actual-panel handler regressions pass.
- Quantified tracking curves; small-packet gains can be close. Native engines are unchanged.

## Completed: 0.3.2 profile scope

- Removed the unused Custom tab and its coming-soon message.
- Ordered the profile controls Omarchy → Mac → Win, including keyboard navigation.
- Dropped the separate Custom engine/editor roadmap; native customization belongs in Omarchy.

## Completed: 0.3.3 profile defaults

- Added Restore defaults to Omarchy, Mac, and Win using controller-owned presets.
- Replaced the redundant Windows preset button with the common reset action.
- Reset affects only the selected style and uses the existing trial/Keep/Revert flow.
- Added reset isolation, persistence, rollback/failure, and panel-click coverage.

## Completed: 0.3.4 bar labels

- Added persistent Letter (O/M/W) and Code (OMA/MAC/WIN) choices; Code is the default.
- Appearance saves immediately, independently of pointer trials and profile defaults.
- Verified persistence across controller reloads, profile changes, resets, Keep/Revert.

## Deferred: Windows scroll and button controls

Natural scrolling and primary-button/handedness controls were requested for Win,
then deferred when the owner prioritized the Mac profile. Win currently exposes
speed and EPP only. These additional controls are not implemented and require a
separate follow-up; the native engine behavior must remain unchanged.

## Completed: 0.4.0 installation and dependencies

- One `install.sh` entry point installs missing Arch packages and builds both
  native modules from bundled pinned sources, including the Windows adapter patch.
- First-use setup UI uses the same detached worker and Omarchy Polkit dialog.
- Source/ABI readiness, persistent rollback/recovery, update and full removal.
- Keep/Revert remains enabled; saved profiles and bar preferences are preserved.
- 68 Python tests, 24 native tests, 1,280 Mac samples, onboarding/panel QML checks,
  and actual desktop installation/idempotency passed. See [details](INSTALLATION.md).
- Installation readiness is independent of live profile transitions, including
  trial replacement and Keep; normal tuning no longer opens the repair panel.
- The private remote exists; public distribution and marketplace submission are pending.

## Completed: publication preparation

- Filled click cursor bar icon (selected on 2026-09-22), active OS header and current panel preview.
- Hidden bar label mode keeps only the clickable cursor icon and trial highlight,
  with the same independent persistence as Letter/Code.
- 70 Python tests, including the Git-managed installation/update boundary.
- Hosted CI workflow, QML lint helper and source-archive/provenance checks.
- Fresh native build, 24 native tests, 1,280 samples and actual QML checks passed.
- Local marketplace static preflight has no findings; installer privileges
  require maintainer review. Public release and submission drafts are prepared.

## Completed: Pointer Feel identity

- Product title, plugin ID, CLI, Python module, Mac module, build targets and
  source archives use the Pointer Feel identity.
- Repository and local source directory are named `omarchy-pointer-feel`.
- Desktop integration and preference paths use `pointer-feel`; the active
  installation preserves all saved profiles, the bar label and bar position.
- The README preview shows the renamed panel and Hidden label option.
- Third-party Windows and libpointing identities, licenses and pinned source
  hashes remain intact. Trackpad support is not added by this rename.

## Next: shared native backend

Keep exactly one hook. Preserve Windows reference output and the configured
Omarchy input path. Extend persistence with schema migrations, device identity,
and revision handling where required.

Acceptance: identical Windows outputs for replayed reports; unchanged Omarchy
native/raw deltas; precision, fast transit, diagonal, reversal, and drag scenarios.
Exercise zero/invalid values, timestamp repetition/wrap, idle gaps, device changes,
output continuity, monotonic interpolation, and state resets.

## Next: Mac equivalence and direct Apple port

Resolve the reuse/distribution conditions of the relevant Apple files before
porting implementation code. Select table/parametric inputs with recorded
provenance. The implemented Sequoia table reference is a separate experimental
model; it does not settle direct-port timing/parameter questions. Add measured
acceleration-off behavior before exposing that switch.

Acceptance: source-versioned parameters and reference input/output traces.
If Mac hardware is available, capture OS build, actual device properties,
tracking speed, report rate, and display conditions. Compare timing/state as
well as output. Without those captures, do not claim exact modern-macOS parity;
local experimental implementation can still proceed.

## Daily-use coverage and distribution

Validate measured report rates, relevant higher-frequency devices, multiple
physical mice, Bluetooth/receiver reconnect, suspend/resume, 1/1.25/1.5/2 display
scales, mixed monitors, logout/login, reboot, and Hyprland upgrades.

Frontend acceptance: click and keyboard controls, Escape, IPC show/hide, shell
reload, disable/re-enable, removal, and recovery from unavailable backend.
Keep microbenchmarks separate from end-to-end latency claims. Broader user tests
do not substitute for Windows/macOS reference comparisons.

Unified build/install/update/uninstall is implemented in 0.4.0. Validation is
recorded in docs/INSTALLATION.md. The remote is private and marketplace
submission has not been created. Broader compositor/hardware coverage remains
separate from validating this installation on the current stack.
