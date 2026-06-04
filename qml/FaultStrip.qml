import QtQuick
import QtQuick.Layouts

// Горизонтальная полоса иконок активных ошибок
RowLayout {
    id: root
    property var faults: ([])  // [{id, level, short, full, icon, color}]
    property var tokens: ({})
    spacing: 26

    signal errorTapped(var fault)

    Repeater {
        model: root.faults

        Column {
            spacing: 7
            Layout.alignment: Qt.AlignHCenter

            // Кружок
            Rectangle {
                width: 64; height: 64
                radius: 32
                color: modelData.level === "critical" ? tokens.critical : tokens.warning
                anchors.horizontalCenter: parent.horizontalCenter

                Text {
                    anchors.centerIn: parent
                    text: modelData.icon
                    font.family: "Material Design Icons"
                    font.pixelSize: 34
                    color: "#ffffff"
                }

                // Пульсация для критических
                SequentialAnimation on scale {
                    running: modelData.level === "critical"
                    loops: Animation.Infinite
                    NumberAnimation { to: 1.06; duration: 700; easing.type: Easing.InOutSine }
                    NumberAnimation { to: 1.0;  duration: 700; easing.type: Easing.InOutSine }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: root.errorTapped(modelData)
                }
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: modelData.short
                font.pixelSize: 12
                font.weight: Font.DemiBold
                color: tokens.textSecondary
            }
        }
    }
}
