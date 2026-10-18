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


class np_3p3(baseCell):
    """GF180MCU 3.3V N+/P-sub diode (LVS device np_3p3)."""

    comp_layer = laylyr.COMP_drawing
    nplus_layer = laylyr.Nplus_drawing
    pplus_layer = laylyr.Pplus_drawing
    cont_layer = laylyr.Contact_drawing
    metal1_layer = laylyr.Metal1_drawing
    metal1_label_layer = laylyr.Metal1_Label_drawing
    diode_mk_layer = laylyr.DIODE_MK_drawing

    # geometry constants (um)
    tie_w = .36          # P tie stripe width
    sep = .48            # P-to-N active separation
    impl_enc = .16       # implant enclosure
    cont_enc = .07       # contact enclosure
    cont_size = .22
    cont_spacing = .28

    min_w_um = .36
    min_l_um = .36
    default_w = "1u"
    default_l = "1u"

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
        shapes = []
        nx1 = self.tie_w + self.sep  # N stripe left edge

        # P terminal stripe
        shapes.append(self._rect(self.comp_layer, 0, 0, self.tie_w, l_um))
        shapes.append(self._rect(
            self.pplus_layer, -self.impl_enc, -self.impl_enc,
            self.tie_w + self.impl_enc, l_um + self.impl_enc))
        shapes.append(self._rect(self.metal1_layer, 0, 0, self.tie_w, l_um))
        shapes.extend(self.contactArray(
            self.cont_layer, 0, 0, self.tie_w, l_um,
            self.cont_enc, self.cont_size, self.cont_spacing))
        shapes.append(self._pin(
            self.metal1_layer, "p", 0, 0, self.tie_w, l_um))
        shapes.append(self._label(
            self.metal1_label_layer, "p", 0, 0, self.tie_w, l_um))

        # N diode stripe
        shapes.append(self._rect(
            self.comp_layer, nx1, 0, nx1 + w_um, l_um))
        shapes.append(self._rect(
            self.nplus_layer, nx1 - self.impl_enc, -self.impl_enc,
            nx1 + w_um + self.impl_enc, l_um + self.impl_enc))
        shapes.append(self._rect(
            self.metal1_layer, nx1, 0, nx1 + w_um, l_um))
        shapes.extend(self.contactArray(
            self.cont_layer, nx1, 0, nx1 + w_um, l_um,
            self.cont_enc, self.cont_size, self.cont_spacing))
        shapes.append(self._pin(
            self.metal1_layer, "m", nx1, 0, nx1 + w_um, l_um))
        shapes.append(self._label(
            self.metal1_label_layer, "m", nx1, 0, nx1 + w_um, l_um))

        # diode marker over the union
        shapes.append(self._rect(
            self.diode_mk_layer, -self.impl_enc, -self.impl_enc,
            nx1 + w_um + self.impl_enc, l_um + self.impl_enc))
        return shapes


