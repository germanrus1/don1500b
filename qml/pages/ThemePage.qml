import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    property var tokens: ({})

    Column {
        anchors { top: parent.top; left: parent.left; right: parent.right }
        padding: 22; spacing: 16

        Text {
            text: "ОФОРМЛЕНИЕ ДИСПЛЕЯ"
            font.pixelSize: 11; font.weight: Font.Bold; font.letterSpacing: 2
            color: tokens.textSecondary; bottomPadding: 2
        }

        // Светлая / Тёмная
        Rectangle {
            width: parent.width - parent.padding * 2
            height: 68; radius: 16
            color: tokens.surface
            border.color: tokens.border; border.width: 1

            Row {
                anchors { fill: parent; margins: 6 }
                spacing: 0

                Repeater {
                    model: [
                        {val: "light", label: "Светлая", icon: "light_mode"},
                        {val: "dark",  label: "Тёмная",  icon: "dark_mode"},
                    ]

                    Rectangle {
                        width: parent.width / 2; height: parent.height
                        radius: 12
                        color: bridge.theme === modelData.val ? tokens.primary : "transparent"

                        Row {
                            anchors.centerIn: parent
                            spacing: 8
                            Text {
                                text: modelData.icon
                                font.family: "Material Design Icons"
                                font.pixelSize: 22
                                color: bridge.theme === modelData.val
                                       ? tokens.onPrimary : tokens.textSecondary
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            Text {
                                text: modelData.label
                                font.pixelSize: 17; font.weight: Font.DemiBold
                                color: bridge.theme === modelData.val
                                       ? tokens.onPrimary : tokens.textSecondary
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: bridge.setTheme(modelData.val)
                        }
                    }
                }
            }
        }

        Text {
            text: "РЕЖИМ ОКНА"
            font.pixelSize: 11; font.weight: Font.Bold; font.letterSpacing: 2
            color: tokens.textSecondary; topPadding: 4
        }

        Rectangle {
            width: parent.width - parent.padding * 2
            height: 68; radius: 16
            color: tokens.surface
            border.color: tokens.border; border.width: 1

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
                        color: bridge.windowMode === modelData.val ? tokens.primary : "transparent"

                        Text {
                            anchors.centerIn: parent
                            text: modelData.label
                            font.pixelSize: 17; font.weight: Font.DemiBold
                            color: bridge.windowMode === modelData.val
                                   ? tokens.onPrimary : tokens.textSecondary
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: bridge.setWindowMode(modelData.val)
                        }
                    }
                }
            }
        }
    }
}
