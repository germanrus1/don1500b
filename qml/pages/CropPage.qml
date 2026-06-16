import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    property var tokens: ({})

    Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: col.implicitHeight + 44
        clip: true
        ScrollBar.vertical: ScrollBar {}

        Column {
            id: col
            width: parent.width
            topPadding: 20; bottomPadding: 28
            leftPadding: 22; rightPadding: 22
            spacing: 14

            Text {
                text: "ВЫБОР КУЛЬТУРЫ"
                font.pixelSize: 11; font.weight: Font.Bold; font.letterSpacing: 2
                color: tokens.textSecondary || "#5d6b7e"
            }

            Rectangle {
                width: parent.width - 44
                height: cropRep.count * 64
                radius: 16; clip: true
                color: tokens.surface || "#ffffff"
                border.color: tokens.border || "#e1e6ee"; border.width: 1

                Column {
                    anchors.fill: parent

                    Repeater {
                        id: cropRep
                        model: bridge ? bridge.cropItems : []

                        Rectangle {
                            width: parent.width
                            height: 64
                            color: "transparent"

                            Rectangle {
                                anchors { top: parent.top; left: parent.left; right: parent.right }
                                height: 1; color: tokens.border || "#e1e6ee"
                                visible: index > 0
                            }

                            RowLayout {
                                anchors {
                                    left: parent.left; right: parent.right
                                    leftMargin: 18; rightMargin: 18
                                    verticalCenter: parent.verticalCenter
                                }
                                spacing: 14

                                // Иконка культуры
                                Rectangle {
                                    width: 40; height: 40; radius: 10
                                    Layout.alignment: Qt.AlignVCenter
                                    color: Qt.rgba(
                                        parseInt(modelData.color.slice(1,3), 16) / 255,
                                        parseInt(modelData.color.slice(3,5), 16) / 255,
                                        parseInt(modelData.color.slice(5,7), 16) / 255, 0.18)
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
                                    Layout.alignment: Qt.AlignVCenter
                                    text: modelData.name
                                    font.pixelSize: 18
                                    font.weight: (bridge && modelData.name === bridge.culture)
                                                 ? Font.DemiBold : Font.Normal
                                    color: (bridge && modelData.name === bridge.culture)
                                           ? (tokens.primary || "#1f6feb")
                                           : (tokens.textPrimary || "#192230")
                                }

                                // Галочка
                                Text {
                                    Layout.alignment: Qt.AlignVCenter
                                    visible: bridge && modelData.name === bridge.culture
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
}
