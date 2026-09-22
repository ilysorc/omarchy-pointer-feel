#!/usr/bin/env python3
"""One installation transaction for dependencies, native modules and Omarchy UI."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile

from mouse_style import (Controller, ControlError, MAC_DEFAULT, WINDOWS_DEFAULT,
                         atomic_write, migrate_config, read_json, write_json)

ROOT = Path(__file__).resolve().parent
PLUGIN_ID = "ilysorc.mouse-style"
PACKAGES = ("python", "git", "coreutils", "gcc", "make", "cmake", "pkgconf", "polkit")
MODULES = ("windows-pointer-linux.so", "mouse-style-mac.so")
SUPPORTED = ("0.56.2",)
INPUT_MARKER = '-- Mouse Style preferences (managed by the bar panel).\n'
INPUT_ROUTE = 'dofile(os.getenv("HOME") .. "/.config/hypr/mouse-style.lua")'
START_MARKER = '-- Restore the saved Mouse Style profile.\n'
BUNDLE = ("manifest.json", "FlowIcon.qml", "FlowButton.qml", "ProfileHeader.qml", "BarWidget.qml", "Panel.qml", "PointerState.qml",
          "SetupState.qml", "SetupPanel.qml", "mouse_style.py", "setup.py", "install.sh",
          "CMakeLists.txt", "src", "tools", "scripts", "tests", "vendor", "README.md", "LICENSE", "NOTICE.md", "docs", "preview.png")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bundle_files(root):
    for name in BUNDLE:
        path = root / name
        if not path.exists():
            raise ControlError(f"Incomplete source bundle: {name}")
        for item in sorted(path.rglob("*")) if path.is_dir() else [path]:
            if item.is_symlink():
                raise ControlError(f"Source symlinks are not supported: {item}")
            if item.is_file() and "__pycache__" not in item.parts:
                yield item.relative_to(root)


def source_revision(root):
    result = hashlib.sha256()
    for name in bundle_files(root):
        if name.parts[0] in ("docs", "tests", "README.md", "LICENSE", "NOTICE.md", "preview.png"):
            continue  # Documentation updates do not invalidate native builds.
        result.update(str(name).encode() + b"\0" + (root / name).read_bytes())
    return result.hexdigest()


def input_config(original):
    return original if INPUT_ROUTE in original else original.rstrip() + "\n\n" + INPUT_MARKER + INPUT_ROUTE + "\n"


def startup_config(original, home):
    command = f'o.launch_on_start("{home}/.local/bin/mouse-style restore")'
    if command in original:
        return original
    old = r'''(?m)^\s*o\.launch_on_start\(["'](?:[^"'\n]*/)?windows-pointer on["']\)\s*$'''
    if len(re.findall(old, original)) > 1:
        raise ControlError("Multiple Windows startup helpers found. Remove duplicate startup owners first.")
    if re.search(old, original):
        return re.sub(old, lambda _: command, original)
    return original.rstrip() + "\n\n" + START_MARKER + command + "\n"


class FileTransaction:
    """Persist preimages before every owned write; recover an interrupted commit."""
    def __init__(self, home, directory):
        self.home, self.directory = home.resolve(), directory
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.journal = directory / "journal.json"
        self.records = []
        if not self.journal.exists():
            write_json(self.journal, {"state": "pending", "files": []})

    def remember(self, path):
        path = Path(path)
        relative = str(path.relative_to(self.home))
        if path.is_symlink() or not path.resolve().is_relative_to(self.home):
            raise ControlError(f"Refusing to replace a symlink or external path: {path}")
        if any(row["path"] == relative for row in self.records):
            return
        row = {"path": relative, "exists": path.exists()}
        if path.exists():
            if not path.is_file():
                raise ControlError(f"Expected a regular file: {path}")
            row["mode"] = path.stat().st_mode & 0o777
            saved = self.directory / "files" / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, saved)
        self.records.append(row)
        write_json(self.journal, {"state": "pending", "files": self.records})

    def put(self, path, content, mode=0o644):
        self.remember(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix=".mouse-style-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content.encode() if isinstance(content, str) else content)
            os.chmod(temp, mode)
            os.replace(temp, path)
        finally:
            Path(temp).unlink(missing_ok=True)

    def remove(self, path):
        self.remember(path)
        path.unlink(missing_ok=True)

    def rollback(self):
        for row in reversed(self.records):
            path = self.home / row["path"]
            if not path.resolve().is_relative_to(self.home) or path.is_symlink():
                raise ControlError(f"Cannot restore an external path: {path}")
            if row["exists"]:
                saved = self.directory / "files" / row["path"]
                self.put(path, saved.read_bytes(), row["mode"])
            else:
                path.unlink(missing_ok=True)
        write_json(self.journal, {"state": "rolled-back", "files": self.records})

    def finish(self):
        write_json(self.journal, {"state": "complete", "files": self.records})


class Installer:
    def __init__(self, root=ROOT, home=None, controller=None, runner=None):
        self.root = Path(root).resolve()
        self.home = Path(home or Path.home()).resolve()
        self.controller = controller or Controller(self.home)
        self.runner = runner or subprocess.run
        self.state = self.home / ".local/state/mouse-style"
        self.plugin = self.home / ".config/omarchy/plugins" / PLUGIN_ID
        self.receipt = self.state / "installation.json"
        self.progress_file = self.state / "setup.json"
        self.pending = self.state / "setup-transaction.json"
        self.log = self.state / "setup.log"

    def run(self, argv, *, timeout=30, check=True, capture=True):
        result = self.runner([str(x) for x in argv], text=True, capture_output=capture, timeout=timeout)
        if check and result.returncode:
            detail = ((result.stderr or "") + (result.stdout or ""))[-1800:].strip() if capture else "See the setup log."
            raise ControlError(f"{argv[0]} failed (exit {result.returncode}). {detail}")
        return result

    def report(self, phase, message):
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        write_json(self.progress_file, {"phase": phase, "message": message})
        print(message, flush=True)

    @contextmanager
    def lock(self):
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (self.state / "setup.lock").open("a") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ControlError("Mouse Style setup is already running.")
            yield

    def running(self):
        path = self.state / "setup.lock"
        if not path.exists():
            return False
        with path.open("r") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return False
            except BlockingIOError:
                return True

    def version(self):
        value = json.loads(self.run(["hyprctl", "version", "-j"]).stdout)
        if not value.get("commit") or not value.get("version"):
            raise ControlError("Cannot identify the running Hyprland build.")
        return value

    def missing_packages(self):
        return [name for name in PACKAGES if self.run(["pacman", "-Q", name], check=False).returncode]

    def status(self):
        running = self.running()
        progress = read_json(self.progress_file) if self.progress_file.exists() else {}
        ready, reason = False, "Install the required components to finish setting up Mouse Style."
        try:
            saved = read_json(self.receipt)
            version = self.version()
            # Installation readiness is independent of live pointer state.
            # Switching profiles unloads/reloads engines, replacing trials updates
            # their candidate, and Keep removes the trial before saving preferences.
            # Polling those steps here can mistake a valid transition for missing
            # components and hide Keep/Revert. The controller owns runtime checks
            # under its own lock; setup checks only the installed bundle/integration.
            ready = (not self.pending.exists() and saved.get("revision") == source_revision(self.root)
                     and saved.get("abi") == version.get("abiHash", version["commit"])
                     and all((self.home / name).is_file() and digest(self.home / name) == checksum
                             for name, checksum in saved["artifacts"].items())
                     and INPUT_ROUTE in (self.home / ".config/hypr/input.lua").read_text()
                     and "mouse-style restore" in (self.home / ".config/hypr/autostart.lua").read_text())
            if not ready:
                reason = "Finish setup to install or rebuild the components for this version."
        except (OSError, ValueError, KeyError, ControlError):
            pass
        if running:
            reason = progress.get("message", "Preparing Mouse Style…")
        elif progress.get("phase") == "error" and not ready:
            reason = progress.get("message", reason)
        elif ready:
            reason = "Mouse Style is ready."
        return {"ready": ready, "running": running, "message": reason,
                "interrupted": self.pending.exists()}

    def preflight(self):
        for name in ("omarchy", "omarchy-shell", "hyprctl", "pacman"):
            if not shutil.which(name):
                raise ControlError("Mouse Style requires a running Omarchy desktop on Arch Linux.")
        version = self.version()
        if version["version"] not in SUPPORTED:
            raise ControlError(f"Hyprland {version['version']} is not supported by this release. Supported: {', '.join(SUPPORTED)}.")
        if self.controller.pending():
            raise ControlError("Keep or revert the active pointer trial before installing or updating.")
        main = (self.home / ".config/hypr/hyprland.lua").read_text()
        for module in ("hypr.input", "hypr.autostart"):
            if not re.search(r'''require\(\s*["']''' + re.escape(module) + r'''["']\s*\)''', main):
                raise ControlError(f"The Lua configuration must load {module}.")
        errors = self.controller.backend.run("configerrors", json_output=True)
        if any(str(e).strip() for e in errors):
            raise ControlError("Resolve existing Hyprland configuration errors before setup: " + str(errors))
        self.run(["omarchy", "plugin", "validate", self.root])
        source_revision(self.root)  # Detect an incomplete archive before installing packages.
        return version

    def install_packages(self, packages):
        if not packages:
            return
        self.report("packages", "Installing required packages: " + ", ".join(packages))
        if Path("/var/lib/pacman/db.lck").exists():
            raise ControlError("Another package operation is running. Wait for it to finish and retry.")
        if sys.stdin.isatty() and sys.stdout.isatty():
            prefix = ["sudo"]
        else:
            prefix = ["/usr/bin/pkexec", "--disable-internal-agent"]
        # Only the trusted system package manager runs with elevated privileges.
        self.run(prefix + ["/usr/bin/pacman", "-S", "--needed", "--noconfirm", "--", *packages],
                 timeout=None, capture=False)
        if self.missing_packages():
            raise ControlError("Required packages are still missing. Check the setup log and retry.")

    def check_headers(self, version):
        result = self.run(["pkg-config", "--modversion", "hyprland"], check=False)
        if result.returncode or result.stdout.strip() != version["version"]:
            raise ControlError("Hyprland development files do not match the running session. Finish the Omarchy update and log in again before retrying.")
        flags = shlex.split(self.run(["pkg-config", "--cflags-only-I", "hyprland"]).stdout)
        candidates = [Path(flag[2:]) / suffix for flag in flags if flag.startswith("-I")
                      for suffix in ("hyprland/src/version.h", "src/version.h", "version.h")]
        header = next((path for path in candidates if path.is_file()), None)
        if header is None:
            raise ControlError("Hyprland development headers are missing from its pkg-config include paths. Repair the Hyprland package before retrying.")
        match = re.search(r'#define\s+GIT_COMMIT_HASH\s+"([^"]+)"', header.read_text())
        if not match or match[1] != version["commit"]:
            raise ControlError("Installed Hyprland headers and the running compositor have different commits. Log in again after completing the system update.")
        self.run(["pkg-config", "--cflags", "--libs", "hyprland"])

    def build(self, version):
        self.check_headers(version)
        self.report("build", "Building Windows and Mac pointer components…")
        cache = self.home / ".cache/mouse-style/builds"
        cache.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix="build-", dir=cache))
        try:
            self.run(["cmake", "-S", self.root, "-B", output, "-G", "Unix Makefiles",
                      "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_TESTING=OFF", "-DMOUSE_STYLE_BUILD_PLUGIN=ON"],
                     timeout=180, capture=False)
            self.run(["cmake", "--build", output, "--parallel", str(min(4, os.cpu_count() or 1)),
                      "--target", "windows-pointer-linux", "mouse-style-mac"], timeout=900, capture=False)
            for name in MODULES:
                if not (output / name).is_file() or (output / name).read_bytes()[:4] != b"\x7fELF":
                    raise ControlError(f"Build did not produce a native module: {name}")
            self.check_headers(self.version())
            if self.version().get("abiHash") != version.get("abiHash"):
                raise ControlError("Hyprland changed while building. Retry setup in the current session.")
            return output
        except BaseException:
            shutil.rmtree(output)
            raise

    def unload(self):
        binaries = {"windows-pointer-linux": self.controller.backend.plugin,
                    "mouse-style-mac": self.controller.backend.mac_plugin}
        for item in self.controller.backend.run("plugin", "list", json_output=True):
            if item.get("name") in binaries:
                self.controller.backend.run("plugin", "unload", str(binaries[item["name"]]))

    def recover(self):
        if not self.pending.exists():
            return
        saved = read_json(self.pending)
        directory = Path(saved["backup"])
        if not directory.resolve().is_relative_to(self.state / "install-backups"):
            raise ControlError("Invalid setup recovery journal.")
        transaction = FileTransaction(self.home, directory)
        transaction.records = read_json(transaction.journal)["files"]
        with self.controller.lock():
            self.unload()
            transaction.rollback()
            self.controller.backend.run("reload", "config-only")
            if saved.get("config"):
                self.controller.backend.apply(saved["config"])
            self.pending.unlink()
        self.report("recovered", "Restored the installation interrupted before completion.")

    def active_config(self):
        current = self.controller.backend.snapshot()
        if self.controller.config_file.exists():
            config = self.controller.confirmed()
        else:
            config = {"version": 3, "profile": "omarchy", "windows": deepcopy(WINDOWS_DEFAULT),
                      "mac": deepcopy(MAC_DEFAULT), "omarchy": self.controller.backend.native_settings()}
        if current["profile"] not in ("omarchy", "mac", "win"):
            raise ControlError("Cannot adopt an unverified pointer state.")
        config["profile"] = current["profile"]
        key = "windows" if current["profile"] == "win" else current["profile"]
        config[key] = current[key]
        return migrate_config(config, None)

    def activate(self, build, version):
        self.report("activate", "Installing and verifying the pointer components…")
        with self.controller.lock():
            if self.controller.pending():
                raise ControlError("Keep or revert the pointer trial before completing setup.")
            rollback_config = self.active_config()
            # After an ABI upgrade startup may have fallen back to native motion.
            # Repair must restore the saved style, not overwrite it with that fallback.
            # A full uninstall intentionally retains config.json so a later
            # install restores the user's last confirmed profile. Only a truly
            # fresh install without that file should adopt the native runtime.
            config = self.controller.confirmed() if self.controller.config_file.exists() else rollback_config
            backup = self.state / "install-backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            tx = FileTransaction(self.home, backup)
            previous = read_json(self.receipt) if self.receipt.exists() else {}
            input_path, startup_path = [self.home / ".config/hypr" / name for name in ("input.lua", "autostart.lua")]
            original_input, original_startup = input_path.read_text(), startup_path.read_text()
            startup = startup_config(original_startup, self.home)
            startup_original = previous.get("adopted_startup")
            if startup_original is None:
                startup_original = next((line for line in original_startup.splitlines()
                                         if re.fullmatch(r'''\s*o\.launch_on_start\(["'](?:[^"'\n]*/)?windows-pointer on["']\)\s*''', line)), "")
            write_json(self.pending, {"backup": str(backup), "config": rollback_config})
            try:
                # Read back both modules before restoring the user's active profile.
                self.unload()
                artifacts = {}
                for name in MODULES:
                    destination = self.home / ".local/lib/hyprland/plugins" / name
                    tx.put(destination, (build / name).read_bytes(), 0o755)
                    artifacts[str(destination.relative_to(self.home))] = digest(destination)
                for name in bundle_files(self.root):
                    destination = self.plugin / name
                    if destination.resolve() != (self.root / name).resolve():
                        if (self.plugin / ".git").exists():
                            raise ControlError("This plugin is managed by Git. Update its checkout and run its install.sh instead.")
                        tx.put(destination, (self.root / name).read_bytes(), 0o755 if name.name == "install.sh" else 0o644)
                launcher = self.home / ".local/bin/mouse-style"
                tx.put(launcher, '#!/bin/sh\nexec python3 "$HOME/.config/omarchy/plugins/' + PLUGIN_ID + '/mouse_style.py" "$@"\n', 0o755)
                artifacts[str(launcher.relative_to(self.home))] = digest(launcher)
                legacy = self.home / ".local/lib/mouse-style/mouse_style.py"
                if legacy.is_file() and legacy.read_text().startswith('#!/usr/bin/env python3\n"""Transactional Windows'):
                    tx.remove(legacy)
                tx.put(input_path, input_config(original_input))
                tx.put(startup_path, startup)
                tx.remember(self.controller.config_file)
                tx.remember(self.controller.lua_file)
                write_json(self.controller.config_file, config)
                # Verify native settings and each engine through the real controller.
                for profile in ("omarchy", "win", "mac", config["profile"]):
                    candidate = deepcopy(config)
                    candidate["profile"] = profile
                    self.controller.write_lua(candidate)
                    self.controller.backend.preflight(candidate)
                    self.controller.backend.apply(candidate)
                self.controller.backend.run("reload")
                self.controller.backend.preflight(config)
                self.controller.backend.verify(config)
                record = {"schema": 1, "revision": source_revision(self.root),
                          "abi": version.get("abiHash", version["commit"]), "version": version["version"],
                          "artifacts": artifacts, "adopted_startup": startup_original,
                          "backup": str(backup), "bundle": [str(x) for x in bundle_files(self.root)]}
                tx.put(self.receipt, json.dumps(record, indent=2) + "\n")
                tx.finish()
                self.pending.unlink()
            except BaseException:
                self.unload()
                tx.rollback()
                self.controller.backend.run("reload", "config-only")
                self.controller.backend.apply(rollback_config)
                self.pending.unlink(missing_ok=True)
                raise
        return backup

    def install(self, no_restart=False):
        with self.lock():
            self.recover()
            self.report("check", "Checking the desktop and required components…")
            version = self.preflight()
            if self.status()["ready"]:
                # An explicit repair can restore the saved runtime without a
                # rebuild. Recheck trials under the mutation lock: one may have
                # started after preflight. Passive readiness polling never does this.
                with self.controller.lock():
                    if self.controller.pending():
                        raise ControlError("Keep or revert the pointer trial before completing setup.")
                    config = self.controller.confirmed()
                    self.controller.backend.preflight(config)
                    try:
                        self.controller.backend.verify(config)
                    except ControlError:
                        self.controller.restore()
                self.run(["omarchy-shell", "shell", "rescanPlugins"])
                self.run(["omarchy", "plugin", "enable", PLUGIN_ID])
                self.report("ready", "Mouse Style is already installed and up to date.")
                return
            self.install_packages(self.missing_packages())
            build = self.build(version)
            try:
                backup = self.activate(build, version)
            finally:
                shutil.rmtree(build)
            self.run(["omarchy-shell", "shell", "rescanPlugins"])
            self.run(["omarchy", "plugin", "enable", PLUGIN_ID])
            self.report("ready", f"Mouse Style is ready. Settings preserved. Backup: {backup}")
        if not no_restart:
            self.run(["omarchy", "restart", "shell"])

    def uninstall(self, no_restart=False):
        with self.lock():
            self.recover()
            if not self.receipt.exists():
                raise ControlError("No managed installation found. Run setup once to migrate the development copy.")
            record = read_json(self.receipt)
            with self.controller.lock():
                if self.controller.pending():
                    raise ControlError("Keep or revert the active trial before uninstalling.")
                config = self.active_config()
                backup = self.state / "install-backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-uninstall")
                tx = FileTransaction(self.home, backup)
                write_json(self.pending, {"backup": str(backup), "config": config})
                try:
                    self.unload()
                    input_path = self.home / ".config/hypr/input.lua"
                    startup_path = self.home / ".config/hypr/autostart.lua"
                    tx.put(input_path, input_path.read_text().replace(INPUT_MARKER, "").replace(INPUT_ROUTE + "\n", ""))
                    command = f'o.launch_on_start("{self.home}/.local/bin/mouse-style restore")'
                    # Retire the adopted standalone loader as well: uninstall returns
                    # to the user's underlying native configuration, not another hook.
                    tx.put(startup_path, startup_path.read_text().replace(START_MARKER, "").replace(command + "\n", ""))
                    tx.remove(self.controller.lua_file)
                    for name in record["artifacts"]:
                        path = self.home / name
                        if path.exists() and digest(path) != record["artifacts"][name]:
                            raise ControlError(f"Installed file was changed outside Mouse Style; preserved: {path}")
                        tx.remove(path)
                    tx.remove(self.receipt)
                    self.controller.backend.run("reload")
                    if any(str(e).strip() for e in self.controller.backend.run("configerrors", json_output=True)):
                        raise ControlError("Hyprland reported an error while removing the managed configuration.")
                    tx.finish()
                    self.pending.unlink()
                except BaseException:
                    tx.rollback()
                    self.controller.backend.run("reload", "config-only")
                    self.controller.backend.apply(config)
                    self.pending.unlink(missing_ok=True)
                    raise
            self.run(["omarchy", "plugin", "remove", PLUGIN_ID, "--yes"])
            self.report("removed", "Mouse Style removed; native input restored. Preferences and backups retained. Shared system packages retained.")
        if not no_restart:
            self.run(["omarchy", "restart", "shell"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--status", action="store_true", help="Read installation readiness as JSON; never install packages.")
    action.add_argument("--plan", action="store_true", help="Show the required package plan without changes.")
    action.add_argument("--uninstall", action="store_true")
    action.add_argument("--background", action="store_true", help="Launch an independent setup worker for the bar.")
    parser.add_argument("--yes", action="store_true", help="Accept setup/configuration changes; system authentication still applies.")
    parser.add_argument("--no-restart", action="store_true", help="Keep the current Omarchy shell running (onboarding).")
    args = parser.parse_args()
    installer = Installer()
    try:
        if args.status:
            print(json.dumps(installer.status()))
            return 0
        if args.plan:
            version = installer.preflight()
            print(json.dumps({"hyprland": version["version"], "missing_packages": installer.missing_packages(),
                              "components": list(MODULES), "ready": installer.status()["ready"]}, indent=2))
            return 0
        if os.geteuid() == 0:
            raise ControlError("Run setup as your desktop user, without sudo.")
        if not args.yes:
            if not sys.stdin.isatty():
                raise ControlError("Start setup from the Mouse Style panel, or run ./install.sh in a terminal.")
            prompt = "Remove Mouse Style and return to native input?" if args.uninstall else "Install required packages, build pointer components and integrate Mouse Style?"
            if input(prompt + " [y/N] ").lower() not in ("y", "yes"):
                print("Cancelled.")
                return 1
        if args.background:
            if installer.running():
                return 0
            installer.state.mkdir(parents=True, exist_ok=True, mode=0o700)
            with installer.log.open("w") as log:
                subprocess.Popen([sys.executable, str(ROOT / "setup.py"), "--yes", "--no-restart"],
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                 start_new_session=True, close_fds=True)
            return 0
        def interrupted(signum, frame):
            raise ControlError("Setup interrupted. Run setup again to resume safely.")
        signal.signal(signal.SIGTERM, interrupted)
        if args.uninstall:
            installer.uninstall(args.no_restart)
        else:
            installer.install(args.no_restart)
        return 0
    except (ControlError, OSError, ValueError, KeyError, subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
        if args.status:
            print(json.dumps({"ready": False, "running": False, "message": str(exc)}))
        else:
            installer.report("error", str(exc) or "Setup cancelled; retry when ready.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
