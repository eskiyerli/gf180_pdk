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
from PySide6.QtCore import QPointF

import revedaEditor.common.layoutShapes as lshp
from .base import baseCell, laylyr




# ---------------------------------------------------------------------------
# Generic MOS generators
#
# Ports of upstream mos.py / draw_mos.py (KLayout PCells) for the registered
# generator names ``nmos``, ``pmos``, ``nmos_10p0_asym`` and
# ``pmos_10p0_asym``.  All geometry constants below are the upstream values
# converted to micrometers (upstream dbu = 1 nm; this PDK uses a 1 nm grid,
# so the port is geometrically identical modulo GridFix rounding of derived
# contact offsets).
# ---------------------------------------------------------------------------

_MOS_VOLT_CHOICES = ("3.3V", "5V", "6V")
_MOS_BULK_CHOICES = ("None", "Bulk Tie", "Guard Ring")

# upstream mos.py minima (um)
_MOS_3P3_L = .28
_MOS_3P3_W = .22
_MOS_56_W = .30
_NMOS_5P0_L = .60
_NMOS_6P0_L = .70
_PMOS_5P0_L = .50
_PMOS_6P0_L = .55
_MOS_GRW_MIN = .36

_LDMOS_L_MIN = .6
_LDMOS_L_MAX = 20.
_LDMOS_W_MIN = 4.
_LDMOS_W_MAX = 50.


class _upstreamMosBase(baseCell):
    """Shared helpers for the upstream draw_mos.py ports."""

    comp_layer = laylyr.COMP_drawing
    poly_layer = laylyr.Poly2_drawing
    poly_label_layer = laylyr.Poly2_Label_drawing
    nplus_layer = laylyr.Nplus_drawing
    pplus_layer = laylyr.Pplus_drawing
    cont_layer = laylyr.Contact_drawing
    metal1_layer = laylyr.Metal1_drawing
    metal1_label_layer = laylyr.Metal1_Label_drawing

    @staticmethod
    def _bool(value) -> bool:
        """Coerce a stored boolean/flag parameter."""
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)

    def _poly(self, layer, points):
        """layoutPolygon from a list of (x, y) micrometer tuples."""
        scene_pts = [
            self.toSceneCoord(QPointF(self.GridFix(x), self.GridFix(y)))
            for x, y in points
        ]
        return lshp.layoutPolygon(scene_pts, layer)

    def _frame(self, layer, xi0, yi0, xi1, yi1, width):
        """Rectangular ring polygon, upstream draw_mos.py vertex order.

        ``(xi0, yi0, xi1, yi1)`` is the ring's inner edge; the outer edge
        is the inner box grown by ``width`` on every side.
        """
        xo0, yo0 = xi0 - width, yi0 - width
        xo1, yo1 = xi1 + width, yi1 + width
        return self._poly(layer, [
            (xo0, yo0), (xo0, yi1), (xi0, yi1), (xi0, yi0),
            (xi1, yi0), (xi1, yi1), (xo0, yi1), (xo0, yo1),
            (xo1, yo1), (xo1, yo0),
        ])

    def _contacts(self, x0, y0, nx, ny, px, py, size):
        """Contact array of ``nx * ny`` cuts starting at (x0, y0).

        ``px``/``py`` are the (signed) pitch between successive cut lower
        left corners, matching the upstream CellInstArray vectors.
        """
        shapes = []
        for i in range(max(int(nx), 0)):
            for j in range(max(int(ny), 0)):
                x = x0 + i * px
                y = y0 + j * py
                shapes.append(self._rect(
                    self.cont_layer, x, y, x + size, y + size))
        return shapes


