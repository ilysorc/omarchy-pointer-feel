pragma ComponentBehavior: Bound
import QtQuick
import qs.Commons
import qs.Ui as Ui

Ui.PanelHero {
    id: root
    property string profile: "unknown"
    property bool trial: false
    readonly property bool knownProfile: profile === "win" || profile === "mac" || profile === "omarchy"
    readonly property string profileName: profile === "win" ? "Windows" : profile === "mac" ? "Mac" : profile === "omarchy" ? "Omarchy" : "Unverified"

    title: "Pointer Feel"
    meta: "Active: " + profileName + (trial ? " · trial" : "")

    iconComponent: Component {
        Item {
            width: root.iconSize
            height: root.iconSize

            Ui.OpticalGlyph {
                anchors.fill: parent
                visible: root.knownProfile
                text: root.profile === "win" ? "\uf17a" : root.profile === "mac" ? "\uf179" : root.profile === "omarchy" ? "\ue900" : ""
                fontFamily: root.profile === "omarchy" ? "omarchy" : "JetBrainsMono Nerd Font"
                fontSize: root.iconSize
                color: Color.accent
            }
            FlowIcon {
                anchors.fill: parent
                visible: !root.knownProfile
                color: Color.accent
            }
        }
    }
}
