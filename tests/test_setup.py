from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import setup
from pointer_feel import Controller, ControlError, write_json
from test_controller import FakeHyprland, WIN


VERSION = {"version": "0.56.2", "commit": "test-commit", "abiHash": "test-abi"}


class Backend(FakeHyprland):
    def __init__(self, home):
        super().__init__()
        self.plugin = home / ".local/lib/hyprland/plugins/windows-pointer-linux.so"
        self.mac_plugin = self.plugin.with_name("pointer-feel-mac.so")
        self.fail_profile = None

    def run(self, *args, json_output=False):
        if args[:2] == ("plugin", "list"):
            name = {"win": "windows-pointer-linux", "mac": "pointer-feel-mac"}.get(self.current["profile"])
            return [{"name": name}] if name else []
        if args[:2] == ("plugin", "unload"):
            self.current["profile"] = "omarchy"
        if args[0] == "configerrors":
            return [""]  # Real hyprctl uses this for an empty error list.
        return "ok"

    def apply(self, config):
        super().apply(config)
        if self.fail_profile == config["profile"]:
            self.fail_profile = None
            raise ControlError("Injected native module load failure")


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        hypr = self.home / ".config/hypr"
        hypr.mkdir(parents=True)
        (hypr / "hyprland.lua").write_text('require("hypr.input")\nrequire("hypr.autostart")\n')
        (hypr / "input.lua").write_text('-- Personal input\n')
        (hypr / "autostart.lua").write_text('o.launch_on_start("my-app")\n')
        self.backend = Backend(self.home)
        self.backend.plugin.parent.mkdir(parents=True)
        self.backend.plugin.write_bytes(b"existing-native-windows")
        self.controller = Controller(self.home, self.backend)
        write_json(self.controller.config_file, WIN)
        write_json(self.controller.ui_file, {"bar_label": "letter"})
        self.controller.write_lua(WIN)
        self.installed = set(setup.PACKAGES)
        self.commands = []
        self.deny = False
        self.installer = setup.Installer(home=self.home, controller=self.controller, runner=self.run_command)
        self.builds = 0
        self.installer.build = self.build

    def run_command(self, argv, **kwargs):
        self.commands.append(argv)
        code, output = 0, ""
        if argv == ["hyprctl", "version", "-j"]:
            output = json.dumps(VERSION)
        elif argv[:2] == ["pacman", "-Q"]:
            code = int(argv[2] not in self.installed)
        elif "/usr/bin/pacman" in argv:
            if self.deny:
                code = 126
            else:
                self.installed.update(argv[argv.index("--") + 1:])
        return subprocess.CompletedProcess(argv, code, output, "")

    def build(self, version):
        self.builds += 1
        path = self.home / "build-test"
        path.mkdir(exist_ok=True)
        for name in setup.MODULES:
            (path / name).write_bytes(b"\x7fELF" + name.encode())
        return path

    def install(self):
        with patch("setup.shutil.which", return_value="/usr/bin/test"), patch("builtins.print"):
            self.installer.install(no_restart=True)

    def test_missing_dependencies_installed_in_one_privileged_transaction(self):
        self.installed -= {"cmake", "gcc", "pkgconf"}
        with patch("sys.stdin.isatty", return_value=False):
            self.install()
        installs = [cmd for cmd in self.commands if "/usr/bin/pacman" in cmd]
        self.assertEqual(len(installs), 1)
        self.assertEqual(installs[0][:3], ["/usr/bin/pkexec", "--disable-internal-agent", "/usr/bin/pacman"])
        self.assertNotIn("-Sy", installs[0])
        self.assertEqual(set(installs[0][installs[0].index("--") + 1:]), {"gcc", "cmake", "pkgconf"})
        self.assertTrue(self.installer.status()["ready"])

    def test_password_cancellation_preserves_working_installation(self):
        self.installed.remove("cmake")
        self.deny = True
        original = self.backend.plugin.read_bytes()
        with self.assertRaises(ControlError):
            self.install()
        self.assertEqual(self.builds, 0)
        self.assertEqual(self.backend.plugin.read_bytes(), original)
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertFalse(self.installer.receipt.exists())

    def test_success_preserves_preferences_and_second_install_does_not_rebuild(self):
        self.install()
        self.assertTrue(self.installer.status()["ready"])
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertEqual(self.controller.ui_settings(), {"bar_label": "letter"})
        self.assertEqual(self.backend.current, WIN)
        self.install()
        self.assertEqual(self.builds, 1)
        self.assertFalse(any("/usr/bin/pacman" in cmd for cmd in self.commands))
        self.assertEqual((self.home / ".config/hypr/input.lua").read_text().count(setup.INPUT_ROUTE), 1)
        self.assertEqual((self.home / ".config/hypr/autostart.lua").read_text().count("pointer-feel restore"), 1)

    def test_module_failure_rolls_back_binaries_configuration_and_new_files(self):
        old = self.backend.plugin.read_bytes()
        old_input = (self.home / ".config/hypr/input.lua").read_text()
        self.backend.fail_profile = "mac"
        with self.assertRaisesRegex(ControlError, "native module"):
            self.install()
        self.assertEqual(self.backend.plugin.read_bytes(), old)
        self.assertFalse(self.backend.mac_plugin.exists())
        self.assertEqual((self.home / ".config/hypr/input.lua").read_text(), old_input)
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertEqual(self.backend.current, WIN)
        self.assertFalse(self.installer.receipt.exists())
        self.assertFalse(self.installer.pending.exists())

    def test_fresh_native_install_starts_native_and_builds_both_modules(self):
        self.controller.config_file.unlink()
        self.backend.current["profile"] = "omarchy"
        self.backend.plugin.unlink()
        self.install()
        self.assertEqual(self.controller.confirmed()["profile"], "omarchy")
        self.assertEqual(self.backend.current["profile"], "omarchy")
        self.assertTrue(self.backend.plugin.exists() and self.backend.mac_plugin.exists())

    def test_setup_from_its_git_managed_plugin_checkout_preserves_sources(self):
        root = self.installer.plugin
        for relative in setup.bundle_files(self.installer.root):
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.installer.root / relative, destination)
        subprocess.run(["git", "init", "--quiet", str(root)], check=True)
        self.installer.root = root
        revision = setup.source_revision(root)
        self.install()
        self.assertTrue(self.installer.status()["ready"])
        self.assertEqual(setup.source_revision(root), revision)
        self.assertTrue((root / ".git/HEAD").is_file())
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertEqual(self.backend.current, WIN)

    def test_setup_does_not_overwrite_a_different_git_managed_checkout(self):
        root = self.installer.plugin
        root.mkdir(parents=True)
        subprocess.run(["git", "init", "--quiet", str(root)], check=True)
        local_file = root / "manifest.json"
        local_file.write_text('"retained checkout"\n')
        old_binary = self.backend.plugin.read_bytes()
        with self.assertRaisesRegex(ControlError, "managed by Git"):
            self.install()
        self.assertEqual(local_file.read_text(), '"retained checkout"\n')
        self.assertEqual(self.backend.plugin.read_bytes(), old_binary)
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertEqual(self.backend.current, WIN)

    def test_changed_abi_or_missing_binary_requires_repair(self):
        self.install()
        with patch.object(self.installer, "version", return_value={**VERSION, "abiHash": "new-build"}):
            self.assertFalse(self.installer.status()["ready"])
        self.backend.mac_plugin.unlink()
        self.assertFalse(self.installer.status()["ready"])

    def test_runtime_profile_does_not_determine_installation_readiness(self):
        self.install()
        self.backend.current["profile"] = "omarchy"
        self.assertTrue(self.installer.status()["ready"])
        # A read crossing a native module unload must not imply missing files.
        with patch.object(self.backend, "snapshot", side_effect=ControlError("Engine is unloading")):
            self.assertTrue(self.installer.status()["ready"])

    def test_readiness_during_profile_switches_and_keep_commit(self):
        self.install()
        observations = []
        apply = self.backend.apply

        def observe(phase):
            observations.append((phase, self.installer.status()["ready"]))

        def apply_with_polls(config):
            observe("before apply " + config["profile"])
            # Switching native engines unloads one before loading the next.
            self.backend.current["profile"] = "omarchy"
            observe("module unloaded before " + config["profile"])
            apply(config)
            observe("after apply " + config["profile"])

        def write_with_poll(path, data):
            if path == self.controller.config_file:
                # Keep removes preview.json before committing config.json.
                self.assertIsNone(self.controller.pending())
                observe("Keep before saving " + data["profile"])
            write_json(path, data)

        with patch.object(self.backend, "apply", side_effect=apply_with_polls), \
                patch("pointer_feel.write_json", side_effect=write_with_poll), self.controller.lock():
            for profile in ("omarchy", "win", "mac", "win", "omarchy", "mac"):
                trial = self.controller.preview(profile, spawn=False)
                observe("trial " + profile)
                self.controller.confirm(trial["preview"]["token"])
                observe("saved " + profile)
            # Replace a trial and revert to its original rollback anchor.
            trial = self.controller.preview("win", spawn=False)
            trial = self.controller.preview("omarchy", spawn=False,
                                            replace_token=trial["preview"]["token"])
            self.controller.revert(trial["preview"]["token"])
            observe("reverted")
        self.assertEqual([phase for phase, ready in observations if not ready], [])
        self.assertEqual(self.backend.current, self.controller.confirmed())

    def test_readiness_still_detects_damaged_or_changed_installation(self):
        self.install()
        with patch("setup.source_revision", return_value="changed-source"):
            self.assertFalse(self.installer.status()["ready"])
        input_file = self.home / ".config/hypr/input.lua"
        original = input_file.read_text()
        input_file.write_text("-- Integration removed\n")
        self.assertFalse(self.installer.status()["ready"])
        input_file.write_text(original)
        self.backend.mac_plugin.write_bytes(b"damaged-native-module")
        self.assertFalse(self.installer.status()["ready"])

    def test_active_pointer_trial_does_not_open_setup_panel(self):
        self.install()
        self.backend.current["profile"] = "mac"
        candidate = deepcopy(WIN)
        candidate["profile"] = "mac"
        write_json(self.controller.pending_file, {
            "token": "trial-token", "session": self.controller.session,
            "candidate": candidate,
        })
        self.assertTrue(self.installer.status()["ready"])

    def test_build_failure_does_not_modify_runtime(self):
        def fail(version):
            raise ControlError("compiler failed")
        self.installer.build = fail
        before = self.backend.plugin.read_bytes()
        with self.assertRaisesRegex(ControlError, "compiler failed"):
            self.install()
        self.assertEqual(before, self.backend.plugin.read_bytes())
        self.assertEqual(self.backend.current, WIN)

    def test_repair_restores_saved_profile_after_native_startup_fallback(self):
        self.install()
        self.backend.current["profile"] = "omarchy"
        self.backend.mac_plugin.unlink()
        self.install()
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertEqual(self.backend.current, WIN)
        self.assertEqual(self.builds, 2)

    def test_runtime_only_repair_restores_saved_profile_without_rebuilding(self):
        self.install()
        self.backend.current["profile"] = "omarchy"
        self.install()
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertEqual(self.backend.current, WIN)
        self.assertEqual(self.builds, 1)

    def test_reinstall_after_uninstall_restores_saved_profile_without_receipt(self):
        self.backend.current["profile"] = "omarchy"
        self.backend.plugin.unlink(missing_ok=True)
        self.backend.mac_plugin.unlink(missing_ok=True)
        self.assertFalse(self.installer.receipt.exists())
        self.install()
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertEqual(self.backend.current["profile"], "win")

    def test_lock_prevents_concurrent_installers(self):
        with self.installer.lock():
            self.assertTrue(self.installer.running())
            with self.assertRaisesRegex(ControlError, "already running"):
                with self.installer.lock():
                    self.fail("second installer acquired the lock")
        self.assertFalse(self.installer.running())

    def test_recovery_restores_interrupted_file_transaction(self):
        file = self.home / ".config/hypr/input.lua"
        original = file.read_text()
        backup = self.installer.state / "install-backups/interrupted"
        tx = setup.FileTransaction(self.home, backup)
        tx.put(file, "incomplete change")
        write_json(self.installer.pending, {"backup": str(backup), "config": WIN})
        with patch("builtins.print"):
            self.installer.recover()
        self.assertEqual(file.read_text(), original)
        self.assertEqual(self.backend.current, WIN)
        self.assertFalse(self.installer.pending.exists())

    def test_uninstall_preserves_unrelated_later_edits_and_shared_packages(self):
        self.install()
        file = self.home / ".config/hypr/input.lua"
        file.write_text(file.read_text() + "-- Added later\n")
        with patch("builtins.print"):
            self.installer.uninstall(no_restart=True)
        self.assertEqual(file.read_text(), "-- Personal input\n\n-- Added later\n")
        self.assertNotIn("pointer-feel restore", (file.parent / "autostart.lua").read_text())
        self.assertIn("my-app", (file.parent / "autostart.lua").read_text())
        self.assertFalse(self.backend.plugin.exists())
        self.assertFalse(self.backend.mac_plugin.exists())
        self.assertFalse(self.installer.receipt.exists())
        self.assertTrue(self.controller.config_file.exists())
        self.assertTrue(self.controller.ui_file.exists())
        self.assertFalse(any("/usr/bin/pacman" in cmd for cmd in self.commands))

    def test_uninstall_changed_artifact_fails_and_restores_integration(self):
        self.install()
        self.backend.mac_plugin.write_bytes(b"user-replacement")
        with patch("builtins.print"), self.assertRaisesRegex(ControlError, "changed outside"):
            self.installer.uninstall(no_restart=True)
        self.assertTrue(self.installer.receipt.exists())
        self.assertIn(setup.INPUT_ROUTE, (self.home / ".config/hypr/input.lua").read_text())
        self.assertEqual(self.backend.mac_plugin.read_bytes(), b"user-replacement")

    def test_transaction_rejects_symlinks(self):
        file = self.home / "external"
        file.symlink_to("/etc/hosts")
        tx = setup.FileTransaction(self.home, self.home / "backup")
        with self.assertRaises(ControlError):
            tx.put(file, "replacement")

    def test_unknown_hyprland_refused_before_package_install(self):
        with patch.object(self.installer, "version", return_value={**VERSION, "version": "0.99.0"}):
            with self.assertRaisesRegex(ControlError, "not supported"):
                self.install()
        self.assertEqual(self.builds, 0)
        self.assertFalse(any("/usr/bin/pacman" in cmd for cmd in self.commands))

    def test_pending_trial_blocks_install_before_packages(self):
        write_json(self.controller.pending_file, {"token": "pending"})
        with self.assertRaisesRegex(ControlError, "Keep or revert"):
            self.install()
        self.assertEqual(self.builds, 0)

    def test_headers_resolved_from_pkg_config_cflags_without_includedir_variable(self):
        include = self.home / "include path"
        header = include / "hyprland/src/version.h"
        header.parent.mkdir(parents=True)
        header.write_text('#define GIT_COMMIT_HASH "test-commit"\n')
        def metadata(argv, **kwargs):
            if "--modversion" in argv:
                value = "0.56.2\n"
            elif "--cflags-only-I" in argv:
                value = '-I"' + str(include) + '"'
            else:
                value = ""
            return subprocess.CompletedProcess(argv, 0, value, "")
        with patch.object(self.installer, "run", side_effect=metadata):
            self.installer.check_headers(VERSION)
            header.write_text('#define GIT_COMMIT_HASH "another-build"\n')
            with self.assertRaisesRegex(ControlError, "different commits"):
                self.installer.check_headers(VERSION)


if __name__ == "__main__":
    unittest.main()
