# Mouse Style research

Checked on 2026-09-20. Current scope: Omarchy / Mac / Win on Omarchy/Hyprland.
The initial Custom candidate was removed from product scope in 0.3.2.
This document separates observed facts, upstream claims, and proposed behavior.
The product is English-language and vendor-neutral; a test device is not a
product default or a universal compatibility claim.

## Local reference and evidence limits

The inspected environment runs Hyprland 0.56.2, commit
`efb50993780079460b0cbed1363e2166a2de1d9f`, and windows-pointer-linux 1.0.0.
The original approved Windows preference was speed 10/20 with EPP enabled.
The test mouse was an MX Master 3S using a receiver at a separately verified
1000 sensor DPI. Display scale was 1 and backend display DPI was 96. These are
historical test conditions, not required hardware or application defaults.

Global native sensitivity was 0, force_no_accel false, and accel_profile unset.
Omarchy's default input.lua set sensitivity to 0 without specifying a mouse
acceleration profile. No active user flat/adaptive override was found.

The user approved the resulting pointer feel. Independent bit-for-bit Windows
comparison, measured device report rate, and end-to-end latency were not tested.
The legacy source checkout has a local Hyprland compatibility patch; its engine
source/header have no local changes. The new project preserves the reference
engine separately and leaves that checkout intact.

## Windows engine

