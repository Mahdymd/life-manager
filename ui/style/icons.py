"""ui/style/icons.py — Theme-aware geometric icon set (no emojis).

Constitution §4: "Never use emojis as icons – use the defined icon set."
This module draws simple Material-style geometric icons with QPainter so
the app has zero external font/SVG dependency while remaining theme-aware.
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF

from ui.style.theme_manager import colors


def _pen(color: str, width: float = 1.8) -> QPen:
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _draw_icon(name: str, size: int, color: str) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    m = size * 0.18
    r = QRectF(m, m, size - 2 * m, size - 2 * m)
    c = QColor(color)
    pen = _pen(color, max(1.4, size * 0.08))
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)

    if name == "home":
        path = QPainterPath()
        path.moveTo(r.left() + r.width() * 0.1, r.center().y() + r.height() * 0.05)
        path.lineTo(r.center().x(), r.top())
        path.lineTo(r.right() - r.width() * 0.1, r.center().y() + r.height() * 0.05)
        path.lineTo(r.right() - r.width() * 0.1, r.bottom())
        path.lineTo(r.left() + r.width() * 0.35, r.bottom())
        path.lineTo(r.left() + r.width() * 0.35, r.center().y() + r.height() * 0.25)
        path.lineTo(r.right() - r.width() * 0.35, r.center().y() + r.height() * 0.25)
        path.lineTo(r.right() - r.width() * 0.35, r.bottom())
        path.lineTo(r.left() + r.width() * 0.1, r.bottom())
        path.closeSubpath()
        p.drawPath(path)
    elif name == "check":
        path = QPainterPath()
        path.moveTo(r.left() + r.width() * 0.15, r.center().y())
        path.lineTo(r.center().x() - r.width() * 0.05, r.bottom() - r.height() * 0.2)
        path.lineTo(r.right() - r.width() * 0.1, r.top() + r.height() * 0.2)
        p.drawPath(path)
    elif name == "target":
        p.drawEllipse(r)
        p.drawEllipse(r.adjusted(r.width() * 0.22, r.height() * 0.22,
                                 -r.width() * 0.22, -r.height() * 0.22))
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        cx, cy = r.center().x(), r.center().y()
        rad = r.width() * 0.12
        p.drawEllipse(QPointF(cx, cy), rad, rad)
    elif name == "flame":
        path = QPainterPath()
        path.moveTo(r.center().x(), r.bottom())
        path.cubicTo(r.left(), r.center().y() + r.height() * 0.2,
                     r.left() + r.width() * 0.1, r.top() + r.height() * 0.15,
                     r.center().x(), r.top())
        path.cubicTo(r.right() - r.width() * 0.1, r.top() + r.height() * 0.15,
                     r.right(), r.center().y() + r.height() * 0.2,
                     r.center().x(), r.bottom())
        p.drawPath(path)
    elif name == "money":
        p.drawRoundedRect(r, r.width() * 0.15, r.height() * 0.15)
        p.drawLine(QPointF(r.center().x(), r.top() + r.height() * 0.22),
                   QPointF(r.center().x(), r.bottom() - r.height() * 0.22))
        p.drawArc(QRectF(r.center().x() - r.width() * 0.22, r.top() + r.height() * 0.28,
                         r.width() * 0.44, r.height() * 0.28), 0, 180 * 16)
        p.drawArc(QRectF(r.center().x() - r.width() * 0.22, r.center().y() - r.height() * 0.05,
                         r.width() * 0.44, r.height() * 0.28), 180 * 16, 180 * 16)
    elif name == "journal":
        p.drawRoundedRect(r, 2, 2)
        for i in range(3):
            y = r.top() + r.height() * (0.3 + i * 0.2)
            p.drawLine(QPointF(r.left() + r.width() * 0.2, y),
                       QPointF(r.right() - r.width() * 0.2, y))
    elif name == "note":
        path = QPainterPath()
        path.moveTo(r.left(), r.top())
        path.lineTo(r.right() - r.width() * 0.25, r.top())
        path.lineTo(r.right(), r.top() + r.height() * 0.25)
        path.lineTo(r.right(), r.bottom())
        path.lineTo(r.left(), r.bottom())
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(r.right() - r.width() * 0.25, r.top()),
                   QPointF(r.right() - r.width() * 0.25, r.top() + r.height() * 0.25))
        p.drawLine(QPointF(r.right() - r.width() * 0.25, r.top() + r.height() * 0.25),
                   QPointF(r.right(), r.top() + r.height() * 0.25))
    elif name == "focus":
        p.drawEllipse(r)
        p.drawLine(QPointF(r.center().x(), r.top() + r.height() * 0.15),
                   QPointF(r.center().x(), r.center().y()))
        p.drawLine(QPointF(r.center().x(), r.center().y()),
                   QPointF(r.center().x() + r.width() * 0.25, r.center().y() + r.height() * 0.1))
    elif name == "health":
        p.drawRoundedRect(QRectF(r.center().x() - r.width() * 0.12, r.top(),
                                 r.width() * 0.24, r.height()), 2, 2)
        p.drawRoundedRect(QRectF(r.left(), r.center().y() - r.height() * 0.12,
                                 r.width(), r.height() * 0.24), 2, 2)
    elif name == "learning":
        path = QPainterPath()
        path.moveTo(r.center().x(), r.top() + r.height() * 0.15)
        path.lineTo(r.left(), r.top() + r.height() * 0.35)
        path.lineTo(r.left(), r.bottom() - r.height() * 0.15)
        path.lineTo(r.center().x(), r.bottom() - r.height() * 0.3)
        path.lineTo(r.right(), r.bottom() - r.height() * 0.15)
        path.lineTo(r.right(), r.top() + r.height() * 0.35)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(r.center().x(), r.top() + r.height() * 0.15),
                   QPointF(r.center().x(), r.bottom() - r.height() * 0.3))
    elif name == "calendar":
        p.drawRoundedRect(r.adjusted(0, r.height() * 0.12, 0, 0), 2, 2)
        p.drawLine(QPointF(r.left(), r.top() + r.height() * 0.35),
                   QPointF(r.right(), r.top() + r.height() * 0.35))
        p.drawLine(QPointF(r.left() + r.width() * 0.28, r.top()),
                   QPointF(r.left() + r.width() * 0.28, r.top() + r.height() * 0.25))
        p.drawLine(QPointF(r.right() - r.width() * 0.28, r.top()),
                   QPointF(r.right() - r.width() * 0.28, r.top() + r.height() * 0.25))
    elif name == "chart":
        p.drawLine(QPointF(r.left(), r.bottom()), QPointF(r.right(), r.bottom()))
        p.drawLine(QPointF(r.left(), r.bottom()), QPointF(r.left(), r.top()))
        path = QPainterPath()
        path.moveTo(r.left() + r.width() * 0.15, r.bottom() - r.height() * 0.25)
        path.lineTo(r.left() + r.width() * 0.4, r.bottom() - r.height() * 0.55)
        path.lineTo(r.left() + r.width() * 0.65, r.bottom() - r.height() * 0.4)
        path.lineTo(r.right() - r.width() * 0.1, r.top() + r.height() * 0.2)
        p.drawPath(path)
    elif name == "settings":
        p.drawEllipse(r.adjusted(r.width() * 0.28, r.height() * 0.28,
                                 -r.width() * 0.28, -r.height() * 0.28))
        cx, cy = r.center().x(), r.center().y()
        for i in range(8):
            import math
            a = i * math.pi / 4
            x1 = cx + math.cos(a) * r.width() * 0.32
            y1 = cy + math.sin(a) * r.height() * 0.32
            x2 = cx + math.cos(a) * r.width() * 0.48
            y2 = cy + math.sin(a) * r.height() * 0.48
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    elif name == "menu":
        for i in range(3):
            y = r.top() + r.height() * (0.25 + i * 0.25)
            p.drawLine(QPointF(r.left() + r.width() * 0.1, y),
                       QPointF(r.right() - r.width() * 0.1, y))
    elif name == "close":
        p.drawLine(r.topLeft() + QPointF(r.width() * 0.15, r.height() * 0.15),
                   r.bottomRight() - QPointF(r.width() * 0.15, r.height() * 0.15))
        p.drawLine(r.topRight() + QPointF(-r.width() * 0.15, r.height() * 0.15),
                   r.bottomLeft() + QPointF(r.width() * 0.15, -r.height() * 0.15))
    elif name == "warning":
        path = QPainterPath()
        path.moveTo(r.center().x(), r.top())
        path.lineTo(r.right(), r.bottom() - r.height() * 0.05)
        path.lineTo(r.left(), r.bottom() - r.height() * 0.05)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(r.center().x(), r.top() + r.height() * 0.35),
                   QPointF(r.center().x(), r.bottom() - r.height() * 0.3))
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(r.center().x(), r.bottom() - r.height() * 0.18),
                      size * 0.04, size * 0.04)
    elif name == "empty":
        p.drawRoundedRect(r, 3, 3)
        p.drawLine(QPointF(r.left() + r.width() * 0.2, r.center().y()),
                   QPointF(r.right() - r.width() * 0.2, r.center().y()))
    elif name == "search":
        p.drawEllipse(r.adjusted(0, 0, -r.width() * 0.25, -r.height() * 0.25))
        p.drawLine(QPointF(r.center().x() + r.width() * 0.2, r.center().y() + r.height() * 0.2),
                   QPointF(r.right() - r.width() * 0.05, r.bottom() - r.height() * 0.05))
    elif name == "save":
        path = QPainterPath()
        path.moveTo(r.left(), r.top())
        path.lineTo(r.right() - r.width() * 0.2, r.top())
        path.lineTo(r.right(), r.top() + r.height() * 0.2)
        path.lineTo(r.right(), r.bottom())
        path.lineTo(r.left(), r.bottom())
        path.closeSubpath()
        p.drawPath(path)
        p.drawRect(QRectF(r.left() + r.width() * 0.2, r.top(),
                          r.width() * 0.45, r.height() * 0.28))
        p.drawRect(QRectF(r.left() + r.width() * 0.2, r.center().y(),
                          r.width() * 0.6, r.height() * 0.35))
    elif name == "star":
        import math
        path = QPainterPath()
        cx, cy = r.center().x(), r.center().y()
        outer, inner = r.width() * 0.45, r.width() * 0.18
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rad = outer if i % 2 == 0 else inner
            pt = QPointF(cx + math.cos(a) * rad, cy + math.sin(a) * rad)
            if i == 0:
                path.moveTo(pt)
            else:
                path.lineTo(pt)
        path.closeSubpath()
        p.drawPath(path)
    elif name == "chevron_left":
        path = QPainterPath()
        path.moveTo(r.center().x() + r.width() * 0.15, r.top() + r.height() * 0.15)
        path.lineTo(r.center().x() - r.width() * 0.15, r.center().y())
        path.lineTo(r.center().x() + r.width() * 0.15, r.bottom() - r.height() * 0.15)
        p.drawPath(path)
    elif name == "chevron_right":
        path = QPainterPath()
        path.moveTo(r.center().x() - r.width() * 0.15, r.top() + r.height() * 0.15)
        path.lineTo(r.center().x() + r.width() * 0.15, r.center().y())
        path.lineTo(r.center().x() - r.width() * 0.15, r.bottom() - r.height() * 0.15)
        p.drawPath(path)
    elif name == "pause":
        w = r.width() * 0.22
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(r.left() + r.width() * 0.2, r.top() + r.height() * 0.15,
                                 w, r.height() * 0.7), 1, 1)
        p.drawRoundedRect(QRectF(r.right() - r.width() * 0.2 - w, r.top() + r.height() * 0.15,
                                 w, r.height() * 0.7), 1, 1)
    elif name == "play":
        path = QPainterPath()
        path.moveTo(r.left() + r.width() * 0.25, r.top() + r.height() * 0.15)
        path.lineTo(r.right() - r.width() * 0.15, r.center().y())
        path.lineTo(r.left() + r.width() * 0.25, r.bottom() - r.height() * 0.15)
        path.closeSubpath()
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(path)
    elif name == "add":
        p.drawLine(QPointF(r.center().x(), r.top() + r.height() * 0.15),
                   QPointF(r.center().x(), r.bottom() - r.height() * 0.15))
        p.drawLine(QPointF(r.left() + r.width() * 0.15, r.center().y()),
                   QPointF(r.right() - r.width() * 0.15, r.center().y()))
    elif name == "bolt":
        path = QPainterPath()
        path.moveTo(r.center().x() + r.width() * 0.1, r.top())
        path.lineTo(r.left() + r.width() * 0.2, r.center().y())
        path.lineTo(r.center().x(), r.center().y())
        path.lineTo(r.center().x() - r.width() * 0.1, r.bottom())
        path.lineTo(r.right() - r.width() * 0.2, r.center().y())
        path.lineTo(r.center().x(), r.center().y())
        path.closeSubpath()
        p.drawPath(path)
    elif name == "trash":
        p.drawLine(QPointF(r.left(), r.top() + r.height() * 0.18),
                   QPointF(r.right(), r.top() + r.height() * 0.18))
        p.drawRoundedRect(QRectF(r.left() + r.width() * 0.15, r.top() + r.height() * 0.18,
                                 r.width() * 0.7, r.height() * 0.82), 2, 2)
        p.drawLine(QPointF(r.left() + r.width() * 0.35, r.top() + r.height() * 0.18),
                   QPointF(r.left() + r.width() * 0.35, r.top()))
        p.drawLine(QPointF(r.right() - r.width() * 0.35, r.top() + r.height() * 0.18),
                   QPointF(r.right() - r.width() * 0.35, r.top()))
        p.drawLine(QPointF(r.left() + r.width() * 0.35, r.top() + r.height() * 0.18),
                   QPointF(r.right() - r.width() * 0.35, r.top()))
    elif name == "edit":
        path = QPainterPath()
        path.moveTo(r.left(), r.bottom())
        path.lineTo(r.left(), r.bottom() - r.height() * 0.22)
        path.lineTo(r.right() - r.width() * 0.22, r.top())
        path.lineTo(r.right(), r.top() + r.height() * 0.22)
        path.lineTo(r.left() + r.width() * 0.22, r.bottom())
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(r.right() - r.width() * 0.35, r.top() + r.height() * 0.18),
                   QPointF(r.right() - r.width() * 0.08, r.top() + r.height() * 0.45))
    elif name == "refresh":
        p.drawArc(r, 20 * 16, 260 * 16)
        arrow = QPainterPath()
        arrow.moveTo(r.right() - r.width() * 0.05, r.top() + r.height() * 0.05)
        arrow.lineTo(r.right() + r.width() * 0.05, r.top() + r.height() * 0.25)
        arrow.lineTo(r.right() - r.width() * 0.18, r.top() + r.height() * 0.28)
        p.drawPath(arrow)
    elif name == "undo":
        p.drawArc(r, 90 * 16, 240 * 16)
        arrow = QPainterPath()
        arrow.moveTo(r.left() - r.width() * 0.02, r.top() + r.height() * 0.05)
        arrow.lineTo(r.left() + r.width() * 0.08, r.top() + r.height() * 0.3)
        arrow.lineTo(r.left() + r.width() * 0.28, r.top() + r.height() * 0.15)
        p.drawPath(arrow)
    elif name == "clock":
        p.drawEllipse(r)
        p.drawLine(QPointF(r.center().x(), r.center().y()),
                   QPointF(r.center().x(), r.top() + r.height() * 0.22))
        p.drawLine(QPointF(r.center().x(), r.center().y()),
                   QPointF(r.center().x() + r.width() * 0.22, r.center().y() + r.height() * 0.05))
    elif name == "moon":
        outer = QPainterPath()
        outer.addEllipse(r)
        inner = QPainterPath()
        inner.addEllipse(r.adjusted(r.width() * 0.28, -r.height() * 0.08,
                                    r.width() * 0.08, r.height() * 0.08))
        crescent = outer.subtracted(inner)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(crescent)
    elif name == "droplet":
        path = QPainterPath()
        path.moveTo(r.center().x(), r.top())
        path.cubicTo(r.right() + r.width() * 0.05, r.top() + r.height() * 0.55,
                    r.right() - r.width() * 0.02, r.bottom(),
                    r.center().x(), r.bottom())
        path.cubicTo(r.left() + r.width() * 0.02, r.bottom(),
                    r.left() - r.width() * 0.05, r.top() + r.height() * 0.55,
                    r.center().x(), r.top())
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(path)
    elif name == "coffee":
        p.drawRoundedRect(QRectF(r.left(), r.top() + r.height() * 0.25,
                                 r.width() * 0.72, r.height() * 0.6), 2, 2)
        p.drawArc(QRectF(r.left() + r.width() * 0.62, r.top() + r.height() * 0.35,
                         r.width() * 0.3, r.height() * 0.35), -90 * 16, 180 * 16)
        p.drawLine(QPointF(r.left() + r.width() * 0.2, r.top() + r.height() * 0.2),
                   QPointF(r.left() + r.width() * 0.2, r.top()))
        p.drawLine(QPointF(r.left() + r.width() * 0.4, r.top() + r.height() * 0.2),
                   QPointF(r.left() + r.width() * 0.4, r.top()))
    elif name == "pin":
        p.drawEllipse(QRectF(r.left(), r.top(), r.width(), r.width()))
        p.drawLine(QPointF(r.center().x(), r.top() + r.width()),
                   QPointF(r.center().x(), r.bottom()))
    elif name == "scale":
        p.drawLine(QPointF(r.left(), r.top()), QPointF(r.right(), r.top()))
        p.drawLine(QPointF(r.center().x(), r.top()), QPointF(r.center().x(), r.bottom()))
        p.drawLine(QPointF(r.left() + r.width() * 0.15, r.bottom()),
                   QPointF(r.right() - r.width() * 0.15, r.bottom()))
        p.drawLine(QPointF(r.left(), r.top()), QPointF(r.left() - r.width() * 0.05, r.top() + r.height() * 0.28))
        p.drawLine(QPointF(r.right(), r.top()), QPointF(r.right() + r.width() * 0.05, r.top() + r.height() * 0.28))
        p.drawArc(QRectF(r.left() - r.width() * 0.18, r.top() + r.height() * 0.15,
                         r.width() * 0.36, r.height() * 0.28), 200 * 16, 140 * 16)
        p.drawArc(QRectF(r.right() - r.width() * 0.18, r.top() + r.height() * 0.15,
                         r.width() * 0.36, r.height() * 0.28), 200 * 16, 140 * 16)
    elif name == "tag":
        path = QPainterPath()
        path.moveTo(r.left(), r.top())
        path.lineTo(r.center().x() + r.width() * 0.1, r.top())
        path.lineTo(r.right(), r.center().y())
        path.lineTo(r.center().x() + r.width() * 0.1, r.bottom())
        path.lineTo(r.left(), r.bottom())
        path.closeSubpath()
        p.drawPath(path)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(r.left() + r.width() * 0.2, r.center().y()), size * 0.04, size * 0.04)
    elif name == "monitor":
        p.drawRoundedRect(QRectF(r.left(), r.top(), r.width(), r.height() * 0.7), 1, 1)
        p.drawLine(QPointF(r.center().x(), r.top() + r.height() * 0.7),
                   QPointF(r.center().x(), r.bottom()))
        p.drawLine(QPointF(r.left() + r.width() * 0.25, r.bottom()),
                   QPointF(r.right() - r.width() * 0.25, r.bottom()))
    elif name == "message":
        p.drawRoundedRect(QRectF(r.left(), r.top(), r.width(), r.height() * 0.75), 4, 4)
        path = QPainterPath()
        path.moveTo(r.left() + r.width() * 0.2, r.top() + r.height() * 0.75)
        path.lineTo(r.left() + r.width() * 0.12, r.bottom())
        path.lineTo(r.left() + r.width() * 0.42, r.top() + r.height() * 0.75)
        p.drawPath(path)
    elif name == "palette":
        p.drawEllipse(r)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        for dx, dy in [(-0.2, -0.15), (0.15, -0.2), (0.22, 0.12), (-0.1, 0.22)]:
            p.drawEllipse(QPointF(r.center().x() + r.width() * dx,
                                   r.center().y() + r.height() * dy), size * 0.05, size * 0.05)
    elif name == "upload":
        p.drawLine(QPointF(r.center().x(), r.top()), QPointF(r.center().x(), r.center().y() + r.height() * 0.1))
        arrow = QPainterPath()
        arrow.moveTo(r.center().x() - r.width() * 0.2, r.top() + r.height() * 0.25)
        arrow.lineTo(r.center().x(), r.top())
        arrow.lineTo(r.center().x() + r.width() * 0.2, r.top() + r.height() * 0.25)
        p.drawPath(arrow)
        p.drawLine(QPointF(r.left(), r.bottom() - r.height() * 0.15),
                   QPointF(r.left(), r.bottom()))
        p.drawLine(QPointF(r.left(), r.bottom()), QPointF(r.right(), r.bottom()))
        p.drawLine(QPointF(r.right(), r.bottom()), QPointF(r.right(), r.bottom() - r.height() * 0.15))
    elif name == "bug":
        p.drawEllipse(QRectF(r.left() + r.width() * 0.2, r.top() + r.height() * 0.15,
                             r.width() * 0.6, r.height() * 0.6))
        p.drawLine(QPointF(r.center().x(), r.top() + r.height() * 0.15), QPointF(r.center().x(), r.top()))
        for dx in (-0.35, 0.35):
            p.drawLine(QPointF(r.center().x() + r.width() * dx * 0.5, r.center().y()),
                       QPointF(r.center().x() + r.width() * dx, r.center().y() - r.height() * 0.15))
            p.drawLine(QPointF(r.center().x() + r.width() * dx * 0.5, r.center().y() + r.height() * 0.2),
                       QPointF(r.center().x() + r.width() * dx, r.center().y() + r.height() * 0.3))
    elif name == "trending_up":
        p.drawLine(QPointF(r.left(), r.bottom() - r.height() * 0.15),
                   QPointF(r.left() + r.width() * 0.35, r.top() + r.height() * 0.45))
        p.drawLine(QPointF(r.left() + r.width() * 0.35, r.top() + r.height() * 0.45),
                   QPointF(r.left() + r.width() * 0.55, r.top() + r.height() * 0.65))
        p.drawLine(QPointF(r.left() + r.width() * 0.55, r.top() + r.height() * 0.65),
                   QPointF(r.right(), r.top()))
        p.drawLine(QPointF(r.right() - r.width() * 0.25, r.top()), QPointF(r.right(), r.top()))
        p.drawLine(QPointF(r.right(), r.top()), QPointF(r.right(), r.top() + r.height() * 0.25))
    elif name == "trending_down":
        p.drawLine(QPointF(r.left(), r.top() + r.height() * 0.15),
                   QPointF(r.left() + r.width() * 0.35, r.bottom() - r.height() * 0.45))
        p.drawLine(QPointF(r.left() + r.width() * 0.35, r.bottom() - r.height() * 0.45),
                   QPointF(r.left() + r.width() * 0.55, r.bottom() - r.height() * 0.65))
        p.drawLine(QPointF(r.left() + r.width() * 0.55, r.bottom() - r.height() * 0.65),
                   QPointF(r.right(), r.bottom()))
        p.drawLine(QPointF(r.right() - r.width() * 0.25, r.bottom()), QPointF(r.right(), r.bottom()))
        p.drawLine(QPointF(r.right(), r.bottom()), QPointF(r.right(), r.bottom() - r.height() * 0.25))
    elif name == "award":
        p.drawEllipse(QRectF(r.left() + r.width() * 0.12, r.top(), r.width() * 0.76, r.width() * 0.76))
        path = QPainterPath()
        path.moveTo(r.left() + r.width() * 0.28, r.top() + r.width() * 0.6)
        path.lineTo(r.left() + r.width() * 0.15, r.bottom())
        path.lineTo(r.center().x(), r.bottom() - r.height() * 0.15)
        path.lineTo(r.right() - r.width() * 0.15, r.bottom())
        path.lineTo(r.right() - r.width() * 0.28, r.top() + r.width() * 0.6)
        p.drawPath(path)
    elif name == "dot":
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(r.center(), r.width() * 0.32, r.width() * 0.32)
    elif name == "info":
        p.drawEllipse(r)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(r.center().x(), r.top() + r.height() * 0.26), size * 0.045, size * 0.045)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(pen)
        p.drawLine(QPointF(r.center().x(), r.center().y() - r.height() * 0.02),
                   QPointF(r.center().x(), r.bottom() - r.height() * 0.18))
    elif name == "compass":
        p.drawEllipse(r)
        needle = QPainterPath()
        needle.moveTo(r.center().x() + r.width() * 0.18, r.top() + r.height() * 0.28)
        needle.lineTo(r.center().x() - r.width() * 0.08, r.center().y() + r.height() * 0.04)
        needle.lineTo(r.center().x() - r.width() * 0.18, r.bottom() - r.height() * 0.28)
        needle.lineTo(r.center().x() + r.width() * 0.08, r.center().y() - r.height() * 0.04)
        needle.closeSubpath()
        p.drawPath(needle)
    elif name == "keyboard":
        p.drawRoundedRect(QRectF(r.left(), r.top() + r.height() * 0.15,
                                 r.width(), r.height() * 0.65), 2, 2)
        for row_i, row_y in enumerate((0.32, 0.5)):
            for col_i in range(4):
                x = r.left() + r.width() * (0.12 + col_i * 0.22)
                p.drawRect(QRectF(x, r.top() + r.height() * row_y, r.width() * 0.12, r.height() * 0.1))
        p.drawRect(QRectF(r.left() + r.width() * 0.25, r.top() + r.height() * 0.68,
                          r.width() * 0.5, r.height() * 0.1))
    elif name == "smile":
        p.drawEllipse(r)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(r.left() + r.width() * 0.33, r.top() + r.height() * 0.4), size * 0.03, size * 0.03)
        p.drawEllipse(QPointF(r.right() - r.width() * 0.33, r.top() + r.height() * 0.4), size * 0.03, size * 0.03)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(pen)
        mouth = QPainterPath()
        mouth.moveTo(r.left() + r.width() * 0.28, r.top() + r.height() * 0.6)
        mouth.quadTo(r.center().x(), r.bottom() - r.height() * 0.08,
                    r.right() - r.width() * 0.28, r.top() + r.height() * 0.6)
        p.drawPath(mouth)
    else:
        p.drawEllipse(r)

    p.end()
    return pm


# Module key → icon name used by sidebar / command palette
MODULE_ICONS = {
    "dashboard": "home",
    "tasks": "check",
    "goals": "target",
    "habits": "flame",
    "finance": "money",
    "journal": "journal",
    "notes": "note",
    "focus": "focus",
    "health": "health",
    "learning": "learning",
    "calendar": "calendar",
    "analytics": "chart",
    "settings": "settings",
}


def icon(name: str, size: int = 20, color: Optional[str] = None) -> QIcon:
    """Return a theme-aware QIcon for the given geometric icon name."""
    c = color or colors().text_primary
    return QIcon(_draw_icon(name, size, c))


def module_icon(module: str, size: int = 20, color: Optional[str] = None) -> QIcon:
    return icon(MODULE_ICONS.get(module, "home"), size, color)
