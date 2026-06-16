import QtQuick
import QtQuick.Layouts

Item {
    id: root
    property var tokens: ({})

    // Сигнал для main.qml — открыть меню
    signal menuRequested()

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
            id: menuBtn
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
                onClicked: root.menuRequested()
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
            id: cropRow
            anchors { right: parent.right; rightMargin: 14; verticalCenter: parent.verticalCenter }
            spacing: 9

            property var cropMeta: {
                if (!bridge) return {"icon": "", "color": "#22a05a"}
                var items = bridge.cropItems
                var name = bridge.culture
                for (var i = 0; i < items.length; i++) {
                    if (items[i].name === name) return items[i]
                }
                return {"icon": "", "color": "#22a05a"}
            }

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
                    text: bridge ? bridge.culture : ""
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                    color: tokens.textPrimary
                }
            }

            Rectangle {
                width: 34; height: 34
                radius: 10
                color: Qt.rgba(
                    parseInt(cropRow.cropMeta.color.slice(1,3), 16) / 255,
                    parseInt(cropRow.cropMeta.color.slice(3,5), 16) / 255,
                    parseInt(cropRow.cropMeta.color.slice(5,7), 16) / 255,
                    0.16)
                anchors.verticalCenter: parent.verticalCenter
                Text {
                    anchors.centerIn: parent
                    text: cropRow.cropMeta.icon
                    font.family: "Material Design Icons"
                    font.pixelSize: 22
                    color: cropRow.cropMeta.color
                }
            }
        }
    }

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

        SensorColumn {
            Layout.preferredWidth: 232
            Layout.fillHeight: true
            sensors: bridge ? bridge.leftSensors : []
            tokens: root.tokens
            dashboard: root
        }

        Rectangle { width: 1; Layout.fillHeight: true; color: tokens.border }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Column {
                anchors.centerIn: parent
                spacing: 22

                Speedometer {
                    tokens: root.tokens
                    value: bridge ? bridge.speed : 0
                    anchors.horizontalCenter: parent.horizontalCenter
                }

                FaultStrip {
                    id: faultStrip
                    visible: bridge && bridge.faults.length > 0
                    faults: bridge ? bridge.faults : []
                    tokens: root.tokens
                    anchors.horizontalCenter: parent.horizontalCenter
                    onErrorTapped: function(fault) { errorPopup.show(fault) }
                }
            }
        }

        Rectangle { width: 1; Layout.fillHeight: true; color: tokens.border }

        SensorColumn {
            Layout.preferredWidth: 232
            Layout.fillHeight: true
            sensors: bridge ? bridge.rightSensors : []
            tokens: root.tokens
            dashboard: root
        }
    }

    // ── Тост ─────────────────────────────────────────────────────────────
    Rectangle {
        id: toast
        visible: false
        radius: 10
        color: "#1c1e24"
        border.color: Qt.rgba(1, 1, 1, 0.08); border.width: 1
        height: 38
        width: toastText.implicitWidth + 28
        z: 20

        Text {
            id: toastText
            anchors.centerIn: parent
            color: "#ffffff"
            font.pixelSize: 14
            font.weight: Font.DemiBold
        }

        Timer { id: toastTimer; interval: 2200; onTriggered: toast.visible = false }
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

    // ── Попап ошибки ──────────────────────────────────────────────────────
    Item {
        id: errorPopup
        anchors.fill: parent
        visible: false
        z: 30

        function show(fault) {
            faultData.level = fault.level || ""
            faultData.icon  = fault.icon  || ""
            faultData.title = fault.full  || fault.short || ""
            faultData.desc  = fault.full  || ""
            errorPopup.visible = true
        }

        QtObject {
            id: faultData
            property string level: ""
            property string icon:  ""
            property string title: ""
            property string desc:  ""
        }

        // Затемнение
        Rectangle {
            anchors.fill: parent
            color: Qt.rgba(0, 0, 0, 0.55)
            MouseArea { anchors.fill: parent; onClicked: errorPopup.visible = false }
        }

        // Карточка (по центру, не перекрывает колонки датчиков)
        Rectangle {
            anchors.centerIn: parent
            width: Math.min(520, parent.width - 520)
            height: cardCol.implicitHeight + 48
            radius: 12
            color: "#1c1e24"
            border.color: Qt.rgba(1, 1, 1, 0.08); border.width: 1

            Column {
                id: cardCol
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 26 }
                spacing: 12

                // Шапка
                Row {
                    spacing: 12
                    Rectangle {
                        width: 46; height: 46; radius: 23
                        color: faultData.level === "critical" ? tokens.critical : tokens.warning
                        Text {
                            anchors.centerIn: parent
                            text: faultData.icon
                            font.family: "Material Design Icons"
                            font.pixelSize: 26
                            color: "#ffffff"
                        }
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: faultData.level === "critical" ? "КРИТИЧЕСКАЯ ОШИБКА" : "ПРЕДУПРЕЖДЕНИЕ"
                        font.pixelSize: 11; font.weight: Font.Bold
                        font.letterSpacing: 1.5
                        color: faultData.level === "critical" ? tokens.critical : tokens.warning
                    }
                }

                // Заголовок
                Text {
                    width: parent.width
                    text: faultData.title
                    font.pixelSize: 20; font.weight: Font.Bold
                    color: "#ffffff"
                    wrapMode: Text.WordWrap
                }

                // Описание
                Text {
                    width: parent.width
                    text: "Датчик: " + faultData.title
                    font.pixelSize: 14
                    color: "#aab0bd"
                    wrapMode: Text.WordWrap
                    lineHeight: 1.5
                }
            }

            // Кнопка закрыть
            Rectangle {
                anchors { top: parent.top; right: parent.right; margins: 16 }
                width: 40; height: 40; radius: 10
                color: Qt.rgba(1, 1, 1, 0.08)
                Text {
                    anchors.centerIn: parent
                    text: bridge ? bridge.uiIcons.close : "✕"
                    font.family: "Material Design Icons"
                    font.pixelSize: 22
                    color: "#ffffff"
                }
                MouseArea { anchors.fill: parent; onClicked: errorPopup.visible = false }
            }
        }
    }
}
