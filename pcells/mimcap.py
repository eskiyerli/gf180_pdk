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


class mim_2p0fF(baseCell):
    """GF180MCU 2.0 fF/um2 MIM capacitor (LVS device mim_single_2p0fF).

    ``option`` selects the metal stack: A -> Metal3/Metal2/Via2 (3LM),
    B -> Metal4/Metal3/Via3 (4LM), C -> Metal5/Metal4/Via4 (5LM). When not
    given, the GF_PDK_OPTION environment variable is used (default A).
    """

    min_size_um = 5.0    # GF DRC MIM.8a: FuseTop area >= 25 um2
    default_w = "5u"
    default_l = "5u"

    fuse_top_layer = laylyr.FuseTop_drawing
    cap_mk_layer = laylyr.CAP_MK_drawing
    mim_l_mk_layer = laylyr.MIM_L_MK_drawing

    bot_enc = .6         # bottom plate extension over top plate
    via_size = .26
    via_enc = .40
    via_spacing = .50
    mim_l_h = .1         # MIM_L_MK strip height

    # option -> (top metal, bottom metal, via cut) layer names
    OPTION_LAYERS = {
        "A": ("Metal3", "Metal2", "Via2"),
        "B": ("Metal4", "Metal3", "Via3"),
        "C": ("Metal5", "Metal4", "Via4"),
    }

    def __init__(self, w=default_w, l=default_l, option=None):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.option = self._resolve_option(option)
        super().__init__([])

    @staticmethod
    def _resolve_option(option):
        if option is None:
            option = os.environ.get("GF_PDK_OPTION", "A")
        option = str(option).upper()
        if option not in ("A", "B", "C"):
            raise ValueError(f"Invalid MIM stack option: {option}")
        return option

    def __call__(self, w, l, option=None):
        w_um = max(self._microns(w), self.min_size_um)
        l_um = max(self._microns(l), self.min_size_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.option = self._resolve_option(option)
        self.shapes = self._generate(w_um, l_um)
        return self

    def _generate(self, w_um, l_um):
        top_name, bot_name, via_name = self.OPTION_LAYERS[self.option]
        top_layer = getattr(laylyr, f"{top_name}_drawing")
        bot_layer = getattr(laylyr, f"{bot_name}_drawing")
        via_layer = getattr(laylyr, f"{via_name}_drawing")
        top_label_layer = getattr(laylyr, f"{top_name}_Label_drawing")
        bot_label_layer = getattr(laylyr, f"{bot_name}_Label_drawing")

        shapes = []
        # plates
        shapes.append(self._rect(
            bot_layer, -self.bot_enc, -self.bot_enc,
            w_um + self.bot_enc, l_um + self.bot_enc))
        shapes.append(self._rect(top_layer, 0, 0, w_um, l_um))
        shapes.append(self._rect(self.fuse_top_layer, 0, 0, w_um, l_um))

        # via array within the top plate
        shapes.extend(self.contactArray(
            via_layer, 0, 0, w_um, l_um,
            self.via_enc, self.via_size, self.via_spacing))

        # markers
        shapes.append(self._rect(
            self.mim_l_mk_layer, 0, 0, w_um, self.mim_l_h))
        shapes.append(self._rect(
            self.cap_mk_layer, -self.bot_enc, -self.bot_enc,
            w_um + self.bot_enc, l_um + self.bot_enc))

        # terminals: G on the top plate, B on the bottom plate
        shapes.append(self._pin(top_layer, "G", 0, 0, w_um, l_um))
        shapes.append(self._label(top_label_layer, "G", 0, 0, w_um, l_um))
        shapes.append(self._pin(
            bot_layer, "B", -self.bot_enc, -self.bot_enc,
            w_um + self.bot_enc, l_um + self.bot_enc))
        shapes.append(self._label(
            bot_label_layer, "B", -self.bot_enc, -self.bot_enc,
            w_um + self.bot_enc, l_um + self.bot_enc))
        return shapes


class mimcap(baseCell):
    """Generic upstream-compatible GF180MCU MIM capacitor generator.

    Mirrors the upstream ``mimcap(w, l, mim_option, metal_level)`` PCell.
    ``mim_option`` is ``MIM-A`` (top plate Metal3/FuseTop over Metal2 with
    Via2, per upstream ``draw_mimcap``) or ``MIM-B``, where ``metal_level``
    selects the stack: M4 -> Metal4/Metal3/Via3, M5 -> Metal5/Metal4/Via4,
    M6 -> MetalTop/Metal5/Via5. The GF_PDK_OPTION environment variable
    (default A) restricts the choice: stack option A allows only MIM-A
    while options B and C allow only MIM-B; an invalid combination raises
    TypeError. Minimum ``w``/``l`` is the upstream 0.28 um.
    """

    min_size_um = 0.28   # upstream draw_mimcap minimum w/l
    default_w = "0.28u"
    default_l = "0.28u"

    fuse_top_layer = laylyr.FuseTop_drawing
    cap_mk_layer = laylyr.CAP_MK_drawing
    mim_l_mk_layer = laylyr.MIM_L_MK_drawing

    bot_enc = .6         # bottom plate extension over top plate
    via_size = .26
    via_enc = .40
    via_spacing = .50
    mim_l_h = .1         # MIM_L_MK strip height

    mim_options = ("MIM-A", "MIM-B")
    metal_levels = ("M4", "M5", "M6")

    # MIM-A always uses Metal3 top / Metal2 bottom / Via2 (upstream).
    MIM_A_LAYERS = ("Metal3", "Metal2", "Via2")
    # metal_level -> (top metal, bottom metal, via cut) for MIM-B
    METAL_LEVEL_LAYERS = {
        "M4": ("Metal4", "Metal3", "Via3"),
        "M5": ("Metal5", "Metal4", "Via4"),
        "M6": ("MetalTop", "Metal5", "Via5"),
    }

    def __init__(self, w=default_w, l=default_l, mim_option="MIM-A",
                 metal_level="M4"):
        self.w = self._meters(w)
        self.l = self._meters(l)
        self.mim_option = self._resolve_mim_option(mim_option)
        self.metal_level = self._resolve_metal_level(metal_level)
        super().__init__([])

    @classmethod
    def _resolve_mim_option(cls, mim_option):
        mim_option = str(mim_option).upper()
        if mim_option not in cls.mim_options:
            raise ValueError(f"Invalid mim_option: {mim_option}")
        return mim_option

    @classmethod
    def _resolve_metal_level(cls, metal_level):
        metal_level = str(metal_level).upper()
        if metal_level not in cls.metal_levels:
            raise ValueError(f"Invalid metal_level: {metal_level}")
        return metal_level

    def _check_stack(self):
        """Apply the GF_PDK_OPTION restriction (upstream produce_impl)."""
        stack = os.environ.get("GF_PDK_OPTION", "A").upper()
        if stack == "A":
            allowed = self.mim_option == "MIM-A"
        elif stack in ("B", "C"):
            allowed = self.mim_option == "MIM-B"
        else:
            raise ValueError(f"Invalid GF_PDK_OPTION: {stack}")
        if not allowed:
            raise TypeError(
                f"Current stack ({stack}) doesn't allow this option")

    def _stack_layers(self):
        """(top metal, bottom metal, via cut) layer names for the stack."""
        if self.mim_option == "MIM-A":
            return self.MIM_A_LAYERS
        return self.METAL_LEVEL_LAYERS[self.metal_level]

    def __call__(self, w=None, l=None, mim_option=None, metal_level=None):
        if w is not None:
            self.w = self._meters(w)
        if l is not None:
            self.l = self._meters(l)
        if mim_option is not None:
            self.mim_option = self._resolve_mim_option(mim_option)
        if metal_level is not None:
            self.metal_level = self._resolve_metal_level(metal_level)
        self._check_stack()
        w_um = max(self.w * 1e6, self.min_size_um)
        l_um = max(self.l * 1e6, self.min_size_um)
        self.w = w_um * 1e-6
        self.l = l_um * 1e-6
        self.shapes = self._generate(w_um, l_um)
        return self

    def _generate(self, w_um, l_um):
        top_name, bot_name, via_name = self._stack_layers()
        top_layer = getattr(laylyr, f"{top_name}_drawing")
        bot_layer = getattr(laylyr, f"{bot_name}_drawing")
        via_layer = getattr(laylyr, f"{via_name}_drawing")
        top_label_layer = getattr(laylyr, f"{top_name}_Label_drawing")
        bot_label_layer = getattr(laylyr, f"{bot_name}_Label_drawing")

        shapes = []
        # plates
        shapes.append(self._rect(
            bot_layer, -self.bot_enc, -self.bot_enc,
            w_um + self.bot_enc, l_um + self.bot_enc))
        shapes.append(self._rect(top_layer, 0, 0, w_um, l_um))
        shapes.append(self._rect(self.fuse_top_layer, 0, 0, w_um, l_um))

        # via array within the top plate
        shapes.extend(self.contactArray(
            via_layer, 0, 0, w_um, l_um,
            self.via_enc, self.via_size, self.via_spacing))

        # markers
        shapes.append(self._rect(
            self.mim_l_mk_layer, 0, 0, w_um, self.mim_l_h))
        shapes.append(self._rect(
            self.cap_mk_layer, -self.bot_enc, -self.bot_enc,
            w_um + self.bot_enc, l_um + self.bot_enc))

        # terminals: G on the top plate, B on the bottom plate
        shapes.append(self._pin(top_layer, "G", 0, 0, w_um, l_um))
        shapes.append(self._label(top_label_layer, "G", 0, 0, w_um, l_um))
        shapes.append(self._pin(
            bot_layer, "B", -self.bot_enc, -self.bot_enc,
            w_um + self.bot_enc, l_um + self.bot_enc))
        shapes.append(self._label(
            bot_label_layer, "B", -self.bot_enc, -self.bot_enc,
            w_um + self.bot_enc, l_um + self.bot_enc))
        return shapes
