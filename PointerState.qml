pragma ComponentBehavior: Bound
import QtQuick
import Quickshell.Io

Item {
    id: root
    property var snapshot: null
    property bool operational: true
    property bool requestRunning: false
    property var queuedAction: null
    // Background reads must not disable controls or reset hover/focus.
    readonly property bool busy: queuedAction !== null || (requestRunning && commandKind !== "status")
    property bool panelOpen: false
    property string actionError: ""
    property string readError: ""
    property string commandKind: "status"
    readonly property string error: actionError || readError
    readonly property bool trial: snapshot !== null && snapshot.preview !== null
    readonly property string profile: snapshot ? snapshot.profile : "unknown"
    readonly property string labelStyle: snapshot && snapshot.ui ? snapshot.ui.bar_label : "code"
    readonly property string codeLabel: profile === "win" ? "WIN" : profile === "mac" ? "MAC" : profile === "omarchy" ? "OMA" : "?"
    readonly property string shortLabel: labelStyle === "hidden" ? "" : labelStyle === "letter" ? codeLabel.charAt(0) : codeLabel
    readonly property string barLabel: shortLabel ? shortLabel + (trial ? " ·" : "") : ""

    function run(args) {
        if (!operational) return
        if (busy) return
        if (requestRunning || process.running) {
            // Serialize writes behind an in-flight read without losing a click.
            if (args[0] !== "status") queuedAction = args
            return
        }
        start(args)
    }
    function start(args) {
        commandKind = args[0]
        if (commandKind !== "status") actionError = ""
        requestRunning = true
        process.command = ["timeout", "--kill-after=2s", "25s", "mouse-style"].concat(args)
        process.running = true
        watchdog.restart()
    }
    function refresh() { run(["status"]) }
    function applySettings(args) {
        if (trial) args = args.concat(["--replace-token", snapshot.preview.token])
        run(args)
    }
    function preview(profile, speed, epp) {
        var args = ["preview", profile]
        if (profile === "win") args = args.concat(["--speed", String(speed), "--epp", epp ? "on" : "off"])
        applySettings(args)
    }
    function previewOmarchy(settings) {
        applySettings(["preview", "omarchy", "--accel", settings.accel_profile || "system",
             "--sensitivity", String(settings.sensitivity), "--scroll-factor", String(settings.scroll_factor),
             "--natural-scroll", settings.natural_scroll ? "on" : "off",
             "--left-handed", settings.left_handed ? "on" : "off"])
    }
    function previewMac(tracking, natural, left) {
        applySettings(["preview", "mac", "--tracking", String(tracking),
             "--natural-scroll", natural ? "on" : "off", "--left-handed", left ? "on" : "off"])
    }
    function restoreDefaults(profile) { applySettings(["preview", profile, "--defaults"]) }
    function setBarLabel(mode) { run(["bar-label", mode]) }
    function confirm() { if (trial) run(["confirm", snapshot.preview.token]) }
    function revert() { if (trial) run(["revert", snapshot.preview.token]) }

    Process {
        id: process
        stdout: StdioCollector { id: output; waitForEnd: true }
        stderr: StdioCollector { id: errors; waitForEnd: true }
        onExited: function(code, exitStatus) {
            var text = output.text
            var detail = errors.text
            Qt.callLater(function() {
                if (!root.requestRunning) return
                watchdog.stop()
                try {
                    var result = JSON.parse(text)
                    if (code !== 0 || exitStatus !== 0 || result.ok !== true)
                        throw new Error(result.error || detail || "The command did not complete.")
                    root.snapshot = result
                    root.readError = ""
                } catch (failure) {
                    var message = String(failure.message || failure)
                    if (root.commandKind === "status") root.readError = message
                    else root.actionError = message
                    // Never leave an old check mark visible after an unknown result.
                    root.snapshot = null
                }
                if (root.queuedAction !== null && root.snapshot !== null) {
                    root.start(root.queuedAction)
                    root.queuedAction = null
                } else {
                    root.queuedAction = null
                    root.requestRunning = false
                }
            })
        }
    }
    Timer {
        id: watchdog
        interval: 28000
        onTriggered: {
            if (process.running) process.signal(9)
            root.queuedAction = null
            root.requestRunning = false
            root.snapshot = null
            root.readError = "The operation did not respond. Current state will be checked again."
        }
    }
    Timer {
        interval: root.trial ? 750 : root.panelOpen ? 2500 : 6000
        repeat: true
        running: root.operational
        onTriggered: root.refresh()
    }
    Component.onCompleted: refresh()
    onOperationalChanged: if (operational) refresh()
}
