# Architecture and product contract

Status: **1.0.0 Omarchy, experimental Mac, and Win implemented**.

## Product scope

English-language, vendor-neutral selection in this order: **Omarchy → Mac → Win**.
A separate Custom profile is out of scope. Native pointer customization belongs
in Omarchy; this does not imply an arbitrary curve editor is implemented.
Never assume a brand, sensor DPI, report rate, or vendor configuration utility.
Expose unknown values as unknown. Observed mouse names may appear in diagnostics;
they must not change the generic UI or establish a compatibility claim.

The bar shows the verified active profile, not an optimistic selection.
Sliders keep a local value during a drag and apply on release; toggles and
keyboard/wheel changes apply directly. There is no second Try step. Polling
cannot overwrite a drag or briefly replace a queued value with an old readback.
An active trial remains editable; only a running mutation disables controls.
Unsupported profiles are disabled.

Each style exposes its own operating-system settings. Win exposes the upstream
1–20 speed and EPP controls. Omarchy exposes native System/Adaptive/Flat,
sensitivity, scroll speed, natural scrolling, and left-handed buttons.
Flat is an existing Omarchy/libinput option.
Mac identifies its measured Sequoia 15.3.2 reference and exposes tracking 1–10,
natural scrolling, and primary-button choice.

## Current 1.0.0 implementation

```text
Omarchy bar and panel (QML)
       | bounded process calls on user action / status polling
pointer-feel controller (Python)
       | load / unload / reload and verified status
Windows module OR Mac reference module (mutually exclusive)
       | Windows engine or native passthrough when unloaded
Hyprland pointer path
```

Mac uses a separate ABI-checked module, unloaded before the Windows module is loaded.
Only one motion hook is active at a time. No Python/QML work runs per mouse event.
No kernel module, root daemon, vendor service, or second Quickshell process is
introduced. The first installation adopts the existing Windows preferences or
starts from native Omarchy if no backend is active. Windows availability is
reported separately from the selected/saved profile.

The installer adds a final managed settings include and a `pointer-feel restore`
startup route. It preserves unrelated input settings and prevents a duplicate
common `windows-pointer on` helper. A different native plugin manager remains an
explicit integration consideration; two loaders must not compete.

## Omarchy contract

Omarchy unloads the Windows module and applies native `input` options through
the generated Lua include. It then reloads and verifies every managed global
value. System acceleration preserves the empty/default libinput choice;
Adaptive and Flat explicitly select those native profiles. No synthetic curve
is used. This is not a factory reset of all Omarchy configuration.

Preferences use schema version 3: `windows`, `mac`, and `omarchy` are independent
objects. Version 2 gains a separate Mac reference preset; existing values survive. Upgrading version 1 renames `default` to `omarchy`, retains Windows
preferences, and adopts the current native input values. The old CLI profile
name remains an alias. Installation backs up the old configuration first.

The native options are global. Existing per-device settings take precedence;
shared acceleration/sensitivity may affect touchpads inheriting those defaults.
Keyboard and device rules are not rewritten. In Win mode the generated file
contains no native input overrides, so a reload restores the user's base input
configuration. Inactive profile settings are retained for the next switch.

`force_no_accel=true` bypasses transformed cursor deltas in this Hyprland version.
Activation reports the conflict instead of silently changing that option.
Advanced libinput custom curves are not edited in this version.

## Profile defaults

Each profile has a Restore defaults action backed by `preview PROFILE --defaults`.
Defaults live in the controller: Omarchy System/0/1×/natural-off/left-primary,
Mac reference level 4/natural-on/left-primary, and Win 10/EPP-on. It replaces only
the selected profile's settings, retaining saved or pending preferences for the
others. Defaults cannot be mixed with manual settings in one command. Resetting
an active trial uses its token and original rollback anchor; Keep saves the result.
This resets managed input preferences, not the desktop configuration or hardware DPI.

## Bar label preference

On 2026-09-22, the owner selected the filled click cursor: a solid pointer with
three short click rays, replacing the previous pointer-and-curve mark.
`FlowIcon.qml` draws it as a theme-colored vector; `FlowButton.qml` preserves
Omarchy's widget interaction behavior and places the profile label beside it.
The icon uses the shell's icon size token and does not depend on a font glyph.

The panel uses Omarchy's shared `PanelHero` header. `ProfileHeader.qml` shows
the active profile's logo beside the product title: the bundled Omarchy font's
menu mark, or the Apple/Windows glyphs in Omarchy's JetBrainsMono Nerd Font.
It follows verified `PointerState.profile`, including trials and reverts; an
unknown state shows the click cursor with "Unverified" rather than retaining a stale OS logo.
The header follows theme colors and type sizing independently of the bar label.

Letter displays O/M/W; Code displays OMA/MAC/WIN and is the default for existing
installations. Hidden leaves only the cursor icon, with no label spacing or trial
dot; the widget keeps its tooltip, click target and active trial highlight. Setup
still shows its label when required. `pointer-feel bar-label letter|code|hidden` writes `ui.json` atomically under
the controller lock and returns refreshed status. The frontend reads `ui.bar_label`.
Appearance is persisted immediately, separately from pointer preferences. It does
not reload the motion engine, start/confirm a trial, or renew its timer. Profile
switches, Restore defaults, Keep, Revert, and startup restore leave it intact.

