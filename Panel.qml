pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls as Controls
import qs.Commons
import qs.Ui as Ui

Ui.KeyboardPanel {
    id: root
    required property PointerState pointerState
    property int draftSpeed: 10
    property bool draftEpp: true
    property bool edited: false
    property string draftProfile: ""
    property string draftAccel: ""
    property real draftSensitivity: 0
    property real draftScroll: 1
    property bool draftNatural: false
    property bool draftLeft: false
    property int draftTracking: 4
    property bool draftMacNatural: true
    property bool draftMacLeft: false
    readonly property bool showingMac: pointerState.profile === "mac"
    readonly property bool macAvailable: pointerState.snapshot !== null && pointerState.snapshot.available.indexOf("mac") >= 0
    readonly property bool macLocked: locked || !macAvailable
    readonly property bool showingWindows: pointerState.profile === "win"
    readonly property bool showingOmarchy: pointerState.profile === "omarchy"
    readonly property var fontStyle: Style.font
    readonly property bool locked: pointerState.busy || pointerState.snapshot === null
    readonly property bool windowsAvailable: pointerState.snapshot !== null && pointerState.snapshot.available.indexOf("win") >= 0
    readonly property bool windowsLocked: locked || !windowsAvailable
    contentWidth: fittedContentWidth(Style.space(370))
    contentHeight: fittedContentHeight(content.implicitHeight)
    focusTarget: keys

    function syncDraft() {
        if (pointerState.busy || !pointerState.snapshot || speedSlider.pressed || nativeSpeed.pressed || scrollSpeed.pressed || macSpeed.pressed) return
        if (draftProfile !== pointerState.profile) {
            edited = false
            draftProfile = pointerState.profile
        }
        if (edited) return
        draftSpeed = pointerState.snapshot.windows.speed
        draftEpp = pointerState.snapshot.windows.epp
        var native = pointerState.snapshot.omarchy
        draftAccel = native.accel_profile
        draftSensitivity = native.sensitivity
        draftScroll = native.scroll_factor
        draftNatural = native.natural_scroll
        draftLeft = native.left_handed
        draftTracking = pointerState.snapshot.mac.tracking
        draftMacNatural = pointerState.snapshot.mac.natural_scroll
        draftMacLeft = pointerState.snapshot.mac.left_handed
    }
    function previewWin() {
        if (windowsLocked) return
        edited = false
        pointerState.preview("win", draftSpeed, draftEpp)
    }
    function nativeDraft() {
        return {accel_profile: draftAccel, sensitivity: draftSensitivity,
                scroll_factor: draftScroll, natural_scroll: draftNatural, left_handed: draftLeft}
    }
    function previewOmarchy() {
        if (locked) return
        edited = false
        pointerState.previewOmarchy(nativeDraft())
    }
    function previewMac() {
        if (macLocked) return
        edited = false
        pointerState.previewMac(draftTracking, draftMacNatural, draftMacLeft)
    }
    function selectProfile(profile) {
        if (locked || profile === pointerState.profile) return
        resetDraft()
        if (profile === "win") previewWin()
        else if (profile === "mac") previewMac()
        else previewOmarchy()
    }
    function resetDraft() { edited = false; syncDraft() }
    onOpenChanged: {
        if (open) { syncDraft(); pointerState.refresh() }
    }
    property Connections snapshotConnection: Connections {
        target: root.pointerState
        function onSnapshotChanged() { root.syncDraft() }
        function onBusyChanged() { if (!root.pointerState.busy) root.syncDraft() }
    }

    FocusScope {
        id: keys
        anchors.fill: parent
        focus: true
        Keys.onEscapePressed: root.close()
        Keys.onReturnPressed: {
            if (root.pointerState.trial && !root.pointerState.busy) root.pointerState.confirm()
        }

        Column {
            id: content
            width: parent.width
            spacing: Style.space(10)

            ProfileHeader {
                objectName: "profileHeader"
                width: parent.width
                profile: root.pointerState.profile
                trial: root.pointerState.trial
            }
            Flow {
                width: parent.width
                spacing: Style.space(6)
                Ui.Button {
                    objectName: "omarchyTab"
                    text: "Omarchy"; bordered: true; focusable: true
                    active: root.pointerState.profile === "omarchy"
                    enabled: !root.locked
                    onClicked: root.selectProfile("omarchy")
                }
                Ui.Button {
                    objectName: "macTab"
                    text: "Mac"; bordered: true; focusable: true
                    active: root.showingMac
                    enabled: !root.macLocked
                    onClicked: root.selectProfile("mac")
                }
                Ui.Button {
                    objectName: "winTab"
                    text: "Win"; bordered: true; focusable: true
                    active: root.pointerState.profile === "win"
                    enabled: !root.windowsLocked
                    onClicked: root.selectProfile("win")
                }
            }
            Label {
                text: root.pointerState.profile === "omarchy"
                    ? "Native Omarchy behavior. Adjust acceleration, speed, and scrolling below."
                    : root.showingMac ? "macOS Sequoia 15.3.2 measured reference. Experimental."
                    : "Windows pointer behavior. Adjust speed and precision below."
                opacity: 0.8
            }
            Label {
                text: "Settings apply immediately. Release a slider to apply."
                opacity: 0.7; font.pixelSize: root.fontStyle.caption
            }
            Ui.PanelSeparator {}
            Column {
                objectName: "windowsSettings"
                visible: root.showingWindows
                width: parent.width
                spacing: Style.space(10)
            Label { text: "WINDOWS SETTINGS"; opacity: 0.65; font.pixelSize: root.fontStyle.caption }
            Label { text: "Pointer speed  ·  " + root.draftSpeed + " / 20" }
            Controls.Slider {
                id: speedSlider
                objectName: "speedSlider"
                width: parent.width
                from: 1; to: 20; stepSize: 1
                snapMode: Controls.Slider.SnapAlways
                value: root.draftSpeed
                enabled: !root.windowsLocked
                Accessible.name: "Windows pointer speed"
                onMoved: { root.draftSpeed = Math.round(value); root.edited = true; if (!pressed) root.previewWin() }
                onPressedChanged: { if (!pressed && root.edited) root.previewWin() }
                background: Rectangle {
                    x: speedSlider.leftPadding
                    y: speedSlider.topPadding + speedSlider.availableHeight / 2 - height / 2
                    width: speedSlider.availableWidth
                    height: Style.space(3)
                    color: Color.foreground; opacity: 0.3
                    radius: height / 2
                    Rectangle { width: speedSlider.visualPosition * parent.width; height: parent.height; color: Color.accent; radius: height / 2 }
                }
                handle: Rectangle {
                    x: speedSlider.leftPadding + speedSlider.visualPosition * (speedSlider.availableWidth - width)
                    y: speedSlider.topPadding + speedSlider.availableHeight / 2 - height / 2
                    implicitWidth: Style.space(14); implicitHeight: Style.space(14)
                    radius: width / 2; color: Color.accent
                }
            }
            Ui.Button {
                width: parent.width
                objectName: "windowsPrecision"
                text: "Enhance pointer precision: " + (root.draftEpp ? "On" : "Off")
                active: root.draftEpp
                bordered: true; focusable: true
                enabled: !root.windowsLocked
                onClicked: { root.draftEpp = !root.draftEpp; root.previewWin() }
            }
            }
            Column {
                objectName: "macSettings"
                visible: root.showingMac
                width: parent.width
                spacing: Style.space(10)
                Label { text: "MAC SETTINGS"; opacity: 0.65; font.pixelSize: root.fontStyle.caption }
                Label { text: "Tracking speed  ·  " + root.draftTracking + " / 10" }
                NativeSlider {
                    id: macSpeed
                objectName: "macSpeed"
                    from: 1; to: 10; stepSize: 1
                    value: root.draftTracking
                    enabled: !root.macLocked
                    Accessible.name: "Mac tracking speed"
                    onMoved: { root.draftTracking = Math.round(value); root.edited = true; if (!pressed) root.previewMac() }
                onPressedChanged: { if (!pressed && root.edited) root.previewMac() }
                }
                Ui.Button {
                    objectName: "macNatural"
                    text: "Natural scrolling: " + (root.draftMacNatural ? "On" : "Off")
                    width: parent.width; bordered: true; focusable: true
                    active: root.draftMacNatural; enabled: !root.macLocked
                    onClicked: { root.draftMacNatural = !root.draftMacNatural; root.previewMac() }
                }
                Ui.Button {
                    text: "Primary button: " + (root.draftMacLeft ? "Right" : "Left")
                    width: parent.width; bordered: true; focusable: true
                    active: root.draftMacLeft; enabled: !root.macLocked
                    onClicked: { root.draftMacLeft = !root.draftMacLeft; root.previewMac() }
                }
                Label {
                    text: "Measured at 400 DPI / 125 Hz. Other devices may feel different; exact macOS parity is not verified."
                    opacity: 0.7; font.pixelSize: root.fontStyle.caption
                }
                Label {
                    text: "Pointer acceleration is included in this reference. Mac scroll momentum is not implemented."
                    opacity: 0.7; font.pixelSize: root.fontStyle.caption
                }
            }
            Column {
                objectName: "omarchySettings"
                visible: root.showingOmarchy
                width: parent.width
                spacing: Style.space(10)
                Label { text: "OMARCHY SETTINGS"; opacity: 0.65; font.pixelSize: root.fontStyle.caption }
                Label { text: "Acceleration" }
                Flow {
                    width: parent.width
                    spacing: Style.space(6)
                    Ui.Button {
                        text: "System"; bordered: true; focusable: true
                        active: root.draftAccel === ""; enabled: !root.locked
                        onClicked: { root.draftAccel = ""; root.previewOmarchy() }
                    }
                    Ui.Button {
                        text: "Adaptive"; bordered: true; focusable: true
                        active: root.draftAccel === "adaptive"; enabled: !root.locked
                        onClicked: { root.draftAccel = "adaptive"; root.previewOmarchy() }
                    }
                    Ui.Button {
                        text: "Flat"; bordered: true; focusable: true
                        active: root.draftAccel === "flat"; enabled: !root.locked
                        onClicked: { root.draftAccel = "flat"; root.previewOmarchy() }
                    }
                }
                Label {
                    text: root.draftAccel === "flat" ? "Constant gain, without speed-based acceleration."
                        : root.draftAccel === "adaptive" ? "Faster movement increases pointer speed."
                        : "Use the device's default acceleration profile."
                    opacity: 0.7; font.pixelSize: root.fontStyle.caption
                }
                Label { text: "Sensitivity  ·  " + root.draftSensitivity.toFixed(2) }
                NativeSlider {
                    id: nativeSpeed
                    objectName: "nativeSpeed"
                    from: -1; to: 1; stepSize: 0.05
                    value: root.draftSensitivity
                    Accessible.name: "Omarchy sensitivity"
                    onMoved: { root.draftSensitivity = Math.round(value * 100) / 100; root.edited = true; if (!pressed) root.previewOmarchy() }
                onPressedChanged: { if (!pressed && root.edited) root.previewOmarchy() }
                }
                Label { text: "Scroll speed  ·  " + root.draftScroll.toFixed(1) + "×" }
                NativeSlider {
                    id: scrollSpeed
                objectName: "scrollSpeed"
                    from: 0.1; to: 5; stepSize: 0.1
                    value: root.draftScroll
                    Accessible.name: "Omarchy scroll speed"
                    onMoved: { root.draftScroll = Math.round(value * 10) / 10; root.edited = true; if (!pressed) root.previewOmarchy() }
                onPressedChanged: { if (!pressed && root.edited) root.previewOmarchy() }
                }
                Ui.Button {
                    width: parent.width; bordered: true; focusable: true
                    text: "Natural scrolling: " + (root.draftNatural ? "On" : "Off")
                    active: root.draftNatural; enabled: !root.locked
                    onClicked: { root.draftNatural = !root.draftNatural; root.previewOmarchy() }
                }
                Ui.Button {
                    width: parent.width; bordered: true; focusable: true
                    text: "Left-handed buttons: " + (root.draftLeft ? "On" : "Off")
                    active: root.draftLeft; enabled: !root.locked
                    onClicked: { root.draftLeft = !root.draftLeft; root.previewOmarchy() }
                }
                Label {
                    text: "Shared input settings. Device-specific overrides take precedence."
                    opacity: 0.65; font.pixelSize: root.fontStyle.caption
                }
            }
            Ui.Button {
                objectName: "restoreDefaults"
                text: "Restore defaults"; bordered: true; focusable: true
                enabled: !root.locked && (root.showingOmarchy
                    || (root.showingMac && root.macAvailable)
                    || (root.showingWindows && root.windowsAvailable))
                onClicked: {
                    root.edited = false
                    root.pointerState.restoreDefaults(root.pointerState.profile)
                }
            }
            Label { text: "Hardware DPI stays unchanged."; opacity: 0.65; font.pixelSize: root.fontStyle.caption }
            Label {
                visible: root.pointerState.snapshot !== null && !root.windowsAvailable
                text: "Windows mode requires a compatible windows-pointer-linux backend."
                color: Color.accent
            }
            Ui.PanelSeparator {}
            Label { text: "Bar label"; opacity: 0.65; font.pixelSize: root.fontStyle.caption }
            Row {
                spacing: Style.space(6)
                Ui.Button {
                    objectName: "labelLetter"
                    text: "Letter"; bordered: true; focusable: true
                    active: root.pointerState.labelStyle === "letter"
                    enabled: !root.locked
                    onClicked: if (!active) root.pointerState.setBarLabel("letter")
                }
                Ui.Button {
                    objectName: "labelCode"
                    text: "Code"; bordered: true; focusable: true
                    active: root.pointerState.labelStyle === "code"
                    enabled: !root.locked
                    onClicked: if (!active) root.pointerState.setBarLabel("code")
                }
                Ui.Button {
                    objectName: "labelHidden"
                    text: "Hidden"; bordered: true; focusable: true
                    active: root.pointerState.labelStyle === "hidden"
                    enabled: !root.locked
                    onClicked: if (!active) root.pointerState.setBarLabel("hidden")
                }
            }
            Label { text: "Saved immediately."; opacity: 0.65; font.pixelSize: root.fontStyle.caption }
            Ui.PanelSeparator {}
            Label {
                visible: root.pointerState.trial
                text: root.pointerState.trial ? "Reverting in " + root.pointerState.snapshot.preview.seconds + " s" : ""
                color: Color.accent; font.bold: true
            }
            Row {
                visible: root.pointerState.trial
                spacing: Style.space(8)
                Ui.Button {
                    text: "Keep"; bordered: true; focusable: true
                    enabled: !root.pointerState.busy
                    onClicked: root.pointerState.confirm()
                }
                Ui.Button {
                    text: "Revert"; bordered: true; focusable: true
                    enabled: !root.pointerState.busy
                    onClicked: root.pointerState.revert()
                }
            }
            Label {
                visible: root.pointerState.error !== ""
                text: root.pointerState.error
                color: Color.accent
            }
            Label {
                text: root.pointerState.snapshot && root.pointerState.snapshot.message
                    ? root.pointerState.snapshot.message
                    : "Settings apply immediately. Release a slider to apply; Keep saves your changes."
                opacity: 0.8
            }
        }
    }
    component NativeSlider: Controls.Slider {
        id: control
        width: parent.width
        snapMode: Controls.Slider.SnapAlways
        enabled: !root.locked
        background: Rectangle {
            x: control.leftPadding
            y: control.topPadding + control.availableHeight / 2 - height / 2
            width: control.availableWidth
            height: Style.space(3)
            color: Color.foreground; opacity: 0.3
            radius: height / 2
            Rectangle { width: control.visualPosition * parent.width; height: parent.height; color: Color.accent; radius: height / 2 }
        }
        handle: Rectangle {
            x: control.leftPadding + control.visualPosition * (control.availableWidth - width)
            y: control.topPadding + control.availableHeight / 2 - height / 2
            implicitWidth: Style.space(14); implicitHeight: Style.space(14)
            radius: width / 2; color: Color.accent
        }
    }
    component Label: Text {
        width: parent.width
        textFormat: Text.PlainText
        wrapMode: Text.Wrap
        color: Color.foreground
        font.family: root.fontStyle.family
        font.pixelSize: root.fontStyle.bodySmall
    }
}
