import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

ScrollView {
    property var tokens: ({})
    contentWidth: availableWidth

    Column {
        width: parent.availableWidth
        padding: 22; spacing: 12

        Text {
            text: "АКТИВНЫЕ ДАТЧИКИ"
            font.pixelSize: 11; font.weight: Font.Bold; font.letterSpacing: 2
            color: tokens.textSecondary || "#5d6b7e"
        }

        Rectangle {
            width: parent.width - parent.padding * 2
            height: sensorRepeater.count * 64
            radius: 16; clip: true
            color: tokens.surface || "#ffffff"
            border.color: tokens.border || "#e1e6ee"; border.width: 1

            Column {
                anchors.fill: parent

                Repeater {
                    id: sensorRepeater
                    model: bridge ? bridge.sensorValues : []

                    Rectangle {
                        width: parent.width; height: 64
                        color: "transparent"

                        Rectangle {
                            anchors { top: parent.top; left: parent.left; right: parent.right }
                            height: 1
                            color: tokens.border || "#e1e6ee"
                            visible: index > 0
                        }

                        RowLayout {
                            anchors { fill: parent; leftMargin: 16; rightMargin: 16 }
                            spacing: 14

                            // Иконка-чип
                            Rectangle {
                                width: 40; height: 40; radius: 10
                                color: Qt.rgba(
                                    parseInt(modelData.color.slice(1,3), 16) / 255,
                                    parseInt(modelData.color.slice(3,5), 16) / 255,
                                    parseInt(modelData.color.slice(5,7), 16) / 255,
                                    bridge && bridge.theme === "dark" ? 0.22 : 0.15)
                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.icon
                                    font.family: "Material Design Icons"
                                    font.pixelSize: 24
                                    color: modelData.color
                                }
                            }

                            // Полное название датчика
                            Text {
                                Layout.fillWidth: true
                                text: modelData.full || ""
                                font.pixelSize: 14
                                font.weight: Font.Medium
                                color: tokens.textPrimary || "#192230"
                                elide: Text.ElideRight
                                wrapMode: Text.NoWrap
                            }

                            // Toggle
                            Rectangle {
                                id: toggleRect
                                width: 54; height: 32; radius: 999
                                property bool on: true
                                color: on ? modelData.color : (tokens.border || "#e1e6ee")

                                Rectangle {
                                    width: 26; height: 26; radius: 13
                                    color: "#ffffff"
                                    x: parent.on ? parent.width - width - 3 : 3
                                    anchors.verticalCenter: parent.verticalCenter
                                    Behavior on x { NumberAnimation { duration: 150 } }
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: toggleRect.on = !toggleRect.on
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
