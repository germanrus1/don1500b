import math

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetricsF, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QWidget

_SIZE  = 256
_SW    = 14       # arc stroke width
_A0    = 135.0    # start angle: screen coords (y-down, 0=right, CW positive)
_SWEEP = 270.0
_STEPS = 6        # major tick intervals → 7 labels: 0, 5, 10 … 30


def _polar(cx: float, cy: float, r: float, deg: float):
    rad = math.radians(deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


class Speedometer(QWidget):
    """Circular speedometer rendered with QPainter, design-faithful to tokens-precision.js."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value   = 0.0
        self._max     = 30.0
        self._unit    = "км/ч"
        self._label   = "СКОРОСТЬ"
        self._primary = QColor("#1f6feb")
        self._border  = QColor("#e1e6ee")
        self._text_p  = QColor("#192230")
        self._text_s  = QColor("#5d6b7e")
        self._surface = QColor("#ffffff")
        self.setFixedSize(_SIZE, _SIZE)

    # ── Public API ─────────────────────────────────────────────────────────

    def set_value(self, v: float):
        self._value = v
        self.update()

    def apply_tokens(self, t: dict):
        self._primary = QColor(t.get("primary",        "#1f6feb"))
        self._border  = QColor(t.get("border",         "#e1e6ee"))
        self._text_p  = QColor(t.get("text_primary",   "#192230"))
        self._text_s  = QColor(t.get("text_secondary", "#5d6b7e"))
        self._surface = QColor(t.get("surface",        "#ffffff"))
        self.update()

    # ── Paint ──────────────────────────────────────────────────────────────

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = cy = _SIZE / 2.0
        r    = (_SIZE - _SW) / 2.0 - 6.0
        frac = max(0.0, min(1.0, self._value / self._max))
        rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)

        # In QPainter: angle 0 = 3 o'clock, positive = CCW.
        # JS arc: A0=135° CW from right → QPainter: -135.
        # Sweep  270° CW                → QPainter: -270.
        qt_start = int(-_A0 * 16)

        # ── Background arc ────────────────────────────────────────────────
        self._arc_pen(p, self._border, _SW)
        p.drawArc(rect, qt_start, int(-_SWEEP * 16))

        # ── Progress arc ──────────────────────────────────────────────────
        if frac > 0.001:
            self._arc_pen(p, self._primary, _SW)
            p.drawArc(rect, qt_start, int(-_SWEEP * frac * 16))

        # ── Major ticks + numeric scale ───────────────────────────────────
        lf  = self._font("mono", 10, QFont.Weight.DemiBold)
        lfm = QFontMetricsF(lf)
        p.setFont(lf)

        for i in range(_STEPS + 1):
            ang    = _A0 + (_SWEEP / _STEPS) * i
            ix, iy = _polar(cx, cy, r - _SW/2 - 8, ang)
            ox, oy = _polar(cx, cy, r - _SW/2 - 2, ang)

            tp = QPen(self._text_s, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(tp)
            p.setOpacity(0.55)
            p.drawLine(QPointF(ix, iy), QPointF(ox, oy))
            p.setOpacity(1.0)

            lx, ly = _polar(cx, cy, r - _SW/2 - 22, ang)
            txt    = str(round(self._max / _STEPS * i))
            tw = lfm.horizontalAdvance(txt)
            th = lfm.height()
            p.setPen(QPen(self._text_s))
            p.drawText(QRectF(lx - tw/2 - 1, ly - th/2, tw + 2, th),
                       Qt.AlignmentFlag.AlignCenter, txt)

        # ── Minor ticks ───────────────────────────────────────────────────
        mp = QPen(self._text_s, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(mp)
        p.setOpacity(0.3)
        for i in range(_STEPS * 5 + 1):
            if i % 5 == 0:
                continue
            ang    = _A0 + (_SWEEP / (_STEPS * 5)) * i
            ix, iy = _polar(cx, cy, r - _SW/2 - 5, ang)
            ox, oy = _polar(cx, cy, r - _SW/2 - 1, ang)
            p.drawLine(QPointF(ix, iy), QPointF(ox, oy))
        p.setOpacity(1.0)

        # ── Needle ────────────────────────────────────────────────────────
        ang = _A0 + _SWEEP * frac
        nx, ny   = _polar(cx, cy, r - _SW - 6,  ang)
        bx1, by1 = _polar(cx, cy, 7,             ang + 90)
        bx2, by2 = _polar(cx, cy, 7,             ang - 90)
        tx,  ty  = _polar(cx, cy, 17,            ang + 180)

        poly = QPolygonF([QPointF(nx, ny), QPointF(bx1, by1),
                          QPointF(tx, ty), QPointF(bx2, by2)])
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._primary))
        p.drawPolygon(poly)

        # ── Hub ───────────────────────────────────────────────────────────
        p.setPen(QPen(self._primary, 3.5))
        p.setBrush(QBrush(self._surface))
        p.drawEllipse(QPointF(cx, cy), 13.0, 13.0)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._primary))
        p.drawEllipse(QPointF(cx, cy), 4.0, 4.0)

        # ── "СКОРОСТЬ" label (above hub) ──────────────────────────────────
        sf  = self._font("sans", 9, QFont.Weight.Bold, spacing=1.4)
        sfm = QFontMetricsF(sf)
        p.setFont(sf)
        p.setPen(QPen(self._text_s))
        p.drawText(QPointF(cx - sfm.horizontalAdvance(self._label) / 2, cy - 44),
                   self._label)

        # ── Digital readout (below hub) ───────────────────────────────────
        vf  = self._font("mono", 26, QFont.Weight.Bold)
        vfm = QFontMetricsF(vf)
        val_str = f"{self._value:.1f}"
        vw = vfm.horizontalAdvance(val_str)

        uf  = self._font("sans", 11, QFont.Weight.DemiBold)
        ufm = QFontMetricsF(uf)
        uw  = ufm.horizontalAdvance(self._unit)

        x0       = cx - (vw + 4 + uw) / 2
        baseline = cy + 52

        p.setFont(vf)
        p.setPen(QPen(self._text_p))
        p.drawText(QPointF(x0, baseline), val_str)

        p.setFont(uf)
        p.setPen(QPen(self._primary))
        p.drawText(QPointF(x0 + vw + 4, baseline), self._unit)

        p.end()

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _arc_pen(p: QPainter, color: QColor, width: float):
        pen = QPen(color, width, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

    @staticmethod
    def _font(family: str, size: int, weight=QFont.Weight.Normal, spacing: float = 0) -> QFont:
        if family == "mono":
            f = QFont("IBM Plex Mono, Courier New, monospace", size)
        else:
            f = QFont("IBM Plex Sans, Segoe UI, Ubuntu, sans-serif", size)
        f.setWeight(weight)
        if spacing:
            f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
        return f
