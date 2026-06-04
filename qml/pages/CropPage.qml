import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    property var tokens: ({})
    contentWidth: availableWidth

    Column {
        width: parent.availableWidth
        padding: 22
        spacing: 12

        Text {
            text: "ВЫБОР КУЛЬТУРЫ"
            font.pixelSize: 11; font.weight: Font.Bold; font.letterSpacing: 2
            color: tokens.textSecondary || "#5d6b7e"
        }

        Rectangle {
            width: parent.width - parent.padding * 2
            height: cropRepeater.count * 60
            radius: 16
            color: tokens.surface || "#ffffff"
            border.color: tokens.border || "#e1e6ee"
            border.width: 1
            clip: true

            Column {
                anchors.fill: parent

                Repeater {
                    id: cropRepeater
                    model: bridge ? bridge.cropItems : []

                    Rectangle {
                        width: parent.width
                        height: 60
                        color: "transparent"

                        Rectangle {
                            anchors { top: parent.top; left: parent.left; right: parent.right }
                            height: 1
                            color: tokens.border || "#e1e6ee"
                            visible: index > 0
                        }

                        RowLayout {
                            anchors { fill: parent; leftMargin: 16; rightMargin: 18 }
                            spacing: 14

                            // Иконка культуры
                            Rectangle {
                                width: 38; height: 38; radius: 10
                                color: Qt.rgba(
                                    parseInt(modelData.color.slice(1,3), 16) / 255,
                                    parseInt(modelData.color.slice(3,5), 16) / 255,
                                    parseInt(modelData.color.slice(5,7), 16) / 255,
                                    0.18)

                                Text {
                                    anchors.centerIn: parent
                                    text: modelData.icon
                                    font.family: "Material Design Icons"
                                    font.pixelSize: 22
                                    color: modelData.color
                                }
                            }

                            // Название
                            Text {
                                Layout.fillWidth: true
                                text: modelData.name
                                font.pixelSize: 18
                                font.weight: modelData.name === (bridge ? bridge.culture : "")
                                             ? Font.DemiBold : Font.Normal
                                color: modelData.name === (bridge ? bridge.culture : "")
                                       ? (tokens.primary || "#1f6feb")
                                       : (tokens.textPrimary || "#192230")
                            }

                            // Галочка (только у выбранной)
                            Text {
                                visible: modelData.name === (bridge ? bridge.culture : "")
                                text: bridge ? bridge.uiIcons.check : ""
                                font.family: "Material Design Icons"
                                font.pixelSize: 24
                                color: tokens.primary || "#1f6feb"
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: bridge && bridge.setCulture(modelData.name)
                        }
                    }
                }
            }
        }
    }
}