class _genericMosBase(_upstreamMosBase):
    """Port of upstream draw_nmos/draw_pmos (multi-finger, bulk options)."""

    polarity = "n"
    volt_choices = _MOS_VOLT_CHOICES
    bulk_choices = _MOS_BULK_CHOICES
    # (min_l, min_w) per operating voltage, upstream mos.py coerce rules
    volt_minima = {
        "3.3V": (_MOS_3P3_L, _MOS_3P3_W),
        "5V": (_NMOS_5P0_L, _MOS_56_W),
        "6V": (_NMOS_6P0_L, _MOS_56_W),
    }

    dnwell_layer = laylyr.DNWELL_drawing
    lvpwell_layer = laylyr.LVPWELL_drawing
    dualgate_layer = laylyr.Dualgate_drawing
    v5xtor_layer = laylyr.V5_XTOR_drawing
    nwell_layer = laylyr.Nwell_drawing

    def __init__(self, w="0.22u", l="0.28u", ld="0.44u", nf="1",
                 grw="0.36u", volt="3.3V", bulk="Bulk Tie",
                 deepnwell=False, pcmpgr=False):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.ld = self._meters(ld)
        self.nf = max(int(float(nf)), 1)
        self.grw = self._meters(grw)
        self.volt = volt
        self.bulk = bulk
        self.deepnwell = self._bool(deepnwell)
        self.pcmpgr = self._bool(pcmpgr)
        super().__init__([])

    def __call__(self, w="0.22u", l="0.28u", ld="0.44u", nf="1",
                 grw="0.36u", volt="3.3V", bulk="Bulk Tie",
                 deepnwell=False, pcmpgr=False):
        if volt not in self.volt_choices:
            raise ValueError(f"Unsupported volt option: {volt}")
        if bulk not in self.bulk_choices:
            raise ValueError(f"Unsupported bulk option: {bulk}")
        min_l, min_w = self.volt_minima[volt]
        w_um = max(self._microns(w), min_w)
        l_um = max(self._microns(l), min_l)
        ld_um = self._microns(ld)
        nf = max(int(float(nf)), 1)
        grw_um = max(self._microns(grw), _MOS_GRW_MIN)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.ld = ld_um * 1e-6
        self.nf = nf
        self.grw = grw_um * 1e-6
        self.volt = volt
        self.bulk = bulk
        self.deepnwell = self._bool(deepnwell)
        self.pcmpgr = self._bool(pcmpgr)
        self.shapes = self._generate(
            w_um, l_um, ld_um, nf, grw_um, volt, bulk,
            self.deepnwell, self.pcmpgr)
        return self

    def _generate(self, w_um, l_um, ld_um, nf, grw_um, volt, bulk,
                  deepnwell, pcmpgr):
        is_pmos = self.polarity == "p"
        is_hv = volt in ("5V", "6V")
        implant_layer = self.pplus_layer if is_pmos else self.nplus_layer
        # opposite-polarity implant for ties and guard rings
        tie_layer = self.nplus_layer if is_pmos else self.pplus_layer

        # upstream draw_mos.py constants (um)
        cmp2cont = .07
        cont_size = .22
        impl_enc = .16          # np_enc_cmp / pp_enc_cmp
        cont2ply = .15
        ply_ext = .22           # ply_ext_cmp
        impl_gate = .23         # np_enc_gate
        cont2cont = .28
        dg_enc_ply = .4
        dg_enc_cmp = .24
        metal_violat = .01
        min_cmp_area = .2025
        dg_enc_dnw = .5         # dg_enc_dnwell
        pcmp_gr2dnw = 2.5
        gr_w = .36              # fixed width of the pcmp guard ring
        # Upstream uses .28 for the 3.3V non-deepnwell case, but that puts
        # the bulk-tie/guard-ring implant edge .12 um from the opposite
        # diffusion implant and violates PP.3a/NP.3a (.16 um).  .32 is the
        # minimum deviation that lands exactly on the rule limit.
        cmp2cmp = .36 if (deepnwell or is_hv) else .32
        ply2gr = .3 if (deepnwell or is_hv) else .1
        if is_pmos:
            nwell_enc_p = .6 if is_hv else .43    # nwell_enc_pcomp
            nwell_enc_n = .16 if is_hv else .12   # nwell_enc_ncomp
            dnw_enc_n = .66 if is_hv else .62     # dnwell_enc_ncmp
            dnw_enc_p = 1.1 if is_hv else .93     # dnwell_enc_pcmp
        else:
            lvp_enc_n = .6 if is_hv else .43      # lvpwell_enc_ncmp
            lvp_enc_p = .16 if is_hv else .12     # lvpwell_enc_pcmp
            dnw_enc_lvp = 2.5                     # dnwell_enc_lvpwell

        w_min_cont = cont_size + 2 * cmp2cont     # .36
        ld_violat = 0.
        if w_um < w_min_cont and nf == 1:
            ld_violat = .22 if is_hv else .02

        pitch = ld_um + ld_violat + l_um + cont2ply - cmp2cont
        total_x = 2 * (ld_um + ld_violat) + l_um + (nf - 1) * pitch
        pyp = ply_ext + ply2gr    # guard-ring inner clearance, y

        shapes = []

        # main diffusion (dogbone landing when W fits no contact)
        w_eff = w_um
        w_changed = False
        if w_um < w_min_cont:
            dy_c = (w_min_cont - w_um) / 2
            shapes.append(self._rect(
                self.comp_layer, 0, dy_c, total_x, w_um + dy_c))
            w_eff = w_min_cont
            w_changed = True
        else:
            shapes.append(self._rect(self.comp_layer, 0, 0, total_x, w_eff))

        # implant over the whole transistor
        shapes.append(self._rect(
            implant_layer, -impl_enc, -impl_gate,
            total_x + impl_enc, w_eff + impl_gate))

        # Poly2 gates + G pins
        for i in range(nf):
            gx1 = ld_um + ld_violat + i * pitch
            gx2 = gx1 + l_um
            shapes.append(self._rect(
                self.poly_layer, gx1, -ply_ext, gx2, w_eff + ply_ext))
            shapes.append(self._pin(
                self.poly_layer, "G", gx1, -ply_ext, gx2, w_eff + ply_ext))
            if i == 0:
                shapes.append(self._label(
                    self.poly_label_layer, "G", gx1, -ply_ext, gx2,
                    w_eff + ply_ext))

        # contact array bookkeeping (upstream formulas)
        nx = int((ld_um - (cont_size + cmp2cont + cont2ply))
                 / (cont2cont + cont_size)) + 1
        ny = int((w_eff - (cont_size + 2 * cmp2cont))
                 / (cont2cont + cont_size)) + 1
        dx = ((ld_um - nx * cont_size - (nx - 1) * cont2cont)
              * cmp2cont / cont_size)
        dy = (w_eff - ny * cont_size - (ny - 1) * cont2cont) / 2

        cont_ok = nx > 0 and ny > 0
        # upstream guards S/D contacts+metals on ld >= 440 dbu
        draw_sd = cont_ok and not (w_changed and nf > 1) and ld_um >= .44
        d_labeled = False
        if draw_sd:
            # left (source) contacts + Metal1
            shapes.extend(self._contacts(
                dx, dy, nx, ny, cont_size + cont2cont,
                cont_size + cont2cont, cont_size))
            m_left = (-metal_violat, -metal_violat,
                      ld_um + metal_violat - (cont_size - 2 * cmp2cont),
                      w_eff + metal_violat)
            shapes.append(self._rect(self.metal1_layer, *m_left))
            shapes.append(self._pin(self.metal1_layer, "S", *m_left))
            shapes.append(self._label(self.metal1_label_layer, "S", *m_left))
            # right diffusion of every finger, alternating D/S
            for i in range(nf):
                cx0 = (pitch * i + 2 * (ld_um + ld_violat) + l_um
                       - cont_size - dx)
                shapes.extend(self._contacts(
                    cx0, dy, nx, ny, -(cont_size + cont2cont),
                    cont_size + cont2cont, cont_size))
                m_right = (
                    (ld_um + 2 * ld_violat + l_um + cont2ply - cmp2cont)
                    * (i + 1),
                    -metal_violat,
                    ld_um + metal_violat + ld_violat
                    + pitch * (i + 1) - (cont_size - 2 * cmp2cont),
                    w_eff + metal_violat)
                shapes.append(self._rect(self.metal1_layer, *m_right))
                pin_name = "D" if i % 2 == 0 else "S"
                shapes.append(self._pin(
                    self.metal1_layer, pin_name, *m_right))
                if pin_name == "D" and not d_labeled:
                    d_labeled = True
                    shapes.append(self._label(
                        self.metal1_label_layer, "D", *m_right))

        # extra COMP strips so the dogbone keeps contact clearance (nf == 1)
        if nf == 1 and w_changed:
            shapes.append(self._rect(
                self.comp_layer, 0, 0,
                ld_um - (cont_size - 2 * cmp2cont), w_eff))
            shapes.append(self._rect(
                self.comp_layer,
                ld_um + 2 * ld_violat + l_um + cont2ply - cmp2cont, 0,
                ld_um + ld_violat + pitch - (cont_size - 2 * cmp2cont),
                w_eff))

        def emit_marker(box):
            """5V/6V marker boxes (V5_XTOR + Dualgate / Dualgate only)."""
            if volt == "5V":
                shapes.append(self._rect(self.v5xtor_layer, *box))
                shapes.append(self._rect(self.dualgate_layer, *box))
            elif volt == "6V":
                shapes.append(self._rect(self.dualgate_layer, *box))

        def grow(box, enc):
            return (box[0] - enc, box[1] - enc,
                    box[2] + enc, box[3] + enc)

        def deepnwell_stack(well):
            """DNWELL (+ marker) over the polarity well box, plus pcmpgr."""
            dnw_box = well if is_pmos else grow(well, dnw_enc_lvp)
            shapes.append(self._rect(self.dnwell_layer, *dnw_box))
            emit_marker(grow(dnw_box, dg_enc_dnw))
            if pcmpgr:
                inner = grow(dnw_box, pcmp_gr2dnw)
                shapes.append(self._frame(
                    self.comp_layer, *inner, gr_w))
                shapes.append(self._frame(
                    tie_layer, inner[0] + impl_enc, inner[1] + impl_enc,
                    inner[2] - impl_enc, inner[3] - impl_enc,
                    gr_w + 2 * impl_enc))

        if bulk == "Bulk Tie":
            if deepnwell:
                if is_pmos:
                    deepnwell_stack((
                        -(dnw_enc_n + cmp2cmp + ld_um), -dnw_enc_p,
                        total_x + dnw_enc_p, w_eff + dnw_enc_p))
                else:
                    shapes.append(self._rect(
                        self.lvpwell_layer,
                        -(lvp_enc_p + cmp2cmp + ld_um), -lvp_enc_n,
                        total_x + lvp_enc_n, w_eff + lvp_enc_n))
                    deepnwell_stack((
                        -(lvp_enc_p + cmp2cmp + ld_um), -lvp_enc_n,
                        total_x + lvp_enc_n, w_eff + lvp_enc_n))
            else:
                emit_marker((
                    -(cmp2cmp + dg_enc_cmp) - ld_um,
                    -(dg_enc_ply + ply_ext),
                    total_x + dg_enc_cmp,
                    w_eff + dg_enc_ply + ply_ext))
                if is_pmos:
                    shapes.append(self._rect(
                        self.nwell_layer,
                        -(nwell_enc_n + cmp2cmp + ld_um), -nwell_enc_p,
                        total_x + nwell_enc_p, w_eff + nwell_enc_p))

            # bulk tie on the left (min-area COMP violation allowance)
            tie_violat = 0.
            if ld_um > 0 and w_eff * ld_um < min_cmp_area:
                tie_violat = (min_cmp_area / ld_um - w_eff) / 2 * 1.05
            tie = (-cmp2cmp - ld_um, -tie_violat,
                   -cmp2cmp, w_eff + tie_violat)
            shapes.append(self._rect(self.comp_layer, *tie))
            shapes.append(self._rect(
                tie_layer,
                -cmp2cmp - impl_enc - ld_um, -impl_enc - tie_violat,
                -cmp2cmp + impl_enc, w_eff + tie_violat + impl_enc))
            if cont_ok:
                shapes.extend(self._contacts(
                    -(cmp2cmp + cont_size) - dx * cont_size / (2 * cmp2cont),
                    dy, nx, ny, -(cont_size + cont2cont),
                    cont_size + cont2cont, cont_size))
            shapes.append(self._rect(self.metal1_layer, *tie))
            shapes.append(self._pin(self.metal1_layer, "B", *tie))
            shapes.append(self._label(self.metal1_label_layer, "B", *tie))

        elif bulk == "Guard Ring":
            if deepnwell:
                if is_pmos:
                    deepnwell_stack((
                        -(dnw_enc_n + cmp2cmp + grw_um),
                        -(dnw_enc_n + pyp + grw_um),
                        total_x + grw_um + cmp2cmp + dnw_enc_n,
                        w_eff + pyp + grw_um + dnw_enc_n))
                else:
                    shapes.append(self._rect(
                        self.lvpwell_layer,
                        -(lvp_enc_p + cmp2cmp + grw_um),
                        -(lvp_enc_p + pyp + grw_um),
                        total_x + grw_um + cmp2cmp + lvp_enc_p,
                        w_eff + pyp + grw_um + lvp_enc_p))
                    deepnwell_stack((
                        -(lvp_enc_p + cmp2cmp + grw_um),
                        -(lvp_enc_p + pyp + grw_um),
                        total_x + grw_um + cmp2cmp + lvp_enc_p,
                        w_eff + pyp + grw_um + lvp_enc_p))
            else:
                emit_marker((
                    -(cmp2cmp + dg_enc_cmp) - grw_um,
                    -(pyp + dg_enc_cmp) - grw_um,
                    total_x + grw_um + cmp2cmp + dg_enc_cmp,
                    w_eff + pyp + dg_enc_cmp + grw_um))
                if is_pmos:
                    shapes.append(self._rect(
                        self.nwell_layer,
                        -(nwell_enc_n + cmp2cmp + grw_um),
                        -(ply_ext + ply2gr + nwell_enc_n + grw_um),
                        total_x + grw_um + nwell_enc_n + cmp2cmp,
                        w_eff + ply_ext + ply2gr + nwell_enc_n + grw_um))

            # guard-ring frames: COMP and Metal1 share the same ring,
            # the tie implant ring is inset/enclosed by impl_enc
            ri = (-cmp2cmp, -pyp, total_x + cmp2cmp, w_eff + pyp)
            shapes.append(self._frame(self.comp_layer, *ri, grw_um))
            shapes.append(self._frame(
                tie_layer, ri[0] + impl_enc, ri[1] + impl_enc,
                ri[2] - impl_enc, ri[3] - impl_enc, grw_um + 2 * impl_enc))
            shapes.append(self._frame(self.metal1_layer, *ri, grw_um))
            b_box = (ri[0] - grw_um, ri[1], ri[0], ri[3])
            shapes.append(self._pin(self.metal1_layer, "B", *b_box))
            shapes.append(self._label(self.metal1_label_layer, "B", *b_box))

            # guard-ring contacts (upstream formulas)
            nxgr = int((grw_um - (cont_size + 2 * cmp2cont))
                       / (cont2cont + cont_size)) + 1
            nygr = int(((2 * grw_um + w_eff + 2 * pyp)
                        - (cont_size + 2 * cmp2cont))
                       / (cont2cont + cont_size)) + 1
            dxgr = (grw_um - nxgr * cont_size
                    - (nxgr - 1) * cont2cont) / 2
            dygr = ((2 * grw_um + w_eff + 2 * pyp)
                    - nygr * cont_size - (nygr - 1) * cont2cont) / 2
            nxgr_h = int(((total_x + 2 * cmp2cmp) - 2 * cont2cont)
                         / (cont2cont + cont_size)) + 1
            dxgr_h = ((total_x + cont2cont) - nxgr_h * cont_size
                      - (nxgr_h - 1) * cont2cont) / 2
            csp = cont_size + cont2cont
            # left and right vertical bars
            shapes.extend(self._contacts(
                ri[0] - grw_um + dxgr, ri[1] - grw_um + dygr,
                nxgr, nygr, csp, csp, cont_size))
            shapes.extend(self._contacts(
                total_x + grw_um - dxgr + (cmp2cmp - cont_size),
                ri[1] - grw_um + dygr, nxgr, nygr, -csp, csp, cont_size))
            # bottom and top horizontal bars
            shapes.extend(self._contacts(
                -(2 * cmp2cont) + dxgr_h,
                -(2 * cont_size) - ply2gr - dxgr,
                nxgr_h, nxgr, csp, -csp, cont_size))
            shapes.extend(self._contacts(
                -(2 * cmp2cont) + dxgr_h, w_eff + pyp + dxgr,
                nxgr_h, nxgr, csp, csp, cont_size))

        else:  # bulk == "None"
            if deepnwell:
                if is_pmos:
                    deepnwell_stack((
                        -dnw_enc_p, -dnw_enc_p,
                        total_x + dnw_enc_p, w_eff + dnw_enc_p))
                else:
                    shapes.append(self._rect(
                        self.lvpwell_layer, -lvp_enc_n, -lvp_enc_n,
                        total_x + lvp_enc_n, w_eff + lvp_enc_n))
                    deepnwell_stack((
                        -lvp_enc_n, -lvp_enc_n,
                        total_x + lvp_enc_n, w_eff + lvp_enc_n))
            else:
                emit_marker((
                    -dg_enc_cmp, -(dg_enc_ply + ply_ext),
                    total_x + dg_enc_cmp,
                    w_eff + dg_enc_ply + ply_ext))
                if is_pmos:
                    shapes.append(self._rect(
                        self.nwell_layer, -nwell_enc_p, -nwell_enc_p,
                        total_x + nwell_enc_p, w_eff + nwell_enc_p))

        return shapes


