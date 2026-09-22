pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Shapes

Item {
    id: root
    required property color color
    implicitWidth: 16
    implicitHeight: 16

    // Filled click cursor with three rays, drawn on the approved 16-unit grid.
    Shape {
        anchors.centerIn: parent
        width: 16
        height: 16
        scale: Math.min(root.width, root.height) / 16
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeWidth: 0.6
            strokeColor: root.color
            fillColor: root.color
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: "M5 5 L14 7.7 L10.5 9.2 L13.4 12.1 L12.1 13.4 L9.2 10.5 L7.7 14 Z" }
        }
        ShapePath {
            fillColor: "transparent"
            strokeColor: root.color
            strokeWidth: 1.5
            capStyle: ShapePath.RoundCap
            PathSvg { path: "M1.6 1.6L3 3M5.4 1v1.8M1 5.4h1.8" }
        }
    }
}
