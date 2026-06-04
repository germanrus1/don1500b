import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Главная страница меню — сетка навигационных карточек
ScrollView {
    id: root
    property var tokens: ({})
    signal navigate(int pageIndex)

    contentWidth: availableWidth

    // Данные с MDI unicode-символами приходят из bridge
    readonly property var navItems: bridge ? bridge.navItems : []

    Column {
        width: root.availableWidth
        padding: 22
        spacing: 14

        Text {
            text: "НАВИГАЦИЯ"
            font.pixelSize: 11; font.weight: Font.Bold
            font.letterSpacing: 2
            color: tokens.textSecondary
            bottomPadding: 2
        }

        Grid {
            width: parent.width - parent.padding * 2
            columns: 3
            spacing: 14

            Repeater {
                model: root.navItems

                // Карточка
                Rectangle {
                    width: (parent.width - parent.spacing * 2) / 3
                    height: 124
                    radius: 16
                    color: tokens.surface
                    border.color: modelData.danger ? tokens.critical : tokens.border
                    border.width: modelData.danger ? 2 : 1

                    Column {
                        anchors {
                            left: parent.left; bottom: parent.bottom
                            margins: 18; bottomMargin: 18
                        }
                        spacing: 0

                        // Чип-иконка
                        Rectangle {
                            width: 50; height: 50; radius: 12
                            color: Qt.rgba(
                                parseInt(modelData.color.slice(1,3), 16) / 255,
                                parseInt(modelData.color.slice(3,5), 16) / 255,
                                parseInt(modelData.color.slice(5,7), 16) / 255,
                                tokens === bridge.tokens && bridge.theme === "dark" ? 0.24 : 0.16
                            )
                            Text {
                                anchors.centerIn: parent
                                text: modelData.icon
                                font.family: "Material Design Icons"
                                font.pixelSize: 30
                                color: modelData.color
                            }
                        }

                        Item { width: 1; height: 12 }

                        Text {
                            text: modelData.label
                            font.pixelSize: 19
                            font.weight: Font.DemiBold
                            color: modelData.danger ? tokens.critical : tokens.textPrimary
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.navigate(modelData.page)
                    }
                }
            }
        }
    }
}
