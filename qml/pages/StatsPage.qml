import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: root
    property var tokens: ({})
    contentWidth: availableWidth

    // Обновляем при показе страницы
    onVisibleChanged: if (visible) statsModel.refresh()

    QtObject {
        id: statsModel
        property var data: ({})
        function refresh() { data = bridge.stats }
    }

    Column {
        width: root.availableWidth
        padding: 22; spacing: 16

        // ── 3 метрики ──────────────────────────────────────────────────────
        Row {
            width: parent.width - parent.padding * 2
            spacing: 14

            Repeater {
                model: [
                    {key: "area",    unit: "га",  label: "Площадь",           color: "#22a05a"},
                    {key: "unloads", unit: "шт",  label: "Разгрузок бункера", color: "#f0871a"},
                    {key: "harvest", unit: "т",   label: "Намолот",           color: "#3b82f6"},
                ]

                Rectangle {
                    width: (parent.width - 28) / 3
                    height: 110; radius: 16
                    color: tokens.surface
                    border.color: tokens.border; border.width: 1

                    // Верхняя цветная полоска
                    Rectangle {
                        anchors { top: parent.top; left: parent.left; right: parent.right }
                        height: 3; radius: 16
                        color: modelData.color
                    }

                    Column {
                        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; leftMargin: 18; rightMargin: 18 }
                        spacing: 6

                        Row {
                            spacing: 4
                            Text {
                                text: statsModel.data[modelData.key] ?? "—"
                                font.family: "IBM Plex Mono, Courier New"
                                font.pixelSize: 38; font.weight: Font.DemiBold
                                color: modelData.color
                            }
                            Text {
                                text: " " + modelData.unit
                                font.pixelSize: 14; font.weight: Font.DemiBold
                                color: tokens.textSecondary
                                anchors.baseline: undefined
                            }
                        }
                        Text {
                            text: modelData.label
                            font.pixelSize: 13
                            color: tokens.textSecondary
                        }
                    }
                }
            }
        }

        // ── Детализация ───────────────────────────────────────────────────
        Text {
            text: "ДЕТАЛИЗАЦИЯ"
            font.pixelSize: 11; font.weight: Font.Bold; font.letterSpacing: 2
            color: tokens.textSecondary
        }

        Rectangle {
            width: parent.width - parent.padding * 2
            radius: 16
            color: tokens.surface
            border.color: tokens.border; border.width: 1
            height: detailCol.implicitHeight
            clip: true

            Column {
                id: detailCol
                width: parent.width

                Repeater {
                    model: [
                        {key: "date",     label: "Дата"},
                        {key: "workTime", label: "Время в работе"},
                        {key: "culture",  label: "Культура"},
                        {key: "unloads",  label: "Разгрузок"},
                    ]

                    Rectangle {
                        width: parent.width
                        height: 54
                        color: index % 2 === 0 ? tokens.surface : Qt.rgba(
                            parseInt(tokens.bg.slice(1,3), 16) / 255,
                            parseInt(tokens.bg.slice(3,5), 16) / 255,
                            parseInt(tokens.bg.slice(5,7), 16) / 255, 1)

                        Rectangle {
                            anchors { top: parent.top; left: parent.left; right: parent.right }
                            height: 1; color: tokens.border
                            visible: index > 0
                        }

                        RowLayout {
                            anchors { fill: parent; leftMargin: 18; rightMargin: 18 }
                            Text {
                                Layout.fillWidth: true
                                text: modelData.label
                                font.pixelSize: 16; color: tokens.textSecondary
                            }
                            Text {
                                text: statsModel.data[modelData.key] ?? "—"
                                font.family: "IBM Plex Mono, Courier New"
                                font.pixelSize: 16; font.weight: Font.DemiBold
                                color: tokens.textPrimary
                            }
                        }
                    }
                }
            }
        }
    }
}