class dnwpw(baseCell):
    """GF180MCU DNWELL/PWELL 3.3V diode (LVS device dnwpw_3p3)."""

    lvpwell_layer = laylyr.LVPWELL_drawing
    dnwell_layer = laylyr.DNWELL_drawing
    comp_layer = laylyr.COMP_drawing
    nplus_layer = laylyr.Nplus_drawing
    pplus_layer = laylyr.Pplus_drawing
    cont_layer = laylyr.Contact_drawing
    metal1_layer = laylyr.Metal1_drawing
    metal1_label_layer = laylyr.Metal1_Label_drawing
    well_diode_mk_layer = laylyr.WELL_DIODE_MK_drawing

    # geometry constants (um)
    dnw_enc = 2.5        # DNWELL enclosure of LVPWELL
    ring_inset = .12     # P ring inset from LVPWELL edge
    ring_w = .36         # ring COMP width
    pn_sep = .32         # P-to-N active spacing
    n_ext = .56          # N stripe vertical extension
    impl_enc = .16       # implant enclosure
    cont_enc = .07       # contact enclosure
    cont_size = .22
    cont_spacing = .25

    min_w_um = 1.20
    min_l_um = 1.20
    default_w = "3u"
    default_l = "3u"

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
        shapes = []

        # wells
        shapes.append(self._rect(self.lvpwell_layer, 0, 0, w_um, l_um))
        shapes.append(self._rect(
            self.dnwell_layer, -self.dnw_enc, -self.dnw_enc,
            w_um + self.dnw_enc, l_um + self.dnw_enc))

        # P+ COMP ring (four non-overlapping segments)
        i0 = self.ring_inset
        i1 = self.ring_inset + self.ring_w
        ring_segments = [
            (i0, i0, i1, l_um - i0),                      # left
            (w_um - i1, i0, w_um - i0, l_um - i0),        # right
            (i1, i0, w_um - i1, i1),                      # bottom
            (i1, l_um - i1, w_um - i1, l_um - i0),        # top
        ]
        for idx, (x1, y1, x2, y2) in enumerate(ring_segments):
            shapes.append(self._rect(self.comp_layer, x1, y1, x2, y2))
            shapes.append(self._rect(
                self.pplus_layer, x1 - self.impl_enc, y1 - self.impl_enc,
                x2 + self.impl_enc, y2 + self.impl_enc))
            shapes.append(self._rect(self.metal1_layer, x1, y1, x2, y2))
            shapes.extend(self.contactArray(
                self.cont_layer, x1, y1, x2, y2,
                self.cont_enc, self.cont_size, self.cont_spacing))
            shapes.append(self._pin(
                self.metal1_layer, "p", x1, y1, x2, y2))
            if idx == 0:
                shapes.append(self._label(
                    self.metal1_label_layer, "p", x1, y1, x2, y2))

        # N+ tie stripe to the left of LVPWELL (DNWELL terminal)
        tx1 = i0 - self.pn_sep - self.ring_w
        tx2 = tx1 + self.ring_w
        ty1 = -self.n_ext
        ty2 = l_um + self.n_ext
        shapes.append(self._rect(self.comp_layer, tx1, ty1, tx2, ty2))
        shapes.append(self._rect(
            self.nplus_layer, tx1 - self.impl_enc, ty1 - self.impl_enc,
            tx2 + self.impl_enc, ty2 + self.impl_enc))
        shapes.append(self._rect(self.metal1_layer, tx1, ty1, tx2, ty2))
        shapes.extend(self.contactArray(
            self.cont_layer, tx1, ty1, tx2, ty2,
            self.cont_enc, self.cont_size, self.cont_spacing))
        shapes.append(self._pin(self.metal1_layer, "m", tx1, ty1, tx2, ty2))
        shapes.append(self._label(
            self.metal1_label_layer, "m", tx1, ty1, tx2, ty2))

        # well-diode marker exactly over LVPWELL
        shapes.append(self._rect(self.well_diode_mk_layer, 0, 0, w_um, l_um))
        return shapes


