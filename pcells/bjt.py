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
"""Fixed-layout PCells converted from bundled GDS data.

The authoritative fixed mask layouts ship as GDS under ``pcells/data/``
(copied from the Apache-2.0 GF180MCU open PDK) and are converted to native
Revolution shapes at runtime. Currently covers the ten fixed BJT variants
and the bundled efuse cell.
"""
from functools import lru_cache
from pathlib import Path

import gdstk
from PySide6.QtCore import QPointF

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.common.layoutShapes as lshp

from .base import baseCell, laylyr


@lru_cache(maxsize=None)
def _read_fixed_gds(gds_subdir, cell_name, pin_names, label_texttypes,
                    normalize_origin):
    """Read/flatten a bundled GDS once per cell name.

    Returns ``(polygons, labels)`` where polygons are
    ``(layer, datatype, ((x, y), ...))`` tuples in micrometers and labels
    are ``(text, x, y)`` terminal labels whose text is in ``pin_names``
    and whose texttype is in ``label_texttypes``. When
    ``normalize_origin`` is set, all geometry is translated so the
    bounding-box lower-left corner sits at the origin.
    """
    path = (Path(__file__).parent / "data" / gds_subdir
            / f"{cell_name}.gds")
    library = gdstk.read_gds(str(path))
    top = library.top_level()
    if len(top) != 1:
        raise ValueError(
            f"{cell_name}: expected one top-level cell in {path}, "
            f"found {[cell.name for cell in top]}")
    flat = top[0].copy(f"{cell_name}_flat").flatten()
    dx = dy = 0.0
    if normalize_origin:
        bbox = flat.bounding_box()
        if bbox is not None:
            (x0, y0), _ = bbox
            dx, dy = -x0, -y0
    polygons = tuple(
        (poly.layer, poly.datatype,
         tuple((x + dx, y + dy) for x, y in poly.points))
        for poly in flat.polygons)
    labels = tuple(
        (label.text, label.origin[0] + dx, label.origin[1] + dy)
        for label in flat.labels
        if label.text in pin_names
        and label.texttype in label_texttypes)
    return polygons, labels


class _fixedGdsCell(baseCell):
    """Converts a bundled fixed GDS layout into native PCell shapes."""

    cell_name = ""
    pin_names = ()

    metal1_gds = (34, 0)
    gds_subdir = ""
    label_texttypes = (0,)
    normalize_origin = False

    def __init__(self):
        super().__init__([])
        self.shapes = self._generate()

    def __call__(self):
        self.shapes = self._generate()
        return self

    def _gds_data(self):
        """Read/flatten the bundled GDS for ``self.cell_name`` (cached).

        Delegates to the module-level ``_read_fixed_gds`` cache so the
        lookup honors an instance-level ``cell_name`` (used by the generic
        ``npn_bjt``/``pnp_bjt`` classes) while each underlying GDS file is
        still parsed only once.
        """
        return _read_fixed_gds(
            self.gds_subdir, self.cell_name, self.pin_names,
            self.label_texttypes, self.normalize_origin)

    def _generate(self):
        polygons, term_labels = self._gds_data()
        shapes = []
        m1_polys = []
        for gds_layer, datatype, points in polygons:
            layer = ddef.layLayer.filterByGDSLayer(
                laylyr.pdkAllLayers, gds_layer, datatype)
            if layer.gdsLayer != gds_layer or layer.datatype != datatype:
                raise ValueError(
                    f"{self.cell_name}: no PDK layer for GDS "
                    f"{gds_layer}/{datatype}")
            scene_pts = [self.toSceneCoord(QPointF(x, y)) for x, y in points]
            shapes.append(lshp.layoutPolygon(scene_pts, layer))
            if (gds_layer, datatype) == self.metal1_gds:
                xs = [x for x, _ in points]
                ys = [y for _, y in points]
                m1_polys.append((min(xs), min(ys), max(xs), max(ys)))

        seen = set()
        for text, lx, ly in term_labels:
            candidates = [bb for bb in m1_polys
                          if bb[0] <= lx <= bb[2] and bb[1] <= ly <= bb[3]]
            if not candidates:
                continue
            x1, y1, x2, y2 = min(
                candidates, key=lambda bb: (bb[2] - bb[0]) * (bb[3] - bb[1]))
            key = (text, x1, y1, x2, y2)
            if key in seen:
                continue
            seen.add(key)
            shapes.append(self._pin(
                laylyr.Metal1_drawing, text, x1, y1, x2, y2))
            shapes.append(self._label(
                laylyr.Metal1_Label_drawing, text, x1, y1, x2, y2))

        found = {key[0] for key in seen}
        missing = [name for name in self.pin_names if name not in found]
        if missing:
            raise ValueError(
                f"{self.cell_name}: no Metal1 footprint for pins {missing}")
        return shapes


