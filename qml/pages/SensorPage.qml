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
            color: tokens.textSecondary; bottomPadding: 2
        }

        Rectangle {
            width: parent.width - parent.padding * 2
            height: sensorRepeater.count * 60
            radius: 16; clip: true
            color: tokens.surface
            border.color: tokens.border; border.width: 1

            Column {
                anchors.fill: parent

                Repeater {
                    id: sensorRepeater
                    model: bridge.sensorValues

                    Rectangle {
                        width: parent.width; height: 60
                        color: "transparent"

                        Rectangle {
                            anchors { top: parent.top; left: parent.left; right: parent.right }
                            height: 1; color: tokens.border; visible: index > 0
                        }

                        RowLayout {
                            anchors { fill: parent; leftMargin: 16; rightMargin: 16 }
                            spacing: 13

                            // Иконка-чип
                            Rectangle {
                                width: 38; height: 38; radius: 10
                                color: Qt.rgba(
                                    parseInt(modelData.color.slice(1,3), 16) / 255,
                                    parseInt(modelData.color.slice(3,5), 16) / 255,
                                    parseInt(modelData.color.slice(5,7), 16) / 255,
                                    bridge.theme === "dark" ? 0.22 : 0.15)
                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.icon
                                    font.family: "Material Design Icons"
                                    font.pixelSize: 22
                                    color: modelData.color
                                }
                            }

                            Text {
                                Layout.fillWidth: true
                                text: modelData.full
                                font.pixelSize: 15; font.weight: Font.Medium
                                color: tokens.textPrimary
                                elide: Text.ElideRight
                            }

                            // Toggle (упрощённый)
                            Rectangle {
                                width: 54; height: 32; radius: 999
                                color: toggleOn.checked ? modelData.color : tokens.border

                                property bool checked: true  // TODO: read from config

                                Rectangle {
                                    width: 26; height: 26; radius: 13
                                    color: "#ffffff"
                                    x: parent.checked ? parent.width - width - 3 : 3
                                    anchors.verticalCenter: parent.verticalCenter
                                    Behavior on x { NumberAnimation { duration: 150 } }
                                }
                                id: toggleOn
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: toggleOn.checked = !toggleOn.checked
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