[windows-pointer-linux](https://github.com/junaga/windows-pointer-linux/tree/0bdd644d420737a7aea506e252fc5e12db34c599)
separates a compositor-independent C++ engine from its adapter. Its API accepts
one two-axis integer report and display DPI, preserving state and fractional
remainders. Exact Windows 11 equivalence is the upstream author's claim.

Use the pinned engine unchanged. It does not consume an event timestamp; adding
a timestamp to a shared adapter must not alter its input semantics. Extra DPI
normalization, smoothing, or gain ahead of Win would change the approved path.
The selected sources, tests, and replay tool retain their BSD-3-Clause notices.

## Apple source: more than a guessed curve

The inspected Apple revision is `777ccd9698845aadf711e32d843c8c9b777431d9`,
imported as IOHIDFamily-2238.100.59 on 2026-04-17. No unverified mapping from that
number to a marketed macOS release is assumed.

[IOHIDAcceleration.cpp](https://github.com/apple-oss-distributions/IOHIDFamily/blob/777ccd9698845aadf711e32d843c8c9b777431d9/IOHIDEventSystemPlugIns/IOHIDAcceleration.cpp#L136)
contains pointer application logic with two-axis magnitude and optional
report-rate/timestamp adjustment. Its scroll-history algorithm is a different
class and must not be mistaken for pointer filtering.

[IOHIDAccelerationAlgorithm.cpp](https://github.com/apple-oss-distributions/IOHIDFamily/blob/777ccd9698845aadf711e32d843c8c9b777431d9/IOHIDEventSystemPlugIns/IOHIDAccelerationAlgorithm.cpp)
contains table and parametric implementations. The latter combines polynomial,
tangent-line, and square-root regions with parameter interpolation. A port must
follow executable behavior and reference outputs, not only simplified comments.

[IOHIDPointerScrollFilter.cpp](https://github.com/apple-oss-distributions/IOHIDFamily/blob/777ccd9698845aadf711e32d843c8c9b777431d9/IOHIDEventSystemPlugIns/IOHIDPointerScrollFilter.cpp#L628)
selects effective curves from device/user properties, with table fallback.
Algorithm code alone does not identify a given Mac/mouse combination's effective
curve, resolution, tracking preference, or rate configuration.

Conclusion: a versioned Apple-reference engine is a serious candidate, not merely
a generic sigmoid approximation. Modern macOS parity still requires effective
parameters and comparison data. Public source availability is not a licensing
decision: no explicit license header was found in the inspected implementation
files or general root LICENSE in that tree. Resolve their reuse conditions before
porting code; do not infer them from unrelated IOHID files. They remain only in
the ignored research cache, not the compiled/vendored product.

## libpointing and legacy Mac data

[TransferFunction.cpp](https://github.com/INRIA/libpointing/blob/ecb67da58145343c9fa64211d629730134fe74ae/pointing/transferfunctions/TransferFunction.cpp#L212)
falls back to measured darwin-16 tables when its OSXFunction implementation is
unavailable. The library does not itself attach to a Wayland desktop cursor.

The [dataset metadata](https://github.com/INRIA/libpointing/blob/ecb67da58145343c9fa64211d629730134fe74ae/pointing-echomouse/darwin-16/config.dict)
identifies macOS 10.12/Sierra in 2016, 400 CPI at 125 Hz, and a 60 Hz display.
There are ten settings; the dataset's default alias is 0.6875. Neither that value
nor the data age should be hidden behind a generic modern-Mac label.

Its [license declaration](https://github.com/INRIA/libpointing/blob/ecb67da58145343c9fa64211d629730134fe74ae/LICENSE.md)
is GPL-2.0-or-later. Retain applicable notices/conditions if code or data is later
included. This is a useful secondary reference or explicitly labeled Mac legacy
experiment, not proof of current macOS equivalence.

## Sequoia measurement reference: selected for 0.3

A follow-up inspection found `darwin-24` in the same pinned libpointing revision.
Its [metadata](https://github.com/INRIA/libpointing/blob/ecb67da58145343c9fa64211d629730134fe74ae/pointing-echomouse/darwin-24/config.dict)
identifies macOS Sequoia 15.3.2, 400 CPI/125 Hz, and ten measured tracking levels.
This supersedes the initial assumption that Sierra was the only usable dataset.

Version 0.3 vendors these tables and GPL license files. The compiled Mac adapter
matches all 1,280 published axis samples and follows libpointing's unnormalised
lookup convention. This is an experimental measured reference, not the unresolved
Apple parametric-engine port. Hardware/rate/display differences and macOS temporal
behavior remain unverified. [Implementation and evidence](MAC-REFERENCE.md).

## Native Omarchy

[Hyprland's onMouseMoved](https://github.com/hyprwm/Hyprland/blob/efb50993780079460b0cbed1363e2166a2de1d9f/src/managers/input/InputManager.cpp#L127)
consumes accelerated delta and unaccelerated motion separately. The Windows hook
replaces delta. Unloading it restores the existing native path; a future shared
dispatcher can pass the event through unchanged.

The initial Default prototype only unloaded the engine. The 0.2 product contract
renames this style Omarchy and exposes its real native input controls. Shared
values are verified after reload; per-device overrides keep their precedence.
System leaves the acceleration profile at the device default; Flat and Adaptive
are explicit choices. None of these is a factory reset of the desktop.
force_no_accel can bypass transformed deltas, so activation needs explicit
validation rather than a successful-looking checkbox.

## Prior Custom research (out of product scope)

The [Raw Accel guide](https://github.com/RawAccelOfficial/rawaccel/blob/master/doc/Guide.md)
distinguishes output/input sensitivity from the derivative of output speed.
Threshold and cap transitions can introduce discontinuities. The editor should
show the relevant quantities and generate charts from the actual evaluator.

Previously considered controls (not planned): flat/smooth/point curves, low-speed multiplier, acceleration
onset, transition width, limit, advanced axis ratio, explicit normalization,
named presets, import/export, preview, and undo. Extra models should arrive with
defined units and tests. Smoothing and snapping are not default requirements.

[libinput Custom](https://wayland.freedesktop.org/libinput/doc/latest/pointer-acceleration.html#ptraccel-profile-custom)
is a useful sampled-curve alternative. Its points must follow its output-speed
semantics; an editor's gain values cannot simply be copied. It does not recreate
the Windows engine's state or Apple's timing behavior automatically.

[maccel](https://github.com/Gnarus-G/maccel) is a Linux custom acceleration kernel
module, not evidence of macOS emulation despite its name. The existing user-level
compositor path avoids adding DKMS or an evdev/uinput grab daemon for this project.

## Time, DPI, and input classes

Sensor DPI, physical display PPI, and logical desktop scale are distinct. The
backend's display DPI 96 is not hardware mouse DPI. Physical-speed curve models
need a reliable or explicitly calibrated sensor DPI instead of an assumed value.

[SMotionEvent](https://github.com/hyprwm/Hyprland/blob/efb50993780079460b0cbed1363e2166a2de1d9f/src/devices/IPointer.hpp#L19)
provides uint32 millisecond timestamps at the inspected hook. High-rate mice may
produce multiple reports per timestamp. Sampling callback wall time instead can
feed scheduling jitter into acceleration. Higher-rate support needs an evaluated
timestamp source or aggregation policy, not a blanket polling-rate claim.

Keep both axes from the same report together. Preserve existing Win seat-state
semantics. Define device-scoped timing/DPI history for other engines. Test
repeated timestamps, wrap, long gaps, device changes, and display transitions.
The current native module bypasses touchpads, virtual devices, and unsupported
fractional/rotated input. Those are real boundaries of the first release.

## Omarchy integration

The [development contract](https://plugins.omarchy.org/develop.html) supports a
bar widget and attached panel. User plugin files are copied into the user-owned
plugin directory. The validator rejects symlinks. The installed shell exposes
shared UI components; its virtual qs imports need mapping for standalone lint.
A vendor widget is neither a dependency nor a placement anchor.

The [publishing guide](https://plugins.omarchy.org/publish.html) and
[Hyprland plugin documentation](https://wiki.hypr.land/Plugins/Using-Plugins/)
make frontend packaging and native compatibility separate concerns. Do not ship
one native binary as compatible with arbitrary compositor versions. Version 0.4.0 now builds both modules through a unified installer and includes
transactional update/removal; see [installation evidence](INSTALLATION.md).
Support for additional compositor releases remains distribution work.

## Decision

Win, Omarchy, and the experimental Sequoia measurement reference have a working
0.3 panel with separate, persistent settings.
A separate Custom profile/editor is no longer planned. Native customization
belongs in Omarchy; the research above does not establish implemented controls.
A direct Apple engine port still needs effective parameters, source reuse terms,
and timing/reference verification. The measured Mac reference is implemented
under its separately documented source/data terms. No generic sigmoid will be labeled
as an implemented Mac profile.