class nmos(_genericMosBase):
    """Generic NMOS (upstream ``nmos`` generator: 3.3V/5V/6V, bulk options)."""

    polarity = "n"


class pmos(_genericMosBase):
    """Generic PMOS (upstream ``pmos`` generator: 3.3V/5V/6V, bulk options)."""

    polarity = "p"
    volt_minima = {
        "3.3V": (_MOS_3P3_L, _MOS_3P3_W),
        "5V": (_PMOS_5P0_L, _MOS_56_W),
        "6V": (_PMOS_6P0_L, _MOS_56_W),
    }


# ---------------------------------------------------------------------------
# Symbol-cell MOS generators
#
# Upstream registers the concrete names only as symbols; the KLayout
# generators are nmos/pmos/nmos_6p0_nat.  The classes below are
# fixed-voltage bindings of the generic draw_nmos/draw_pmos port above
# (bulk Tie/None/Guard Ring, deepnwell, pcmpgr, ld and grw are all
# supported), except nmos_6p0_nat which ports upstream's separate
# draw_nmos_6p0_nat function.
# ---------------------------------------------------------------------------

class _symbolMosBase(_genericMosBase):
    """MOS symbol cell: generic generator bound to a fixed ``volt``."""

    volt = "3.3V"
    voltage = "3.3V"        # introspection alias used by the test-suite
    sab = False
    native = False
    default_w = "0.22u"
    default_l = "0.28u"
    min_w_um = _MOS_3P3_W
    min_l_um = _MOS_3P3_L
    sab_layer = laylyr.SAB_drawing
    esd_mk_layer = laylyr.ESD_MK_drawing

    def __init__(self, w="0.22u", l="0.28u", nf="1", bulk="Bulk Tie",
                 grw="0.36u", ld="0.44u", deepnwell=False, pcmpgr=False):
        super().__init__(w=w, l=l, ld=ld, nf=nf, grw=grw, volt=self.volt,
                         bulk=bulk, deepnwell=deepnwell, pcmpgr=pcmpgr)

    def __call__(self, w="0.22u", l="0.28u", nf="1", bulk="Bulk Tie",
                 grw="0.36u", ld="0.44u", deepnwell=False, pcmpgr=False):
        super().__call__(w=w, l=l, ld=ld, nf=nf, grw=grw, volt=self.volt,
                         bulk=bulk, deepnwell=deepnwell, pcmpgr=pcmpgr)
        if self.sab:
            self.shapes.extend(self._sab_shapes())
        return self

    def _sab_shapes(self):
        """SAB strip over the gates + ESD_MK marker over the active."""
        w_um = self.w * 1e6
        l_um = self.l * 1e6
        ld_um = self.ld * 1e6
        ld_v = 0.
        if w_um < .36 and self.nf == 1:
            ld_v = .22 if self.volt in ("5V", "6V") else .02
        pitch = ld_um + ld_v + l_um + .15 - .07
        total_x = 2 * (ld_um + ld_v) + l_um + (self.nf - 1) * pitch
        gx1 = ld_um + ld_v
        gx2 = gx1 + (self.nf - 1) * pitch + l_um
        return [
            self._rect(self.sab_layer, gx1 - .05, -.10, gx2 + .05,
                       w_um + .10),
            self._rect(self.esd_mk_layer, -.10, -.10, total_x + .10,
                       w_um + .10),
        ]


