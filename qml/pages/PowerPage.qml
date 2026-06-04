import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    property var tokens: ({})
    signal cancelled()
    signal confirmed()

    Column {
        anchors.centerIn: parent
        spacing: 22

        // Иконка
        Rectangle {
            width: 88; height: 88; radius: 44
            color: Qt.rgba(
                parseInt(tokens.critical.slice(1,3), 16) / 255,
                parseInt(tokens.critical.slice(3,5), 16) / 255,
                parseInt(tokens.critical.slice(5,7), 16) / 255,
                0.12)
            anchors.horizontalCenter: parent.horizontalCenter
            Text {
                anchors.centerIn: parent
                text: bridge ? bridge.uiIcons.power : ""
                font.family: "Material Design Icons"
                font.pixelSize: 48
                color: tokens.critical
            }
        }

        Column {
            spacing: 6
            anchors.horizontalCenter: parent.horizontalCenter
            Text {
                text: "Выключить компьютер?"
                font.pixelSize: 24; font.weight: Font.DemiBold
                color: tokens.textPrimary
                anchors.horizontalCenter: parent.horizontalCenter
            }
            Text {
                text: "Текущая статистика смены будет сохранена."
                font.pixelSize: 15; color: tokens.textSecondary
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }

        Row {
            spacing: 14
            anchors.horizontalCenter: parent.horizontalCenter

            // Отмена
            Rectangle {
                width: 160; height: 56; radius: 999
                color: "transparent"
                border.color: tokens.border; border.width: 1
                Text { anchors.centerIn: parent; text: "Отмена"; font.pixelSize: 17; font.weight: Font.DemiBold; color: tokens.textPrimary }
                MouseArea { anchors.fill: parent; onClicked: cancelled() }
            }

            // Выключить
            Rectangle {
                width: 200; height: 56; radius: 999
                color: tokens.critical
                Row {
                    anchors.centerIn: parent; spacing: 8
                    Text {
                        text: bridge ? bridge.uiIcons.power : ""
                        font.family: "Material Design Icons"; font.pixelSize: 22
                        color: "#ffffff"; anchors.verticalCenter: parent.verticalCenter
                    }
                    Text { text: "Выключить"; font.pixelSize: 17; font.weight: Font.Bold; color: "#ffffff"; anchors.verticalCenter: parent.verticalCenter }
                }
                MouseArea { anchors.fill: parent; onClicked: confirmed() }
            }
        }
    }
}
