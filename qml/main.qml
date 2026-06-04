import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1024
    height: 600
    visible: true
    title: "Дон 1500б"

    // Загрузка шрифта MDI
    FontLoader {
        id: mdiFont
        source: "file:///C:/Users/mrger/AppData/Roaming/Python/Python311/site-packages/qtawesome/fonts/materialdesignicons6-webfont-6.9.96.ttf"
    }

    flags: (bridge && bridge.windowMode === "fullscreen")
           ? Qt.FramelessWindowHint
           : Qt.Window

    // Токены с fallback до инициализации bridge
    readonly property var tok: bridge ? bridge.tokens : ({
        bg: "#eef1f5", surface: "#ffffff", menuBg: "#ffffff",
        textPrimary: "#192230", textSecondary: "#5d6b7e",
        primary: "#1f6feb", onPrimary: "#ffffff",
        border: "#e1e6ee", critical: "#d92d20", warning: "#e8830c"
    })

    // ── Material тема ─────────────────────────────────────────────────────
    Material.theme:      bridge && bridge.theme === "dark" ? Material.Dark : Material.Light
    Material.primary:    tok.primary
    Material.accent:     tok.primary
    Material.background: tok.bg
    Material.foreground: tok.textPrimary

    background: Rectangle { color: tok.bg }

    // ── Основной экран ────────────────────────────────────────────────────
    Dashboard {
        anchors.fill: parent
        tokens: tok
        onMenuRequested: menuOverlay.visible = true
    }

    // ── Меню ─────────────────────────────────────────────────────────────
    MenuOverlay {
        id: menuOverlay
        anchors.fill: parent
        tokens: tok
        visible: false
        z: 50
    }

    Component.onCompleted: {
        if (bridge && bridge.windowMode === "fullscreen")
            root.showFullScreen()
    }
}
