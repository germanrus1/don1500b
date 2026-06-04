import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    property var tokens: ({})

    // Состояние вкладок
    property int tabIndex: 0   // 0=сессия 1=день 2=сезон

    Column {
        anchors { fill: parent; margins: 22 }
        spacing: 16

        // ── Вкладки: Сессия / День / Сезон ───────────────────────────────
        Rectangle {
            width: parent.width
            height: 56; radius: 16
            color: tokens.surface || "#ffffff"
            border.color: tokens.border || "#e1e6ee"; border.width: 1

            Row {
                anchors { fill: parent; margins: 5 }
                spacing: 0

                Repeater {
                    model: ["Сессия", "День", "Сезон"]

                    Rectangle {
                        width: parent.width / 3; height: parent.height
                        radius: 12
                        color: tabIndex === index
                               ? (tokens.primary || "#1f6feb") : "transparent"

                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            font.pixelSize: 16; font.weight: Font.DemiBold
                            color: tabIndex === index
                                   ? (tokens.onPrimary || "#fff")
                                   : (tokens.textSecondary || "#5d6b7e")
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: tabIndex = index
                        }
                    }
                }
            }
        }

        // ── Контент по вкладке ────────────────────────────────────────────
        ScrollView {
            width: parent.width
            height: parent.height - 56 - 16
            contentWidth: availableWidth

            Column {
                width: parent.availableWidth
                spacing: 14

                // Метрики (3 плитки)
                Row {
                    width: parent.width
                    spacing: 12

                    Repeater {
                        model: tabIndex === 0 ? sessionMetrics
                             : tabIndex === 1 ? dayMetrics
                             : seasonMetrics

                        Rectangle {
                            width: (parent.width - 24) / 3
                            height: 100; radius: 16
                            color: tokens.surface || "#ffffff"
                            border.color: tokens.border || "#e1e6ee"; border.width: 1

                            Rectangle {
                                anchors { top: parent.top; left: parent.left; right: parent.right }
                                height: 3; radius: 16
                                color: modelData.color
                            }

                            Column {
                                anchors {
                                    left: parent.left; right: parent.right
                                    verticalCenter: parent.verticalCenter
                                    leftMargin: 14; rightMargin: 14
                                }
                                spacing: 4

                                Row {
                                    spacing: 3
                                    Text {
                                        text: modelData.value
                                        font.family: "IBM Plex Mono, Courier New"
                                        font.pixelSize: 28; font.weight: Font.DemiBold
                                        color: modelData.color
                                    }
                                    Text {
                                        visible: modelData.unit.length > 0
                                        text: " " + modelData.unit
                                        font.pixelSize: 13
                                        color: tokens.textSecondary || "#5d6b7e"
                                        anchors.bottom: parent.bottom
                                        bottomPadding: 4
                                    }
                                }
                                Text {
                                    text: modelData.label
                                    font.pixelSize: 12
                                    color: tokens.textSecondary || "#5d6b7e"
                                    width: parent.width
                                    elide: Text.ElideRight
                                }
                            }
                        }
                    }
                }

                // Детализация
                Text {
                    text: "ДЕТАЛИЗАЦИЯ"
                    font.pixelSize: 11; font.weight: Font.Bold; font.letterSpacing: 2
                    color: tokens.textSecondary || "#5d6b7e"
                }

                Rectangle {
                    width: parent.width
                    height: detailRepeater.count * 54
                    radius: 16; clip: true
                    color: tokens.surface || "#ffffff"
                    border.color: tokens.border || "#e1e6ee"; border.width: 1

                    Column {
                        width: parent.width

                        Repeater {
                            id: detailRepeater
                            model: tabIndex === 0 ? sessionRows
                                 : tabIndex === 1 ? dayRows
                                 : seasonRows

                            Rectangle {
                                width: parent.width; height: 54
                                color: index % 2 === 1
                                       ? Qt.rgba(
                                           parseInt((tokens.bg || "#eef1f5").slice(1,3), 16)/255,
                                           parseInt((tokens.bg || "#eef1f5").slice(3,5), 16)/255,
                                           parseInt((tokens.bg || "#eef1f5").slice(5,7), 16)/255, 1)
                                       : (tokens.surface || "#ffffff")

                                Rectangle {
                                    anchors { top: parent.top; left: parent.left; right: parent.right }
                                    height: 1; color: tokens.border || "#e1e6ee"
                                    visible: index > 0
                                }

                                RowLayout {
                                    anchors { fill: parent; leftMargin: 18; rightMargin: 18 }
                                    Text {
                                        Layout.fillWidth: true
                                        text: modelData.label
                                        font.pixelSize: 15
                                        color: tokens.textSecondary || "#5d6b7e"
                                    }
                                    Text {
                                        text: modelData.value
                                        font.family: "IBM Plex Mono, Courier New"
                                        font.pixelSize: 15; font.weight: Font.DemiBold
                                        color: tokens.textPrimary || "#192230"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // ── Данные: Сессия ────────────────────────────────────────────────────
    property var _s: bridge ? bridge.statsSession : ({})
    property var sessionMetrics: [
        {value: _s.weightKg  || "—", unit: "кг",  label: "Намолот",      color: "#3b82f6"},
        {value: _s.unloads   || "0", unit: "шт",  label: "Разгрузок",    color: "#f0871a"},
        {value: _s.efficiency|| "—", unit: "",    label: "Эффективность", color: "#22a05a"},
    ]
    property var sessionRows: [
        {label: "Культура",        value: _s.culture   || "—"},
        {label: "Время в работе",  value: _s.workTime  || "—"},
        {label: "Время молотьбы",  value: _s.threshTime|| "—"},
        {label: "Предупреждений",  value: _s.warnCount || "—"},
    ]

    // ── Данные: День ──────────────────────────────────────────────────────
    property var _d: bridge ? bridge.statsDay : ({})
    property var dayMetrics: [
        {value: _d.weightKg  || "—", unit: "",   label: "Намолот",    color: "#3b82f6"},
        {value: _d.unloads   || "0", unit: "шт", label: "Разгрузок",  color: "#f0871a"},
        {value: _d.efficiency|| "—", unit: "",   label: "КПД",         color: "#22a05a"},
    ]
    property var dayRows: [
        {label: "Дата",            value: _d.date      || "—"},
        {label: "Сессий за день",  value: _d.sessions  || "—"},
        {label: "Время в работе",  value: _d.workTime  || "—"},
        {label: "Ошибок",          value: _d.errors    || "—"},
    ]

    // ── Данные: Сезон ─────────────────────────────────────────────────────
    property var _z: bridge ? bridge.statsSeason : ({})
    property var seasonMetrics: [
        {value: _z.weightT     || "—", unit: "",   label: "Намолот",    color: "#3b82f6"},
        {value: _z.unloads     || "0", unit: "шт", label: "Разгрузок",  color: "#f0871a"},
        {value: _z.days        || "0", unit: "дн", label: "Рабочих дней",color: "#22a05a"},
    ]
    property var seasonRows: [
        {label: "Сезон",           value: _z.year        || "—"},
        {label: "Время молотьбы",  value: _z.threshHours || "—"},
        {label: "Лучший день",     value: _z.bestDay     || "—"},
        {label: "Намолот лучшего", value: _z.bestDayKg   || "—"},
    ]
}