class _diodeBase(baseCell):
    """Shared layers/helpers for the generic upstream diode generators.

    Geometry constants and option semantics follow the GF180MCU KLayout
    reference ``draw_diode.py``; coordinates below are micrometers.
    """

    # layer bindings
    comp_layer = laylyr.COMP_drawing
    nplus_layer = laylyr.Nplus_drawing
    pplus_layer = laylyr.Pplus_drawing
    nwell_layer = laylyr.Nwell_drawing
    lvpwell_layer = laylyr.LVPWELL_drawing
    dnwell_layer = laylyr.DNWELL_drawing
    dualgate_layer = laylyr.Dualgate_drawing
    cont_layer = laylyr.Contact_drawing
    metal1_layer = laylyr.Metal1_drawing
    metal1_label_layer = laylyr.Metal1_Label_drawing
    diode_mk_layer = laylyr.DIODE_MK_drawing
    well_diode_mk_layer = laylyr.WELL_DIODE_MK_drawing
    sc_mk_layer = laylyr.Schottky_diode_drawing   # GDS 241/0, upstream sc_diode_mk

    # geometry constants (um), shared defaults
    impl_enc = .16         # implant enclosure of COMP
    cont_enc = .07         # contact enclosure by COMP landing
    cont_size = .22
    cont_spacing = .28
    pcmp_gr2dnw = 2.5      # guard-ring spacing to DNWELL
    gr_w = .36             # guard-ring COMP width (upstream ncmp_w)

    default_w = "0.22u"
    default_l = "0.36u"
    min_w_um = .22
    min_l_um = .36

    @staticmethod
    def _bool_opt(value):
        """Coerce a bool-ish pcell parameter (bool/int/str) to bool."""
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)

    @staticmethod
    def _hv(volt):
        """True when ``volt`` selects the upstream 5/6V (Dualgate) option."""
        v = str(volt).strip()
        if v == "3.3V":
            return False
        if v in ("5/6V", "5V", "6V"):
            return True
        raise ValueError(f"Unsupported diode voltage option: {volt}")

    def _contacts(self, x1, y1, x2, y2):
        """contactArray with 1e-9 um slack on the enclosure.

        baseCell.contactArray compares ``box - 2*enc < size`` in raw
        floats, so an exactly-minimum 0.36 um landing (0.22 um free) can
        underflow to 0.21999.. and yield zero cuts where upstream places
        one. The slack only shifts sub-nanometer margins; GridFix snaps
        every cut to the same integer-DBU position.
        """
        return self.contactArray(
            self.cont_layer, x1, y1, x2, y2,
            self.cont_enc - 1e-9, self.cont_size, self.cont_spacing)

    def _tap(self, shapes, impl_layer, x1, y1, x2, y2, pin=None,
             label=False, cont_box=None):
        """COMP stripe/ring segment with implant, Metal1, contacts and pin."""
        e = self.impl_enc
        shapes.append(self._rect(self.comp_layer, x1, y1, x2, y2))
        shapes.append(self._rect(
            impl_layer, x1 - e, y1 - e, x2 + e, y2 + e))
        shapes.append(self._rect(self.metal1_layer, x1, y1, x2, y2))
        cx1, cy1, cx2, cy2 = (
            cont_box if cont_box is not None else (x1, y1, x2, y2))
        shapes.extend(self._contacts(cx1, cy1, cx2, cy2))
        if pin is not None:
            shapes.append(self._pin(
                self.metal1_layer, pin, x1, y1, x2, y2))
            if label:
                shapes.append(self._label(
                    self.metal1_label_layer, pin, x1, y1, x2, y2))

    def _ring(self, layer, inner, outer):
        """Four non-overlapping rects covering ``outer`` minus ``inner``."""
        ix1, iy1, ix2, iy2 = inner
        ox1, oy1, ox2, oy2 = outer
        return [
            self._rect(layer, ox1, oy1, ix1, oy2),          # left
            self._rect(layer, ix2, oy1, ox2, oy2),          # right
            self._rect(layer, ix1, oy1, ix2, iy1),          # bottom
            self._rect(layer, ix1, iy2, ix2, oy2),          # top
        ]

    def _dnw_guard_ring(self, shapes, dnw_box):
        """Upstream P+ guard ring: COMP ring then P+ ring around ``dnw_box``."""
        g = self.pcmp_gr2dnw
        e = self.impl_enc
        w = self.gr_w
        inner = (dnw_box[0] - g, dnw_box[1] - g,
                 dnw_box[2] + g, dnw_box[3] + g)
        outer = (inner[0] - w, inner[1] - w,
                 inner[2] + w, inner[3] + w)
        shapes.extend(self._ring(self.comp_layer, inner, outer))
        pp_inner = (inner[0] + e, inner[1] + e,
                    inner[2] - e, inner[3] - e)
        pp_outer = (outer[0] - e, outer[1] - e,
                    outer[2] + e, outer[3] + e)
        shapes.extend(self._ring(self.pplus_layer, pp_inner, pp_outer))


