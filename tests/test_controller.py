from copy import deepcopy
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from mouse_style import Controller, ControlError, Hyprland, validate, write_json, migrate_config, render_lua, MAC_DEFAULT, PROFILE_DEFAULTS


NATIVE = {"accel_profile": "", "sensitivity": 0, "scroll_factor": 1,
          "natural_scroll": False, "left_handed": False}
WIN = {"version": 3, "profile": "win", "windows": {"speed": 10, "epp": True}, "omarchy": NATIVE, "mac": MAC_DEFAULT}


class FakeHyprland:
    def __init__(self):
        self.current = deepcopy(WIN)
        self.fail_next = False
        self.applications = []

    def available_profiles(self):
        return ["win", "mac", "omarchy"]

    def native_settings(self):
        return deepcopy(self.current["omarchy"])

    def snapshot(self):
        return {"profile": self.current["profile"],
                "windows": self.current["windows"] if self.current["profile"] == "win" else None,
                "omarchy": deepcopy(self.current["omarchy"]) if self.current["profile"] == "omarchy" else None,
                "mac": deepcopy(self.current["mac"]) if self.current["profile"] == "mac" else None,
                "backend": None}

    def preflight(self, config):
        pass

    def apply(self, config):
        self.applications.append(deepcopy(config))
        self.current = deepcopy(config)
        if self.fail_next:
            self.fail_next = False
            raise ControlError("Injected failure after changing the backend")
        self.verify(config)

    def verify(self, config):
        if self.current != config:
            raise ControlError("Backend did not apply requested settings")
        return self.snapshot()


