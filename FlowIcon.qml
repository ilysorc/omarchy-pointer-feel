pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Shapes

Item {
    id: root
    required property color color
    implicitWidth: 16
    implicitHeight: 16

    // Original Flow mark: a pointer and its motion curve on a 16-unit grid.
    Shape {
        anchors.centerIn: parent
        width: 16
        height: 16
        scale: Math.min(root.width, root.height) / 16
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeWidth: -1
            fillColor: root.color
            PathSvg { path: "M2.5 1.75 11.25 7.75 7.7 8.45 6.05 12.15Z" }
        }
        ShapePath {
            fillColor: "transparent"
            strokeColor: root.color
            strokeWidth: 1.5
            capStyle: ShapePath.RoundCap
            PathSvg { path: "M9 13.5c3.1 0 5-1.75 5-4.5" }
        }
    }
}
