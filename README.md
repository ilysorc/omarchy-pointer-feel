# Pointer Feel

Switch between Omarchy's native mouse settings, Windows-style pointer
acceleration, and an experimental Mac reference from the Omarchy bar.

**Version 1.0.0 · Requires Omarchy with Hyprland 0.56.2 and Lua configuration.**

![Pointer Feel filled cursor bar icon and panel with the Windows profile selected](preview.png)

## Profiles

| Profile | Controls | Restore defaults |
|---|---|---|
| Omarchy | System / Adaptive / Flat acceleration, sensitivity, scroll speed, natural scrolling, left-handed buttons | System acceleration, sensitivity 0, scroll 1×, natural scrolling off, left primary button |
| Mac | Tracking speed 1–10, natural scrolling, primary button | Tracking 4/10, natural scrolling on, left primary button |
| Win | Pointer speed 1–20, Enhance pointer precision | Speed 10/20, Enhance pointer precision on |

Each profile retains its own settings. Hardware DPI is unchanged.
**System** uses the device's default libinput acceleration profile;
**Adaptive** and **Flat** explicitly select those native profiles. Omarchy's
sensitivity range is −1 to +1; its scroll speed range is 0.1–5×.

The Mac profile uses libpointing's measurements from **macOS Sequoia 15.3.2**,
recorded at 400 CPI and 125 Hz. It is experimental: exact macOS behavior across
different hardware is unverified, and Mac wheel momentum and trackpad gestures
are not implemented. See the [Mac reference](docs/MAC-REFERENCE.md) for the
measurement conditions and model limits.

## Install

```sh
omarchy plugin add https://github.com/ilysorc/omarchy-pointer-feel.git --enable
```

Open **Pointer Feel** in the bar and click **Install / Repair**. Adding the plugin
does not automatically install its dependencies; this button starts the complete
setup. You can close the panel while setup runs.

Alternatively, from a clone or extracted source archive:

```sh
./install.sh
```

Run setup as your desktop user, without `sudo`. It installs missing packages,
builds both native pointer modules, adds the bar widget, and configures saved
settings to load at login. Existing saved preferences are preserved. Finish any
active Keep/Revert trial before installing or updating.

Required packages are Python, Git, coreutils, GCC, Make, CMake, pkgconf, and Polkit.
Setup may ask for your password to install missing packages from your configured
Arch repositories. Compilation runs as your normal user; the native sources are
bundled with the plugin. GTest is needed only for development tests.

The installed Hyprland headers must match the running compositor. Unsupported
versions are rejected before native setup. If Python is missing, the shell
bootstrap offers to install it before these checks can run.

## Use

Click the cursor icon in the bar, then choose **Omarchy**, **Mac**, or **Win**.
Changes take effect immediately; sliders apply when released.

- **Keep** saves the trial's changes. Saved settings are restored at login.
- **Revert** restores the settings from before the trial.
- If you do not choose Keep within **15 seconds**, the trial reverts automatically.
  Closing the panel does not stop the timer or save the trial.
- Further adjustments restart the timer. You can switch profiles within a trial;
  Keep saves all its changes, and Revert restores its original starting state.
- **Restore defaults** resets only the selected profile and starts or updates a
  trial. It does not reset other profiles, device overrides, or hardware DPI.

Tab moves between controls; Escape closes the panel.

**Bar Label** controls the text next to the theme-colored cursor icon:

| Option | Display |
|---|---|
| Letter | O / M / W |
| Code | OMA / MAC / WIN (default) |
| Hidden | Icon only |

Bar appearance saves immediately and does not need Keep. With Hidden selected,
the icon remains clickable and shows the profile in its tooltip. When setup is
required, the bar still displays **Setup**.

## Device support

The Windows and Mac motion engines target physical mice connected by cable,
wireless receiver, or Bluetooth. They bypass touchpads, tablets, virtual pointers,
and unsupported fractional or rotated raw input. There is no per-device profile
selector, and not every mouse model has been tested.

