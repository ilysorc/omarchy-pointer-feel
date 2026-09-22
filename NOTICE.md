# Licensing and provenance

Mouse Style is distributed under GPL-2.0-or-later. See LICENSE for the GPL v2
text; you may use version 2 or any later version. Copyright 2026 Mouse Style
contributors.

The Windows reference engine and native adapter are from junaga/windows-pointer-linux,
revision 0bdd644d420737a7aea506e252fc5e12db34c599, under BSD-3-Clause. Their original
license remains in vendor/windows-pointer-linux/LICENSE. The engine is unchanged.
The native adapter includes the documented Hyprland 0.56 compatibility patch;
the original adapter and checksums are included alongside it.

The macOS Sequoia reference data is from INRIA/libpointing, revision
ecb67da58145343c9fa64211d629730134fe74ae, under GPL-2.0-or-later. Its license,
copyright notices, measurements and provenance remain in vendor/libpointing-sequoia.

No Apple implementation code is included. The Mac mode is an experimental
measured reference, not a claim of exact macOS behavior. All dependencies needed
to build the native modules are either in this source bundle or installed from
the user's configured Arch repositories. Setup does not fetch or execute code
from mutable external Git branches.
