import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    property var tokens: ({})

    // Когда windowMode меняется — применяем режим окна
    Connections {
        target: bridge
        function onWindowModeChanged() {
            var w = bridge.windowMode
            if (w === "fullscreen") {
                // Доступ к ApplicationWindow через родителей
                var win = parent
                while (win && !win.hasOwnProperty("showFullScreen")) win = win.parent
                if (win) win.showFullScreen()
            } else {
                var win2 = parent
                while (win2 && !win2.hasOwnProperty("showNormal")) win2 = win2.parent
                if (win2) win2.showNormal()
            }
        }
    }

    Column {
        anchors { top: parent.top; left: parent.left; right: parent.right }
        padding: 22; spacing: 16

        Text {
            text: "ОФОРМЛЕНИЕ ДИСПЛЕЯ"
            font.pixelSize: 11; font.weight: Font.Bold; font.letterSpacing: 2
            color: tokens.textSecondary || "#5d6b7e"
        }

        // ── Светлая / Тёмная ─────────────────────────────────────────────
        Rectangle {
            width: parent.width - parent.padding * 2
            height: 64; radius: 16
            color: tokens.surface || "#ffffff"
            border.color: tokens.border || "#e1e6ee"; border.width: 1

            Row {
                anchors { fill: parent; margins: 6 }
                spacing: 0

                Repeater {
                    model: [
                        {val: "light", label: "Светлая", iconKey: "sun"},
                        {val: "dark",  label: "Тёмная",  iconKey: "moon"},
                    ]

                    Rectangle {
                        width: parent.width / 2; height: parent.height
                        radius: 12
                        color: bridge && bridge.theme === modelData.val
                               ? (tokens.primary || "#1f6feb") : "transparent"

                        Row {
                            anchors.centerIn: parent
                            spacing: 8

                            Text {
                                text: bridge ? bridge.uiIcons[modelData.iconKey] || "" : ""
                                font.family: "Material Design Icons"
                                font.pixelSize: 20
                                color: bridge && bridge.theme === modelData.val
                                       ? (tokens.onPrimary || "#fff")
                                       : (tokens.textSecondary || "#5d6b7e")
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            Text {
                                text: modelData.label
                                font.pixelSize: 16; font.weight: Font.DemiBold
                                color: bridge && bridge.theme === modelData.val
                                       ? (tokens.onPrimary || "#fff")
                                       : (tokens.textSecondary || "#5d6b7e")
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: bridge && bridge.setTheme(modelData.val)
                        }
                    }
                }
            }
        }

        Text {
            text: "РЕЖИМ ОКНА"
            font.pixelSize: 11; font.weight: Font.Bold; font.letterSpacing: 2
            color: tokens.textSecondary || "#5d6b7e"
        }

        // ── Оконный / Полный экран ─────────────────────────────────────────
        Rectangle {
            width: parent.width - parent.padding * 2
            height: 64; radius: 16
            color: tokens.surface || "#ffffff"
            border.color: tokens.border || "#e1e6ee"; border.width: 1

            Row {
                anchors { fill: parent; margins: 6 }
                spacing: 0

                Repeater {
                    model: [
                        {val: "windowed",   label: "Оконный"},
                        {val: "fullscreen", label: "Полный экран"},
                    ]

                    Rectangle {
                        width: parent.width / 2; height: parent.height
                        radius: 12
                        color: bridge && bridge.windowMode === modelData.val
                               ? (tokens.primary || "#1f6feb") : "transparent"

                        Text {
                            anchors.centerIn: parent
                            text: modelData.label
                            font.pixelSize: 16; font.weight: Font.DemiBold
                            color: bridge && bridge.windowMode === modelData.val
                                   ? (tokens.onPrimary || "#fff")
                                   : (tokens.textPrimary || "#192230")
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: bridge && bridge.setWindowMode(modelData.val)
                        }
                    }
                }
            }
        }
    }
}
