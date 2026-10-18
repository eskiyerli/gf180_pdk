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
import os

from .base import baseCell, laylyr


class _unsalicidedResistor(baseCell):
    """Shared geometry for the GF180MCU unsalicided 3-terminal resistors.

    The marked body is ``(0,0,w,l)``; terminals extend left/right under SAB.
    """

    body_kind = "diff"        # "diff" (COMP) or "poly" (Poly2)
    implant = "n"             # "n" (Nplus) or "p" (Pplus)
    bulk_well = "lvpwell"     # "lvpwell" | "nwell" | "substrate"

    comp_layer = laylyr.COMP_drawing
    poly_layer = laylyr.Poly2_drawing
    nplus_layer = laylyr.Nplus_drawing
    pplus_layer = laylyr.Pplus_drawing
    sab_layer = laylyr.SAB_drawing
    res_mk_layer = laylyr.RES_MK_drawing
    cont_layer = laylyr.Contact_drawing
    metal1_layer = laylyr.Metal1_drawing
    metal1_label_layer = laylyr.Metal1_Label_drawing
    lvpwell_layer = laylyr.LVPWELL_drawing
    nwell_layer = laylyr.Nwell_drawing

    # common constants (um)
    cont_size = .22
    cont_spacing = .25
    cont_enc = .07            # contact enclosure
    term_w = .34              # metal terminal width
    impl_act_enc = .18        # implant enclosure of active
    bulk_w = .36              # bulk tie active width

    # kind-dependent constants
    body_end = .44            # conductor extension past the body, diff
    body_end_poly = .51       # conductor extension past the body, poly
    sab_y = .23               # SAB y-extension past body, diff
    sab_y_poly = .28          # SAB y-extension past body, poly
    impl_poly_enc = .30       # implant enclosure of poly conductor
    term_enc = .06            # metal enclosure of terminal contacts
    lvpwell_enc = .60         # LVPWELL enclosure (nplus_u)
    nwell_enc = .93           # Nwell enclosure (pplus_u)
    bulk_sep = .48            # subclass overrides

    min_w_um = .42
    min_l_um = .42
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
        is_poly = self.body_kind == "poly"
        conductor = self.poly_layer if is_poly else self.comp_layer
        implant_layer = (self.nplus_layer if self.implant == "n"
                         else self.pplus_layer)
        end = self.body_end_poly if is_poly else self.body_end
        sab_ext = self.sab_y_poly if is_poly else self.sab_y
        impl_enc = self.impl_poly_enc if is_poly else self.impl_act_enc

        shapes = []

        # resistor body markers
        shapes.append(self._rect(self.res_mk_layer, 0, 0, w_um, l_um))
        shapes.append(self._rect(self.sab_layer, 0, -sab_ext, w_um, l_um + sab_ext))

        # body/terminal conductor
        shapes.append(self._rect(conductor, -end, 0, w_um + end, l_um))
        shapes.append(self._rect(
            implant_layer, -end - impl_enc, -impl_enc,
            w_um + end + impl_enc, l_um + impl_enc))

        # terminals (M left, P right)
        for x1, x2, name in (
            (-end, -end + self.term_w, "M"),
            (w_um + end - self.term_w, w_um + end, "P"),
        ):
            shapes.append(self._rect(
                self.metal1_layer, x1, .01, x2, l_um - .01))
            shapes.extend(self.contactArray(
                self.cont_layer, x1, .01, x2, l_um - .01,
                self.term_enc, self.cont_size, self.cont_spacing))
            shapes.append(self._pin(
                self.metal1_layer, name, x1, .01, x2, l_um - .01))
            shapes.append(self._label(
                self.metal1_label_layer, name, x1, .01, x2, l_um - .01))

        # bulk tie left of the left terminal
        tie_x2 = -end - self.bulk_sep
        tie_x1 = tie_x2 - self.bulk_w
        tie_implant = (self.pplus_layer if self.implant == "n" or
                       self.bulk_well == "substrate"
                       else self.nplus_layer)
        shapes.append(self._rect(self.comp_layer, tie_x1, 0, tie_x2, l_um))
        shapes.append(self._rect(
            tie_implant, tie_x1 - self.impl_act_enc, -self.impl_act_enc,
            tie_x2 + self.impl_act_enc, l_um + self.impl_act_enc))
        shapes.append(self._rect(self.metal1_layer, tie_x1, 0, tie_x2, l_um))
        shapes.extend(self.contactArray(
            self.cont_layer, tie_x1, 0, tie_x2, l_um,
            self.cont_enc, self.cont_size, self.cont_spacing))
        shapes.append(self._pin(
            self.metal1_layer, "B", tie_x1, 0, tie_x2, l_um))
        shapes.append(self._label(
            self.metal1_label_layer, "B", tie_x1, 0, tie_x2, l_um))

        # well enclosure
        if self.bulk_well == "lvpwell":
            shapes.append(self._rect(
                self.lvpwell_layer, tie_x1 - self.lvpwell_enc,
                -self.lvpwell_enc, w_um + end + self.lvpwell_enc,
                l_um + self.lvpwell_enc))
        elif self.bulk_well == "nwell":
            shapes.append(self._rect(
                self.nwell_layer, tie_x1 - self.nwell_enc,
                -self.nwell_enc, w_um + end + self.nwell_enc,
                l_um + self.nwell_enc))
        return shapes


class nplus_u(_unsalicidedResistor):
    body_kind = "diff"
    implant = "n"
    bulk_well = "lvpwell"
    bulk_sep = .48