class _fixedBjt(_fixedGdsCell):
    """Fixed BJT PCell backed by a bundled GDS under ``data/bjt/``."""

    gds_subdir = "bjt"


class vnpn_10x10(_fixedBjt):
    cell_name = "vnpn_10x10"
    pin_names = ("C", "B", "E", "S")


class vnpn_5x5(_fixedBjt):
    cell_name = "vnpn_5x5"
    pin_names = ("C", "B", "E", "S")


class vnpn_0p54x16(_fixedBjt):
    cell_name = "vnpn_0p54x16"
    pin_names = ("C", "B", "E", "S")


class vnpn_0p54x8(_fixedBjt):
    cell_name = "vnpn_0p54x8"
    pin_names = ("C", "B", "E", "S")


class vnpn_0p54x4(_fixedBjt):
    cell_name = "vnpn_0p54x4"
    pin_names = ("C", "B", "E", "S")


class vnpn_0p54x2(_fixedBjt):
    cell_name = "vnpn_0p54x2"
    pin_names = ("C", "B", "E", "S")


class vpnp_10x10(_fixedBjt):
    cell_name = "vpnp_10x10"
    pin_names = ("C", "B", "E")


class vpnp_5x5(_fixedBjt):
    cell_name = "vpnp_5x5"
    pin_names = ("C", "B", "E")


class vpnp_0p42x10(_fixedBjt):
    cell_name = "vpnp_0p42x10"
    pin_names = ("C", "B", "E")


class vpnp_0p42x5(_fixedBjt):
    cell_name = "vpnp_0p42x5"
    pin_names = ("C", "B", "E")


class _genericBjt(_fixedBjt):
    """Parameterized fixed BJT matching the upstream generic generators.

    ``Type`` selects one of the bundled GDS layouts; the geometry and pins
    are those of the corresponding concrete PCell class.
    """

    type_choices = ()
    default_type = ""

    def __init__(self, Type=None):
        if Type is None:
            Type = self.default_type
        self.Type = self._resolve_type(Type)
        self.cell_name = self.Type
        super().__init__()

    def __call__(self, Type=None):
        if Type is None:
            Type = self.Type
        self.Type = self._resolve_type(Type)
        self.cell_name = self.Type
        self.shapes = self._generate()
        return self

    @classmethod
    def _resolve_type(cls, Type):
        Type = str(Type)
        if Type not in cls.type_choices:
            raise ValueError(
                f"Invalid {cls.__name__} Type: {Type}; "
                f"choices are {', '.join(cls.type_choices)}")
        return Type


class npn_bjt(_genericBjt):
    """Generic NPN BJT generator (upstream ``npn_bjt(Type)``).

    ``Type`` is one of the six vnpn cell names; pins are C/B/E/S.
    """

    default_type = "vnpn_10x10"
    type_choices = ("vnpn_10x10", "vnpn_5x5", "vnpn_0p54x16",
                    "vnpn_0p54x8", "vnpn_0p54x4", "vnpn_0p54x2")
    pin_names = ("C", "B", "E", "S")

    def __init__(self, Type="vnpn_10x10"):
        super().__init__(Type=Type)


class pnp_bjt(_genericBjt):
    """Generic PNP BJT generator (upstream ``pnp_bjt(Type)``).

    ``Type`` is one of the four vpnp cell names; pins are C/B/E.
    """

    default_type = "vpnp_10x10"
    type_choices = ("vpnp_10x10", "vpnp_5x5", "vpnp_0p42x10", "vpnp_0p42x5")
    pin_names = ("C", "B", "E")

    def __init__(self, Type="vpnp_10x10"):
        super().__init__(Type=Type)


class efuse(_fixedGdsCell):
    """Fixed efuse PCell backed by the bundled ``data/efuse/efuse.gds``.

    Terminal labels are on Metal1 texttype 10 and the upstream geometry is
    offset far from the origin, so it is normalized to its lower-left corner.
    """

    cell_name = "efuse"
    pin_names = ("in", "out")
    gds_subdir = "efuse"
    label_texttypes = (0, 10)
    normalize_origin = True
