# 
# Revolution EDA
# 
# Copyright (c) 2026 Revolution Semiconductor
#
# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
##
import math

from PySide6.QtCore import QPoint, QPointF, QRectF
from PySide6.QtGui import QFont, QFontDatabase
from quantiphy import Quantity

import revedaEditor.common.layoutShapes as lshp
from revedaEditor.backend.pdkLoader import lazyPDKModule

laylyr = lazyPDKModule("layoutLayers")
fabproc = lazyPDKModule("process")


class baseCell(lshp.layoutPcell):
    """
    Base class for all layout parametric cells.
    """

    grid = 0.001  # layout grid in um

    def __init__(self, shapes=None):
        if shapes is None:
            shapes = []
        super().__init__(shapes)
        fixedPitchFamilies = [
            font for font in QFontDatabase().families()
            if QFontDatabase().isFixedPitch(font)
        ]
        if fixedPitchFamilies:
            self._fixedFont = QFont(fixedPitchFamilies[0], 4)
        else:
            self._fixedFont = QFont("Monospace", 4)
        self._labelFontStyle = self._fixedFont.styleName()
        self._labelFontFamily = self._fixedFont.family()
        self._labelFontSize = self._fixedFont.pointSize()
        self._labelFontTuple = (
            self._labelFontFamily,
            self._labelFontStyle,
            self._labelFontSize,
        )

    @classmethod
    def GridFix(cls, value):
        """Round a micrometer coordinate to the nearest layout grid point."""
        return round(value / cls.grid) * cls.grid

    @staticmethod
    def toSceneCoord(point: QPointF) -> QPoint:
        point *= fabproc.dbu
        return QPoint(round(point.x()), round(point.y()))

    @staticmethod
    def toLayoutCoord(point: QPoint) -> QPointF:
        point /= fabproc.dbu
        return point.toPointF()

    @staticmethod
    def toSceneDimension(value: float) -> int:
        return round(value * fabproc.dbu)

    @staticmethod
    def toLayoutDimension(value: int) -> float:
        return value / fabproc.dbu

    @staticmethod
    def _meters(value) -> float:
        """Coerce a string/Quantity/number to a float in SI meters."""
        return Quantity(value).real

    def _microns(self, value) -> float:
        return self._meters(value) * 1e6

    def _rect(self, layer, x1, y1, x2, y2):
        """layoutRect from micrometer coordinates, normalized and grid-fixed."""
        xa, xb = sorted((self.GridFix(x1), self.GridFix(x2)))
        ya, yb = sorted((self.GridFix(y1), self.GridFix(y2)))
        return lshp.layoutRect(
            self.toSceneCoord(QPointF(xa, ya)),
            self.toSceneCoord(QPointF(xb, yb)),
            layer,
        )

    def _pin(self, layer, name, x1, y1, x2, y2):
        """layoutPin from micrometer coordinates on the given layer."""
        xa, xb = sorted((self.GridFix(x1), self.GridFix(x2)))
        ya, yb = sorted((self.GridFix(y1), self.GridFix(y2)))
        return lshp.layoutPin(
            self.toSceneCoord(QPointF(xa, ya)),
            self.toSceneCoord(QPointF(xb, yb)),
            name,
            lshp.layoutPin.pinDirs[2],
            lshp.layoutPin.pinTypes[0],
            layer,
        )

    def _label(self, layer, name, x1, y1, x2, y2):
        """layoutLabel centered on the micrometer box."""
        point1 = self.toSceneCoord(QPointF(self.GridFix(x1), self.GridFix(y1)))
        point2 = self.toSceneCoord(QPointF(self.GridFix(x2), self.GridFix(y2)))
        center = QRectF(point1, point2).center().toPoint()
        return lshp.layoutLabel(
            center,
            name,
            *self._labelFontTuple,
            lshp.layoutLabel.LABEL_ALIGNMENTS[0],
            lshp.layoutLabel.LABEL_ORIENTS[0],
            layer,
        )

    def contactArray(self, contLayer, xl, yl, xh, yh, enclosure,
                     size=.22, spacing=.25):
        """Maximum centered contact-cut array fitting the box.

        ``enclosure`` is applied on every edge; cuts are ``size`` squares with
        at least ``spacing`` between them, with residual space split evenly to
        both edges. Returns a list of layoutRect cuts (possibly empty).
        """
        shapes = []
        # 1e-9 um slack absorbs float error on exact-fit boxes (e.g. a
        # 0.36 um landing minus 2*0.07 enclosure underflows 0.22 um by
        # ~3e-17); GridFix still snaps every cut to the same position.
        slack = 1e-9
        w = xh - xl - 2 * enclosure
        h = yh - yl - 2 * enclosure
        if w < size - slack or h < size - slack:
            return shapes
        nx = 1 + int(math.floor((w - size + slack) / (size + spacing)))
        ny = 1 + int(math.floor((h - size + slack) / (size + spacing)))
        margin_x = (w - nx * size - (nx - 1) * spacing) / 2
        margin_y = (h - ny * size - (ny - 1) * spacing) / 2
        for i in range(nx):
            for j in range(ny):
                x = self.GridFix(xl + enclosure + margin_x
                                 + i * (size + spacing))
                y = self.GridFix(yl + enclosure + margin_y
                                 + j * (size + spacing))
                shapes.append(lshp.layoutRect(
                    self.toSceneCoord(QPointF(x, y)),
                    self.toSceneCoord(QPointF(x + size, y + size)),
                    contLayer,
                ))
        return shapes
