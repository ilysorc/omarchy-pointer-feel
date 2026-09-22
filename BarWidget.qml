pragma ComponentBehavior: Bound
import QtQuick
import qs.Ui as Ui

Ui.Panel {
    id: root
    moduleName: "ilysorc.mouse-style"
    ipcTarget: moduleName
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight

    SetupState {
        id: setup
        onCheckedChanged: if (checked && !ready) root.open()
        onReadyChanged: if (checked && !ready) root.open()
    }
    PointerState {
        id: state
        operational: setup.ready && !setup.running
        panelOpen: root.opened
    }
    FlowButton {
        id: button
        anchors.fill: parent
        bar: root.bar
        text: setup.ready ? state.shortLabel + (state.trial ? " ·" : "") : "Setup"
        active: state.trial
        tooltipText: "Mouse Style · " + (state.profile === "win" ? "Windows" : state.profile === "mac" ? "Mac (experimental)" : state.profile === "omarchy" ? "Omarchy" : "Reading status")
        onPressed: function(mouseButton) {
            if (mouseButton === Qt.LeftButton) root.toggle()
            else if (mouseButton === Qt.RightButton) state.refresh()
        }
    }
    Panel {
        anchorItem: button
        owner: root
        bar: root.bar
        open: root.opened && setup.ready && !setup.running
        pointerState: state
    }
    SetupPanel {
        anchorItem: button
        owner: root
        bar: root.bar
        open: root.opened && (!setup.ready || setup.running)
        setupState: setup
    }
}
