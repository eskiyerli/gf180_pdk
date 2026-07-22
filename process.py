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
# import revedaEditor.backend.dataDefinitions as ddef
from PySide6.QtWidgets import (QApplication, )
from quantiphy import Quantity

from revedaEditor.backend.pdkLoader import importPDKModule

app = QApplication.instance()

laylyr = importPDKModule("layoutLayers")
techParams = importPDKModule("gf180_mcu_tech").GF180_MCU_Tech().techParams

# common process parameters
dbu = 1000  # physical distance between two points on the layout editor, 1um/1000=1n
snapGrid = 50  # 50nm
majorGrid = 100  # 100nm
gdsUnit = Quantity("1 nm")
gdsPrecision = Quantity("1 nm")