class np_diode(_diodeBase):
    """GF180MCU N+/P-sub diode, upstream ``np_diode`` generator.

    Covers np_3p3/np_6p0 and their deep-nwell (_dw) variants via the
    ``volt``/``deepnwell``/``pcmpgr`` options. Pins: ``p`` on the P+ tie,
    ``m`` on the N+ diode stripe.
    """

    # geometry constants (um)
    tie_w = .36            # fixed P+ tie stripe width (upstream ncmp_w)
    sep = .48              # P-to-N active separation (pcmp2ncmp_spc)
    dualgate_cmp_enc = .24
    dg_enc_dnwell = .5
    dnwell_enc_lvpwell = 2.5
    lvpwell_enc_ncmp = .6
    lvpwell_enc_pcmp = .16
    min_cmp_area = .2025   # min COMP area; dog-bones the tie stripe
    cont_spacing = .28

    default_w = "0.22u"
    default_l = "0.36u"
    # upstream coerce_parameters_impl clamps w to np_l (0.36), not np_w
    min_w_um = .36
    min_l_um = .36

    def __init__(self, w=default_w, l=default_l,
                 volt="3.3V", deepnwell=False, pcmpgr=False):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.volt = str(volt)
        self.deepnwell = self._bool_opt(deepnwell)
        self.pcmpgr = self._bool_opt(pcmpgr)
        super().__init__([])

    def __call__(self, w, l, volt="3.3V", deepnwell=False, pcmpgr=False):
        w_um = max(self._microns(w), self.min_w_um)
        l_um = max(self._microns(l), self.min_l_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.volt = str(volt)
        self.deepnwell = self._bool_opt(deepnwell)
        self.pcmpgr = self._bool_opt(pcmpgr)
        self.shapes = self._generate(
            w_um, l_um, self._hv(volt), self.deepnwell, self.pcmpgr)
        return self

    def _generate(self, w_um, l_um, hv, deepnwell, pcmpgr):
        shapes = []
        e = self.impl_enc
        nw = self.tie_w
        px1 = nw + self.sep
        px2 = px1 + w_um

        # min-area dog-bone extension of the narrow tie stripe
        tv = 0.0
        if l_um * nw < self.min_cmp_area:
            tv = (self.min_cmp_area / nw - l_um) / 2

        # P+ tie stripe (p terminal); contacts stay on the unextended box
        self._tap(shapes, self.pplus_layer, 0, -tv, nw, l_um + tv,
                  pin="p", label=True, cont_box=(0, 0, nw, l_um))
        # N+ diode stripe (m terminal)
        self._tap(shapes, self.nplus_layer, px1, 0, px2, l_um,
                  pin="m", label=True)

        # Deep NWELL: LVPWELL under both stripes, DNWELL enclosure
        dnw = None
        if deepnwell:
            lvp = (-self.lvpwell_enc_pcmp, -self.lvpwell_enc_ncmp,
                   px2 + self.lvpwell_enc_ncmp, l_um + self.lvpwell_enc_ncmp)
            shapes.append(self._rect(self.lvpwell_layer, *lvp))
            de = self.dnwell_enc_lvpwell
            dnw = (lvp[0] - de, lvp[1] - de, lvp[2] + de, lvp[3] + de)
            shapes.append(self._rect(self.dnwell_layer, *dnw))
            if pcmpgr:
                self._dnw_guard_ring(shapes, dnw)

        if hv:
            mk = (-self.dualgate_cmp_enc, -self.dualgate_cmp_enc,
                  px2 + self.dualgate_cmp_enc, l_um + self.dualgate_cmp_enc)
            shapes.append(self._rect(self.diode_mk_layer, *mk))
            if deepnwell:
                ge = self.dg_enc_dnwell
                shapes.append(self._rect(
                    self.dualgate_layer,
                    dnw[0] - ge, dnw[1] - ge, dnw[2] + ge, dnw[3] + ge))
            else:
                shapes.append(self._rect(self.dualgate_layer, *mk))
        else:
            shapes.append(self._rect(
                self.diode_mk_layer, -e, -e, px2 + e, l_um + e))
        return shapes


class pn_diode(_diodeBase):
    """GF180MCU P+/Nwell diode, upstream ``pn_diode`` generator.

    Covers pn_3p3/pn_6p0 and deep-nwell (_dw) variants. Pins: ``m`` on the
    N+ Nwell tie, ``p`` on the P+ diode stripe.
    """

    tie_w = .36            # fixed N+ tie stripe width (upstream ncmp_w)
    sep = .48
    nwell_ncmp_enc = .12   # 3.3V Nwell enclosure of the tie stripe
    nwell_pcmp_enc = .43   # 3.3V Nwell enclosure elsewhere
    nwell_ncmp_enc_hv = .16
    nwell_pcmp_enc_hv = .6
    dnwell_violat_hv = .12
    dnwell_enc_nwell = .5
    dg_enc_dnwell = .5
    min_cmp_area = .2025
    cont_spacing = .28

    default_w = "0.22u"
    default_l = "0.36u"

    def __init__(self, w=default_w, l=default_l,
                 volt="3.3V", deepnwell=False, pcmpgr=False):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.volt = str(volt)
        self.deepnwell = self._bool_opt(deepnwell)
        self.pcmpgr = self._bool_opt(pcmpgr)
        super().__init__([])

    def __call__(self, w, l, volt="3.3V", deepnwell=False, pcmpgr=False):
        w_um = max(self._microns(w), self.min_w_um)
        l_um = max(self._microns(l), self.min_l_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.volt = str(volt)
        self.deepnwell = self._bool_opt(deepnwell)
        self.pcmpgr = self._bool_opt(pcmpgr)
        self.shapes = self._generate(
            w_um, l_um, self._hv(volt), self.deepnwell, self.pcmpgr)
        return self

    def _generate(self, w_um, l_um, hv, deepnwell, pcmpgr):
        shapes = []
        e = self.impl_enc
        nw = self.tie_w
        px1 = nw + self.sep
        px2 = px1 + w_um

        enc_n, enc_p, dv = (self.nwell_ncmp_enc, self.nwell_pcmp_enc, 0.0)
        if hv or deepnwell:
            enc_n, enc_p, dv = (self.nwell_ncmp_enc_hv,
                                self.nwell_pcmp_enc_hv,
                                self.dnwell_violat_hv)

        tv = 0.0
        if l_um * nw < self.min_cmp_area:
            tv = (self.min_cmp_area / nw - l_um) / 2

        # N+ Nwell tie stripe (m terminal)
        self._tap(shapes, self.nplus_layer, 0, -tv, nw, l_um + tv,
                  pin="m", label=True, cont_box=(0, 0, nw, l_um))
        # P+ diode stripe (p terminal)
        self._tap(shapes, self.pplus_layer, px1, 0, px2, l_um,
                  pin="p", label=True)

        # Nwell over the whole device
        nwl = (-enc_n - dv, -enc_p, px2 + enc_p, l_um + enc_p)
        shapes.append(self._rect(self.nwell_layer, *nwl))

        # Deep NWELL under the Nwell, optional P+ guard ring
        dnw = None
        if deepnwell:
            de = self.dnwell_enc_nwell
            dnw = (nwl[0] - de, nwl[1] - de, nwl[2] + de, nwl[3] + de)
            shapes.append(self._rect(self.dnwell_layer, *dnw))
            if pcmpgr:
                self._dnw_guard_ring(shapes, dnw)

        if hv:
            if deepnwell:
                ge = self.dg_enc_dnwell
                shapes.append(self._rect(
                    self.dualgate_layer,
                    dnw[0] - ge, dnw[1] - ge, dnw[2] + ge, dnw[3] + ge))
            else:
                shapes.append(self._rect(
                    self.dualgate_layer,
                    nwl[0] - dv, nwl[1], nwl[2], nwl[3]))

        # diode marker exactly over the P+ stripe (both voltage options)
        shapes.append(self._rect(self.diode_mk_layer, px1, 0, px2, l_um))
        return shapes


class nwp_diode(_diodeBase):
    """GF180MCU Nwell/P-sub diode, upstream ``nwp_diode`` generator.

    Covers nwp_3p3/nwp_6p0. Pins: ``p`` on the P+ substrate tie,
    ``m`` on the N+ Nwell contact stripe.
    """

    tie_w = .36
    sep = .44              # P-to-N active separation (pcmp2ncmp_spc)
    dualgate_cmp_enc = .24
    cont_spacing = .28

    default_w = "0.22u"
    default_l = "0.36u"

    def __init__(self, w=default_w, l=default_l,
                 volt="3.3V"):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.volt = str(volt)
        super().__init__([])

    def __call__(self, w, l, volt="3.3V"):
        w_um = max(self._microns(w), self.min_w_um)
        l_um = max(self._microns(l), self.min_l_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.volt = str(volt)
        self.shapes = self._generate(w_um, l_um, self._hv(volt))
        return self

    def _generate(self, w_um, l_um, hv):
        shapes = []
        e = self.impl_enc
        nw = self.tie_w
        px1 = nw + self.sep
        px2 = px1 + w_um

        # P+ substrate tie (p terminal), N+ stripe inside Nwell (m terminal)
        self._tap(shapes, self.pplus_layer, 0, 0, nw, l_um,
                  pin="p", label=True)
        self._tap(shapes, self.nplus_layer, px1, 0, px2, l_um,
                  pin="m", label=True)

        # Nwell encloses the N+ stripe by the implant enclosure
        shapes.append(self._rect(
            self.nwell_layer, px1 - e, -e, px2 + e, l_um + e))

        if hv:
            dg = (-self.dualgate_cmp_enc, -self.dualgate_cmp_enc,
                  px2 + self.dualgate_cmp_enc, l_um + self.dualgate_cmp_enc)
            shapes.append(self._rect(self.well_diode_mk_layer, *dg))
            shapes.append(self._rect(self.dualgate_layer, *dg))
        else:
            shapes.append(self._rect(
                self.well_diode_mk_layer, -e, -e, px2 + e, l_um + e))
        return shapes


class dnwpw_diode(_diodeBase):
    """GF180MCU LVPWELL/DNWELL diode, upstream ``dnwpw_diode`` generator.

    Covers dnwpw_3p3/dnwpw_6p0. ``w``/``l`` size the LVPWELL opening.
    Pins: ``p`` on the inner P+ LVPWELL ring, ``m`` on the N+ DNWELL tie
    stripe. The unconditional upstream substrate guard ring at 5 um is a
    tap ring, not a device terminal, so it carries no pin.
    """

    cmp_w = .36            # ring COMP width
    lvpwell_pcmp_enc = .12
    lvpwell_pcmp_enc_hv = .16
    pcmp2ncmp_spc = .32
    pcmp2ncmp_spc_hv = .36
    ncmp_ext = .56         # N stripe vertical extension past LVPWELL
    lvpwell_gr_spc = 5.0   # outer substrate guard-ring spacing
    cont_spc_tol = .11     # extra contact keep-off at ring corners
    dnwell_enc_lvpwell = 2.5
    dualgate_lvpwell_enc = 3.0
    cont_spacing = .25

    default_w = "0.22u"
    default_l = "0.36u"

    def __init__(self, w=default_w, l=default_l,
                 volt="3.3V"):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.volt = str(volt)
        super().__init__([])

    def __call__(self, w, l, volt="3.3V"):
        w_um = max(self._microns(w), self.min_w_um)
        l_um = max(self._microns(l), self.min_l_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.volt = str(volt)
        self.shapes = self._generate(w_um, l_um, self._hv(volt))
        return self

    def _generate(self, w_um, l_um, hv):
        shapes = []
        cw = self.cmp_w
        tol = self.cont_spc_tol
        pe = self.lvpwell_pcmp_enc_hv if hv else self.lvpwell_pcmp_enc
        spc = self.pcmp2ncmp_spc_hv if hv else self.pcmp2ncmp_spc
        gs = self.lvpwell_gr_spc

        # wells
        shapes.append(self._rect(self.lvpwell_layer, 0, 0, w_um, l_um))
        de = self.dnwell_enc_lvpwell
        shapes.append(self._rect(
            self.dnwell_layer, -de, -de, w_um + de, l_um + de))

        # inner P+ ring inside LVPWELL (p terminal)
        ring = [
            (pe, pe, pe + cw, l_um - pe),                     # left
            (w_um - pe - cw, pe, w_um - pe, l_um - pe),       # right
            (pe + cw, l_um - pe - cw, w_um - pe - cw,
             l_um - pe),                                      # top
            (pe + cw, pe, w_um - pe - cw, pe + cw),           # bottom
        ]
        for idx, (x1, y1, x2, y2) in enumerate(ring):
            cont_box = (x1, y1, x2, y2)
            if idx >= 2:   # top/bottom keep contacts tol away from corners
                cont_box = (x1 + tol, y1, x2 - tol, y2)
            self._tap(shapes, self.pplus_layer, x1, y1, x2, y2,
                      pin="p", label=(idx == 0), cont_box=cont_box)

        # N+ DNWELL tie stripe left of LVPWELL (m terminal)
        tx1 = pe - spc - cw
        tx2 = pe - spc
        self._tap(shapes, self.nplus_layer,
                  tx1, -self.ncmp_ext, tx2, l_um + self.ncmp_ext,
                  pin="m", label=True)

        # outer P+ substrate guard ring (upstream draws it unconditionally)
        gr = [
            (-gs - cw, -gs - cw, -gs, l_um + gs + cw),                # left
            (w_um + gs, -gs - cw, w_um + gs + cw, l_um + gs + cw),    # right
            (-gs, l_um + gs, w_um + gs, l_um + gs + cw),              # top
            (-gs, -gs - cw, w_um + gs, -gs),                          # bottom
        ]
        for idx, (x1, y1, x2, y2) in enumerate(gr):
            cont_box = (x1, y1, x2, y2)
            if idx >= 2:
                cont_box = (x1 + tol, y1, x2 - tol, y2)
            self._tap(shapes, self.pplus_layer, x1, y1, x2, y2,
                      pin=None, cont_box=cont_box)

        # well-diode marker exactly over LVPWELL
        shapes.append(self._rect(self.well_diode_mk_layer, 0, 0, w_um, l_um))

        if hv:
            ge = self.dualgate_lvpwell_enc
            shapes.append(self._rect(
                self.dualgate_layer, -ge, -ge, w_um + ge, l_um + ge))
        return shapes


class dnwps_diode(_diodeBase):
    """GF180MCU DNWELL/P-sub diode, upstream ``dnwps_diode`` generator.

    Covers dnwps_3p3/dnwps_6p0. ``w``/``l`` size the DNWELL opening.
    Pins: ``m`` on the inner N+ DNWELL ring, ``p`` on the outer P+
    substrate ring (the LVS ``terminal_p`` ptap).
    """

    cmp_w = .36
    dnwell_pcmp_enc = .62
    dnwell_pcmp_enc_hv = .66
    lvpwell_gr_spc = 2.5   # outer P+ ring spacing to DNWELL
    cont_spc_tol = .11
    dualgate_enc = .5      # upstream dualgate_lvpwell_enc
    impl_enc = .03         # upstream implant_comp_enc for this device
    cont_spacing = .25

    default_w = "0.22u"
    default_l = "0.36u"

    def __init__(self, w=default_w, l=default_l,
                 volt="3.3V"):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.volt = str(volt)
        super().__init__([])

    def __call__(self, w, l, volt="3.3V"):
        w_um = max(self._microns(w), self.min_w_um)
        l_um = max(self._microns(l), self.min_l_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.volt = str(volt)
        self.shapes = self._generate(w_um, l_um, self._hv(volt))
        return self

    def _generate(self, w_um, l_um, hv):
        shapes = []
        cw = self.cmp_w
        tol = self.cont_spc_tol
        pe = self.dnwell_pcmp_enc_hv if hv else self.dnwell_pcmp_enc
        gs = self.lvpwell_gr_spc

        # DNWELL
        shapes.append(self._rect(self.dnwell_layer, 0, 0, w_um, l_um))

        # inner N+ ring inside DNWELL (m terminal)
        ring = [
            (pe, pe, pe + cw, l_um - pe),
            (w_um - pe - cw, pe, w_um - pe, l_um - pe),
            (pe + cw, l_um - pe - cw, w_um - pe - cw, l_um - pe),
            (pe + cw, pe, w_um - pe - cw, pe + cw),
        ]
        for idx, (x1, y1, x2, y2) in enumerate(ring):
            cont_box = (x1, y1, x2, y2)
            if idx >= 2:
                cont_box = (x1 + tol, y1, x2 - tol, y2)
            self._tap(shapes, self.nplus_layer, x1, y1, x2, y2,
                      pin="m", label=(idx == 0), cont_box=cont_box)

        # outer P+ substrate ring (p terminal)
        gr = [
            (-gs - cw, -gs - cw, -gs, l_um + gs + cw),
            (w_um + gs, -gs - cw, w_um + gs + cw, l_um + gs + cw),
            (-gs, l_um + gs, w_um + gs, l_um + gs + cw),
            (-gs, -gs - cw, w_um + gs, -gs),
        ]
        for idx, (x1, y1, x2, y2) in enumerate(gr):
            cont_box = (x1, y1, x2, y2)
            if idx >= 2:
                cont_box = (x1 + tol, y1, x2 - tol, y2)
            self._tap(shapes, self.pplus_layer, x1, y1, x2, y2,
                      pin="p", label=(idx == 0), cont_box=cont_box)

        # well-diode marker exactly over DNWELL
        shapes.append(self._rect(self.well_diode_mk_layer, 0, 0, w_um, l_um))

        if hv:
            ge = self.dualgate_enc
            shapes.append(self._rect(
                self.dualgate_layer, -ge, -ge, w_um + ge, l_um + ge))
        return shapes


class sc_diode(_diodeBase):
    """GF180MCU Schottky diode, upstream ``sc_diode`` generator.

    ``m`` interleaved N+ fingers (pin ``N``) alternate with ``m`` bare-COMP
    Schottky fingers (pin ``P``) inside DNWELL; ``w`` is fixed at 0.62 um
    upstream. Marker is the Schottky_diode layer (GDS 241/0).
    """

    ncmp_metcmp_spc = .28  # N+ finger to Schottky finger spacing
    ncmp_w = .36           # N+ finger COMP width
    sc_w = .62             # fixed Schottky finger width
    impl_enc = .03
    cont_spacing = .25
    metcmp_min_spc = .92   # Metal1-finger pitch spacing
    met_cmp_enc_in = .23   # Metal1 extension into the bus bars
    met_ncmp_enc = .46     # bus-bar offset past the finger ends
    dnwell_cmp_enc_x = .76
    dnwell_cmp_enc_y = 1.4
    sc_mk_cmp_enc = .16
    met_conn_w = .23       # bus-bar Metal1 width

    default_w = "0.62u"
    default_l = "1u"
    default_m = "4"
    min_w_um = .62
    min_l_um = 1.0

    def __init__(self, w=default_w, l=default_l, m=default_m, pcmpgr=False):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.m = max(int(float(m)), 1)
        self.pcmpgr = self._bool_opt(pcmpgr)
        super().__init__([])

    def __call__(self, w, l, m=default_m, pcmpgr=False):
        # upstream coerces w to sc_w whenever it differs (readonly param)
        w_um = self.sc_w
        l_um = max(self._microns(l), self.min_l_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.m = max(int(float(m)), 1)
        self.pcmpgr = self._bool_opt(pcmpgr)
        self.shapes = self._generate(w_um, l_um, self.m, self.pcmpgr)
        return self

    def _generate(self, w_um, l_um, m, pcmpgr):
        shapes = []
        e = self.impl_enc
        nw = self.ncmp_w
        sw = w_um                      # coerced to sc_w
        sp = self.ncmp_metcmp_spc
        pitch = 2 * sp + sw + nw       # ncmp_min_spc + ncmp_w
        total_w = (m + 1) * nw + m * (2 * sp + sw)

        # interleaved fingers: N+ stripes on pitch, Schottky COMP between
        for i in range(m + 1):
            x = i * pitch
            shapes.append(self._rect(self.comp_layer, x, 0, x + nw, l_um))
            shapes.append(self._rect(
                self.nplus_layer, x - e, -e, x + nw + e, l_um + e))
            shapes.append(self._rect(
                self.metal1_layer, x, -self.met_cmp_enc_in,
                x + nw, l_um))
            shapes.extend(self._contacts(x, 0, x + nw, l_um))
            shapes.append(self._pin(
                self.metal1_layer, "N", x, -self.met_cmp_enc_in,
                x + nw, l_um))
            if i == 0:
                shapes.append(self._label(
                    self.metal1_label_layer, "N",
                    x, -self.met_cmp_enc_in, x + nw, l_um))
        for j in range(m):
            x = nw + sp + j * pitch
            met_y2 = l_um + (self.met_cmp_enc_in if m > 1 else 0.0)
            shapes.append(self._rect(self.comp_layer, x, 0, x + sw, l_um))
            shapes.append(self._rect(
                self.metal1_layer, x, 0, x + sw, met_y2))
            shapes.extend(self._contacts(x, 0, x + sw, l_um))
            shapes.append(self._pin(
                self.metal1_layer, "P", x, 0, x + sw, met_y2))
            if j == 0:
                shapes.append(self._label(
                    self.metal1_label_layer, "P", x, 0, x + sw, met_y2))

        # DNWELL encloses the whole finger array
        dx, dy = self.dnwell_cmp_enc_x, self.dnwell_cmp_enc_y
        dnw = (-dx, -dy, total_w + dx, l_um + dy)
        shapes.append(self._rect(self.dnwell_layer, *dnw))

        # optional P+ guard ring around the DNWELL edge
        if pcmpgr:
            self._dnw_guard_ring(shapes, dnw)

        # Schottky marker over the finger array
        se = self.sc_mk_cmp_enc
        shapes.append(self._rect(
            self.sc_mk_layer, -se, -se, total_w + se, l_um + se))

        # Metal1 bus bars: bottom shorts the N fingers, top shorts the
        # Schottky fingers (only when more than one finger exists)
        me = self.met_ncmp_enc
        mw = self.met_conn_w
        shapes.append(self._rect(
            self.metal1_layer, 0, -me, total_w, -me + mw))
        if m > 1:
            shapes.append(self._rect(
                self.metal1_layer, nw + sp, l_um + me - mw,
                total_w - nw - sp, l_um + me))
        return shapes
