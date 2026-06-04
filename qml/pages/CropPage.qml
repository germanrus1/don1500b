import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
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
            color: tokens.textSecondary; bottomPadding: 2
        }

        Rectangle {
            width: parent.width - parent.padding * 2
            height: cropRepeater.count * 60
            radius: 16
            color: tokens.surface
            border.color: tokens.border; border.width: 1
            clip: true

            Column {
                anchors.fill: parent

                Repeater {
                    id: cropRepeater
                    model: bridge.cultures

                    Rectangle {
                        width: parent.width
                        height: 60
                        color: index % 2 === 0 ? tokens.surface : Qt.rgba(
                            parseInt(tokens.bg.slice(1,3), 16) / 255,
                            parseInt(tokens.bg.slice(3,5), 16) / 255,
                            parseInt(tokens.bg.slice(5,7), 16) / 255, 1)

                        // Разделитель
                        Rectangle {
                            anchors { top: parent.top; left: parent.left; right: parent.right }
                            height: 1; color: tokens.border
                            visible: index > 0
                        }

                        RowLayout {
                            anchors {
                                fill: parent; leftMargin: 18; rightMargin: 18
                            }
                            spacing: 0

                            Text {
                                Layout.fillWidth: true
                                text: modelData
                                font.pixelSize: 18
                                font.weight: modelData === bridge.culture ? Font.DemiBold : Font.Normal
                                color: modelData === bridge.culture
                                       ? tokens.primary : tokens.textPrimary
                            }

                            Text {
                                visible: modelData === bridge.culture
                                text: bridge ? bridge.uiIcons.check : ""
                                font.family: "Material Design Icons"
                                font.pixelSize: 26
                                color: tokens.primary
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: bridge.setCulture(modelData)
                        }
                    }
                }
            }
        }
    }
}
