pragma ComponentBehavior: Bound
import QtQuick
import qs.Commons
import qs.Ui as Ui

Ui.KeyboardPanel {
    id: root
    required property SetupState setupState
    readonly property var fontStyle: Style.font
    contentWidth: fittedContentWidth(Style.space(370))
    contentHeight: fittedContentHeight(content.implicitHeight)
    focusTarget: keys
    FocusScope {
        id: keys
        anchors.fill: parent
        focus: true
        Keys.onEscapePressed: root.close()
        Column {
            id: content
            width: parent.width
            spacing: Style.space(12)
            Text {
                text: "Set up Mouse Style"
                color: Color.foreground
                font.family: root.fontStyle.family
                font.pixelSize: root.fontStyle.subtitle
                font.bold: true
            }
            Text {
                width: parent.width
                text: "Install the required components for Omarchy, Mac and Windows pointer styles. Your pointer preferences will be preserved."
                wrapMode: Text.WordWrap
                color: Color.foreground
                font.family: root.fontStyle.family
                font.pixelSize: root.fontStyle.body
            }
            Text {
                width: parent.width
                text: root.setupState.message
                wrapMode: Text.WrapAnywhere
                color: Color.accent
                font.family: root.fontStyle.family
                font.pixelSize: root.fontStyle.body
            }
            Ui.Button {
                objectName: "installComponents"
                text: root.setupState.running || root.setupState.launchPending ? "Installing…" : "Install / Repair"
                bordered: true
                focusable: true
                enabled: root.setupState.checked && !root.setupState.running && !root.setupState.launchPending
                onClicked: root.setupState.install()
            }
            Text {
                width: parent.width
                text: "Setup installs missing system packages and adds the startup integration. Omarchy may ask for your password. Building can take a few minutes; you can close this panel."
                wrapMode: Text.WordWrap
                opacity: 0.7
                color: Color.foreground
                font.family: root.fontStyle.family
                font.pixelSize: root.fontStyle.caption
            }
        }
    }
}
