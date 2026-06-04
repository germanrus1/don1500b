import QtQuick

Canvas {
    id: root
    width: 256; height: 256

    property var tokens: ({})
    property real value: 0.0
    property real maxValue: 30.0
    property string unit: "км/ч"
    property string label: "СКОРОСТЬ"

    onValueChanged: requestPaint()
    onTokensChanged: requestPaint()

    // Константы совпадают с дизайном (JS-координаты, y вниз)
    readonly property real arcStart: 135.0
    readonly property real arcSweep: 270.0
    readonly property int  arcWidth: 14
    readonly property int  arcSteps: 6

    onPaint: {
        var ctx = getContext("2d")
        ctx.clearRect(0, 0, width, height)

        var A0    = arcStart
        var SWEEP = arcSweep
        var SW    = arcWidth
        var STEPS = arcSteps

        var cx = width / 2, cy = height / 2
        var r  = (width - SW) / 2 - 6
        var frac = Math.max(0, Math.min(1, value / maxValue))

        // Конвертация: угол от правого края, по часовой → радианы (y вниз)
        function toRad(deg) { return deg * Math.PI / 180 }
        function polar(cx, cy, r, deg) {
            return [cx + r * Math.cos(toRad(deg)), cy + r * Math.sin(toRad(deg))]
        }

        // ── Фоновая дуга ──────────────────────────────────────────────────
        ctx.beginPath()
        ctx.arc(cx, cy, r, toRad(A0), toRad(A0 + SWEEP), false)
        ctx.strokeStyle = tokens.border
        ctx.lineWidth   = SW
        ctx.lineCap     = "round"
        ctx.stroke()

        // ── Прогресс-дуга ────────────────────────────────────────────────
        if (frac > 0.001) {
            ctx.beginPath()
            ctx.arc(cx, cy, r, toRad(A0), toRad(A0 + SWEEP * frac), false)
            ctx.strokeStyle = tokens.primary
            ctx.lineWidth   = SW
            ctx.lineCap     = "round"
            ctx.stroke()
        }

        // ── Деления (7 крупных) ───────────────────────────────────────────
        ctx.fillStyle = tokens.textSecondary
        ctx.font = "600 10px 'IBM Plex Mono', monospace"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"

        for (var i = 0; i <= STEPS; i++) {
            var ang  = A0 + (SWEEP / STEPS) * i
            var pi   = polar(cx, cy, r - SW/2 - 8, ang)
            var po   = polar(cx, cy, r - SW/2 - 2, ang)
            ctx.globalAlpha = 0.55
            ctx.beginPath()
            ctx.moveTo(pi[0], pi[1])
            ctx.lineTo(po[0], po[1])
            ctx.strokeStyle = tokens.textSecondary
            ctx.lineWidth   = 2.5
            ctx.lineCap     = "round"
            ctx.stroke()
            ctx.globalAlpha = 1.0

            var lp  = polar(cx, cy, r - SW/2 - 22, ang)
            ctx.fillText(String(Math.round(maxValue / STEPS * i)), lp[0], lp[1])
        }

        // ── Мелкие деления ────────────────────────────────────────────────
        ctx.globalAlpha = 0.3
        for (var j = 0; j <= STEPS * 5; j++) {
            if (j % 5 === 0) continue
            var a2 = A0 + (SWEEP / (STEPS * 5)) * j
            var mi = polar(cx, cy, r - SW/2 - 5, a2)
            var mo = polar(cx, cy, r - SW/2 - 1, a2)
            ctx.beginPath()
            ctx.moveTo(mi[0], mi[1])
            ctx.lineTo(mo[0], mo[1])
            ctx.strokeStyle = tokens.textSecondary
            ctx.lineWidth   = 1.5
            ctx.lineCap     = "round"
            ctx.stroke()
        }
        ctx.globalAlpha = 1.0

        // ── Стрелка ───────────────────────────────────────────────────────
        var needleAng = A0 + SWEEP * frac
        var tip = polar(cx, cy, r - SW - 6, needleAng)
        var b1  = polar(cx, cy, 7, needleAng + 90)
        var b2  = polar(cx, cy, 7, needleAng - 90)
        var tl  = polar(cx, cy, 17, needleAng + 180)

        ctx.beginPath()
        ctx.moveTo(tip[0], tip[1])
        ctx.lineTo(b1[0],  b1[1])
        ctx.lineTo(tl[0],  tl[1])
        ctx.lineTo(b2[0],  b2[1])
        ctx.closePath()
        ctx.fillStyle = tokens.primary
        ctx.fill()

        // ── Ступица ───────────────────────────────────────────────────────
        ctx.beginPath()
        ctx.arc(cx, cy, 13, 0, 2 * Math.PI)
        ctx.fillStyle   = tokens.surface
        ctx.fill()
        ctx.strokeStyle = tokens.primary
        ctx.lineWidth   = 3.5
        ctx.stroke()

        ctx.beginPath()
        ctx.arc(cx, cy, 4, 0, 2 * Math.PI)
        ctx.fillStyle = tokens.primary
        ctx.fill()

        // ── Подпись "СКОРОСТЬ" ────────────────────────────────────────────
        ctx.fillStyle    = tokens.textSecondary
        ctx.font         = "700 9px 'IBM Plex Sans', sans-serif"
        ctx.textAlign    = "center"
        ctx.textBaseline = "middle"
        ctx.fillText(label, cx, cy - 44)

        // ── Цифровое значение ─────────────────────────────────────────────
        var valStr  = value.toFixed(1)
        ctx.font    = "700 26px 'IBM Plex Mono', monospace"
        var valW    = ctx.measureText(valStr).width
        ctx.fillStyle = tokens.textPrimary
        ctx.fillText(valStr, cx - (valW + 4 + ctx.measureText(unit).width) / 2 + valW / 2, cy + 52)

        // Единица
        ctx.font      = "600 11px 'IBM Plex Sans', sans-serif"
        ctx.fillStyle = tokens.primary
        ctx.fillText(unit, cx + (valW + 4 + ctx.measureText(unit).width) / 2 - ctx.measureText(unit).width / 2, cy + 52)
    }
}
