#!/usr/bin/env python3
"""Exercise actual onboarding QML with a fake installer and inert surface."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

QML = r'''
import QtQuick
import QtQuick.Window
import QtTest
import Quickshell
Window {
    id: root
    width: 430; height: 650; visible: true
    Item { id: anchor }
    SetupState { id: setup }
    SetupPanel { id: panel; anchorItem: anchor; bar: null; setupState: setup; open: true }
    TestCase {
        name: "SetupFlow"
        function test_setup() {
            tryVerify(function() { return setup.checked }, 5000)
            verify(!setup.ready)
            var button = findChild(panel, "installComponents")
            verify(button !== null)
            verify(waitForPolish(root))
            verify(button.enabled)
            mouseClick(button)
            tryVerify(function() { return setup.running }, 5000)
            verify(!button.enabled)
            // Closing the surface must not stop the detached installer.
            panel.open = false
            tryVerify(function() { return setup.ready && !setup.running }, 7000)
            compare(setup.message, "Ready")
            console.log("SETUP PANEL PASS")
        }
    }
}
'''

INSTALLER = r'''#!/usr/bin/env bash
case "$1" in
--status)
  if [[ -f "$SETUP_TEST_ROOT/done" ]]; then
    echo '{"ready":true,"running":false,"message":"Ready"}'
  elif [[ -f "$SETUP_TEST_ROOT/started" ]]; then
    echo '{"ready":false,"running":true,"message":"Building"}'
  else
    echo '{"ready":false,"running":false,"message":"Components missing"}'
  fi ;;
--background)
  touch "$SETUP_TEST_ROOT/started"
  (sleep 2; touch "$SETUP_TEST_ROOT/done") >/dev/null 2>&1 & ;;
*) exit 2 ;;
esac
'''


def main():
    source = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="pointer-feel-setup-qml-") as temp:
        root = Path(temp)
        for name in ("SetupState.qml", "SetupPanel.qml"):
            shutil.copyfile(source / name, root / name)
        qs = root / "qs"
        qs.mkdir()
        for entry in Path("/usr/share/omarchy/shell").iterdir():
            if entry.name != "Ui":
                (qs / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
        ui = qs / "Ui"
        ui.mkdir()
        for entry in Path("/usr/share/omarchy/shell/Ui").iterdir():
            if entry.name != "KeyboardPanel.qml":
                (ui / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
        (ui / "KeyboardPanel.qml").write_text('''import QtQuick
Item {
 required property Item anchorItem
 required property QtObject bar
 property bool open: false
 property Item focusTarget
 property int contentWidth: 370
 property int contentHeight: 550
 width: contentWidth; height: contentHeight
 function fittedContentWidth(value) { return value }
 function fittedContentHeight(value) { return value }
 function close() { open = false }
}
''')
        (root / "install.sh").write_text(INSTALLER)
        (root / "shell.qml").write_text(QML)
        env = dict(os.environ, QML_IMPORT_PATH=str(root), QT_QPA_PLATFORM="offscreen", SETUP_TEST_ROOT=str(root))
        result = subprocess.run(["quickshell", "--no-color", "-p", str(root)], env=env,
                                capture_output=True, text=True, timeout=20)
        output = result.stdout + result.stderr
        if result.returncode or "SETUP PANEL PASS" not in output or "FAIL!" in output:
            print(output)
            return 1
        print("PASS: first-use setup installs through the real button, shows progress, prevents duplicate clicks, and completes after closing the panel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