class pplus_u(_unsalicidedResistor):
    body_kind = "diff"
    implant = "p"
    bulk_well = "nwell"
    bulk_sep = .34


class npolyf_u(_unsalicidedResistor):
    body_kind = "poly"
    implant = "n"
    bulk_well = "substrate"
    bulk_sep = .72


class ppolyf_u(_unsalicidedResistor):
    body_kind = "poly"
    implant = "p"
    bulk_well = "substrate"
    bulk_sep = .86


class nwell(baseCell):
    """GF180MCU Nwell resistor (LVS device nwell).

    The marked Nwell body ``(0,0,w,l)`` is extended .48um on both sides by
    external N+ terminal stripes, matching upstream ``draw_nwell_res``.
    """

    nwell_layer = laylyr.Nwell_drawing
    res_mk_layer = laylyr.RES_MK_drawing
    comp_layer = laylyr.COMP_drawing
    nplus_layer = laylyr.Nplus_drawing
    pplus_layer = laylyr.Pplus_drawing
    cont_layer = laylyr.Contact_drawing
    metal1_layer = laylyr.Metal1_drawing
    metal1_label_layer = laylyr.Metal1_Label_drawing

    well_ext = .48         # Nwell extension past the marked body, each side
    res_mk_y = .50         # RES_MK y-extension past the body
    term_w = .36           # N+ terminal stripe width
    term_inset = .12       # terminal y-inset inside the stripe
    impl_enc = .16         # implant enclosure
    cont_size = .22
    cont_spacing = .25
    cont_enc = .07
    tie_sep = .84          # B tie separation from well edge
    tie_w = .36            # B tie width

    min_w_um = .42
    min_l_um = .60
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
        shapes.append(self._rect(
            self.nwell_layer, -self.well_ext, 0, w_um + self.well_ext, l_um))
        shapes.append(self._rect(
            self.res_mk_layer, 0, -self.res_mk_y, w_um, l_um + self.res_mk_y))

        # N+ terminal stripes outside the marked body edges
        for x1, x2, name in (
            (-self.term_w, 0, "M"),
            (w_um, w_um + self.term_w, "P"),
        ):
            shapes.append(self._rect(
                self.comp_layer, x1, self.term_inset, x2,
                l_um - self.term_inset))
            shapes.append(self._rect(
                self.nplus_layer, x1 - self.impl_enc,
                self.term_inset - self.impl_enc, x2 + self.impl_enc,
                l_um - self.term_inset + self.impl_enc))
            shapes.append(self._rect(
                self.metal1_layer, x1, self.term_inset, x2,
                l_um - self.term_inset))
            shapes.extend(self.contactArray(
                self.cont_layer, x1, self.term_inset, x2,
                l_um - self.term_inset, self.cont_enc, self.cont_size,
                self.cont_spacing))
            shapes.append(self._pin(
                self.metal1_layer, name, x1, self.term_inset, x2,
                l_um - self.term_inset))
            shapes.append(self._label(
                self.metal1_label_layer, name, x1, self.term_inset, x2,
                l_um - self.term_inset))

        # P+ substrate tie outside the well:
        # x = -term_w - tie_sep - tie_w .. -term_w - tie_sep
        tx1 = -self.term_w - self.tie_sep - self.tie_w
        tx2 = -self.term_w - self.tie_sep
        shapes.append(self._rect(self.comp_layer, tx1, 0, tx2, l_um))
        shapes.append(self._rect(
            self.pplus_layer, tx1 - self.impl_enc, -self.impl_enc,
            tx2 + self.impl_enc, l_um + self.impl_enc))
        shapes.append(self._rect(self.metal1_layer, tx1, 0, tx2, l_um))
        shapes.extend(self.contactArray(
            self.cont_layer, tx1, 0, tx2, l_um,
            self.cont_enc, self.cont_size, self.cont_spacing))
        shapes.append(self._pin(self.metal1_layer, "B", tx1, 0, tx2, l_um))
        shapes.append(self._label(
            self.metal1_label_layer, "B", tx1, 0, tx2, l_um))
        return shapes


class rm1(baseCell):
    """GF180MCU Metal1 resistor (LVS device rm1)."""

    metal1_layer = laylyr.Metal1_drawing
    metal1_res_layer = laylyr.Metal1_Res_drawing
    metal1_label_layer = laylyr.Metal1_Label_drawing

    ext = .23              # Metal1 extension past the marker on each side

    min_w_um = .23
    min_l_um = .23
    default_w = "0.6u"
    default_l = "0.6u"

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
        shapes.append(self._rect(self.metal1_res_layer, 0, 0, w_um, l_um))
        shapes.append(self._rect(
            self.metal1_layer, -self.ext, 0, w_um + self.ext, l_um))
        shapes.append(self._pin(
            self.metal1_layer, "M", -self.ext, 0, 0, l_um))
        shapes.append(self._label(
            self.metal1_label_layer, "M", -self.ext, 0, 0, l_um))
        shapes.append(self._pin(
            self.metal1_layer, "P", w_um, 0, w_um + self.ext, l_um))
        shapes.append(self._label(
            self.metal1_label_layer, "P", w_um, 0, w_um + self.ext, l_um))
        return shapes


# ----------------------------------------------------------------------------
# Generic resistor generators matching the upstream KLayout PCell names and
# option surface (res.py / draw_res.py of
# globalfoundries-pdk-libs-gf180mcu_fd_pr), minus read-only area/perim and the
# array_x/array_y/x_spacing/y_spacing mosaic parameters.
# ----------------------------------------------------------------------------