## Transactions, persistence, and rollback

Confirmed preferences: `~/.config/pointer-feel/config.json`.
Pending trial: `~/.local/state/pointer-feel/preview.json`.
Generated, guarded Lua preferences: `~/.config/hypr/pointer-feel.lua`.

A file lock serializes controllers and rollback workers. Each trial receives a
unique token and session identity. The controller records the actual previous
runtime settings, starts an independent rollback worker, then applies and reads
back the candidate. Confirm checks the current token and backend again before
saving. Polling never saves preferences. Duplicate application of an already
active and saved profile is a no-op, avoiding unnecessary engine state resets.

A token-matched `preview --replace-token TOKEN` refines the active trial, including
style switches. It retains the original rollback state and other styles' pending
preferences. Each change gets a new token and worker (the old worker exits),
renews the 15-second deadline after readback, and rejects stale edits/confirms.
A failed replacement restores the original state, not an intermediate adjustment.
Identical adjustments are no-ops and do not renew the deadline.

A trial expires 15 seconds after its last applied change. Revert restores the actual previous settings,
which may differ from a stale saved preference. Closing or disabling the panel
does not cancel the rollback worker. This mechanism recovers from a poor speed
choice; it does not guarantee recovery from a compositor crash.

Atomic file replacement avoids partial JSON/Lua. Values are validated before
rendering generated Lua; commands use argv lists, not user-provided shell text.
Startup clears stale trial state and restores the last confirmed preference.
A load failure, including ABI mismatch, is visible rather than being reported
as a successful profile change.

The experimental Mac implementation and limits are documented in [MAC-REFERENCE.md](MAC-REFERENCE.md).

## Planned shared native dispatcher

One native hook should eventually dispatch to unmodified Windows, a versioned
Apple reference, or native Omarchy passthrough. The old Windows module and this
new dispatcher must never be loaded together. Windows engine source and seat
state semantics remain unchanged. Do not prepend normalization, smoothing,
axis ratios, or an extra gain stage to the approved Win path.

The common event model carries both raw axes from one report, native delta,
device identity, source timestamp and its resolution, display scale, and any
verified sensor/report-rate metadata. Each engine uses only its defined inputs.
Mac timing state must not mix histories between unrelated devices.

Keep raw relative-motion events unchanged. Applications using accelerated
relative motion can still be affected; do not promise that every game is immune.
Initially, unsupported fractional/rotated input, touchpads, tablets, and virtual
pointers pass through. Device selection needs stable identifiers, not just the
display name of a receiver.

## Native customization

The Omarchy profile owns native acceleration, sensitivity, and scroll settings.
A separate curve engine/editor is not planned.

Omarchy includes native scroll speed/direction and left-handed button swapping.
Hardware wheel modes, arbitrary button mappings, and cursor themes remain separate.

## Packaging

A complete source bundle contains the QML frontend, Python controller/installer,
Windows native adapter and compatibility patch, and Mac module/data. `install.sh`
is the Bash bootstrap (including missing Python); `setup.py` owns dependency
checks, unprivileged builds, file transactions, readback, and removal. No remote
source code is fetched during setup. The initial supported compositor is 0.56.2.

Omarchy's standard plugin installer deliberately does not run install hooks.
`SetupState.qml` checks readiness independently of pointer polling and opens the
first-use setup panel. One Install / Repair action starts a detached installer;
only missing Arch packages use sudo (TTY) or pkexec (GUI). UI reloads cannot cancel
the worker. Root execution of the whole installer is rejected.

Readiness checks the installed artifacts, source revision, compositor ABI and
startup integration only. Live profiles and trial files are not installation
prerequisites: engine switching and Keep update them in separate steps. Runtime
readback belongs to the controller under its mutation lock. Explicit setup on an
intact installation verifies/restores the saved profile without rebuilding and
still rejects active trials; passive readiness polling never changes profiles.

The saved receipt ties artifacts to the source digest and compositor ABI. Builds
finish before touching the running integration. A setup lock excludes duplicate
workers; the controller lock serializes activation with profile edits. Native
modules are unloaded before atomic replacement. Every style is applied/read back,
then the user's previously active settings are restored. File preimages and an
on-disk recovery journal support rollback and interrupted-activation recovery.
Installed packages remain installed after cancellation/failure of a later phase.

Keep/Revert stays part of normal profile tuning (explicit owner decision). Setup
will not consume or confirm a trial. First installation adopts verified active
settings. Full removal returns to underlying native configuration, preserves
unrelated configuration, retains preferences/backups and shared packages, and
retires any standalone Windows startup route adopted during installation.

A Git-managed plugin checkout is its source of truth; controller launchers execute
from there, so marketplace updates cannot leave a separate stale controller copy.
Source/ABI changes require the same setup again. Local development installation
copies the complete source bundle without modifying an existing Git checkout.
Publishing the public repository and marketplace submission remain separate work.
The uninstall/reinstall path restores an existing confirmed profile from
`config.json` even when the installation receipt has been removed; a truly fresh
install with no saved config adopts the current native runtime.