class nmos_3p3(_symbolMosBase):
    polarity = "n"
    volt = "3.3V"
    voltage = "3.3V"


class nmos_3p3_sab(_symbolMosBase):
    polarity = "n"
    volt = "3.3V"
    voltage = "3.3V"
    sab = True


class nmos_6p0(_symbolMosBase):
    polarity = "n"
    volt = "6V"
    voltage = "6V"
    default_w = "0.30u"
    default_l = "0.70u"
    min_w_um = .30
    min_l_um = _NMOS_6P0_L


class pmos_3p3(_symbolMosBase):
    polarity = "p"
    volt = "3.3V"
    voltage = "3.3V"
    volt_minima = pmos.volt_minima


class pmos_3p3_sab(_symbolMosBase):
    polarity = "p"
    volt = "3.3V"
    voltage = "3.3V"
    volt_minima = pmos.volt_minima
    sab = True


class pmos_6p0(_symbolMosBase):
    polarity = "p"
    volt = "6V"
    voltage = "6V"
    volt_minima = pmos.volt_minima
    default_w = "0.30u"
    default_l = "0.55u"
    min_w_um = .30
    min_l_um = _PMOS_6P0_L


class nmos_6p0_nat(_upstreamMosBase):
    """Port of upstream draw_nmos_6p0_nat (native 6V NMOS, bulk options)."""

    polarity = "n"
    voltage = "6V"
    native = True
    sab = False
    default_w = "0.80u"
    default_l = "1.80u"
    min_w_um = .80
    min_l_um = 1.80
    nat_layer = laylyr.NAT_drawing
    dualgate_layer = laylyr.Dualgate_drawing
    poly_label_layer = laylyr.Poly2_Label_drawing
    metal1_label_layer = laylyr.Metal1_Label_drawing

    def __init__(self, w="0.80u", l="1.80u", nf="1", bulk="Bulk Tie",
                 grw="0.36u", ld="0.44u"):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.ld = self._meters(ld)
        self.nf = max(int(float(nf)), 1)
        self.bulk = bulk
        self.grw = self._meters(grw)
        super().__init__([])

    def __call__(self, w="0.80u", l="1.80u", nf="1", bulk="Bulk Tie",
                 grw="0.36u", ld="0.44u"):
        if bulk not in _MOS_BULK_CHOICES:
            raise ValueError(f"Unsupported bulk option: {bulk}")
        w_um = max(self._microns(w), self.min_w_um)
        l_um = max(self._microns(l), self.min_l_um)
        ld_um = self._microns(ld)
        nf = max(int(float(nf)), 1)
        grw_um = max(self._microns(grw), _MOS_GRW_MIN)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.ld = ld_um * 1e-6
        self.nf = nf
        self.bulk = bulk
        self.grw = grw_um * 1e-6
        self.shapes = self._generate(w_um, l_um, ld_um, nf, grw_um, bulk)
        return self

    def _generate(self, w_um, l_um, ld_um, nf, grw_um, bulk):
        # upstream draw_nmos_6p0_nat constants (um)
        cmp2cont = .07
        cont_size = .22
        impl_enc = .16          # np_enc_cmp / pp_enc_cmp
        cont2ply = .15
        ply_ext = .22           # ply_ext_cmp
        impl_gate = .23         # np_enc_gate
        cont2cont = .28
        cmp2cmp = .36
        nat_enc = 2.0           # nat_enc_cmp
        nec = nat_enc + cmp2cmp  # bulk tie / ring separation from the active

        pitch = ld_um + l_um + cont2ply - cmp2cont
        total_x = 2 * ld_um + l_um + (nf - 1) * pitch
        # upstream ring x extent uses (nf - 1) * (ld + l), not pitch
        ring_x = 2 * ld_um + l_um + (nf - 1) * (ld_um + l_um)

        shapes = []
        shapes.append(self._rect(self.comp_layer, 0, 0, total_x, w_um))
        shapes.append(self._rect(
            self.nplus_layer, -impl_enc, -impl_gate,
            total_x + impl_enc, w_um + impl_gate))
        for layer in (self.nat_layer, self.dualgate_layer):
            shapes.append(self._rect(
                layer, -nat_enc, -nat_enc, total_x + nat_enc,
                w_um + nat_enc))

        # gates
        for i in range(nf):
            gx1 = ld_um + i * pitch
            gx2 = gx1 + l_um
            shapes.append(self._rect(
                self.poly_layer, gx1, -ply_ext, gx2, w_um + ply_ext))
            shapes.append(self._pin(
                self.poly_layer, "G", gx1, -ply_ext, gx2, w_um + ply_ext))
            if i == 0:
                shapes.append(self._label(
                    self.poly_label_layer, "G", gx1, -ply_ext, gx2,
                    w_um + ply_ext))

        # contact bookkeeping (upstream formulas)
        nx = int((ld_um - (cont_size + cmp2cont + cont2ply))
                 / (cont2cont + cont_size)) + 1
        ny = int((w_um - (cont_size + 2 * cmp2cont))
                 / (cont2cont + cont_size)) + 1
        dx = ((ld_um - nx * cont_size - (nx - 1) * cont2cont)
              * cmp2cont / cont_size)
        dy = (w_um - ny * cont_size - (ny - 1) * cont2cont) / 2
        csp = cont_size + cont2cont

        # S/D contacts + metals (no metal_violat on the native device)
        d_labeled = False
        shapes.extend(self._contacts(
            dx, dy, nx, ny, csp, csp, cont_size))
        m_left = (0, 0, ld_um - (cont_size - 2 * cmp2cont), w_um)
        shapes.append(self._rect(self.metal1_layer, *m_left))
        shapes.append(self._pin(self.metal1_layer, "S", *m_left))
        shapes.append(self._label(self.metal1_label_layer, "S", *m_left))
        for i in range(nf):
            cx0 = pitch * i + 2 * ld_um + l_um - cont_size - dx
            shapes.extend(self._contacts(
                cx0, dy, nx, ny, -csp, csp, cont_size))
            m_right = (pitch * (i + 1), 0,
                       ld_um + pitch * (i + 1)
                       - (cont_size - 2 * cmp2cont), w_um)
            shapes.append(self._rect(self.metal1_layer, *m_right))
            pin_name = "D" if i % 2 == 0 else "S"
            shapes.append(self._pin(
                self.metal1_layer, pin_name, *m_right))
            if pin_name == "D" and not d_labeled:
                d_labeled = True
                shapes.append(self._label(
                    self.metal1_label_layer, "D", *m_right))

        if bulk == "Bulk Tie":
            # tie sits outside the NAT enclosure, upstream offset nec
            tie = (-nec - ld_um, 0, -nec, w_um)
            shapes.append(self._rect(self.comp_layer, *tie))
            shapes.append(self._rect(
                self.pplus_layer,
                -nec - impl_enc - ld_um, -impl_enc,
                -nec + impl_enc, w_um + impl_enc))
            shapes.extend(self._contacts(
                -(nec + cont_size) - dx * cont_size / (2 * cmp2cont),
                dy, nx, ny, -csp, csp, cont_size))
            shapes.append(self._rect(self.metal1_layer, *tie))
            shapes.append(self._pin(self.metal1_layer, "B", *tie))
            shapes.append(self._label(self.metal1_label_layer, "B", *tie))

        elif bulk == "Guard Ring":
            ri = (-nec, -nec, ring_x + nec, w_um + nec)
            shapes.append(self._frame(self.comp_layer, *ri, grw_um))
            shapes.append(self._frame(
                self.pplus_layer, ri[0] + impl_enc, ri[1] + impl_enc,
                ri[2] - impl_enc, ri[3] - impl_enc, grw_um + 2 * impl_enc))
            shapes.append(self._frame(self.metal1_layer, *ri, grw_um))
            b_box = (ri[0] - grw_um, ri[1], ri[0], ri[3])
            shapes.append(self._pin(self.metal1_layer, "B", *b_box))
            shapes.append(self._label(
                self.metal1_label_layer, "B", *b_box))

            # guard-ring contacts (upstream formulas)
            nxgr = int((grw_um - (cont_size + 2 * cmp2cont))
                       / csp) + 1
            nygr = int(((2 * grw_um + w_um + 2 * nec)
                        - (cont_size + 2 * cmp2cont)) / csp) + 1
            dxgr = (grw_um - nxgr * cont_size
                    - (nxgr - 1) * cont2cont) / 2
            dygr = ((2 * grw_um + w_um + 2 * nec)
                    - nygr * cont_size - (nygr - 1) * cont2cont) / 2
            nxgr_h = int(((ring_x + 2 * nec) - 2 * cont2cont) / csp) + 1
            dxgr_h = ((ring_x + nec) - nxgr_h * cont_size
                      - (nxgr_h - 1) * cont2cont) / 2
            # left and right vertical bars
            shapes.extend(self._contacts(
                ri[0] - grw_um + dxgr, ri[1] - grw_um + dygr,
                nxgr, nygr, csp, csp, cont_size))
            shapes.extend(self._contacts(
                ring_x + grw_um - dxgr + nec - cont_size,
                ri[1] - grw_um + dygr, nxgr, nygr, -csp, csp, cont_size))
            # bottom and top horizontal bars
            shapes.extend(self._contacts(
                -(nec / 2) + dxgr_h, -(nec + cont_size) - dxgr,
                nxgr_h, nxgr, csp, -csp, cont_size))
            shapes.extend(self._contacts(
                -(nec / 2) + dxgr_h, w_um + nec + dxgr,
                nxgr_h, nxgr, csp, csp, cont_size))

        return shapes


