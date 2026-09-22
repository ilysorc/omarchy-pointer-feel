#!/usr/bin/env python3
"""Read pointer status without changing settings, loading plugins, or tracing input."""
import argparse
import datetime
import json
from pathlib import Path
import subprocess


def probe(argv):
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc)}
    if result.returncode:
        return {"ok": False, "error": (result.stderr or result.stdout).strip()[:500]}
    try:
        return {"ok": True, "value": json.loads(result.stdout)}
    except json.JSONDecodeError:
        return {"ok": False, "error": result.stdout.strip()[:500] or "Empty response"}


def inspect():
    options = {name: probe(["hyprctl", "-j", "getoption", name]) for name in (
        "input:accel_profile", "input:sensitivity", "input:force_no_accel")}
    plugins = probe(["hyprctl", "-j", "plugin", "list"])
    plugin_list = plugins.get("value")
    loaded = isinstance(plugin_list, list) and any(
        isinstance(p, dict) and p.get("name") == "windows-pointer-linux" for p in plugin_list)
    windows = probe(["hyprctl", "-j", "windows-pointer-linux"]) if loaded else {
        "ok": False, "error": "Windows backend not observed; plugin list may be unavailable"}
    if isinstance(plugin_list, list):
        plugins["value"] = [{"name": p.get("name"), "version": p.get("version")}
                            for p in plugin_list if isinstance(p, dict)]
    force_raw = options["input:force_no_accel"].get("value", {}).get("bool")
    # Plugin presence alone does not establish that its output moves the cursor.
    observed = "unknown"
    if loaded and windows["ok"] and isinstance(windows.get("value"), dict) and force_raw is False:
        observed = "windows-backend-loaded"
    elif loaded and force_raw is True:
        observed = "raw-override-bypasses-backend-output"
    elif plugin_list == []:
        observed = "native-path; inspect libinput and per-device settings"

    devices = probe(["hyprctl", "-j", "devices"])
    if devices["ok"]:
        payload = devices.get("value")
        if not isinstance(payload, dict) or not isinstance(payload.get("mice"), list):
            devices = {"ok": False, "error": "Hyprland did not return a pointer device list"}
        else:
            devices["value"] = [{
                "name": d.get("name"), "sensor_dpi": None,
                "sensor_dpi_source": "not reported by this interface"
            } for d in payload["mice"]]
    monitors = probe(["hyprctl", "-j", "monitors"])
    if monitors["ok"] and isinstance(monitors.get("value"), list):
        monitors["value"] = [{k: m.get(k) for k in ("name", "width", "height", "scale")}
                             for m in monitors["value"]]
    return {
        "schema_version": 1,
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "read_only": True,
        "observed_profile": observed,
        "hyprland": probe(["hyprctl", "-j", "version"]),
        "plugins": plugins, "windows": windows, "native_options": options,
        "devices": devices, "monitors": monitors,
        "notes": ["Windows status dpi is display DPI, not mouse sensor DPI.",
                  "Empty accel_profile means no explicit profile override.",
                  "Global options do not enumerate per-device overrides.",
                  "A loaded backend is not an independent motion or latency test."]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write the report to this file")
    args = parser.parse_args()
    report = json.dumps(inspect(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(report)
        print(args.output)
    else:
        print(report, end="")
