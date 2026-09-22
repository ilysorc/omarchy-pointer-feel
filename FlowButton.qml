pragma ComponentBehavior: Bound
import QtQuick
import qs.Commons
import qs.Ui as Ui

Ui.WidgetButton {
    id: root
    // Keep Omarchy's click/hover/tooltip behavior, with our own vector + label.
    labelVisible: false
    property color contentColor: active && useActiveColor ? activeColor : foreground
    implicitWidth: fixedWidth > 0 ? fixedWidth : (vertical ? barSize : content.implicitWidth + scaledHorizontalMargin * 2)
    implicitHeight: fixedHeight > 0 ? fixedHeight : (vertical ? content.implicitHeight + scaledVerticalPadding * 2 : barSize)

    Behavior on contentColor {
        enabled: !root.bar || root.bar.foregroundAnimationEnabled
        ColorAnimation { duration: 160 }
    }

    Row {
        id: content
        anchors.centerIn: parent
        spacing: Style.spaceReal(5)
        rotation: root.textRotation
        FlowIcon {
            objectName: "flowIcon"
            anchors.verticalCenter: parent.verticalCenter
            width: Style.barToken("icon-canvas", 16)
            height: width
            color: root.contentColor
        }
        Text {
            objectName: "profileLabel"
            anchors.verticalCenter: parent.verticalCenter
            textFormat: Text.PlainText
            text: root.text
            color: root.contentColor
            font.family: root.fontFamily
            font.pixelSize: root.fontSize
            renderType: Text.NativeRendering
        }
    }
}
