import QtQuick
import QtQuick.Layouts

Item {
    id: root
    property var tokens: ({})

    // ── Вспомогательная функция ───────────────────────────────────────────
    function sensorData(id) {
        var list = bridge.sensorValues
        for (var i = 0; i < list.length; i++)
            if (list[i].id === id) return list[i]
        return {id: id, display: "—", state: "", unit: ""}
    }

    // ── Верхняя панель ────────────────────────────────────────────────────
    Rectangle {
        id: topBar
        anchors { top: parent.top; left: parent.left; right: parent.right }
        height: 55
        color: tokens.menuBg
        z: 2

        Rectangle {
            anchors { bottom: parent.bottom; left: parent.left; right: parent.right }
            height: 1
            color: tokens.border
        }

        // МЕНЮ
        Rectangle {
            anchors { left: parent.left; leftMargin: 14; verticalCenter: parent.verticalCenter }
            width: menuBtnText.implicitWidth + 40
            height: 42
            radius: 21
            color: tokens.primary

            Row {
                anchors.centerIn: parent
                spacing: 8
                Text {
                    text: bridge ? bridge.uiIcons.menu : ""
                    font.family: "Material Design Icons"
                    font.pixelSize: 22
                    color: tokens.onPrimary
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    id: menuBtnText
                    text: "Меню"
                    font.pixelSize: 17
                    font.weight: Font.Bold
                    color: tokens.onPrimary
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            MouseArea {
                anchors.fill: parent
                onClicked: root.parent.openMenu()
            }
        }

        // Часы
        Text {
            anchors.centerIn: parent
            font.family: "IBM Plex Mono, Courier New"
            font.pixelSize: 30
            font.weight: Font.Bold
            color: tokens.textPrimary
            text: clockTimer.timeStr
        }

        // Культура
        Row {
            anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
            spacing: 9

            Column {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 1
                Text {
                    anchors.right: parent.right
                    text: "КУЛЬТУРА"
                    font.pixelSize: 10
                    font.weight: Font.DemiBold
                    font.letterSpacing: 1.5
                    color: tokens.textSecondary
                }
                Text {
                    anchors.right: parent.right
                    text: bridge.culture
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                    color: tokens.textPrimary
                }
            }

            Rectangle {
                width: 34; height: 34
                radius: 10
                color: Qt.rgba(0x22/255, 0xa0/255, 0x5a/255, 0.16)
                anchors.verticalCenter: parent.verticalCenter
                Text {
                    anchors.centerIn: parent
                    text: bridge ? bridge.uiIcons.leaf : ""
                    font.family: "Material Design Icons"
                    font.pixelSize: 22
                    color: "#22a05a"
                }
            }
        }
    }

    // Часы — таймер
    Timer {
        id: clockTimer
        property string timeStr: Qt.formatDateTime(new Date(), "hh:mm:ss")
        interval: 1000; running: true; repeat: true
        onTriggered: timeStr = Qt.formatDateTime(new Date(), "hh:mm:ss")
    }

    // ── Тело (3 колонки) ──────────────────────────────────────────────────
    RowLayout {
        anchors {
            top: topBar.bottom; bottom: parent.bottom
            left: parent.left; right: parent.right
        }
        spacing: 0

        // Левая колонка (двигатель)
        SensorColumn {
            Layout.preferredWidth: 232
            Layout.fillHeight: true
            sensors: bridge.leftSensors
            tokens: root.tokens
        }

        // Разделитель
        Rectangle { width: 1; Layout.fillHeight: true; color: tokens.border }

        // Центральная панель
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Column {
                anchors.centerIn: parent
                spacing: 22

                Speedometer {
                    id: speedo
                    tokens: root.tokens
                    value: bridge.speed
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                // Полоса ошибок (только при наличии)
                FaultStrip {
                    visible: bridge.faults.length > 0
                    faults: bridge.faults
                    tokens: root.tokens
                    anchors.horizontalCenter: parent.horizontalCenter
                }
            }
        }

        // Разделитель
        Rectangle { width: 1; Layout.fillHeight: true; color: tokens.border }

        // Правая колонка (молотилка)
        SensorColumn {
            Layout.preferredWidth: 232
            Layout.fillHeight: true
            sensors: bridge.rightSensors
            tokens: root.tokens
        }
    }

    // ── Тост ─────────────────────────────────────────────────────────────
    Rectangle {
        id: toast
        visible: false
        radius: 10
        color: "#1c1e24"
        border.color: Qt.rgba(1, 1, 1, 0.08)
        border.width: 1
        height: 38
        width: toastText.implicitWidth + 28
        z: 10

        Text {
            id: toastText
            anchors.centerIn: parent
            color: "#ffffff"
            font.pixelSize: 14
            font.weight: Font.DemiBold
        }

        Timer {
            id: toastTimer
            interval: 2200
            onTriggered: toast.visible = false
        }

        NumberAnimation on opacity { id: fadeIn;  from: 0; to: 1; duration: 160 }
        NumberAnimation on opacity { id: fadeOut; from: 1; to: 0; duration: 400
            onFinished: toast.visible = false }
    }

    function showToast(text, x, y) {
        toastText.text = text
        toast.x = x
        toast.y = y - toast.height / 2
        toast.visible = true
        toast.opacity = 0
        fadeIn.start()
        toastTimer.restart()
    }
}
