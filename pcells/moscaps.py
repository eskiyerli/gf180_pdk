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
from .base import baseCell, laylyr


class _moscapBase(baseCell):
    """Shared geometry for GF180MCU MOS capacitors (LVS devices nmoscap/pmoscap).

    Parameters are total COMP W/L, matching the upstream symbol/model
    convention. The 1.06um W minimum leaves the DRC-minimum .18um Poly2 gate
    after the .44um per-side gate inset.
    """

    polarity = "n"            # "n" -> Nmoscap (Nplus), "p" -> Pmoscap (Pplus)
    voltage = "3.3V"          # "3.3V" | "6V"
    default_w = "1.06u"
    default_l = "1u"
    min_w_um = 1.06
    min_l_um = 1.0

    comp_layer = laylyr.COMP_drawing
    poly_layer = laylyr.Poly2_drawing
    poly_label_layer = laylyr.Poly2_Label_drawing
    nplus_layer = laylyr.Nplus_drawing
    pplus_layer = laylyr.Pplus_drawing
    cont_layer = laylyr.Contact_drawing
    metal1_layer = laylyr.Metal1_drawing
    metal1_label_layer = laylyr.Metal1_Label_drawing
    nwell_layer = laylyr.Nwell_drawing
    dualgate_layer = laylyr.Dualgate_drawing
    moscap_mk_layer = laylyr.MOS_CAP_MK_drawing

    gate_inset = .44       # poly inset from each COMP body edge (x)
    gate_y_ext = .46       # poly/implant extension past body in y
    impl_enc = .16         # implant enclosure of body in x
    bulk_w = .34           # bulk contact stripe width
    cont_size = .22
    cont_spacing = .25
    cont_enc = .07         # contact enclosure on active
    nwell_enc = .60        # Nwell enclosure (pmoscap)
    dg_x_enc = .96         # Dualgate x enclosure (6V)
    dg_y_enc = 1.36        # Dualgate y enclosure (6V)

    def __init__(self, w=default_w, l=default_l):
        self.w = self._meters(w)
        self.l = self._meters(l)
        super().__init__([])

    def __call__(self, w, l):
        w_um = max(self._microns(w), self.min_w_um)
        l_um = max(self._microns(l), self.min_l_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.shapes = self._generate(w_um, l_um)
        return self

    def _generate(self, w_um, l_um):
        implant = (self.nplus_layer if self.polarity == "n"
                   else self.pplus_layer)
        shapes = []

        shapes.append(self._rect(self.comp_layer, 0, 0, w_um, l_um))
        shapes.append(self._rect(
            implant, -self.impl_enc, -self.gate_y_ext,
            w_um + self.impl_enc, l_um + self.gate_y_ext))

        # Poly2 gate
        gx1 = self.gate_inset
        gx2 = w_um - self.gate_inset
        gy1 = -self.gate_y_ext
        gy2 = l_um + self.gate_y_ext
        shapes.append(self._rect(self.poly_layer, gx1, gy1, gx2, gy2))
        shapes.append(self._pin(self.poly_layer, "G", gx1, gy1, gx2, gy2))
        shapes.append(self._label(
            self.poly_label_layer, "G", gx1, gy1, gx2, gy2))

        # bulk/source contact stripes inside COMP (B pins on both)
        first = True
        for x1, x2 in ((0, self.bulk_w), (w_um - self.bulk_w, w_um)):
            shapes.append(self._rect(self.metal1_layer, x1, 0, x2, l_um))
            shapes.extend(self.contactArray(
                self.cont_layer, x1, 0, x2, l_um,
                self.cont_enc, self.cont_size, self.cont_spacing))
            shapes.append(self._pin(self.metal1_layer, "B", x1, 0, x2, l_um))
            if first:
                shapes.append(self._label(
                    self.metal1_label_layer, "B", x1, 0, x2, l_um))
                first = False

        shapes.append(self._rect(
            self.moscap_mk_layer, -self.impl_enc, -self.gate_y_ext,
            w_um + self.impl_enc, l_um + self.gate_y_ext))

        if self.polarity == "p":
            shapes.append(self._rect(
                self.nwell_layer, -self.nwell_enc, -self.nwell_enc,
                w_um + self.nwell_enc, l_um + self.nwell_enc))
        if self.voltage == "6V":
            shapes.append(self._rect(
                self.dualgate_layer, -self.dg_x_enc, -self.dg_y_enc,
                w_um + self.dg_x_enc, l_um + self.dg_y_enc))
        return shapes


class nmoscap_3p3(_moscapBase):
    polarity = "n"
    voltage = "3.3V"


class nmoscap_6p0(_moscapBase):
    polarity = "n"
    voltage = "6V"


class pmoscap_3p3(_moscapBase):
    polarity = "p"
    voltage = "3.3V"


class pmoscap_6p0(_moscapBase):
    polarity = "p"
    voltage = "6V"


def _number_spc_contacts(box_width, min_enc, cont_spacing, cont_width):
    """Port of upstream draw_moscap.number_spc_contacts (microns).

    Returns (number_of_cuts, free_space) for a contact array inside a box of
    width ``box_width`` with ``min_enc`` edge enclosure.
    """
    spc_cont = box_width - 2 * min_enc
    num_cont = int((spc_cont + cont_spacing) / (cont_width + cont_spacing))
    free_spc = box_width - (num_cont * cont_width
                            + (num_cont - 1) * cont_spacing)
    return num_cont, free_spc


class _genericMoscapBase(baseCell):
    """Shared helpers for the upstream-faithful generic MOSCAP PCells.

    These classes reproduce the upstream KLayout generators (moscap.py /
    draw_moscap.py) including their option surface, so the upstream w>=0.22u /
    l>=0.36u minima apply (the simplified concrete classes above need
    w>=1.06u because they omit the gate contact rings).
    """

    polarity = "n"            # "n" -> Nplus body implant, "p" -> Pplus
    default_w = "0.22u"
    default_l = "0.36u"
    min_w_um = .22
    min_l_um = .36
    volt_choices = ("3.3V", "5/6V")

    comp_layer = laylyr.COMP_drawing
    poly_layer = laylyr.Poly2_drawing
    poly_label_layer = laylyr.Poly2_Label_drawing
    nplus_layer = laylyr.Nplus_drawing
    pplus_layer = laylyr.Pplus_drawing
    cont_layer = laylyr.Contact_drawing
    metal1_layer = laylyr.Metal1_drawing
    metal1_label_layer = laylyr.Metal1_Label_drawing
    nwell_layer = laylyr.Nwell_drawing
    lvpwell_layer = laylyr.LVPWELL_drawing
    dnwell_layer = laylyr.DNWELL_drawing
    dualgate_layer = laylyr.Dualgate_drawing
    moscap_mk_layer = laylyr.MOS_CAP_MK_drawing

    cont_size = .22
    cont_spacing = .25

    @staticmethod
    def _to_bool(value):
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)

    @classmethod
    def _check_volt(cls, volt):
        volt = str(volt)
        if volt in ("5V", "6V"):      # tolerate single-rail spellings
            volt = "5/6V"
        if volt not in cls.volt_choices:
            raise ValueError(f"Unsupported volt option: {volt}")
        return volt

    def _rectNZ(self, layer, x1, y1, x2, y2):
        """Rect that disappears when the upstream box would be degenerate.

        Upstream emits possibly-inverted pya.Boxes at the minimum w (e.g. the
        gate opening at w=0.22u); these become empty in KLayout, so here they
        are skipped instead of normalized into small real boxes.
        """
        if x2 <= x1 or y2 <= y1:
            return None
        return self._rect(layer, x1, y1, x2, y2)

    def _num_spc(self, box_width, min_enc):
        num, free = _number_spc_contacts(
            box_width, min_enc, self.cont_spacing, self.cont_size)
        return max(num, 0), free

    def _contArrayAt(self, x0, y0, nx, ny):
        """Contact cuts starting at lower-left (x0, y0), nx by ny."""
        shapes = []
        for i in range(nx):
            for j in range(ny):
                x = self.GridFix(
                    x0 + i * (self.cont_size + self.cont_spacing))
                y = self.GridFix(
                    y0 + j * (self.cont_size + self.cont_spacing))
                shapes.append(self._rect(
                    self.cont_layer, x, y,
                    x + self.cont_size, y + self.cont_size))
        return shapes

    def _contArrayBox(self, x1, y1, x2, y2, enc_x, enc_y):
        """Contact array in a box with per-axis enclosure (upstream pattern)."""
        nx, fx = self._num_spc(x2 - x1, enc_x)
        ny, fy = self._num_spc(y2 - y1, enc_y)
        return self._contArrayAt(x1 + fx / 2, y1 + fy / 2, nx, ny)

    def _ring(self, layer, ix1, iy1, ix2, iy2, ox1, oy1, ox2, oy2):
        """Hollow ring between an inner and an outer box, as four rects.

        Approximates the upstream ``pya.Region(outer) - pya.Region(inner)``
        guard rings; coverage is identical for axis-aligned boxes.
        """
        return [
            self._rect(layer, ox1, oy1, ix1, oy2),   # left
            self._rect(layer, ix2, oy1, ox2, oy2),   # right
            self._rect(layer, ix1, oy1, ix2, iy1),   # bottom
            self._rect(layer, ix1, iy2, ix2, oy2),   # top
        ]

    def _gatePin(self, shapes, gx1, gy1, gx2, gy2):
        """G pin + label on the Poly2 gate box (skipped when degenerate)."""
        if gx2 <= gx1 or gy2 <= gy1:
            return
        shapes.append(self._pin(self.poly_layer, "G", gx1, gy1, gx2, gy2))
        shapes.append(self._label(
            self.poly_label_layer, "G", gx1, gy1, gx2, gy2))


