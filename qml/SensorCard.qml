import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

// Горизонтальная карточка датчика
Rectangle {
    id: root
    property var sensorMeta: ({id:"", short:"", full:"", unit:"", icon:"", color:"#888"})
    property var tokens: ({})

    // Обновляется из bridge.sensorValues
    property string displayValue: "—"
    property string state: ""          // "" | "warning" | "critical"
    property string unit: sensorMeta.unit

    signal tapped(string fullName)

    color: tokens.surface
    radius: 16

    border.color: state === "critical" ? tokens.critical
                : state === "warning"  ? tokens.warning
                : tokens.border
    border.width: state !== "" ? 2 : 1

    layer.enabled: true
    layer.effect: null  // тень убрана для производительности на RPi

    // Касание
    MouseArea {
        anchors.fill: parent
        onClicked: root.tapped(root.sensorMeta.full)
    }

    RowLayout {
        anchors {
            left: parent.left; right: parent.right
            verticalCenter: parent.verticalCenter
            leftMargin: 12; rightMargin: 12
        }
        spacing: 12

        // ── Цветной чип ──────────────────────────────────────────────────
        Rectangle {
            width: 46; height: 46
            radius: 11
            color: Qt.rgba(
                parseInt(root.sensorMeta.color.slice(1,3), 16) / 255,
                parseInt(root.sensorMeta.color.slice(3,5), 16) / 255,
                parseInt(root.sensorMeta.color.slice(5,7), 16) / 255,
                tokens === bridge.tokens && bridge.theme === "dark" ? 0.22 : 0.15
            )

            Text {
                anchors.centerIn: parent
                text: root.sensorMeta.icon
                font.family: "Material Design Icons"
                font.pixelSize: 27
                color: root.sensorMeta.color
            }
        }

        // ── Текст ─────────────────────────────────────────────────────────
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2

            // Название
            Text {
                Layout.fillWidth: true
                text: root.sensorMeta.short
                font.pixelSize: 12
                font.weight: Font.DemiBold
                color: tokens.textSecondary
                elide: Text.ElideRight
            }

            // Значение + единица
            RowLayout {
                spacing: 4
                Text {
                    text: root.displayValue
                    font.family: "IBM Plex Mono, Courier New"
                    font.pixelSize: 31
                    font.weight: Font.Bold
                    color: root.state === "critical" ? tokens.critical
                         : root.state === "warning"  ? tokens.warning
                         : tokens.textPrimary
                    lineHeight: 1
                }
                Text {
                    text: root.unit
                    font.pixelSize: 12
                    font.weight: Font.Medium
                    color: tokens.textSecondary
                    anchors.baseline: undefined
                }
            }
        }
    }
}