class metal_resistor(baseCell):
    """2-terminal metal resistor (upstream ``metal_resistor`` generator).

    ``res_type`` selects the metal and marker layer:
    rm1 -> Metal1/Metal1_Res, rm2 -> Metal2/Metal2_Res,
    rm3 -> Metal3/Metal3_Res, tm6k/tm9k/tm11k/tm30k ->
    MetalTop/Metal6_Res (this PDK names the 110/16 ``MetalTop_Res``
    marker Metal6_Res).  The marked body is ``(0,0,w,l)`` and the metal
    extends ``ext`` on both sides carrying the M/P pins.
    ``GF_PDK_OPTION`` stack restrictions of upstream res.py are enforced:
    option A forbids rm3/tm6k/tm9k/tm11k, option B forbids
    tm6k/tm9k/tm30k, any other option forbids tm6k/tm11k/tm30k.
    """

    # res_type -> (metal layer name, res marker layer name, ext/min um)
    RES_SPECS = {
        "rm1": ("Metal1", "Metal1_Res", .23),
        "rm2": ("Metal2", "Metal2_Res", .28),
        "rm3": ("Metal3", "Metal3_Res", .28),
        "tm6k": ("MetalTop", "Metal6_Res", .36),
        "tm9k": ("MetalTop", "Metal6_Res", .44),
        "tm11k": ("MetalTop", "Metal6_Res", .44),
        "tm30k": ("MetalTop", "Metal6_Res", 1.8),
    }
    # GF_PDK_OPTION -> res_types forbidden on that stack (upstream res.py)
    STACK_FORBIDDEN = {
        "A": ("rm3", "tm6k", "tm9k", "tm11k"),
        "B": ("tm6k", "tm9k", "tm30k"),
    }
    STACK_FORBIDDEN_OTHER = ("tm6k", "tm11k", "tm30k")

    def __init__(self, res_type="rm1", w="0.23u", l="0.23u"):
        self.res_type = self._check_type(res_type)
        self.w = self._meters(w)
        self.l = self._meters(l)
        super().__init__([])

    @classmethod
    def _check_type(cls, res_type):
        if res_type not in cls.RES_SPECS:
            raise ValueError(
                f"Invalid metal resistor type: {res_type!r}")
        return res_type

    def _check_stack(self):
        option = os.environ.get("GF_PDK_OPTION", "A")
        forbidden = self.STACK_FORBIDDEN.get(
            option, self.STACK_FORBIDDEN_OTHER)
        if self.res_type in forbidden:
            raise TypeError(
                f"Current stack ({option}) doesn't allow this option")

    def __call__(self, w, l, res_type=None):
        if res_type is not None:
            self.res_type = self._check_type(res_type)
        self._check_stack()
        w_um = max(self._microns(w), self.RES_SPECS[self.res_type][2])
        l_um = max(self._microns(l), self.RES_SPECS[self.res_type][2])
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.shapes = self._generate(w_um, l_um)
        return self

    def _generate(self, w_um, l_um):
        metal_name, res_name, ext = self.RES_SPECS[self.res_type]
        metal_layer = getattr(laylyr, f"{metal_name}_drawing")
        res_layer = getattr(laylyr, f"{res_name}_drawing")
        label_layer = getattr(laylyr, f"{metal_name}_Label_drawing")
        return [
            self._rect(res_layer, 0, 0, w_um, l_um),
            self._rect(metal_layer, -ext, 0, w_um + ext, l_um),
            self._pin(metal_layer, "M", -ext, 0, 0, l_um),
            self._label(label_layer, "M", -ext, 0, 0, l_um),
            self._pin(metal_layer, "P", w_um, 0, w_um + ext, l_um),
            self._label(label_layer, "P", w_um, 0, w_um + ext, l_um),
        ]


