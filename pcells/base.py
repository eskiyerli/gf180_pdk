import revedaEditor.common.layoutShapes as lshp
from PySide6.QtGui import QFont, QFontDatabase
from revedaEditor.backend.pdkPaths import importPDKModule

gf180_mcu_tech = importPDKModule("gf180_mcu_tech")
laylyr = importPDKModule("layoutLayers")
fabproc = importPDKModule("process")


class baseCell(lshp.layoutPcell):
    """
    Base class for all layout parametric cells.
    """

    techClass = gf180_mcu_tech.GF180_MCU_Tech()
    _techParams = techClass.techParams

    def __init__(self, shapes=list):
        super().__init__(shapes)
        fontFamilies = QFontDatabase().families()
        fontFamily = [
            font for font in fontFamilies if QFontDatabase().isFixedPitch(font)
        ][0]
        self._fixedFont = QFont(fontFamily, 16)
        self._labelFontStyle = self._fixedFont.styleName()
        self._labelFontFamily = self._fixedFont.family()
        self._labelFontSize = self._fixedFont.pointSize()
        self._labelFontTuple = (
            self._labelFontFamily,
            self._labelFontStyle,
            self._labelFontSize,
        )
