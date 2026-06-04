import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts
import "pages"

// Полноэкранный оверлей меню
Rectangle {
    id: root
    property var tokens: ({})
    color: tokens.bg

    property int currentPage: 0  // 0=root 1=crop 2=sensors 3=theme 4=stats 5=power

    readonly property var pageTitle: [
        "Меню", "Культура", "Датчики", "Тема", "Статистика", "Выключение"
    ]

    // Анимация появления
    NumberAnimation on opacity { id: fadeIn; from: 0; to: 1; duration: 180 }
    onVisibleChanged: if (visible) { currentPage = 0; fadeIn.start() }

    // ── Шапка ────────────────────────────────────────────────────────────
    Rectangle {
        id: header
        anchors { top: parent.top; left: parent.left; right: parent.right }
        height: 62
        color: tokens.menuBg
        z: 2

        Rectangle {
            anchors { bottom: parent.bottom; left: parent.left; right: parent.right }
            height: 1; color: tokens.border
        }

        RowLayout {
            anchors { fill: parent; leftMargin: 16; rightMargin: 16 }
            spacing: 12

            // Кнопка "назад"
            Rectangle {
                width: 44; height: 44; radius: 10
                color: "transparent"
                border.color: tokens.border
                border.width: 1
                visible: root.currentPage !== 0
                Layout.alignment: Qt.AlignVCenter

                Text {
                    anchors.centerIn: parent
                    text: bridge ? bridge.uiIcons.back : ""
                    font.family: "Material Design Icons"
                    font.pixelSize: 26
                    color: tokens.textPrimary
                }
                MouseArea { anchors.fill: parent; onClicked: root.currentPage = 0 }
            }

            Text {
                Layout.fillWidth: true
                text: root.pageTitle[root.currentPage]
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: tokens.textPrimary
            }

            // Кнопка закрыть
            Rectangle {
                width: 44; height: 44; radius: 10
                color: "transparent"
                border.color: tokens.border; border.width: 1
                Layout.alignment: Qt.AlignVCenter

                Text {
                    anchors.centerIn: parent
                    text: bridge ? bridge.uiIcons.close : ""
                    font.family: "Material Design Icons"
                    font.pixelSize: 26
                    color: tokens.textPrimary
                }
                MouseArea { anchors.fill: parent; onClicked: root.visible = false }
            }
        }
    }

    // ── Страницы ─────────────────────────────────────────────────────────
    StackLayout {
        anchors { top: header.bottom; bottom: parent.bottom; left: parent.left; right: parent.right }
        currentIndex: root.currentPage

        // 0 — Корень
        MenuRoot {
            tokens: root.tokens
            onNavigate: (idx) => root.currentPage = idx
        }

        // 1 — Культура
        CropPage   { tokens: root.tokens }

        // 2 — Датчики
        SensorPage { tokens: root.tokens }

        // 3 — Тема
        ThemePage  { tokens: root.tokens }

        // 4 — Статистика
        StatsPage  {
            tokens: root.tokens
            visible: root.currentPage === 4
        }

        // 5 — Выключение
        PowerPage  {
            tokens: root.tokens
            onCancelled: root.currentPage = 0
            onConfirmed: { root.visible = false; bridge.shutdown() }
        }
    }
}
