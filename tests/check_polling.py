#!/usr/bin/env python3
"""Exercise the real QML process lifecycle with an isolated, delayed fake CLI.

Requires Quickshell. Never calls the installed controller or changes the mouse.
An optional argument selects another PointerState.qml for regression comparison.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


QML = r'''
import QtQuick
import Quickshell

Item {
    id: root
    property bool badPoll: false
    property bool queued: false
    property int actionIndex: 0
    property var actions: [["preview", "win"], ["confirm"], ["preview", "omarchy"], ["revert"], ["preview", "mac"], ["confirm"], ["preview", "win"], ["revert"]]
    property var profiles: ["win", "win", "omarchy", "win", "mac", "mac", "win", "mac"]
    property var trials: [true, false, true, false, true, false, true, false]
    property bool finished: false

    function check(value, message) {
        if (value) return true
        finished = true
        console.error("POLLING FAIL: " + message)
        Qt.quit()
        return false
    }
    PointerState {
        id: pointer
        panelOpen: true
        onBusyChanged: {
            if (busy && commandKind === "status" && pointer.queuedAction == null)
                root.badPoll = true
        }
    }
    Timer {
        interval: 20; repeat: true; running: !root.finished
        onTriggered: {
            if (!root.check(!root.badPoll, "background reads locked controls")) return
            if (!root.check(pointer.error === "", pointer.error)) return
            if (pointer.requestRunning || pointer.busy || !pointer.snapshot) return
            if (pointer.snapshot.serial < 3) { pointer.refresh(); return }
            if (root.queued) {
                if (!root.check(pointer.profile === root.profiles[root.actionIndex], "queued action was lost")) return
                if (!root.check(pointer.trial === root.trials[root.actionIndex], "incorrect trial state")) return
                root.actionIndex++
                root.queued = false
            }
            if (root.actionIndex === root.actions.length) {
                root.finished = true
                console.log("POLLING PASS")
                Qt.quit()
                return
            }
            pointer.refresh()
            if (!root.check(!pointer.busy, "refresh disabled controls")) return
            var action = root.actions[root.actionIndex]
            if (action[0] === "preview") {
                if (action[1] === "omarchy") pointer.previewOmarchy(pointer.snapshot.omarchy)
                else if (action[1] === "mac") pointer.previewMac(6, true, false)
                else pointer.preview(action[1], 13, false)
            }
            else if (action[0] === "confirm") pointer.confirm()
            else pointer.revert()
            if (!root.check(pointer.busy, "queued mutation did not lock controls")) return
            // Additional clicks and reads must not replace the accepted action.
            pointer.previewOmarchy(pointer.snapshot.omarchy)
            pointer.refresh()
            root.queued = true
        }
    }
}
'''

FAKE_CLI = r'''#!/usr/bin/env python3
import json
from pathlib import Path
import sys
import time

path = Path(__file__).with_suffix(".json")
data = json.loads(path.read_text())
args = sys.argv[1:]
time.sleep(0.15)
data["commands"].append(args[0])
data["serial"] += 1
if args[0] == "preview":
    if args[1] == "omarchy":
        assert args[2:] == ["--accel", "flat", "--sensitivity", "0.25", "--scroll-factor", "1.2", "--natural-scroll", "off", "--left-handed", "off"]
    if args[1] == "mac":
        assert args[2:] == ["--tracking", "6", "--natural-scroll", "on", "--left-handed", "off"]
    data["previous"] = data["profile"]
    data["profile"] = args[1]
    data["preview"] = {"token": "test-token", "seconds": 15}
elif args[0] == "confirm":
    assert args[1] == "test-token"
    data["preview"] = None
elif args[0] == "revert":
    assert args[1] == "test-token"
    data["profile"] = data["previous"]
    data["preview"] = None
path.write_text(json.dumps(data))
print(json.dumps(data))
'''


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "PointerState.qml"
    with tempfile.TemporaryDirectory(prefix="pointer-feel-polling-") as temp:
        root = Path(temp)
        shutil.copyfile(source, root / "PointerState.qml")
        (root / "shell.qml").write_text(QML)
        command = root / "pointer-feel"
        command.write_text(FAKE_CLI)
        command.chmod(0o755)
        data_file = command.with_suffix(".json")
        data_file.write_text(json.dumps({
            "ok": True, "serial": 0, "commands": [], "profile": "omarchy",
            "preview": None, "windows": {"speed": 10, "epp": True},
            "available": ["win", "mac", "omarchy"],
            "mac": {"model": "sequoia-15.3.2", "tracking": 4, "natural_scroll": True, "left_handed": False},
            "omarchy": {"accel_profile": "flat", "sensitivity": 0.25, "scroll_factor": 1.2,
                        "natural_scroll": False, "left_handed": False},
        }))
        env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"], QT_QPA_PLATFORM="offscreen")
        result = subprocess.run(["quickshell", "--no-color", "-p", str(root)],
                                env=env, capture_output=True, text=True, timeout=20)
        output = result.stdout + result.stderr
        if result.returncode or "POLLING PASS" not in output or "POLLING FAIL" in output:
            print(output)
            return 1
        commands = json.loads(data_file.read_text())["commands"]
        assert commands == ["status"] * 3 + ["status", "preview", "status", "confirm", "status", "preview", "status", "revert"] * 2, commands
        print("PASS: polling stays interactive; preview/confirm/revert clicks during reads run once in order.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
