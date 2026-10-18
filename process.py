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
import revedaEditor.backend.dataDefinitions as ddef
from quantiphy import Quantity

from revedaEditor.backend.pdkLoader import lazyPDKModule

laylyr = lazyPDKModule("layoutLayers")
tech = lazyPDKModule("gf180_mcu_tech")
techParams = tech.GF180_MCU_Tech().techParams

# common process parameters
dbu = 1000  # physical distance between two points on the layout editor, 1um/1000=1n
layoutScaler = 1e6 * dbu
snapGrid = 0.05  # 0.05um (50nm)
majorGrid = 0.1  # 0.1um (100nm)
gdsUnit = Quantity("1 nm")
gdsPrecision = Quantity("1 nm")

# via definitions, all distances are in um.
# class viaDefTuple(NamedTuple):
#     name: str
#     layer: layLayer
#     type: str
#     minWidth: float
#     maxWidth: float
#     minHeight: float
#     maxHeight: float
#     minSpacing: float
#     maxSpacing: float
# bottomLayer / topLayer are the two conductor layers a via stitches together,
# and bottom/topEnclosure (in um) are how far each metal must extend past the
# cut on every side.
processVias = [
    ddef.viaDefTuple(
        "contactActive",
        laylyr.Contact_drawing,
        "",
        0.22,
        0.22,
        0.22,
        0.22,
        0.25,
        10.0,
        bottomLayer=laylyr.COMP_drawing,
        topLayer=laylyr.Metal1_drawing,
        bottomEnclosure=0.07,
        topEnclosure=0.06,
    ),
    ddef.viaDefTuple(
        "contactPoly",
        laylyr.Contact_drawing,
        "",
        0.22,
        0.22,
        0.22,
        0.22,
        0.25,
        10.0,
        bottomLayer=laylyr.Poly2_drawing,
        topLayer=laylyr.Metal1_drawing,
        bottomEnclosure=0.07,
        topEnclosure=0.06,
    ),
    ddef.viaDefTuple(
        "via1",
        laylyr.Via1_drawing,
        "",
        0.26,
        0.26,
        0.26,
        0.26,
        0.26,
        10.0,
        bottomLayer=laylyr.Metal1_drawing,
        topLayer=laylyr.Metal2_drawing,
        bottomEnclosure=0.06,
        topEnclosure=0.06,
    ),
    ddef.viaDefTuple(
        "via2",
        laylyr.Via2_drawing,
        "",
        0.26,
        0.26,
        0.26,
        0.26,
        0.26,
        10.0,
        bottomLayer=laylyr.Metal2_drawing,
        topLayer=laylyr.Metal3_drawing,
        bottomEnclosure=0.06,
        topEnclosure=0.06,
    ),
    ddef.viaDefTuple(
        "via3",
        laylyr.Via3_drawing,
        "",
        0.26,
        0.26,
        0.26,
        0.26,
        0.26,
        10.0,
        bottomLayer=laylyr.Metal3_drawing,
        topLayer=laylyr.Metal4_drawing,
        bottomEnclosure=0.06,
        topEnclosure=0.06,
    ),
    ddef.viaDefTuple(
        "via4",
        laylyr.Via4_drawing,
        "",
        0.26,
        0.26,
        0.26,
        0.26,
        0.26,
        10.0,
        bottomLayer=laylyr.Metal4_drawing,
        topLayer=laylyr.Metal5_drawing,
        bottomEnclosure=0.06,
        topEnclosure=0.06,
    ),
    ddef.viaDefTuple(
        "via5",
        laylyr.Via5_drawing,
        "",
        0.26,
        0.26,
        0.26,
        0.26,
        0.26,
        10.0,
        bottomLayer=laylyr.Metal5_drawing,
        topLayer=laylyr.MetalTop_drawing,
        bottomEnclosure=0.06,
        topEnclosure=0.06,
    ),
]

processViaNames = [via.name for via in processVias]

processPaths = [
    ddef.layoutPathDefTuple(
        "nwell", laylyr.Nwell_drawing, "", 0.86, 100.0, 0.86, 1000.0, 0.60, 1000.0
    ),
    ddef.layoutPathDefTuple(
        "active", laylyr.COMP_drawing, "", 0.22, 100.0, 0.22, 1000.0, 0.28, 1000.0
    ),
    ddef.layoutPathDefTuple(
        "poly2", laylyr.Poly2_drawing, "", 0.18, 100.0, 0.18, 1000.0, 0.24, 1000.0
    ),
    ddef.layoutPathDefTuple(
        "metal1", laylyr.Metal1_drawing, "", 0.23, 100.0, 0.23, 1000.0, 0.23, 1000.0
    ),
    ddef.layoutPathDefTuple(
        "metal2", laylyr.Metal2_drawing, "", 0.28, 100.0, 0.28, 1000.0, 0.28, 1000.0
    ),
    ddef.layoutPathDefTuple(
        "metal3", laylyr.Metal3_drawing, "", 0.28, 100.0, 0.28, 1000.0, 0.28, 1000.0
    ),
    ddef.layoutPathDefTuple(
        "metal4", laylyr.Metal4_drawing, "", 0.28, 100.0, 0.28, 1000.0, 0.28, 1000.0
    ),
    ddef.layoutPathDefTuple(
        "metal5", laylyr.Metal5_drawing, "", 0.28, 100.0, 0.28, 1000.0, 0.28, 1000.0
    ),
    ddef.layoutPathDefTuple(
        "metalTop9K", laylyr.MetalTop_drawing, "", 0.36, 100.0, 0.36, 1000.0, 0.38, 1000.0
    ),
    ddef.layoutPathDefTuple(
        "metalTop11K", laylyr.MetalTop_drawing, "", 0.44, 100.0, 0.44, 1000.0, 0.46, 1000.0
    ),
    ddef.layoutPathDefTuple(
        "metalTop30K", laylyr.MetalTop_drawing, "", 1.80, 100.0, 1.80, 1000.0, 1.80, 1000.0
    ),
]
processPathNames = [path.name for path in processPaths]