class _genericBulkResistor(baseCell):
    """Shared geometry for the upstream draw_res.py 3-terminal resistors.

    The marked resistor body is ``(0,0,w,l)``; Metal1 terminals extend
    left/right of the body and a COMP bulk tie (pin B) sits left of the
    left terminal.  Optional DNWELL and P+ guard-ring geometry uses
    upstream spacings; rings are approximated by four nested rectangles
    instead of a boolean-subtracted polygon.
    """

    dnwell_layer = laylyr.DNWELL_drawing
    comp_layer = laylyr.COMP_drawing
    poly_layer = laylyr.Poly2_drawing
    nplus_layer = laylyr.Nplus_drawing
    pplus_layer = laylyr.Pplus_drawing
    sab_layer = laylyr.SAB_drawing
    res_mk_layer = laylyr.RES_MK_drawing
    cont_layer = laylyr.Contact_drawing
    metal1_layer = laylyr.Metal1_drawing
    metal1_label_layer = laylyr.Metal1_Label_drawing
    lvpwell_layer = laylyr.LVPWELL_drawing
    nwell_layer = laylyr.Nwell_drawing
    resistor_layer = laylyr.Resistor_drawing
    dualgate_layer = laylyr.Dualgate_drawing

    # common constants (um)
    cont_size = .22
    cont_spc = .25
    met_cont_enc = .06
    comp_cont_enc = .07
    metal_w = .34
    met_inset = .01          # metal/contact inset inside the extension
    gr_w = .36               # guard ring COMP width
    gr2dnw = 2.5             # guard ring spacing to DNWELL
    dnw_enc_lvpwell = 2.5    # DNWELL enclosure of LVPWELL
    min_cmp_area = .2025
    tol = 1.05
    dg_enc_dnwell = .5       # Dualgate enclosure of DNWELL (5/6V)

    # family constants -- subclasses override
    body_kind = "comp"       # "comp" (diffusion) or "poly" (Poly2)
    salicided = True         # unsalicided families draw SAB
    res_ext = .29            # conductor extension past the marked body
    sab_enc_y = .23          # SAB extension past the body in y
    sab_ext_x = 0.           # SAB extension past the body in x
    body_impl = "n"          # "n" -> Nplus, "p" -> Pplus
    impl_body_enc = .16      # implant enclosure of the conductor
    impl_heads_only = False  # implant only on the extension heads
    tie_impl = "p"           # "p", "n" or "tap" (N+ iff deepnwell)
    tie_spc = .72            # conductor edge to bulk tie spacing
    tie_w = .36              # bulk tie COMP width
    impl_tie_enc = .16       # implant enclosure of the bulk tie
    tie_area_fix = True      # grow tie in y to satisfy min COMP area
    has_sub = False          # B tie is optional (sub parameter)
    terminals_inset = False  # terminal metal inside the extension
    well_kind = "lvpwell"    # "lvpwell", "nwell" or None
    lvpwell_tie_enc = .12    # LVPWELL extension on tie side (deepnwell)
    lvpwell_edge_enc = .43   # LVPWELL enclosure elsewhere (deepnwell)
    well_tie_enc = .12       # Nwell extension on the tie side
    well_edge_enc = .8       # Nwell enclosure elsewhere
    dnw_tie_enc = .62        # DNWELL extension on the tie side
    dnw_tie_enc_56 = .66     # DNWELL tie extension for volt="5/6V"
    dnw_edge_enc = .93       # DNWELL enclosure elsewhere
    gr_impl_enc = .16        # Pplus enclosure of the guard ring
    resistor_blk_enc = None  # Resistor block enclosure (high-Rs only)
    has_volt = False         # volt option (ppolyf_u_high_Rs only)

    min_w_um = .42
    min_l_um = .42
    default_w = "0.42u"
    default_l = "0.42u"

    def __init__(self, w=default_w, l=default_l):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.deepnwell = False
        self.pcmpgr = False
        self.sub = True
        self.volt = "3.3V"
        super().__init__([])

    @staticmethod
    def _check_volt(volt):
        if volt not in ("3.3V", "5/6V"):
            raise ValueError(f"Invalid voltage area: {volt!r}")
        return volt

    def _apply(self, w, l, **opts):
        """Clamp dimensions, store option overrides, regenerate shapes."""
        w_um = max(self._microns(w), self.min_w_um)
        l_um = max(self._microns(l), self.min_l_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        for key, value in opts.items():
            if value is None:
                continue
            if key == "volt":
                self.volt = self._check_volt(value)
            else:
                setattr(self, key, bool(value))
        self.shapes = self._generate(w_um, l_um)
        return self

    def _ring(self, layer, inner, outer):
        """Four rectangles covering the ring between two boxes."""
        ix1, iy1, ix2, iy2 = inner
        ox1, oy1, ox2, oy2 = outer
        return [
            self._rect(layer, ox1, oy1, ox2, iy1),   # bottom bar
            self._rect(layer, ox1, iy2, ox2, oy2),   # top bar
            self._rect(layer, ox1, iy1, ix1, iy2),   # left bar
            self._rect(layer, ix2, iy1, ox2, iy2),   # right bar
        ]

    def _generate(self, w_um, l_um):
        deepnwell = self.deepnwell
        pcmpgr = self.pcmpgr
        sub = self.sub or deepnwell      # upstream forces sub with DNWELL
        volt = self.volt if self.has_volt else "3.3V"
        ext = self.res_ext
        shapes = []

        # resistor body marker, SAB (unsalicided only), conductor, implant
        shapes.append(self._rect(self.res_mk_layer, 0, 0, w_um, l_um))
        if not self.salicided:
            shapes.append(self._rect(
                self.sab_layer, -self.sab_ext_x, -self.sab_enc_y,
                w_um + self.sab_ext_x, l_um + self.sab_enc_y))
        conductor = (self.poly_layer if self.body_kind == "poly"
                     else self.comp_layer)
        shapes.append(self._rect(conductor, -ext, 0, w_um + ext, l_um))
        impl = (self.nplus_layer if self.body_impl == "n"
                else self.pplus_layer)
        be = self.impl_body_enc
        if self.impl_heads_only:
            shapes.append(self._rect(
                impl, -ext - be, -be, 0, l_um + be))
            shapes.append(self._rect(
                impl, w_um, -be, w_um + ext + be, l_um + be))
        else:
            shapes.append(self._rect(
                impl, -ext - be, -be, w_um + ext + be, l_um + be))

        # RESISTOR block marker (ppolyf_u_high_Rs only)
        if self.resistor_blk_enc is not None:
            rb = self.resistor_blk_enc
            shapes.append(self._rect(
                self.resistor_layer, -ext - rb, -rb,
                w_um + ext + rb, l_um + rb))

        # Metal1 terminals (M left, P right) with contacts, pins, labels
        if self.terminals_inset:
            term = ((-ext + self.met_inset,
                     -ext + self.met_inset + self.metal_w),
                    (w_um + ext - self.met_inset - self.metal_w,
                     w_um + ext - self.met_inset))
        else:
            mc = self.cont_size + self.met_cont_enc
            term = ((-mc, self.met_cont_enc),
                    (w_um - self.met_cont_enc, w_um + mc))
        for (x1, x2), name in zip(term, ("M", "P")):
            shapes.append(self._rect(
                self.metal1_layer, x1, self.met_inset, x2,
                l_um - self.met_inset))
            shapes.extend(self.contactArray(
                self.cont_layer, x1, self.met_inset, x2,
                l_um - self.met_inset, self.met_cont_enc,
                self.cont_size, self.cont_spc))
            shapes.append(self._pin(
                self.metal1_layer, name, x1, self.met_inset, x2,
                l_um - self.met_inset))
            shapes.append(self._label(
                self.metal1_label_layer, name, x1, self.met_inset, x2,
                l_um - self.met_inset))

        # bulk tie left of the left terminal: COMP + implant + Metal1 + B
        tx2 = -ext - self.tie_spc
        tx1 = tx2 - self.tie_w
        tv = 0.
        if (self.tie_area_fix
                and l_um * self.tie_w < self.min_cmp_area):
            tv = (self.min_cmp_area / self.tie_w - l_um) / 2 * self.tol
        if sub or not self.has_sub:
            shapes.append(self._rect(
                self.comp_layer, tx1, -tv, tx2, l_um + tv))
            tie_impl = self.tie_impl
            if tie_impl == "tap":
                tie_impl = "n" if deepnwell else "p"
            tie_layer = (self.nplus_layer if tie_impl == "n"
                         else self.pplus_layer)
            te = self.impl_tie_enc
            shapes.append(self._rect(
                tie_layer, tx1 - te, -tv - te, tx2 + te, l_um + tv + te))
            shapes.append(self._rect(
                self.metal1_layer, tx1, -tv, tx2, l_um + tv))
            shapes.extend(self.contactArray(
                self.cont_layer, tx1, -tv, tx2, l_um + tv,
                self.comp_cont_enc, self.cont_size, self.cont_spc))
            shapes.append(self._pin(
                self.metal1_layer, "B", tx1, -tv, tx2, l_um + tv))
            shapes.append(self._label(
                self.metal1_label_layer, "B", tx1, -tv, tx2, l_um + tv))

        # well / DNWELL environment
        dnw_box = None
        if self.well_kind == "lvpwell":
            if deepnwell:
                shapes.append(self._rect(
                    self.lvpwell_layer, tx1 - self.lvpwell_tie_enc,
                    -self.lvpwell_edge_enc,
                    w_um + ext + self.lvpwell_edge_enc,
                    l_um + self.lvpwell_edge_enc))
                d = self.dnw_enc_lvpwell
                dnw_box = (tx1 - self.lvpwell_tie_enc - d,
                           -self.lvpwell_edge_enc - d,
                           w_um + ext + self.lvpwell_edge_enc + d,
                           l_um + self.lvpwell_edge_enc + d)
                shapes.append(self._rect(self.dnwell_layer, *dnw_box))
            else:
                shapes.append(self._rect(
                    self.lvpwell_layer, -ext - be, -be,
                    w_um + ext + be, l_um + be))
        elif self.well_kind == "nwell" and not deepnwell:
            shapes.append(self._rect(
                self.nwell_layer, tx1 - self.well_tie_enc,
                -self.well_edge_enc, w_um + ext + self.well_edge_enc,
                l_um + self.well_edge_enc))
        if deepnwell and self.well_kind != "lvpwell":
            tie_enc = (self.dnw_tie_enc_56 if volt == "5/6V"
                       else self.dnw_tie_enc)
            dnw_box = (tx1 - tie_enc, -self.dnw_edge_enc,
                       w_um + ext + self.dnw_edge_enc,
                       l_um + self.dnw_edge_enc)
            shapes.append(self._rect(self.dnwell_layer, *dnw_box))
            if volt == "5/6V":
                d = self.dg_enc_dnwell
                shapes.append(self._rect(
                    self.dualgate_layer, dnw_box[0] - d, dnw_box[1] - d,
                    dnw_box[2] + d, dnw_box[3] + d))
        elif volt == "5/6V" and not deepnwell:
            rb = self.resistor_blk_enc
            shapes.append(self._rect(
                self.dualgate_layer, -ext - rb, -rb,
                w_um + ext + rb, l_um + rb))

        # P+ guard ring outside the DNWELL (four-rect approximation)
        if dnw_box is not None and pcmpgr:
            g = self.gr2dnw
            ci = (dnw_box[0] - g, dnw_box[1] - g,
                  dnw_box[2] + g, dnw_box[3] + g)
            co = (ci[0] - self.gr_w, ci[1] - self.gr_w,
                  ci[2] + self.gr_w, ci[3] + self.gr_w)
            shapes.extend(self._ring(self.comp_layer, ci, co))
            e = self.gr_impl_enc
            pi = (ci[0] + e, ci[1] + e, ci[2] - e, ci[3] - e)
            po = (co[0] + e, co[1] + e, co[2] + e, co[3] + e)
            shapes.extend(self._ring(self.pplus_layer, pi, po))
        return shapes


class nplus_s_resistor(_genericBulkResistor):
    """3-terminal salicided N+ diffusion resistor (upstream
    ``nplus_s_resistor``).  LVPWELL enclosed; ``deepnwell`` adds
    LVPWELL+DNWELL and ``pcmpgr`` a simplified four-rectangle guard ring.
    ``sub`` omits the B tie when False."""

    res_ext = .29
    body_impl = "n"
    impl_body_enc = .16
    tie_impl = "p"
    tie_spc = .72
    impl_tie_enc = .16
    gr_impl_enc = .16
    has_sub = True
    well_kind = "lvpwell"

    def __init__(self, w="0.42u", l="0.42u",deepnwell=False,
                 pcmpgr=False, sub=True):
        super().__init__(w, l)
        self.deepnwell = bool(deepnwell)
        self.pcmpgr = bool(pcmpgr)
        self.sub = bool(sub)

    def __call__(self, w, l, deepnwell=None, pcmpgr=None, sub=None):
        return self._apply(
            w, l, deepnwell=deepnwell, pcmpgr=pcmpgr, sub=sub)


class pplus_s_resistor(_genericBulkResistor):
    """3-terminal salicided P+ diffusion resistor (upstream
    ``pplus_s_resistor``).  Nwell enclosed; ``deepnwell`` replaces the
    Nwell by DNWELL and ``pcmpgr`` adds a simplified guard ring."""

    res_ext = .29
    body_impl = "p"
    impl_body_enc = .16
    tie_impl = "n"
    tie_spc = .32
    impl_tie_enc = .16
    gr_impl_enc = .16
    well_kind = "nwell"
    well_tie_enc = .12
    well_edge_enc = .8
    dnw_tie_enc = .62
    dnw_edge_enc = .93

    def __init__(self, w="0.42u", l="0.42u",deepnwell=False,
                 pcmpgr=False):
        super().__init__(w, l)
        self.deepnwell = bool(deepnwell)
        self.pcmpgr = bool(pcmpgr)

    def __call__(self, w, l, deepnwell=None, pcmpgr=None):
        return self._apply(w, l, deepnwell=deepnwell, pcmpgr=pcmpgr)


class nplus_u_resistor(_genericBulkResistor):
    """3-terminal unsalicided N+ diffusion resistor (upstream
    ``nplus_u_resistor``).  SAB-masked body, LVPWELL enclosed;
    ``deepnwell``/``pcmpgr`` as in upstream, guard ring approximated by
    nested rectangles.  ``sub`` omits the B tie when False."""

    res_ext = .44
    salicided = False
    sab_enc_y = .23
    body_impl = "n"
    impl_body_enc = .18
    tie_impl = "p"
    tie_spc = .76
    impl_tie_enc = .18
    gr_impl_enc = .18
    terminals_inset = True
    has_sub = True
    well_kind = "lvpwell"

    def __init__(self, w="0.42u", l="0.42u",deepnwell=False,
                 pcmpgr=False, sub=True):
        super().__init__(w, l)
        self.deepnwell = bool(deepnwell)
        self.pcmpgr = bool(pcmpgr)
        self.sub = bool(sub)

    def __call__(self, w, l, deepnwell=None, pcmpgr=None, sub=None):
        return self._apply(
            w, l, deepnwell=deepnwell, pcmpgr=pcmpgr, sub=sub)


class pplus_u_resistor(_genericBulkResistor):
    """3-terminal unsalicided P+ diffusion resistor (upstream
    ``pplus_u_resistor``).  SAB-masked body, Nwell enclosed;
    ``deepnwell``/``pcmpgr`` as in upstream, guard ring approximated by
    nested rectangles."""

    res_ext = .44
    salicided = False
    sab_enc_y = .23
    body_impl = "p"
    impl_body_enc = .18
    tie_impl = "n"
    tie_spc = .34
    impl_tie_enc = .18
    gr_impl_enc = .18
    terminals_inset = True
    well_kind = "nwell"
    well_tie_enc = .12
    well_edge_enc = .93
    dnw_tie_enc = .62
    dnw_edge_enc = .93

    def __init__(self, w="0.42u", l="0.42u",deepnwell=False,
                 pcmpgr=False):
        super().__init__(w, l)
        self.deepnwell = bool(deepnwell)
        self.pcmpgr = bool(pcmpgr)

    def __call__(self, w, l, deepnwell=None, pcmpgr=None):
        return self._apply(w, l, deepnwell=deepnwell, pcmpgr=pcmpgr)


class npolyf_s_resistor(_genericBulkResistor):
    """3-terminal salicided N+ poly resistor (upstream
    ``npolyf_s_resistor``).  P+ substrate tie (N+ tap under
    ``deepnwell``); ``pcmpgr`` adds a simplified guard ring."""

    body_kind = "poly"
    res_ext = .29
    body_impl = "n"
    impl_body_enc = .30
    tie_impl = "tap"
    tie_spc = .72
    impl_tie_enc = .16
    tie_area_fix = False
    gr_impl_enc = .16
    well_kind = None
    dnw_tie_enc = .62
    dnw_edge_enc = 1.34

    def __init__(self, w="0.42u", l="0.42u",deepnwell=False,
                 pcmpgr=False):
        super().__init__(w, l)
        self.deepnwell = bool(deepnwell)
        self.pcmpgr = bool(pcmpgr)

    def __call__(self, w, l, deepnwell=None, pcmpgr=None):
        return self._apply(w, l, deepnwell=deepnwell, pcmpgr=pcmpgr)


class ppolyf_s_resistor(_genericBulkResistor):
    """3-terminal salicided P+ poly resistor (upstream
    ``ppolyf_s_resistor``).  P+ substrate tie (N+ tap under
    ``deepnwell``); ``pcmpgr`` adds a simplified guard ring."""

    body_kind = "poly"
    res_ext = .29
    body_impl = "p"
    impl_body_enc = .30
    tie_impl = "tap"
    tie_spc = .86
    impl_tie_enc = .16
    tie_area_fix = False
    gr_impl_enc = .16
    well_kind = None
    dnw_tie_enc = .62
    dnw_edge_enc = 1.34

    def __init__(self, w="0.42u", l="0.42u",deepnwell=False,
                 pcmpgr=False):
        super().__init__(w, l)
        self.deepnwell = bool(deepnwell)
        self.pcmpgr = bool(pcmpgr)

    def __call__(self, w, l, deepnwell=None, pcmpgr=None):
        return self._apply(w, l, deepnwell=deepnwell, pcmpgr=pcmpgr)


class npolyf_u_resistor(_genericBulkResistor):
    """3-terminal unsalicided N+ poly resistor (upstream
    ``npolyf_u_resistor``).  SAB-masked body, P+ substrate tie (N+ tap
    under ``deepnwell``); ``pcmpgr`` adds a simplified guard ring."""

    body_kind = "poly"
    salicided = False
    res_ext = .51
    sab_enc_y = .28
    body_impl = "n"
    impl_body_enc = .30
    tie_impl = "tap"
    tie_spc = .72
    impl_tie_enc = .16
    tie_area_fix = False
    gr_impl_enc = .16
    terminals_inset = True
    well_kind = None
    dnw_tie_enc = .62
    dnw_edge_enc = 1.34

    def __init__(self, w="0.42u", l="0.42u",deepnwell=False,
                 pcmpgr=False):
        super().__init__(w, l)
        self.deepnwell = bool(deepnwell)
        self.pcmpgr = bool(pcmpgr)

    def __call__(self, w, l, deepnwell=None, pcmpgr=None):
        return self._apply(w, l, deepnwell=deepnwell, pcmpgr=pcmpgr)


class ppolyf_u_resistor(_genericBulkResistor):
    """3-terminal unsalicided P+ poly resistor (upstream
    ``ppolyf_u_resistor``).  SAB-masked body, P+ substrate tie (N+ tap
    under ``deepnwell``); ``pcmpgr`` adds a simplified guard ring."""

    body_kind = "poly"
    salicided = False
    res_ext = .51
    sab_enc_y = .28
    body_impl = "p"
    impl_body_enc = .30
    tie_impl = "tap"
    tie_spc = .86
    impl_tie_enc = .16
    tie_area_fix = False
    gr_impl_enc = .16
    terminals_inset = True
    well_kind = None
    dnw_tie_enc = .62
    dnw_edge_enc = 1.34

    def __init__(self, w="0.42u", l="0.42u",deepnwell=False,
                 pcmpgr=False):
        super().__init__(w, l)
        self.deepnwell = bool(deepnwell)
        self.pcmpgr = bool(pcmpgr)

    def __call__(self, w, l, deepnwell=None, pcmpgr=None):
        return self._apply(w, l, deepnwell=deepnwell, pcmpgr=pcmpgr)


class ppolyf_u_high_Rs_resistor(_genericBulkResistor):
    """High-Rs unsalicided P+ poly resistor (upstream
    ``ppolyf_u_high_Rs_resistor``).  Resistor-block marked SAB body with
    Pplus heads; ``volt`` selects "3.3V" or "5/6V" (Dualgate marker);
    ``deepnwell``/``pcmpgr`` as in upstream, guard ring approximated by
    nested rectangles."""

    body_kind = "poly"
    salicided = False
    res_ext = .64
    sab_enc_y = .28
    sab_ext_x = .1
    body_impl = "p"
    impl_body_enc = .18
    impl_heads_only = True
    tie_impl = "tap"
    tie_spc = .7
    tie_w = .42
    impl_tie_enc = .02
    tie_area_fix = False
    gr_impl_enc = .02
    terminals_inset = True
    well_kind = None
    dnw_tie_enc = .62
    dnw_edge_enc = 1.34
    resistor_blk_enc = .4
    has_volt = True

    def __init__(self, w="0.42u", l="0.42u",volt="3.3V",
                 deepnwell=False, pcmpgr=False):
        super().__init__(w, l)
        self.volt = self._check_volt(volt)
        self.deepnwell = bool(deepnwell)
        self.pcmpgr = bool(pcmpgr)

    def __call__(self, w, l, volt=None, deepnwell=None, pcmpgr=None):
        return self._apply(
            w, l, volt=volt, deepnwell=deepnwell, pcmpgr=pcmpgr)


class nwell_resistor(nwell):
    """3-terminal Nwell resistor (upstream ``nwell_resistor``).

    Shares the corrected ``nwell`` geometry: Nwell extends +/-0.48um,
    RES_MK y +/-0.50um, external N+ terminals +/-0.36um and a P+ bulk tie
    separated 0.84+0.36um; only the upstream w/l minima and defaults
    differ."""

    min_w_um = .42
    min_l_um = .42
    default_w = "0.42u"
    default_l = "0.42u"

    def __init__(self, w=default_w, l=default_l):
        super().__init__(w, l)


class pwell_resistor(baseCell):
    """3-terminal Pwell resistor (upstream ``pwell_resistor``).

    LVPWELL body under a mandatory DNWELL; external P+ terminals carry
    the M/P pins and an N+ bulk tie carries B.  ``pcmpgr`` adds a P+
    guard ring approximated by four nested rectangles at the upstream
    spacings."""

    lvpwell_layer = laylyr.LVPWELL_drawing
    dnwell_layer = laylyr.DNWELL_drawing
    comp_layer = laylyr.COMP_drawing
    nplus_layer = laylyr.Nplus_drawing
    pplus_layer = laylyr.Pplus_drawing
    res_mk_layer = laylyr.RES_MK_drawing
    cont_layer = laylyr.Contact_drawing
    metal1_layer = laylyr.Metal1_drawing
    metal1_label_layer = laylyr.Metal1_Label_drawing

    # constants (um)
    well_ext = .48         # LVPWELL extension past the marked body
    res_mk_y = .50         # RES_MK y-extension past the body
    dnw_enc = 2.5          # DNWELL enclosure of LVPWELL
    term_w = .36           # P+ terminal stripe width
    term_inset = .12       # terminal y-inset inside the stripe
    impl_enc = .16         # implant enclosure
    tie_spc = .84          # B tie separation from the terminal stripe
    tie_w = .36            # B tie width
    gr2dnw = 2.5           # guard ring spacing to DNWELL
    gr_w = .36             # guard ring COMP width
    cont_size = .22
    cont_spc = .25
    cont_enc = .07

    min_w_um = .42
    min_l_um = .42
    default_w = "0.42u"
    default_l = "0.42u"

    def __init__(self, w="0.42u", l="0.42u",pcmpgr=False):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.pcmpgr = bool(pcmpgr)
        super().__init__([])

    def __call__(self, w, l, pcmpgr=None):
        w_um = max(self._microns(w), self.min_w_um)
        l_um = max(self._microns(l), self.min_l_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        if pcmpgr is not None:
            self.pcmpgr = bool(pcmpgr)
        self.shapes = self._generate(w_um, l_um)
        return self

    def _ring(self, layer, inner, outer):
        """Four rectangles covering the ring between two boxes."""
        ix1, iy1, ix2, iy2 = inner
        ox1, oy1, ox2, oy2 = outer
        return [
            self._rect(layer, ox1, oy1, ox2, iy1),
            self._rect(layer, ox1, iy2, ox2, oy2),
            self._rect(layer, ox1, iy1, ix1, iy2),
            self._rect(layer, ix2, iy1, ox2, iy2),
        ]

    def _generate(self, w_um, l_um):
        shapes = []
        shapes.append(self._rect(
            self.res_mk_layer, 0, -self.res_mk_y, w_um,
            l_um + self.res_mk_y))
        shapes.append(self._rect(
            self.lvpwell_layer, -self.well_ext, 0,
            w_um + self.well_ext, l_um))
        dnw_box = (-self.well_ext - self.dnw_enc, -self.dnw_enc,
                   w_um + self.well_ext + self.dnw_enc,
                   l_um + self.dnw_enc)
        shapes.append(self._rect(self.dnwell_layer, *dnw_box))

        # P+ guard ring outside the DNWELL (four-rect approximation)
        if self.pcmpgr:
            g = self.gr2dnw
            ci = (dnw_box[0] - g, dnw_box[1] - g,
                  dnw_box[2] + g, dnw_box[3] + g)
            co = (ci[0] - self.gr_w, ci[1] - self.gr_w,
                  ci[2] + self.gr_w, ci[3] + self.gr_w)
            shapes.extend(self._ring(self.comp_layer, ci, co))
            e = self.impl_enc
            pi = (ci[0] + e, ci[1] + e, ci[2] - e, ci[3] - e)
            po = (co[0] + e, co[1] + e, co[2] + e, co[3] + e)
            shapes.extend(self._ring(self.pplus_layer, pi, po))

        # P+ terminal stripes inside the marked body edges
        for x1, x2, name in (
            (-self.term_w, 0, "M"),
            (w_um, w_um + self.term_w, "P"),
        ):
            shapes.append(self._rect(
                self.comp_layer, x1, self.term_inset, x2,
                l_um - self.term_inset))
            shapes.append(self._rect(
                self.pplus_layer, x1 - self.impl_enc,
                self.term_inset - self.impl_enc, x2 + self.impl_enc,
                l_um - self.term_inset + self.impl_enc))
            shapes.append(self._rect(
                self.metal1_layer, x1, self.term_inset, x2,
                l_um - self.term_inset))
            shapes.extend(self.contactArray(
                self.cont_layer, x1, self.term_inset, x2,
                l_um - self.term_inset, self.cont_enc, self.cont_size,
                self.cont_spc))
            shapes.append(self._pin(
                self.metal1_layer, name, x1, self.term_inset, x2,
                l_um - self.term_inset))
            shapes.append(self._label(
                self.metal1_label_layer, name, x1, self.term_inset, x2,
                l_um - self.term_inset))

        # N+ bulk tie outside the well edge
        tx2 = -self.term_w - self.tie_spc
        tx1 = tx2 - self.tie_w
        shapes.append(self._rect(self.comp_layer, tx1, 0, tx2, l_um))
        shapes.append(self._rect(
            self.nplus_layer, tx1 - self.impl_enc, -self.impl_enc,
            tx2 + self.impl_enc, l_um + self.impl_enc))
        shapes.append(self._rect(
            self.metal1_layer, tx1, 0, tx2, l_um))
        shapes.extend(self.contactArray(
            self.cont_layer, tx1, 0, tx2, l_um,
            self.cont_enc, self.cont_size, self.cont_spc))
        shapes.append(self._pin(
            self.metal1_layer, "B", tx1, 0, tx2, l_um))
        shapes.append(self._label(
            self.metal1_label_layer, "B", tx1, 0, tx2, l_um))
        return shapes
