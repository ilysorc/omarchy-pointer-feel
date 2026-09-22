pragma ComponentBehavior: Bound
import QtQuick
import Quickshell.Io

Item {
    id: root
    property bool checked: false
    property bool ready: false
    property bool running: false
    property string message: "Checking required components…"
    property bool launchPending: false
    readonly property string script: Qt.resolvedUrl("install.sh").toString().replace(/^file:\/\//, "")

    function refresh() { if (!check.running) check.running = true }
    function install() {
        if (running || launchPending) return
        launchPending = true
        message = "Starting setup…"
        launch.running = true
    }
    Process {
        id: check
        command: ["bash", decodeURIComponent(root.script), "--status"]
        stdout: StdioCollector { id: output; waitForEnd: true }
        onExited: function(code, exitStatus) {
            try {
                var result = JSON.parse(output.text)
                root.ready = result.ready === true
                root.running = result.running === true
                root.message = result.message || "Setup needs attention."
            } catch (error) {
                root.ready = false
                root.running = false
                root.message = "Could not check installation. Run install.sh from the plugin folder."
            }
            root.checked = true
        }
    }
    Process {
        id: launch
        // Detaches the long installation from QML and the pointer command timeout.
        command: ["bash", decodeURIComponent(root.script), "--background", "--yes"]
        stderr: StdioCollector { id: errors; waitForEnd: true }
        onExited: function(code, exitStatus) {
            root.launchPending = false
            if (code !== 0 || exitStatus !== 0) root.message = errors.text || "Setup could not start."
            root.refresh()
        }
    }
    Timer {
        interval: root.running || root.launchPending ? 1000 : 10000
        running: true
        repeat: true
        onTriggered: root.refresh()
    }
    Component.onCompleted: refresh()
}