class Transactions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.backend = FakeHyprland()
        self.controller = Controller(Path(self.temp.name), self.backend)
        write_json(self.controller.config_file, WIN)
        self.controller.write_lua(WIN)

    def preview(self, profile="omarchy", **kwargs):
        return self.controller.preview(profile, spawn=False, **kwargs)

    def test_trial_changes_runtime_but_does_not_save(self):
        status = self.preview()
        self.assertEqual(status["profile"], "omarchy")
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertIsNotNone(status["preview"])

    def test_label_preference_persists_without_changing_mouse_settings(self):
        self.assertEqual(self.controller.status()["ui"], {"bar_label": "code"})
        for mode in ("letter", "code", "hidden"):
            self.controller.set_bar_label(mode)
            reloaded = Controller(Path(self.temp.name), self.backend)
            self.assertEqual(reloaded.status()["ui"], {"bar_label": mode})
            self.assertEqual(reloaded.confirmed(), WIN)
            self.assertEqual(self.backend.applications, [])
            self.assertIsNone(reloaded.pending())
        with self.assertRaises(ControlError):
            reloaded.set_bar_label("invalid")
        self.assertEqual(reloaded.ui_settings()["bar_label"], "hidden")

    def test_label_change_does_not_commit_or_extend_trial_and_survives_resets(self):
        token = self.preview("mac", mac={"tracking": 9})["preview"]["token"]
        pending = self.controller.pending()
        count = len(self.backend.applications)
        self.controller.set_bar_label("hidden")
        self.assertEqual(self.controller.pending(), pending)
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertEqual(len(self.backend.applications), count)
        result = self.preview("mac", defaults=True, replace_token=token)
        self.controller.revert(result["preview"]["token"])
        self.assertEqual(self.controller.ui_settings()["bar_label"], "hidden")
        token = self.preview("omarchy")["preview"]["token"]
        self.controller.confirm(token)
        self.controller.restore()
        self.assertEqual(self.controller.ui_settings()["bar_label"], "hidden")

    def test_defaults_reset_only_selected_profile_and_keep_persists(self):
        changed = deepcopy(WIN)
        changed["windows"] = {"speed": 17, "epp": False}
        changed["mac"] = dict(MAC_DEFAULT, tracking=9, natural_scroll=False, left_handed=True)
        changed["omarchy"] = dict(NATIVE, accel_profile="flat", sensitivity=-0.4,
                                  scroll_factor=2.3, natural_scroll=True, left_handed=True)
        for profile in ("omarchy", "mac", "win"):
            with self.subTest(profile=profile):
                before = deepcopy(changed)
                before["profile"] = profile
                write_json(self.controller.config_file, before)
                self.backend.current = deepcopy(before)
                result = self.preview(profile, defaults=True)
                expected = deepcopy(before)
                expected["windows" if profile == "win" else profile] = deepcopy(PROFILE_DEFAULTS[profile])
                self.assertEqual(self.backend.current, expected)
                self.assertEqual(self.controller.confirmed(), before)
                self.controller.confirm(result["preview"]["token"])
                self.controller.restore()
                self.assertEqual(self.controller.confirmed(), expected)
                self.assertEqual(self.backend.current, expected)

    def test_reset_within_trial_keeps_other_edits_and_original_rollback(self):
        token = self.preview("mac", mac={"tracking": 9})["preview"]["token"]
        token = self.preview("win", speed=17, epp=False, replace_token=token)["preview"]["token"]
        result = self.preview("mac", defaults=True, replace_token=token)
        self.assertEqual(result["mac"], MAC_DEFAULT)
        self.assertEqual(result["windows"], {"speed": 17, "epp": False})
        self.controller.revert(result["preview"]["token"])
        self.assertEqual(self.backend.current, WIN)
        self.assertEqual(self.controller.confirmed(), WIN)

    def test_defaults_failure_restores_previous_preferences(self):
        changed = deepcopy(WIN)
        changed["windows"]["speed"] = 17
        self.backend.current = changed
        self.backend.fail_next = True
        with self.assertRaises(ControlError):
            self.preview("win", defaults=True)
        self.assertEqual(self.backend.current, changed)
        self.assertEqual(self.controller.confirmed(), WIN)

    def test_defaults_cannot_mix_with_manual_settings(self):
        for profile, kwargs in (("win", {"speed": 17}), ("win", {"epp": False}),
                                ("mac", {"mac": {"tracking": 9}}),
                                ("omarchy", {"native": {"sensitivity": -0.4}})):
            with self.subTest(profile=profile, kwargs=kwargs), self.assertRaises(ControlError):
                self.preview(profile, defaults=True, **kwargs)
        self.assertEqual(self.backend.applications, [])

    def test_default_reset_is_noop_when_already_active_and_saved(self):
        result = self.preview("win", defaults=True)
        self.assertIsNone(result["preview"])
        self.assertEqual(self.backend.applications, [])

    def test_confirm_persists_default_across_restore(self):
        token = self.preview()["preview"]["token"]
        self.controller.confirm(token)
        self.backend.current = deepcopy(WIN)
        self.controller.restore()
        self.assertEqual(self.backend.current["profile"], "omarchy")
        self.assertIsNone(self.controller.pending())

    def test_expired_trial_restores_actual_prior_settings(self):
        self.backend.current["windows"]["speed"] = 11
        self.preview("win", speed=13)
        pending = self.controller.pending()
        pending["deadline"] = time.monotonic() - 1
        write_json(self.controller.pending_file, pending)
        status = self.controller.status()
        self.assertEqual(status["windows"]["speed"], 11)
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertIsNone(status["preview"])

    def test_stale_confirm_cannot_save_a_new_trial(self):
        token = self.preview()["preview"]["token"]
        with self.assertRaises(ControlError):
            self.controller.confirm("stale-token")
        self.assertEqual(self.controller.pending()["token"], token)
        self.assertEqual(self.controller.confirmed(), WIN)

    def test_confirm_requires_backend_readback(self):
        token = self.preview("win", speed=12)["preview"]["token"]
        self.backend.current["windows"]["speed"] = 10
        with self.assertRaises(ControlError):
            self.controller.confirm(token)
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertIsNotNone(self.controller.pending())

    def test_partial_apply_failure_rolls_back(self):
        self.backend.fail_next = True
        with self.assertRaises(ControlError):
            self.preview("win", speed=15, epp=False)
        self.assertEqual(self.backend.current, WIN)
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertIn('"10/20"', self.controller.lua_file.read_text())
        self.assertIsNone(self.controller.pending())

    def test_watchdog_spawn_failure_never_leaves_a_trial(self):
        with patch.object(self.controller, "spawn_watchdog", side_effect=OSError("spawn failed")):
            with self.assertRaises(ControlError):
                self.controller.preview("omarchy")
        self.assertEqual(self.backend.current, WIN)
        self.assertIsNone(self.controller.pending())

    def test_duplicate_apply_does_not_reset_native_state(self):
        self.preview("win")
        self.assertEqual(self.backend.applications, [])
        self.assertIsNone(self.controller.pending())

    def test_cannot_start_over_an_unconfirmed_trial(self):
        self.preview()
        with self.assertRaises(ControlError):
            self.preview("win")
        self.assertEqual(self.backend.current["profile"], "omarchy")

    def test_adjustment_applies_immediately_and_revert_restores_original_runtime(self):
        self.backend.current["windows"]["speed"] = 11
        first = self.preview("mac", mac={"tracking": 2})["preview"]["token"]
        second = self.preview("mac", mac={"tracking": 10}, replace_token=first)
        self.assertEqual(second["mac"]["tracking"], 10)
        self.assertNotEqual(first, second["preview"]["token"])
        self.assertEqual(self.controller.confirmed(), WIN)
        self.assertEqual(self.controller.revert(second["preview"]["token"])["windows"]["speed"], 11)

    def test_adjusted_trial_renews_deadline_and_expiry_restores_original(self):
        token = self.preview("mac")["preview"]["token"]
        pending = self.controller.pending()
        pending["deadline"] = time.monotonic() + 1
        write_json(self.controller.pending_file, pending)
        self.preview("mac", mac={"tracking": 10}, replace_token=token)
        pending = self.controller.pending()
        self.assertGreater(pending["deadline"], time.monotonic() + 14)
        pending["deadline"] = time.monotonic() - 1
        write_json(self.controller.pending_file, pending)
        self.assertEqual(self.controller.status()["profile"], "win")
        self.assertEqual(self.backend.current, WIN)

    def test_switching_during_trial_retains_each_styles_pending_values(self):
        token = self.preview("mac", mac={"tracking": 9})["preview"]["token"]
        result = self.preview("win", speed=12, replace_token=token)
        self.assertEqual(result["mac"]["tracking"], 9)
        result = self.preview("mac", replace_token=result["preview"]["token"])
        self.assertEqual(result["mac"]["tracking"], 9)
        self.assertEqual(result["windows"]["speed"], 12)
        self.controller.confirm(result["preview"]["token"])
        self.controller.restore()
        self.assertEqual(self.controller.confirmed()["mac"]["tracking"], 9)
        self.assertEqual(self.controller.confirmed()["windows"]["speed"], 12)

    def test_old_token_cannot_confirm_revert_or_replace_an_adjusted_trial(self):
        old = self.preview("mac")["preview"]["token"]
        new = self.preview("mac", mac={"tracking": 9}, replace_token=old)["preview"]["token"]
        for action in (lambda: self.controller.confirm(old), lambda: self.controller.revert(old),
                       lambda: self.preview("win", replace_token=old)):
            with self.assertRaises(ControlError):
                action()
            self.assertEqual(self.controller.pending()["token"], new)
            self.assertEqual(self.backend.current["mac"]["tracking"], 9)

    def test_expired_adjustment_cannot_silently_start_a_new_trial(self):
        token = self.preview("mac")["preview"]["token"]
        pending = self.controller.pending()
        pending["deadline"] = time.monotonic() - 1
        write_json(self.controller.pending_file, pending)
        with self.assertRaises(ControlError):
            self.preview("mac", mac={"tracking": 9}, replace_token=token)
        self.assertEqual(self.backend.current, WIN)
        self.assertIsNone(self.controller.pending())

    def test_failed_adjustment_returns_to_original_not_intermediate_state(self):
        token = self.preview("mac", mac={"tracking": 2})["preview"]["token"]
        self.backend.fail_next = True
        with self.assertRaises(ControlError):
            self.preview("mac", mac={"tracking": 10}, replace_token=token)
        self.assertEqual(self.backend.current, WIN)
        self.assertIsNone(self.controller.pending())

    def test_replacement_watchdog_spawn_failure_restores_original(self):
        token = self.preview("mac")["preview"]["token"]
        with patch.object(self.controller, "spawn_watchdog", side_effect=OSError("spawn failed")):
            with self.assertRaises(ControlError):
                self.controller.preview("mac", mac={"tracking": 10}, replace_token=token)
        self.assertEqual(self.backend.current, WIN)
        self.assertIsNone(self.controller.pending())

    def test_duplicate_adjustment_is_noop_and_does_not_extend_timer(self):
        token = self.preview("mac", mac={"tracking": 9})["preview"]["token"]
        pending = self.controller.pending()
        count = len(self.backend.applications)
        self.preview("mac", mac={"tracking": 9}, replace_token=token)
        self.assertEqual(self.controller.pending(), pending)
        self.assertEqual(len(self.backend.applications), count)

    def test_revert_restores_before_confirmation(self):
        token = self.preview("win", speed=14, epp=False)["preview"]["token"]
        self.controller.revert(token)
        self.assertEqual(self.backend.current, WIN)
        self.assertEqual(self.controller.confirmed(), WIN)

    def test_invalid_preferences_never_reach_runtime(self):
        for speed in (0, 21, True, 1.5):
            with self.assertRaises(ControlError):
                self.preview("win", speed=speed)
        with self.assertRaises(ControlError):
            self.preview("custom")
        self.assertEqual(self.backend.applications, [])

    def test_missing_windows_binary_does_not_advertise_a_working_win_mode(self):
        backend = Hyprland(Path(self.temp.name) / "missing.so")
        self.assertEqual(backend.available_profiles(), ["omarchy"])

    def test_native_settings_persist_independently_of_windows(self):
        original_win = deepcopy(WIN["windows"])
        native = dict(NATIVE, accel_profile="flat", sensitivity=-0.35, scroll_factor=1.4,
                      natural_scroll=True, left_handed=True)
        token = self.preview("omarchy", native=native)["preview"]["token"]
        self.controller.confirm(token)
        self.controller.restore()
        self.assertEqual(self.backend.current["omarchy"], native)
        self.assertEqual(self.controller.confirmed()["windows"], original_win)
        token = self.preview("win", speed=12, epp=False)["preview"]["token"]
        self.controller.confirm(token)
        self.assertEqual(self.controller.confirmed()["omarchy"], native)
        token = self.preview("omarchy")["preview"]["token"]
        self.controller.confirm(token)
        self.assertEqual(self.backend.current["omarchy"], native)
        self.assertEqual(self.controller.confirmed()["windows"], {"speed": 12, "epp": False})

    def test_native_expiry_restores_actual_native_values(self):
        self.backend.current["profile"] = "omarchy"
        self.backend.current["omarchy"] = dict(NATIVE, accel_profile="adaptive", sensitivity=0.25)
        before = deepcopy(self.backend.current)
        self.preview("omarchy", native={"accel_profile": "flat", "sensitivity": -0.4})
        pending = self.controller.pending()
        pending["deadline"] = time.monotonic() - 1
        write_json(self.controller.pending_file, pending)
        self.controller.status()
        self.assertEqual(self.backend.current, before)
        self.assertEqual(self.controller.confirmed(), WIN)

    def test_native_partial_failure_restores_windows(self):
        self.backend.fail_next = True
        with self.assertRaises(ControlError):
            self.preview("omarchy", native={"accel_profile": "flat", "sensitivity": 0.25})
        self.assertEqual(self.backend.current, WIN)
        self.assertIsNone(self.controller.pending())

    def test_reject_invalid_or_wrong_profile_native_values(self):
        for native in ({"sensitivity": 1.1}, {"sensitivity": float("nan")},
                       {"sensitivity": True}, {"scroll_factor": -1}, {"scroll_factor": float("inf")},
                       {"accel_profile": "flat\\\"; os.exit()"}, {"left_handed": "false"},
                       {"natural_scroll": 1}, {"unknown": 1}):
            with self.assertRaises(ControlError):
                self.preview("omarchy", native=native)
        with self.assertRaises(ControlError):
            self.preview("win", native={"sensitivity": 0.4})
        with self.assertRaises(ControlError):
            self.preview("omarchy", speed=15)
        self.assertEqual(self.backend.applications, [])

    def test_migration_keeps_existing_preferences_and_native_values(self):
        native = dict(NATIVE, accel_profile="flat", sensitivity=0.4, natural_scroll=True)
        old = {"version": 1, "profile": "default", "windows": {"speed": 13, "epp": False}}
        upgraded = migrate_config(old, native)
        self.assertEqual(upgraded["profile"], "omarchy")
        self.assertEqual(upgraded["windows"], old["windows"])
        self.assertEqual(upgraded["omarchy"], native)
        self.assertEqual(old["version"], 1)
        self.assertEqual(migrate_config(upgraded, NATIVE), upgraded)

    def test_windows_lua_does_not_apply_stored_native_settings(self):
        config = deepcopy(WIN)
        config["omarchy"] = dict(NATIVE, accel_profile="flat", sensitivity=-0.5)
        self.assertNotIn("input =", render_lua(config))
        config["profile"] = "omarchy"
        self.assertIn('accel_profile = "flat"', render_lua(config))
        self.assertIn('sensitivity = -0.5', render_lua(config))

    def test_native_readback_rejects_unapplied_values(self):
        backend = Hyprland(Path("missing.so"))
        config = deepcopy(WIN)
        config["profile"] = "omarchy"
        config["omarchy"]["sensitivity"] = 0.4
        with patch.object(backend, "snapshot", return_value={"profile": "omarchy", "omarchy": NATIVE}):
            with self.assertRaises(ControlError):
                backend.verify(config)

    def test_default_cli_alias_remains_compatible(self):
        self.assertEqual(self.preview("default")["profile"], "omarchy")

    def test_mac_trial_and_saved_preferences_are_independent(self):
        before = deepcopy(self.controller.confirmed())
        result = self.preview("mac", mac={"tracking": 7, "natural_scroll": False, "left_handed": True})
        self.assertEqual(result["mac"]["tracking"], 7)
        self.assertEqual(self.controller.confirmed(), before)
        self.controller.confirm(result["preview"]["token"])
        restored = self.controller.restore()
        self.assertEqual(restored["mac"]["tracking"], 7)
        self.assertEqual(restored["confirmed"]["windows"], before["windows"])
        self.assertEqual(restored["confirmed"]["omarchy"], before["omarchy"])

    def test_mac_failure_and_expiry_restore_previous_engine(self):
        self.backend.fail_next = True
        with self.assertRaises(ControlError):
            self.preview("mac")
        self.assertEqual(self.backend.current, WIN)
        self.preview("mac")
        pending = self.controller.pending()
        pending["deadline"] = time.monotonic() - 1
        write_json(self.controller.pending_file, pending)
        self.assertEqual(self.controller.status()["profile"], "win")
        self.assertEqual(self.backend.current, WIN)

    def test_mac_to_native_revert_restores_actual_mac_values(self):
        self.backend.current["profile"] = "mac"
        self.backend.current["mac"] = dict(MAC_DEFAULT, tracking=6)
        token = self.preview("omarchy")["preview"]["token"]
        self.assertEqual(self.controller.revert(token)["mac"]["tracking"], 6)

    def test_invalid_mac_preferences_rejected(self):
        for mac in ({"tracking": 0}, {"tracking": 11}, {"tracking": True},
                    {"tracking": 1.5}, {"natural_scroll": "false"}, {"model": "unknown"}):
            with self.assertRaises(ControlError):
                self.preview("mac", mac=mac)
        with self.assertRaises(ControlError):
            self.preview("win", mac={"tracking": 3})
        self.assertEqual(self.backend.applications, [])

    def test_mac_readback_must_match_requested_settings(self):
        backend = Hyprland(Path("missing.so"))
        config = deepcopy(WIN)
        config["profile"] = "mac"
        with patch.object(backend, "snapshot", return_value={"profile": "mac", "mac": dict(MAC_DEFAULT, tracking=9)}):
            with self.assertRaises(ControlError):
                backend.verify(config)

    def test_engine_switch_unloads_before_loading(self):
        backend = Hyprland(Path("windows-pointer-linux.so"))
        for old, new in (("win", "mac"), ("mac", "win"), ("mac", "omarchy")):
            config = deepcopy(WIN)
            config["profile"] = new
            with patch.object(backend, "snapshot", return_value={"profile": old}), \
                 patch.object(backend, "verify"), patch.object(backend, "run") as run:
                backend.apply(config)
                calls = [c.args for c in run.call_args_list]
                self.assertEqual(calls[0][0:2], ("plugin", "unload"))
                if new != "omarchy":
                    self.assertEqual(calls[1][0:2], ("plugin", "load"))
                self.assertEqual(calls[-1], ("reload", "config-only"))

    def test_v2_migration_retains_both_existing_profiles(self):
        old = deepcopy(WIN)
        old.pop("mac")
        old["version"] = 2
        new = migrate_config(old, None)
        self.assertEqual(new["windows"], old["windows"])
        self.assertEqual(new["omarchy"], old["omarchy"])
        self.assertEqual(new["mac"], MAC_DEFAULT)


if __name__ == "__main__":
    unittest.main()
