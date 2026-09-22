#!/usr/bin/env python3
"""Exercise actual Panel controls and PointerState against an isolated fake CLI.

Uses real panel/button/slider code with an inert panel surface offscreen;
never calls real mouse-style or captures desktop input.
QtTest sends mouse/keyboard events into an offscreen window, without desktop input.
"""
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
    visible: true
    width: 420; height: 900
    Item { id: anchor }
    PointerState { id: pointer; panelOpen: true }
    Panel { id: panel; anchorItem: anchor; bar: null; pointerState: pointer }
    TestCase {
        id: test
        name: "DirectSettings"
        function ready() {
            tryVerify(function() { return pointer.snapshot !== null && !pointer.requestRunning && !pointer.busy }, 5000)
            compare(pointer.error, "")
        }
        function control(name) {
            var item = findChild(panel, name)
            verify(item !== null, name + " missing")
            // Finish layout before sending pointer events to a newly visible style.
            verify(waitForPolish(root), "profile layout did not settle")
            verify(item.enabled, name + " disabled")
            return item
        }
        function click(name) { mouseClick(control(name)); ready() }
        function drag(name, value) {
            var slider = control(name)
            var thumb = slider.handle.width / 2
            var startX = slider.leftPadding + thumb + slider.position * (slider.availableWidth - thumb * 2)
            var endX = slider.leftPadding + thumb + ((value - slider.from) / (slider.to - slider.from)) * (slider.availableWidth - thumb * 2)
            mousePress(slider, startX, slider.height / 2)
            verify(slider.pressed, name + " did not receive the press")
            mouseMove(slider, endX, slider.height / 2, 40)
            verify(!pointer.busy, "drag must not reload/disable its own slider")
            mouseRelease(slider, endX, slider.height / 2)
            verify(pointer.busy, "release must apply without another button")
            ready()
        }
        function test_controls() {
            try { exerciseControls() }
            catch (error) {
                console.error("PANEL FAIL: " + String(error.stack || error))
                throw error
            }
        }
        function exerciseControls() {
            ready()
            compare(pointer.profile, "win")
            compare(pointer.shortLabel, "WIN")
            pointer.refresh()
            click("labelLetter")
            compare(pointer.shortLabel, "W")
            verify(!pointer.trial, "label change started a pointer trial")
            // Input accepted during polling, with no transient loss of draft values.
            pointer.refresh()
            click("macTab")
            compare(pointer.profile, "mac")
            compare(pointer.shortLabel, "M")
            var labelTrialToken = pointer.snapshot.preview.token
            click("labelCode")
            compare(pointer.shortLabel, "MAC")
            compare(pointer.snapshot.preview.token, labelTrialToken)
            click("labelLetter")
            compare(pointer.shortLabel, "M")
            verify(pointer.trial)
            verify(!panel.locked, "an active trial must allow tuning")
            var old = pointer.snapshot.preview.token
            pointer.refresh()
            drag("macSpeed", 10)
            compare(pointer.snapshot.mac.tracking, 10)
            compare(panel.draftTracking, 10)
            verify(pointer.snapshot.preview.token !== old)
            click("macNatural")
            compare(pointer.snapshot.mac.natural_scroll, false)
            // Real keyboard input must apply with no second button.
            var mac = control("macSpeed")
            mac.forceActiveFocus()
            keyClick(Qt.Key_Left)
            ready()
            compare(pointer.snapshot.mac.tracking, 9)
            click("winTab")
            drag("speedSlider", 16)
            compare(pointer.snapshot.windows.speed, 16)
            click("windowsPrecision")
            compare(pointer.snapshot.windows.epp, false)
            click("restoreDefaults")
            compare(pointer.snapshot.windows.speed, 10)
            compare(pointer.snapshot.windows.epp, true)
            compare(pointer.snapshot.mac.tracking, 9)
            click("macTab")
            compare(pointer.snapshot.mac.tracking, 9)
            compare(panel.draftTracking, 9)
            click("restoreDefaults")
            compare(pointer.snapshot.mac.tracking, 4)
            compare(pointer.snapshot.mac.natural_scroll, true)
            compare(pointer.snapshot.windows.speed, 10)
            click("omarchyTab")
            compare(pointer.profile, "omarchy")
            compare(pointer.shortLabel, "O")
            click("labelCode")
            compare(pointer.shortLabel, "OMA")
            click("labelLetter")
            drag("nativeSpeed", 0.4)
            compare(pointer.snapshot.omarchy.sensitivity, 0.4)
            drag("scrollSpeed", 1.5)
            compare(pointer.snapshot.omarchy.scroll_factor, 1.5)
            pointer.refresh()
            click("restoreDefaults")
            compare(pointer.snapshot.omarchy.sensitivity, 0)
            compare(pointer.snapshot.omarchy.scroll_factor, 1)
            compare(pointer.snapshot.omarchy.accel_profile, "")
            compare(pointer.snapshot.mac.tracking, 4)
            pointer.revert(); ready()
            compare(pointer.profile, "win")
            compare(pointer.snapshot.windows.speed, 10)
            compare(pointer.snapshot.mac.tracking, 7)
            compare(pointer.shortLabel, "W")
            verify(!pointer.trial)
            // Edits also work directly in a saved profile, without reselecting it.
            drag("speedSlider", 12)
            pointer.confirm(); ready()
            compare(pointer.snapshot.confirmed.windows.speed, 12)
            compare(pointer.shortLabel, "W")
            click("labelCode")
            compare(pointer.shortLabel, "WIN")
            verify(!pointer.trial)
            console.log("PANEL PASS")
        }
    }
}
'''

FAKE = r'''#!/usr/bin/env python3
from copy import deepcopy
import json
from pathlib import Path
import sys
import time
path = Path(__file__).with_suffix('.json')
data = json.loads(path.read_text())
args = sys.argv[1:]
time.sleep(0.10)
data['commands'].append(args)
data['serial'] += 1
if args[0] == 'preview':
    options = args[2:]
    reset = '--defaults' in options
    if reset: options.remove('--defaults')
    flags = dict(zip(options[::2], options[1::2]))
    if data['preview']:
        assert flags.pop('--replace-token') == data['preview']['token']
    else:
        assert '--replace-token' not in flags
        data['previous'] = {k: deepcopy(data[k]) for k in ('profile', 'windows', 'mac', 'omarchy')}
    data['profile'] = args[1]
    section = 'windows' if args[1] == 'win' else args[1]
    if reset:
        assert not flags
        defaults = {
            'windows': {'speed': 10, 'epp': True},
            'mac': {'model': 'sequoia-15.3.2', 'tracking': 4, 'natural_scroll': True, 'left_handed': False},
            'omarchy': {'accel_profile': '', 'sensitivity': 0, 'scroll_factor': 1, 'natural_scroll': False, 'left_handed': False},
        }
        data[section] = defaults[section]
    settings = data[section]
    for key, value in flags.items():
        key = key[2:].replace('-', '_')
        if key == 'accel': key, value = 'accel_profile', '' if value == 'system' else value
        elif key in ('speed', 'tracking'): value = int(value)
        elif key in ('sensitivity', 'scroll_factor'): value = float(value)
        else: value = value == 'on'
        settings[key] = value
    data['preview'] = {'token': str(data['serial']), 'seconds': 15}
