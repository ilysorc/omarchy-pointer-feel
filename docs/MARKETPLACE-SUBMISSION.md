# Marketplace submission draft

Title: **[Plugin]: Pointer Feel**

The owner authorized publication and marketplace submission on 2026-09-22.
Verify public access and the checklist before sending. The issue body starts at
`Repository URL`; do not include this preamble in the issue. Record the resulting
issue URL here after submission.

### Repository URL

https://github.com/ilysorc/omarchy-pointer-feel

### Category

Hardware

### Tags

bar, hyprland, quickshell

### Suggest a missing tag

_No response_

### Maintainer notes

Pointer Feel provides native Omarchy settings, a Windows pointer reference, and
an experimental Mac Sequoia measured reference. It preserves per-profile
preferences and uses 15-second trials with Keep/Revert. Hardware DPI is not
changed.

This release targets Omarchy Quattro with Hyprland 0.56.2 and Lua configuration.
Other Hyprland versions are rejected before native setup; matching headers and
the running compositor ABI are required. When Python is missing, the shell
bootstrap first offers to install it before compositor validation. Exact macOS
parity is not claimed.

Please apply `manual-setup`: after adding/enabling the plugin, the user clicks
Install / Repair once. The same install.sh worker installs missing Arch packages
and builds both modules from bundled pinned sources. Only package installation
uses sudo/Polkit; builds and plugin execution run as the desktop user. No kernel
module or passwordless sudo policy is installed. README documents dependencies,
configuration changes, rollback, update, full removal and retained preferences.

GPL-2.0-or-later; upstream BSD Windows and GPL libpointing notices and hashes are
retained. The root preview shows the current real panel. Local checks and their
limits are recorded in docs/PUBLISHING.md. The local static preflight reported
no findings and the installer/package-manager/privilege capabilities; the
official scan and maintainer review remain pending.

### Submission checklist

- [ ] The repository is public and contains installation and removal instructions.
- [ ] I have documented the plugin license and any external dependencies.
- [ ] I confirm that I own or have permission to submit this plugin and its preview assets.
- [ ] The plugin does not overwrite user configuration without explicit consent.
- [ ] I understand that approval is for listing and is not a security review.