class nmoscap(_genericMoscapBase):
    """Generic NMOS capacitor (outside DNWELL), upstream ``nmoscap`` generator.

    Faithful port of upstream ``draw_nmoscap``: n+ COMP body, Poly2 gate,
    Metal1 bulk straps left/right plus a poly metal plate, contact arrays for
    bulk (left/right columns) and gate (top/bottom strips), MOS_CAP_MK marker,
    LVPWELL; ``deepnwell`` adds a p+ guard ring, LVPWELL and DNWELL, and
    ``pcmpgr`` adds a second p+ guard ring outside DNWELL. ``volt='5/6V'``
    adds Dualgate with upstream enclosures.

    Deviations from upstream:
    * Region-subtracted guard rings are drawn as four non-overlapping
      rectangles (identical coverage for axis-aligned boxes).
    * Upstream inverted/degenerate boxes (e.g. gate opening at w=0.22u) are
      skipped instead of emitted.
    """

    polarity = "n"

    def __init__(self, w="0.22u", l="0.36u", volt="3.3V",
                 deepnwell=False, pcmpgr=False):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.volt = self._check_volt(volt)
        self.deepnwell = self._to_bool(deepnwell)
        self.pcmpgr = self._to_bool(pcmpgr)
        super().__init__([])

    def __call__(self, w="0.22u", l="0.36u", volt="3.3V",
                 deepnwell=False, pcmpgr=False):
        w_um = max(self._microns(w), self.min_w_um)
        l_um = max(self._microns(l), self.min_l_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.volt = self._check_volt(volt)
        self.deepnwell = self._to_bool(deepnwell)
        self.pcmpgr = self._to_bool(pcmpgr)
        self.shapes = self._generate(w_um, l_um)
        return self

    def _generate(self, cmp_w, cmp_l):
        hv = self.volt == "5/6V"
        # upstream draw_nmoscap constants, um
        poly_ext = .46
        implant_cmp_enc = .16
        cmp_poly_enc = .44
        cont_size = self.cont_size
        cont_min_spc = self.cont_spacing
        comp_cont_enc = .07
        met_cont_enc = .06
        metal_cmp_ext_x = .65
        metal_cmp_ext_y = .76
        met_width = 1.
        poly_met_enc_x = .21
        poly_met_enc_y = .01
        met_con_min = .34
        cmp_met_cont_enc_diff = .01
        cmp_cont_poly_spc = .17
        dual_gate_cmp_enc_x = .96
        dual_gate_cmp_enc_y = 1.36
        pcmp2ncmp_spc = .36
        ply2gr_spc = .3
        gr_w = .36
        lvpwell_enc_pcmp = .16 if hv else .12
        dnwell_enc_lvpwell = 2.5
        dg_enc_dnwell = .5
        pcmp_gr2dnw = 2.5

        shapes = []
        # diffusion + implant
        shapes.append(self._rect(self.comp_layer, 0, 0, cmp_w, cmp_l))
        shapes.append(self._rect(
            self.nplus_layer, -implant_cmp_enc, -poly_ext,
            cmp_w + implant_cmp_enc, cmp_l + poly_ext))

        # poly gate
        gx1, gy1 = cmp_poly_enc, -poly_ext
        gx2, gy2 = cmp_w - cmp_poly_enc, cmp_l + poly_ext
        shapes.append(self._rectNZ(self.poly_layer, gx1, gy1, gx2, gy2))
        self._gatePin(shapes, gx1, gy1, gx2, gy2)

        # left/right bulk straps (B terminals)
        lx1, lx2 = -metal_cmp_ext_x, -metal_cmp_ext_x + met_width
        rx1 = cmp_w + metal_cmp_ext_x - met_width
        rx2 = cmp_w + metal_cmp_ext_x
        shapes.append(self._rect(
            self.metal1_layer, lx1, -metal_cmp_ext_y, lx2, cmp_l))
        shapes.append(self._rect(
            self.metal1_layer, rx1, -metal_cmp_ext_y, rx2, cmp_l))
        shapes.append(self._pin(
            self.metal1_layer, "B", lx1, -metal_cmp_ext_y, lx2, cmp_l))
        shapes.append(self._pin(
            self.metal1_layer, "B", rx1, -metal_cmp_ext_y, rx2, cmp_l))
        shapes.append(self._label(
            self.metal1_label_layer, "B",
            lx1, -metal_cmp_ext_y, lx2, cmp_l))

        # poly metal plate over the gate
        shapes.append(self._rectNZ(
            self.metal1_layer,
            cmp_poly_enc + poly_met_enc_x, -poly_ext + poly_met_enc_y,
            cmp_w - cmp_poly_enc - poly_met_enc_x,
            cmp_l + poly_ext - poly_met_enc_y))

        # left/right bulk contact columns
        shapes.extend(self._contArrayBox(
            cmp_met_cont_enc_diff, 0,
            cmp_met_cont_enc_diff + met_con_min, cmp_l,
            met_cont_enc, comp_cont_enc))
        shapes.extend(self._contArrayBox(
            cmp_w - cmp_met_cont_enc_diff - met_con_min, 0,
            cmp_w - cmp_met_cont_enc_diff, cmp_l,
            met_cont_enc, comp_cont_enc))

        # top/bottom gate contact strips (on the poly metal plate)
        nx, fx = self._num_spc(
            cmp_w - 2 * cmp_poly_enc - 2 * poly_met_enc_x, comp_cont_enc)
        ny, fy = self._num_spc(poly_ext - poly_met_enc_y, comp_cont_enc)
        shapes.extend(self._contArrayAt(
            cmp_poly_enc + poly_met_enc_x + fx / 2,
            cmp_l + cmp_cont_poly_spc, nx, ny))
        shapes.extend(self._contArrayAt(
            cmp_poly_enc + poly_met_enc_x + fx / 2,
            -poly_ext + poly_met_enc_y - cmp_cont_poly_spc + fy, nx, ny))

        # marker
        shapes.append(self._rect(
            self.moscap_mk_layer, 0, 0, cmp_w, cmp_l))

        if self.deepnwell:
            # inner p+ guard ring: comp + metal + pplus
            ix1, iy1 = -pcmp2ncmp_spc, -ply2gr_spc - poly_ext
            ix2, iy2 = cmp_w + pcmp2ncmp_spc, cmp_l + poly_ext + ply2gr_spc
            ox1, oy1 = ix1 - gr_w, iy1 - gr_w
            ox2, oy2 = ix2 + gr_w, iy2 + gr_w
            shapes.extend(self._ring(
                self.comp_layer, ix1, iy1, ix2, iy2, ox1, oy1, ox2, oy2))
            shapes.extend(self._ring(
                self.metal1_layer, ix1, iy1, ix2, iy2, ox1, oy1, ox2, oy2))
            shapes.extend(self._ring(
                self.pplus_layer,
                ix1 + implant_cmp_enc, iy1 + implant_cmp_enc,
                ix2 - implant_cmp_enc, iy2 - implant_cmp_enc,
                ox1 - implant_cmp_enc, oy1 - implant_cmp_enc,
                ox2 + implant_cmp_enc, oy2 + implant_cmp_enc))
            for x1, x2 in ((ox1, ix1), (ix2, ox2)):
                shapes.append(self._pin(
                    self.metal1_layer, "B", x1, iy1, x2, iy2))
            shapes.append(self._label(
                self.metal1_label_layer, "B", ox1, iy1, ix1, iy2))

            # guard ring contacts
            num_y, fy = self._num_spc(
                2 * (gr_w + ply2gr_spc + poly_ext) + cmp_l, comp_cont_enc)
            num_x, fx = self._num_spc(
                cmp_w + 2 * (comp_cont_enc + pcmp2ncmp_spc - cont_min_spc),
                comp_cont_enc)
            shapes.extend(self._contArrayAt(
                -pcmp2ncmp_spc - comp_cont_enc - cont_size,
                -ply2gr_spc - poly_ext - gr_w + fy / 2, 1, num_y))
            shapes.extend(self._contArrayAt(
                -pcmp2ncmp_spc + cont_min_spc - comp_cont_enc + fx / 2,
                -ply2gr_spc - poly_ext - comp_cont_enc - cont_size,
                num_x, 1))
            shapes.extend(self._contArrayAt(
                cmp_w + pcmp2ncmp_spc + comp_cont_enc,
                -ply2gr_spc - poly_ext - gr_w + fy / 2, 1, num_y))
            shapes.extend(self._contArrayAt(
                -pcmp2ncmp_spc + cont_min_spc - comp_cont_enc + fx / 2,
                cmp_l + ply2gr_spc + poly_ext + comp_cont_enc, num_x, 1))

            if self.pcmpgr:
                # second p+ guard ring outside DNWELL (comp + pplus only)
                d = gr_w + lvpwell_enc_pcmp + dnwell_enc_lvpwell + pcmp_gr2dnw
                jx1, jy1 = ix1 - d, iy1 - d
                jx2, jy2 = ix2 + d, iy2 + d
                shapes.extend(self._ring(
                    self.comp_layer, jx1, jy1, jx2, jy2,
                    jx1 - gr_w, jy1 - gr_w, jx2 + gr_w, jy2 + gr_w))
                shapes.extend(self._ring(
                    self.pplus_layer,
                    jx1 + implant_cmp_enc, jy1 + implant_cmp_enc,
                    jx2 - implant_cmp_enc, jy2 - implant_cmp_enc,
                    jx1 - gr_w - implant_cmp_enc,
                    jy1 - gr_w - implant_cmp_enc,
                    jx2 + gr_w + implant_cmp_enc,
                    jy2 + gr_w + implant_cmp_enc))

            # lvpwell + dnwell (asymmetric tops, upstream constants)
            e = lvpwell_enc_pcmp
            shapes.append(self._rect(
                self.lvpwell_layer, ox1 - e, oy1 - e,
                ox2 + e, iy2 + gr_w + e))
            d2 = e + dnwell_enc_lvpwell
            shapes.append(self._rect(
                self.dnwell_layer, ox1 - d2, oy1 - d2,
                ox2 + d2, iy2 + gr_w + d2))
        else:
            shapes.append(self._rect(
                self.lvpwell_layer, 0, 0, cmp_w, cmp_l))
            # bottom strap joining the bulk metals
            shapes.append(self._rect(
                self.metal1_layer,
                -metal_cmp_ext_x, -metal_cmp_ext_y - met_width,
                cmp_w + metal_cmp_ext_x, -metal_cmp_ext_y))

        if hv:
            if self.deepnwell:
                t = lvpwell_enc_pcmp + dnwell_enc_lvpwell + dg_enc_dnwell
                shapes.append(self._rect(
                    self.dualgate_layer,
                    -pcmp2ncmp_spc - gr_w - t,
                    -ply2gr_spc - poly_ext - gr_w - t,
                    cmp_w + pcmp2ncmp_spc + gr_w + t,
                    cmp_l + poly_ext + pcmp2ncmp_spc + gr_w + t))
            else:
                shapes.append(self._rect(
                    self.dualgate_layer,
                    -dual_gate_cmp_enc_x, -dual_gate_cmp_enc_y,
                    cmp_w + dual_gate_cmp_enc_x,
                    cmp_l + dual_gate_cmp_enc_y))
        return [s for s in shapes if s is not None]


class pmoscap(_genericMoscapBase):
    """Generic PMOS capacitor (outside DNWELL), upstream ``pmoscap`` generator.

    Faithful port of upstream ``draw_pmoscap``: p+ COMP body in Nwell, Poly2
    gate, Metal1 bulk straps plus top/bottom gate plates, n+ Nwell guard
    ring with contacts, MOS_CAP_MK marker; ``deepnwell`` replaces Nwell by
    DNWELL and ``pcmpgr`` adds an outer p+ guard ring. ``volt='5/6V'`` adds
    Dualgate with upstream enclosures.

    Deviations: same ring-rect and degenerate-box handling as ``nmoscap``.
    """

    polarity = "p"

    def __init__(self, w="0.22u", l="0.36u", volt="3.3V",
                 deepnwell=False, pcmpgr=False):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.volt = self._check_volt(volt)
        self.deepnwell = self._to_bool(deepnwell)
        self.pcmpgr = self._to_bool(pcmpgr)
        super().__init__([])

    def __call__(self, w="0.22u", l="0.36u", volt="3.3V",
                 deepnwell=False, pcmpgr=False):
        w_um = max(self._microns(w), self.min_w_um)
        l_um = max(self._microns(l), self.min_l_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.volt = self._check_volt(volt)
        self.deepnwell = self._to_bool(deepnwell)
        self.pcmpgr = self._to_bool(pcmpgr)
        self.shapes = self._generate(w_um, l_um)
        return self

    def _generate(self, cmp_w, cmp_l):
        hv = self.volt == "5/6V"
        # upstream draw_pmoscap constants, um
        poly_ext = .46
        implant_cmp_enc = .16
        cmp_poly_enc = .44
        comp_cont_enc = .07
        met_cont_enc = .06
        metal_cmp_ext_x = .65
        met_width = 1.
        poly_met_enc_x = .19
        poly_met_enc_y = .01
        met_con_min = .34
        cmp_met_cont_enc_diff = .01
        gr_width = .36
        ncmp_pcmp_spc = .36
        poly_ncmp_spc = .3
        nwell_cmp_enc = .16
        cmp_met_spc = .11
        cont_spc_gr = .11
        dual_gate_cmp_enc_x = .96
        dual_gate_cmp_enc_y = 1.36
        dnwell_enc_ncmp = .66 if hv else .62
        dg_enc_dnwell = .5
        pcmp_gr2dnw = 2.5

        shapes = []
        # diffusion + implant
        shapes.append(self._rect(self.comp_layer, 0, 0, cmp_w, cmp_l))
        shapes.append(self._rect(
            self.pplus_layer, -implant_cmp_enc, -poly_ext,
            cmp_w + implant_cmp_enc, cmp_l + poly_ext))

        # poly gate
        gx1, gy1 = cmp_poly_enc, -poly_ext
        gx2, gy2 = cmp_w - cmp_poly_enc, cmp_l + poly_ext
        shapes.append(self._rectNZ(self.poly_layer, gx1, gy1, gx2, gy2))
        self._gatePin(shapes, gx1, gy1, gx2, gy2)

        # left/right bulk straps (B terminals)
        lx1, lx2 = -ncmp_pcmp_spc - gr_width, -metal_cmp_ext_x + met_width
        rx1 = cmp_w + metal_cmp_ext_x - met_width
        rx2 = cmp_w + ncmp_pcmp_spc + gr_width
        shapes.append(self._rect(self.metal1_layer, lx1, 0, lx2, cmp_l))
        shapes.append(self._rect(self.metal1_layer, rx1, 0, rx2, cmp_l))
        shapes.append(self._pin(self.metal1_layer, "B", lx1, 0, lx2, cmp_l))
        shapes.append(self._pin(self.metal1_layer, "B", rx1, 0, rx2, cmp_l))
        shapes.append(self._label(
            self.metal1_label_layer, "B", lx1, 0, lx2, cmp_l))

        # top/bottom gate metal plates
        px1, px2 = (cmp_poly_enc + poly_met_enc_x,
                    cmp_w - cmp_poly_enc - poly_met_enc_x)
        shapes.append(self._rectNZ(
            self.metal1_layer, px1, cmp_l + cmp_met_spc,
            px2, cmp_l + poly_ext - poly_met_enc_y))
        shapes.append(self._rectNZ(
            self.metal1_layer, px1, -poly_ext + poly_met_enc_y,
            px2, -cmp_met_spc))

        # left/right bulk contact columns
        shapes.extend(self._contArrayBox(
            cmp_met_cont_enc_diff, 0,
            cmp_met_cont_enc_diff + met_con_min, cmp_l,
            met_cont_enc, comp_cont_enc))
        shapes.extend(self._contArrayBox(
            cmp_w - cmp_met_cont_enc_diff - met_con_min, 0,
            cmp_w - cmp_met_cont_enc_diff, cmp_l,
            met_cont_enc, comp_cont_enc))

        # top/bottom gate contacts inside the plates
        nx, fx = self._num_spc(
            cmp_w - 2 * cmp_poly_enc - 2 * poly_met_enc_x, met_cont_enc)
        ny, fy = self._num_spc(met_con_min, met_cont_enc)
        shapes.extend(self._contArrayAt(
            px1 + fx / 2, cmp_l + cmp_met_spc + fy / 2, nx, ny))
        shapes.extend(self._contArrayAt(
            px1 + fx / 2, -poly_ext + poly_met_enc_y + fy / 2, nx, ny))

        # n+ Nwell guard ring: left/right/top/bottom comp + nplus + metal.
        ring_segs = [
            (-ncmp_pcmp_spc - gr_width, -poly_ext - poly_ncmp_spc,
             -ncmp_pcmp_spc, cmp_l + poly_ext + poly_ncmp_spc),        # left
            (cmp_w + ncmp_pcmp_spc, -poly_ext - poly_ncmp_spc,
             cmp_w + ncmp_pcmp_spc + gr_width,
             cmp_l + poly_ext + poly_ncmp_spc),                        # right
            (-ncmp_pcmp_spc - gr_width, cmp_l + poly_ext + poly_ncmp_spc,
             cmp_w + ncmp_pcmp_spc + gr_width,
             cmp_l + poly_ext + poly_ncmp_spc + gr_width),             # top
            (-ncmp_pcmp_spc - gr_width,
             -poly_ext - poly_ncmp_spc - gr_width,
             cmp_w + ncmp_pcmp_spc + gr_width,
             -poly_ext - poly_ncmp_spc),                               # bottom
        ]
        # Upstream nplus deltas per side: left/right grow in x and shrink in
        # y, top/bottom grow on all sides.
        nplus_delta = [
            (-implant_cmp_enc, implant_cmp_enc,
             implant_cmp_enc, -implant_cmp_enc),                       # left
            (-implant_cmp_enc, implant_cmp_enc,
             implant_cmp_enc, -implant_cmp_enc),                       # right
            (-implant_cmp_enc, -implant_cmp_enc,
             implant_cmp_enc, implant_cmp_enc),                        # top
            (-implant_cmp_enc, -implant_cmp_enc,
             implant_cmp_enc, implant_cmp_enc),                        # bottom
        ]
        for idx, (x1, y1, x2, y2) in enumerate(ring_segs):
            dx1, dy1, dx2, dy2 = nplus_delta[idx]
            shapes.append(self._rect(self.comp_layer, x1, y1, x2, y2))
            shapes.append(self._rect(
                self.nplus_layer,
                x1 + dx1, y1 + dy1, x2 + dx2, y2 + dy2))
            shapes.append(self._rect(self.metal1_layer, x1, y1, x2, y2))
            shapes.append(self._pin(self.metal1_layer, "B", x1, y1, x2, y2))
            if idx == 0:
                shapes.append(self._label(
                    self.metal1_label_layer, "B", x1, y1, x2, y2))

        # guard ring contacts
        nx1, fx1 = self._num_spc(gr_width, comp_cont_enc)
        ny1, fy1 = self._num_spc(
            cmp_l + 2 * poly_ext + 2 * poly_ncmp_spc - 2 * cont_spc_gr,
            comp_cont_enc)
        shapes.extend(self._contArrayAt(
            -ncmp_pcmp_spc - gr_width + fx1 / 2,
            cont_spc_gr - poly_ext - poly_ncmp_spc + fy1 / 2, nx1, ny1))
        shapes.extend(self._contArrayAt(
            cmp_w + ncmp_pcmp_spc + fx1 / 2,
            cont_spc_gr - poly_ext - poly_ncmp_spc + fy1 / 2, nx1, ny1))
        nx2, fx2 = self._num_spc(
            cmp_w + 2 * ncmp_pcmp_spc + 2 * gr_width, comp_cont_enc)
        ny2, fy2 = self._num_spc(gr_width, comp_cont_enc)
        shapes.extend(self._contArrayAt(
            -ncmp_pcmp_spc - gr_width + comp_cont_enc,
            cmp_l + poly_ext + poly_ncmp_spc + fy2 / 2, nx2, ny2))
        shapes.extend(self._contArrayAt(
            -ncmp_pcmp_spc - gr_width + comp_cont_enc,
            -poly_ext - poly_ncmp_spc - gr_width + fy2 / 2, nx2, ny2))

        # marker
        shapes.append(self._rect(
            self.moscap_mk_layer, 0, 0, cmp_w, cmp_l))

        if self.deepnwell:
            dn = dnwell_enc_ncmp
            shapes.append(self._rect(
                self.dnwell_layer,
                -ncmp_pcmp_spc - gr_width - dn,
                -poly_ext - poly_ncmp_spc - gr_width - dn,
                cmp_w + ncmp_pcmp_spc + gr_width + dn,
                cmp_l + poly_ext + poly_ncmp_spc + gr_width + dn))
            if self.pcmpgr:
                # outer p+ guard ring beyond DNWELL (comp + pplus only)
                d = ncmp_pcmp_spc + gr_width + dn + pcmp_gr2dnw
                dt = poly_ext + poly_ncmp_spc + gr_width + dn + pcmp_gr2dnw
                jx1, jy1 = -d, -dt
                jx2, jy2 = cmp_w + d, cmp_l + dt
                shapes.extend(self._ring(
                    self.comp_layer, jx1, jy1, jx2, jy2,
                    jx1 - gr_width, jy1 - gr_width,
                    jx2 + gr_width, jy2 + gr_width))
                shapes.extend(self._ring(
                    self.pplus_layer,
                    jx1 + implant_cmp_enc, jy1 + implant_cmp_enc,
                    jx2 - implant_cmp_enc, jy2 - implant_cmp_enc,
                    jx1 - gr_width - implant_cmp_enc,
                    jy1 - gr_width - implant_cmp_enc,
                    jx2 + gr_width + implant_cmp_enc,
                    jy2 + gr_width + implant_cmp_enc))
        else:
            shapes.append(self._rect(
                self.nwell_layer,
                -ncmp_pcmp_spc - gr_width - nwell_cmp_enc,
                -poly_ext - poly_ncmp_spc - gr_width - nwell_cmp_enc,
                cmp_w + ncmp_pcmp_spc + gr_width + nwell_cmp_enc,
                cmp_l + poly_ext + poly_ncmp_spc + gr_width
                + nwell_cmp_enc))

        if hv:
            if self.deepnwell:
                t = dnwell_enc_ncmp + dg_enc_dnwell
                shapes.append(self._rect(
                    self.dualgate_layer,
                    -ncmp_pcmp_spc - gr_width - t,
                    -poly_ext - poly_ncmp_spc - gr_width - t,
                    cmp_w + ncmp_pcmp_spc + gr_width + t,
                    cmp_l + poly_ext + poly_ncmp_spc + gr_width + t))
            else:
                shapes.append(self._rect(
                    self.dualgate_layer,
                    -dual_gate_cmp_enc_x, -dual_gate_cmp_enc_y,
                    cmp_w + dual_gate_cmp_enc_x,
                    cmp_l + dual_gate_cmp_enc_y))
        return [s for s in shapes if s is not None]


class _moscapBBase(_genericMoscapBase):
    """Shared geometry for the inside-well upstream ``*_b`` generators."""

    polarity = "n"            # "n" -> inside Nwell, "p" -> inside Psub
    well_layer = None         # nmoscap_b overrides with Nwell

    def __init__(self, w="0.22u", l="0.36u", volt="3.3V"):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.volt = self._check_volt(volt)
        super().__init__([])

    def __call__(self, w="0.22u", l="0.36u", volt="3.3V"):
        w_um = max(self._microns(w), self.min_w_um)
        l_um = max(self._microns(l), self.min_l_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.volt = self._check_volt(volt)
        self.shapes = self._generate(w_um, l_um)
        return self

    def _generate(self, cmp_w, cmp_l):
        hv = self.volt == "5/6V"
        # upstream draw_*moscap_b constants, um
        poly_ext = .3
        cmp_poly_enc = .44
        comp_cont_enc = .07
        metal_cmp_ext_x = .59
        metal_cmp_ext_y = 2.2
        met_width = 1.
        met_con_min = .34
        cmp_met_cont_enc_diff = .01
        nwell_cmp_enc_x = .18
        nwell_cmp_enc_y = 1.38
        poly_extra_in = .27
        poly_extra_out = .9
        dualgate_cmp_enc_x = .24
        dualgate_cmp_enc_y = 1.6

        implant = (self.nplus_layer if self.polarity == "n"
                   else self.pplus_layer)

        shapes = []
        # diffusion + implant (+ Nwell for nmoscap_b)
        shapes.append(self._rect(self.comp_layer, 0, 0, cmp_w, cmp_l))
        shapes.append(self._rect(
            implant, -nwell_cmp_enc_x, -nwell_cmp_enc_y,
            cmp_w + nwell_cmp_enc_x, cmp_l + nwell_cmp_enc_y))
        if self.well_layer is not None:
            shapes.append(self._rect(
                self.well_layer, -nwell_cmp_enc_x, -nwell_cmp_enc_y,
                cmp_w + nwell_cmp_enc_x, cmp_l + nwell_cmp_enc_y))

        # poly gate
        gx1, gy1 = cmp_poly_enc, -poly_ext
        gx2, gy2 = cmp_w - cmp_poly_enc, cmp_l + poly_ext
        shapes.append(self._rectNZ(self.poly_layer, gx1, gy1, gx2, gy2))
        self._gatePin(shapes, gx1, gy1, gx2, gy2)

        # extra poly fingers (top/bottom)
        fx1, fx2 = (cmp_poly_enc + poly_extra_in,
                    cmp_w - cmp_poly_enc - poly_extra_in)
        shapes.append(self._rectNZ(
            self.poly_layer, fx1, cmp_l + poly_ext,
            fx2, cmp_l + poly_ext + poly_extra_out))
        shapes.append(self._rectNZ(
            self.poly_layer, fx1, -poly_ext - poly_extra_out,
            fx2, -poly_ext))

        # left/right/bottom bulk straps (B terminals)
        lx1, lx2 = -metal_cmp_ext_x, -metal_cmp_ext_x + met_width
        rx1 = cmp_w + metal_cmp_ext_x - met_width
        rx2 = cmp_w + metal_cmp_ext_x
        shapes.append(self._rect(
            self.metal1_layer, lx1, -metal_cmp_ext_y, lx2, cmp_l))
        shapes.append(self._rect(
            self.metal1_layer, rx1, -metal_cmp_ext_y - met_width,
            rx2, cmp_l))
        shapes.append(self._rect(
            self.metal1_layer, lx1, -metal_cmp_ext_y - met_width,
            rx2, -metal_cmp_ext_y))
        shapes.append(self._pin(
            self.metal1_layer, "B", lx1, -metal_cmp_ext_y, lx2, cmp_l))
        shapes.append(self._pin(
            self.metal1_layer, "B", rx1,
            -metal_cmp_ext_y - met_width, rx2, cmp_l))
        shapes.append(self._pin(
            self.metal1_layer, "B", lx1, -metal_cmp_ext_y - met_width,
            rx2, -metal_cmp_ext_y))
        shapes.append(self._label(
            self.metal1_label_layer, "B",
            lx1, -metal_cmp_ext_y, lx2, cmp_l))

        # poly metal plate
        shapes.append(self._rectNZ(
            self.metal1_layer, fx1, -poly_ext - poly_extra_out,
            fx2, cmp_l + poly_ext + poly_extra_out))

        # left/right bulk contact columns
        shapes.extend(self._contArrayBox(
            cmp_met_cont_enc_diff, 0,
            cmp_met_cont_enc_diff + met_con_min, cmp_l,
            comp_cont_enc, comp_cont_enc))
        shapes.extend(self._contArrayBox(
            cmp_w - cmp_met_cont_enc_diff - met_con_min, 0,
            cmp_w - cmp_met_cont_enc_diff, cmp_l,
            comp_cont_enc, comp_cont_enc))

        # top/bottom poly contacts on the extra fingers
        nx, fx = self._num_spc(
            cmp_w - 2 * cmp_poly_enc - 2 * poly_extra_in, comp_cont_enc)
        ny, fy = self._num_spc(poly_extra_out, comp_cont_enc)
        shapes.extend(self._contArrayAt(
            cmp_poly_enc + poly_extra_in + fx / 2,
            cmp_l + poly_ext + fy / 2, nx, ny))
        shapes.extend(self._contArrayAt(
            cmp_poly_enc + poly_extra_in + fx / 2,
            -poly_ext - poly_extra_out + fy / 2, nx, ny))

        # marker
        shapes.append(self._rect(
            self.moscap_mk_layer, 0, 0, cmp_w, cmp_l))

        if hv:
            shapes.append(self._rect(
                self.dualgate_layer,
                -dualgate_cmp_enc_x, -dualgate_cmp_enc_y,
                cmp_w + dualgate_cmp_enc_x, cmp_l + dualgate_cmp_enc_y))
        return [s for s in shapes if s is not None]


class nmoscap_b(_moscapBBase):
    """Generic NMOS capacitor inside Nwell, upstream ``nmoscap_b`` generator.

    Faithful port of upstream ``draw_nmoscap_b``: n+ COMP body in an Nwell
    drawn with upstream enclosure, Poly2 gate with extra top/bottom fingers,
    Metal1 bulk straps and a poly metal plate, contact arrays for bulk
    (left/right columns) and gate (top/bottom strips), MOS_CAP_MK marker and
    Dualgate for ``volt='5/6V'``.
    """

    polarity = "n"
    well_layer = _genericMoscapBase.nwell_layer


class pmoscap_b(_moscapBBase):
    """Generic PMOS capacitor inside Psub, upstream ``pmoscap_b`` generator.

    Same geometry as ``nmoscap_b`` but with p+ implant and no well layer
    (device sits directly in the substrate). ``volt='5/6V'`` adds Dualgate.
    """

    polarity = "p"
    well_layer = None