elif args[0] == 'bar-label':
    assert args[1] in ('letter', 'code')
    data['ui'] = {'bar_label': args[1]}
elif args[0] in ('confirm', 'revert'):
    assert args[1] == data['preview']['token']
    data['preview'] = None
    if args[0] == 'revert': data.update(data['previous'])
    else: data['confirmed'] = {k: deepcopy(data[k]) for k in ('profile', 'windows', 'mac', 'omarchy')}
path.write_text(json.dumps(data))
print(json.dumps(data))
'''


def main():
    source = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='mouse-style-panel-') as temp:
        root = Path(temp)
        for name in ('Panel.qml', 'PointerState.qml', 'ProfileHeader.qml', 'FlowIcon.qml'):
            shutil.copyfile(source / name, root / name)
        # PanelWindow requires a real compositor; replace only its surface shell.
        # All project handlers, Controls.Slider and Omarchy Button remain real.
        qs = root / 'qs'
        qs.mkdir()
        for entry in Path('/usr/share/omarchy/shell').iterdir():
            if entry.name != 'Ui':
                (qs / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
        ui = qs / 'Ui'
        ui.mkdir()
        for entry in Path('/usr/share/omarchy/shell/Ui').iterdir():
            if entry.name != 'KeyboardPanel.qml':
                (ui / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
        (ui / 'KeyboardPanel.qml').write_text("""import QtQuick
Item {
    required property Item anchorItem
    required property QtObject bar
    property bool open: false
    property Item focusTarget
    property int contentWidth: 370
    property int contentHeight: 800
    width: contentWidth; height: contentHeight
    function fittedContentWidth(value) { return value }
    function fittedContentHeight(value) { return value }
    function close() { open = false }
}
""")
        (root / 'shell.qml').write_text(QML)
        command = root / 'mouse-style'
        command.write_text(FAKE)
        command.chmod(0o755)
        (root / 'mouse-style.json').write_text(json.dumps({
            'ok': True, 'serial': 0, 'commands': [], 'profile': 'win',
            'preview': None, 'windows': {'speed': 10, 'epp': True},
            'available': ['win', 'mac', 'omarchy'],
            'mac': {'model': 'sequoia-15.3.2', 'tracking': 7, 'natural_scroll': True, 'left_handed': False},
            'omarchy': {'accel_profile': '', 'sensitivity': 0, 'scroll_factor': 1,
                        'natural_scroll': False, 'left_handed': False},
        }))
        env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH'],
                   QML_IMPORT_PATH=str(root), QT_QPA_PLATFORM='offscreen')
        result = subprocess.run(['quickshell', '--no-color', '-p', str(root)],
                                env=env, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        if result.returncode or 'PANEL PASS' not in output or 'FAIL!' in output:
            print(f'Quickshell exit code: {result.returncode}\n{output}')
            return 1
        data = json.loads((root / 'mouse-style.json').read_text())
        edits = [cmd for cmd in data['commands'] if cmd[0] == 'preview']
        assert len(edits) == 15, edits
        assert [cmd[1] for cmd in edits if "--defaults" in cmd] == ["win", "mac", "omarchy"], edits
        assert all('--replace-token' in cmd for cmd in edits[1:-1]), edits
        print('PASS: actual Mac/Win/Omarchy controls apply on release/click, tune during trials, retain values across polling/style switches, profile defaults reset independently, Letter/Code switches persist across styles/trials, and Keep/Revert work.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