The Omarchy profile changes **shared Hyprland input defaults**. Existing per-device
overrides take precedence; touchpads that inherit those defaults can be affected.
Switching to Win removes this plugin's native input overrides before applying
Windows speed and precision settings.

Other Hyprland versions and other compositors are not supported by this release.

## Update

For a Git-managed installation:

```sh
omarchy plugin update ilysorc.pointer-feel
```

Then open the widget and complete **Install / Repair** if requested. For an
installation from source, update or replace the source folder and run
`./install.sh` again. Saved profile and bar preferences are retained.

A source or Hyprland ABI change can require rebuilding the modules. Setup checks
compatibility before loading them. It also backs up managed configuration files
and rolls back a failed activation. System packages installed before a later
failure remain installed. See the [installation contract](docs/INSTALLATION.md)
for recovery and configuration details.

## Remove or hide

To remove the plugin, its native modules, and its startup integration:

```sh
pointer-feel uninstall
```

You can also run `./install.sh --uninstall` from the source folder. Removal
restores the underlying native input configuration and retains saved preferences,
recovery backups, and shared system packages. Unrelated configuration changes are
preserved.

To hide only the widget:

```sh
omarchy plugin disable ilysorc.pointer-feel
```

Hiding or removing the widget through Omarchy alone does not unload the native
engines or remove their startup configuration. To stop using Windows/Mac motion,
choose **Omarchy** and Keep it, or use the full uninstaller.

## Troubleshooting

- **Setup appears after an update:** run Install / Repair. If the running
  compositor and installed headers differ, finish the Omarchy update and log in
  again before retrying. A new Hyprland release may need a plugin compatibility
  update, not just a rebuild.
- **Settings have no effect:** check for per-device Hyprland overrides. The Win
  and Mac motion engines do not transform touchpad input.
- **Setup fails:** the panel's setup log is at
  `~/.local/state/pointer-feel/setup.log`. Avoid configuring another loader to
  load the same native modules alongside Pointer Feel.

Useful read-only checks:

```sh
pointer-feel status
./install.sh --status
./install.sh --plan
```

| File or directory | Purpose |
|---|---|
| `~/.config/pointer-feel/config.json` | Saved profile settings |
| `~/.config/pointer-feel/ui.json` | Bar appearance |
| `~/.config/hypr/pointer-feel.lua` | Managed input settings |
| `~/.local/state/pointer-feel/install-backups/` | Recovery backups |

## Development

Reference tests require Python, CMake 3.25+, a C++23 compiler, Make, and GTest.
This build does not load native modules or change the desktop's pointer behavior.

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -q
cmake -S . -B build -G 'Unix Makefiles' -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DPOINTER_FEEL_BUILD_PLUGIN=OFF
cmake --build build --parallel 4
ctest --test-dir build --output-on-failure
python3 tests/check_mac_reference.py
python3 tools/check_release.py
```

On a supported Omarchy desktop, validate the UI as well:

```sh
omarchy plugin validate .
python3 tools/check_qml.py
python3 tests/check_panel.py
python3 tests/check_polling.py
python3 tests/check_setup_panel.py
```

The QML helper reports the known upstream `QProcess::ExitStatus` metadata warning
separately from project errors. Validation results and their limits are recorded
in [publication readiness](docs/PUBLISHING.md) and the
[installation record](docs/INSTALLATION.md). See [architecture](docs/DESIGN.md)
and [roadmap](docs/ROADMAP.md) for implementation details and planned work.

## License

Pointer Feel is distributed under **GPL-2.0-or-later**. The Windows reference
engine retains its BSD-3-Clause license; libpointing's Sequoia reference tables
retain their GPL-2.0-or-later notices. See [LICENSE](LICENSE),
[NOTICE.md](NOTICE.md), and the upstream records for
[Windows](vendor/windows-pointer-linux/UPSTREAM.json) and
[libpointing](vendor/libpointing-sequoia/UPSTREAM.json).