class _ldmosAsymBase(_upstreamMosBase):
    """Port of upstream draw_nmos_10p0_asym / draw_pmos_10p0_asym.

    Asymmetric 10 V LDMOS: central drain, two sources and two gates, a
    drift-region marker (MVSD / MVPSD) and a substrate guard ring.  The
    PMOS adds DNWELL / Dualgate / LDMOS_XTOR device markers and an
    optional second (PCMP) guard ring.
    """

    polarity = "n"
    min_w_um = _LDMOS_W_MIN
    max_w_um = _LDMOS_W_MAX
    min_l_um = _LDMOS_L_MIN
    max_l_um = _LDMOS_L_MAX
    vx_ext = .5               # mvsd_ext_cmp / mvpsd_ext_cmp
    mvsd_layer = laylyr.MVSD_drawing

    dnwell_layer = laylyr.DNWELL_drawing
    dualgate_layer = laylyr.Dualgate_drawing
    ldmos_xtor_layer = laylyr.LDMOS_XTOR_drawing

    def __init__(self, w="4u", l="0.6u"):
        self.w = self._meters(w)
        self.l = self._meters(l)
        super().__init__([])

    def _coerce(self, w, l):
        """Clamp w/l to the upstream LDMOS ranges (um)."""
        w_um = min(max(self._microns(w), self.min_w_um), self.max_w_um)
        l_um = min(max(self._microns(l), self.min_l_um), self.max_l_um)
        return w_um, l_um

    def _generate(self, w_um, l_um, double_gr):
        is_pmos = self.polarity == "p"
        implant_layer = self.pplus_layer if is_pmos else self.nplus_layer
        # opposite-polarity implant for the (inner) guard ring
        tie_layer = self.nplus_layer if is_pmos else self.pplus_layer

        # upstream draw_mos.py LDMOS constants (um)
        cmp2cont = .07
        cont_size = .22
        impl_enc = .16          # np_enc_cmp / pp_enc_cmp
        cont2ply = .15
        metal_w = .38
        ply_ext = .4            # ply_ext_cmp
        ply_fld = .2
        impl_gate = .23         # np_enc_gate
        cont2cont = .25
        cmp2cmp = .36
        cmp2gr = .4
        vx_ov = .4              # mvsd_ov_cmp / mvpsd_ov_cmp
        vx2gr = 1.              # mvsd2gr / mvpsd2gr
        ply2gr = .4
        drain2ply = .16
        dg_enc = .5             # dg_enc_cmp (nmos) / dg_enc_pcmp (pmos)
        dnw_enc = .66           # dnw_enc_cmp (pmos)
        pcmp_gr2dnw = 2.5       # pmos only
        vx_ext = self.vx_ext

        w2 = w_um / 2
        # inner/outer guard-ring half extents (x) and ring width
        gr_in_x = (.5 * cont_size + cmp2gr + cont_size + cmp2cont
                   + cont2ply + vx_ov + cmp2cmp)
        gr_out_x = gr_in_x + cont_size + 2 * cmp2cont
        gr_w = cont_size + 2 * cmp2cont
        gr_in_y = vx_ext + vx2gr
        gr_out_y = gr_in_y + gr_w
        csp = cont_size + cont2cont

        shapes = []

        # device marker boxes
        if is_pmos:
            shapes.append(self._rect(
                self.dnwell_layer,
                -(dnw_enc + gr_out_x) - l_um,
                -(gr_out_y + dnw_enc) - w2,
                dnw_enc + gr_out_x + l_um,
                gr_out_y + dnw_enc + w2))
            dg_x = (dg_enc + pcmp_gr2dnw + dnw_enc + 4 * cmp2cont
                    + 2.5 * cont_size + cmp2gr + cont_size + cmp2cont
                    + cont2ply + vx_ov + cmp2cmp)
            dg_y = (vx_ext + vx2gr + 4 * cmp2cont + 2 * cont_size
                    + dg_enc + pcmp_gr2dnw + dnw_enc)
            shapes.append(self._rect(
                self.dualgate_layer,
                -dg_x - l_um, -dg_y - w2, dg_x + l_um, dg_y + w2))
            shapes.append(self._rect(
                self.ldmos_xtor_layer,
                -dg_x - l_um, -dg_y - w2, dg_x + l_um, dg_y + w2))
        else:
            dg_x = dg_enc + gr_out_x
            dg_y = gr_out_y + dg_enc
            shapes.append(self._rect(
                self.dualgate_layer,
                -dg_x - l_um, -dg_y - w2, dg_x + l_um, dg_y + w2))
            shapes.append(self._rect(
                self.ldmos_xtor_layer,
                -dg_x - l_um, -dg_y - w2, dg_x + l_um, dg_y + w2))

        # drain diffusion + drift-region marker
        shapes.append(self._rect(
            self.comp_layer, -cont_size / 2, -w2, cont_size / 2, w2))
        shapes.append(self._rect(
            self.mvsd_layer,
            -(cont_size / 2 + cmp2cmp + vx_ov), -w2 - vx_ext,
            cont_size / 2 + cmp2cmp + vx_ov, w2 + vx_ext))

        # source diffusions (right / left)
        src_x2 = (cont_size / 2 + cmp2cmp + vx_ov + cont2ply
                  + cont_size + cmp2cont) + l_um
        shapes.append(self._rect(
            self.comp_layer, cont_size / 2 + cmp2cmp, -w2, src_x2, w2))
        shapes.append(self._rect(
            self.comp_layer, -(cont_size / 2 + cmp2cmp), -w2, -src_x2, w2))

        # implant over sources/gates/drain surround
        impl_x = (cont_size / 2 + cmp2cmp + vx_ov + cont2ply
                  + cont_size + cmp2cont + impl_enc)
        shapes.append(self._rect(
            implant_layer, -impl_x - l_um, -w2 - impl_gate,
            impl_x + l_um, w2 + impl_gate))

        # Poly2 gates + G pins
        g_x2 = (cont_size / 2 + cmp2cmp + vx_ov) + l_um
        g_y2 = w2 + vx_ext + vx2gr - ply2gr
        for sign in (1, -1):
            shapes.append(self._rect(
                self.poly_layer,
                sign * (cont_size / 2 + drain2ply), -w2 - ply_ext,
                sign * g_x2, g_y2))
            shapes.append(self._pin(
                self.poly_layer, "G",
                sign * (cont_size / 2 + drain2ply), -w2 - ply_ext,
                sign * g_x2, g_y2))

        # contact array bookkeeping (upstream formulas)
        ny = int((w_um - (cont_size + 2 * cmp2cont))
                 / (cont_size + cont2cont)) + 1
        dy = (w_um - ny * cont_size - (ny - 1) * cont2cont) / 2
        ng = int(((l_um + vx_ov + ply_fld) - (cont_size + 2 * cmp2cont))
                 / (cont_size + cont2cont)) + 1
        dg = (l_um + vx_ov + ply_fld - ng * cont_size
              - (ng - 1) * cont2cont) / 2

        # gate contacts + Metal1 straps
        gy = w2 + vx_ext + vx2gr - ply2gr - (metal_w + cont_size) / 2
        shapes.extend(self._contacts(
            (cont_size / 2 + drain2ply) + dg, gy, ng, 1, csp, csp,
            cont_size))
        shapes.extend(self._contacts(
            -(1.5 * cont_size + drain2ply) - dg, gy, ng, 1, -csp, csp,
            cont_size))
        m_y0 = w2 + vx_ext + vx2gr - ply2gr - metal_w
        m_y1 = w2 + vx_ext + vx2gr - ply2gr
        for sign in (1, -1):
            strap = (sign * (cont_size / 2 + drain2ply), m_y0,
                     sign * g_x2, m_y1)
            shapes.append(self._rect(self.metal1_layer, *strap))
            shapes.append(self._pin(self.metal1_layer, "G", *strap))
        shapes.append(self._label(
            self.metal1_label_layer, "G",
            cont_size / 2 + drain2ply, m_y0, g_x2, m_y1))
        shapes.append(self._label(
            self.poly_label_layer, "G",
            cont_size / 2 + drain2ply, -w2 - ply_ext, g_x2, g_y2))

        # drain contacts + Metal1 terminal
        if ny > 0:
            shapes.extend(self._contacts(
                -cont_size / 2, -w2 + dy, 1, ny, csp, csp, cont_size))
        d_box = (-metal_w / 2, -w2, metal_w / 2, w2)
        shapes.append(self._rect(self.metal1_layer, *d_box))
        shapes.append(self._pin(self.metal1_layer, "D", *d_box))
        shapes.append(self._label(self.metal1_label_layer, "D", *d_box))

        # source contacts + Metal1 terminals
        if ny > 0:
            shapes.extend(self._contacts(
                (cont_size / 2 + cmp2cmp + vx_ov + cont2ply) + l_um,
                -w2 + dy, 1, ny, csp, csp, cont_size))
            shapes.extend(self._contacts(
                -(1.5 * cont_size + cmp2cmp + vx_ov + cont2ply) - l_um,
                -w2 + dy, 1, ny, csp, csp, cont_size))
        sm_x1 = (1.5 * cont_size + cmp2cmp + vx_ov + cont2ply + cmp2cont
                 - metal_w) + l_um
        sm_x2 = (1.5 * cont_size + cmp2cmp + vx_ov + cont2ply + cmp2cont
                 ) + l_um
        s_labeled = False
        for sign in (1, -1):
            s_box = (sign * sm_x1, -w2, sign * sm_x2, w2)
            shapes.append(self._rect(self.metal1_layer, *s_box))
            shapes.append(self._pin(self.metal1_layer, "S", *s_box))
            if not s_labeled:
                s_labeled = True
                shapes.append(self._label(
                    self.metal1_label_layer, "S", *s_box))

        # guard ring: COMP frame, opposite-implant frame, Metal1 frame
        ri = (-gr_in_x - l_um, -gr_in_y - w2, gr_in_x + l_um, gr_in_y + w2)
        shapes.append(self._frame(self.comp_layer, *ri, gr_w))
        shapes.append(self._frame(
            tie_layer, ri[0] + impl_enc, ri[1] + impl_enc,
            ri[2] - impl_enc, ri[3] - impl_enc, gr_w + 2 * impl_enc))
        shapes.append(self._frame(self.metal1_layer, *ri, gr_w))
        b_box = (ri[0] - gr_w, ri[1], ri[0], ri[3])
        shapes.append(self._pin(self.metal1_layer, "B", *b_box))
        shapes.append(self._label(self.metal1_label_layer, "B", *b_box))

        # guard-ring contacts (upstream formulas)
        nygr = int((w_um + 2 * (vx_ext + vx2gr + cmp2cont + cont_size)
                    + cont2cont) / csp)
        dygr = (w_um + 2 * (vx_ext + vx2gr + cmp2cont + cont_size)
                - nygr * csp + cont2cont) / 2
        ring_h = (0.5 * cont_size + cmp2gr + cont_size + cmp2cont
                  + cont2ply + vx_ov + cmp2cmp + cmp2cont)
        nxgr_h = int((2 * l_um + 2 * ring_h - cont2cont) / csp)
        dxgr_h = (2 * l_um + 2 * ring_h - nxgr_h * csp + cont2cont) / 2
        # left / right vertical bars
        shapes.extend(self._contacts(
            -(cmp2cont + 1.5 * cont_size + cmp2gr + cont_size + cmp2cont
              + cont2ply + vx_ov + cmp2cmp) - l_um,
            dygr - (vx_ext + vx2gr + cmp2cont + cont_size) - w2,
            1, nygr, csp, csp, cont_size))
        shapes.extend(self._contacts(
            (cmp2cont + 0.5 * cont_size + cmp2gr + cont_size + cmp2cont
             + cont2ply + vx_ov + cmp2cmp) + l_um,
            dygr - (vx_ext + vx2gr + cmp2cont + cont_size) - w2,
            1, nygr, csp, csp, cont_size))
        # bottom / top horizontal bars
        shapes.extend(self._contacts(
            dxgr_h - ring_h - l_um,
            -(vx_ext + vx2gr + cmp2cont + cont_size) - w2,
            nxgr_h, 1, csp, csp, cont_size))
        shapes.extend(self._contacts(
            dxgr_h - ring_h - l_um,
            (vx_ext + vx2gr + cmp2cont) + w2,
            nxgr_h, 1, csp, csp, cont_size))

        # pmos: optional second (PCMP / "DNWELL") guard ring
        if is_pmos and double_gr:
            di_x = (pcmp_gr2dnw + dnw_enc + 2 * cmp2cont
                    + 1.5 * cont_size + cmp2gr + cont_size + cmp2cont
                    + cont2ply + vx_ov + cmp2cmp)
            di_y = (vx_ext + vx2gr + 2 * cmp2cont + cont_size
                    + pcmp_gr2dnw + dnw_enc)
            ri2 = (-di_x - l_um, -di_y - w2, di_x + l_um, di_y + w2)
            shapes.append(self._frame(self.comp_layer, *ri2, gr_w))
            shapes.append(self._frame(
                implant_layer, ri2[0] + impl_enc, ri2[1] + impl_enc,
                ri2[2] - impl_enc, ri2[3] - impl_enc,
                gr_w + 2 * impl_enc))
            shapes.append(self._frame(self.metal1_layer, *ri2, gr_w))
            b2_box = (ri2[0] - gr_w, ri2[1], ri2[0], ri2[3])
            shapes.append(self._pin(self.metal1_layer, "B", *b2_box))

            # DNWELL guard-ring contacts (upstream formulas)
            nygr2 = int((w_um + 2 * (vx_ext + vx2gr + 3 * cmp2cont
                                     + 2 * cont_size + pcmp_gr2dnw
                                     + dnw_enc) + cont2cont) / csp)
            dygr2 = (w_um + 2 * (vx_ext + vx2gr + 3 * cmp2cont
                                 + 2 * cont_size + pcmp_gr2dnw + dnw_enc)
                     - nygr2 * csp + cont2cont) / 2
            ring_h2 = (pcmp_gr2dnw + dnw_enc + 2 * cmp2cont
                       + 1.5 * cont_size + cmp2gr + cont_size
                       + 2 * cmp2cont + cont2ply + vx_ov + cmp2cmp)
            nxgr_h2 = int((2 * l_um + 2 * ring_h2 - cont2cont) / csp)
            dxgr_h2 = (2 * l_um + 2 * ring_h2 - nxgr_h2 * csp
                       + cont2cont) / 2
            vx2_in = (vx_ext + vx2gr + 3 * cmp2cont + 2 * cont_size
                      + pcmp_gr2dnw + dnw_enc)
            shapes.extend(self._contacts(
                -(pcmp_gr2dnw + dnw_enc + 3 * cmp2cont + 2.5 * cont_size
                  + cmp2gr + cont_size + cmp2cont + cont2ply + vx_ov
                  + cmp2cmp) - l_um,
                dygr2 - vx2_in - w2, 1, nygr2, csp, csp, cont_size))
            shapes.extend(self._contacts(
                dxgr_h2 - ring_h2 - l_um, -vx2_in - w2,
                nxgr_h2, 1, csp, csp, cont_size))
            shapes.extend(self._contacts(
                (pcmp_gr2dnw + dnw_enc + 2 * cmp2cont + 1.5 * cont_size
                 + cmp2gr + cont_size + 2 * cmp2cont + cont2ply + vx_ov
                 + cmp2cmp) + l_um,
                dygr2 - vx2_in - w2, 1, nygr2, csp, csp, cont_size))
            shapes.extend(self._contacts(
                dxgr_h2 - ring_h2 - l_um,
                vx_ext + vx2gr + 3 * cmp2cont + cont_size + pcmp_gr2dnw
                + dnw_enc + w2,
                nxgr_h2, 1, csp, csp, cont_size))

        return shapes


class nmos_10p0_asym(_ldmosAsymBase):
    """10 V asymmetric LDNMOS (upstream ``nmos_10p0_asym`` generator)."""

    polarity = "n"
    vx_ext = .5               # mvsd_ext_cmp
    mvsd_layer = laylyr.MVSD_drawing

    def __call__(self, w="4u", l="0.6u"):
        w_um, l_um = self._coerce(w, l)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.shapes = self._generate(w_um, l_um, False)
        return self


class pmos_10p0_asym(_ldmosAsymBase):
    """10 V asymmetric LDPMOS (upstream ``pmos_10p0_asym`` generator)."""

    polarity = "p"
    vx_ext = .8               # mvpsd_ext_cmp
    mvsd_layer = laylyr.MVPSD_drawing

    def __init__(self, w="4u", l="0.6u", double_gr=True):
        self.double_gr = self._bool(double_gr)
        super().__init__(w, l)

    def __call__(self, w="4u", l="0.6u", double_gr=True):
        w_um, l_um = self._coerce(w, l)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.double_gr = self._bool(double_gr)
        self.shapes = self._generate(w_um, l_um, self.double_gr)
        return self
