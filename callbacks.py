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

from quantiphy import Quantity


class baseInst:
    def __init__(self, labels_dict: dict):
        self._labelsDict = labels_dict


class dnwpw(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.r_w = Quantity(self._labelsDict['@r_w'].labelValue)
        self.r_l = Quantity(self._labelsDict['@r_l'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)

    def area_parm(self):
        return self.r_w * self.r_l

    def pj_parm(self):
        return 2 * (self.r_w + self.r_l)


class mim_2p0fF(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)


class nmos_3p3(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)

        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)
        self.nf = int(self._labelsDict['@nf'].labelValue)

    def ad_parm(self):
        return int(
            (self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real

    def pd_parm(self):
        return 2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real)

    def as_parm(self):
        return int(
            (self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real

    def ps_parm(self):
        return 2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real)

    def nrd_parm(self):
        return Quantity('0.18u').real / self.W.real

    def nrs_parm(self):
        return Quantity('0.18u').real / self.W.real


class nmos_3p3_sab(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)
        self.nf = int(self._labelsDict['@nf'].labelValue)

    def ad_parm(self):
        return (int((self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real)

    def pd_parm(self):
        return (2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real))

    def as_parm(self):
        return (int((self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real)

    def ps_parm(self):
        return (2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real))

    def nrd_parm(self):
        return Quantity('0.18u').real / self.W.real

    def nrs_parm(self):
        return Quantity('0.18u').real / self.W.real


class nmos_6p0(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)
        self.nf = int(self._labelsDict['@nf'].labelValue)

    def ad_parm(self):
        return (int((self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real)

    def pd_parm(self):
        return (2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real))

    def as_parm(self):
        return (int((self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real)

    def ps_parm(self):
        return (2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real))

    def nrd_parm(self):
        return Quantity('0.18u').real / self.W.real

    def nrs_parm(self):
        return Quantity('0.18u').real / self.W.real


class nmos_6p0_nat(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)
        self.nf = int(self._labelsDict['@nf'].labelValue)

    def ad_parm(self):
        return (int((self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real)

    def pd_parm(self):
        return (2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real))

    def as_parm(self):
        return (int((self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real)

    def ps_parm(self):
        return (2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real))

    def nrd_parm(self):
        return Quantity('0.18u').real / self.W.real

    def nrs_parm(self):
        return Quantity('0.18u').real / self.W.real


class nmoscap_3p3(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)


class nmoscap_6p0(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)


class np_3p3(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.r_w = Quantity(self._labelsDict['@r_w'].labelValue)
        self.r_l = Quantity(self._labelsDict['@r_l'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)

    def area_parm(self):
        return self.r_w * self.r_l

    def pj_parm(self):
        return 2 * (self.r_w + self.r_l)


class nplus_u(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)


class npolyf_u(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)


class nwell(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)


class pmos_3p3(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)
        self.nf = int(self._labelsDict['@nf'].labelValue)

    def ad_parm(self):
        return int(
            (self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real

    def pd_parm(self):
        return 2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real)

    def as_parm(self):
        return int(
            (self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real

    def ps_parm(self):
        return 2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real)

    def nrd_parm(self):
        return Quantity('0.18u').real / self.W.real

    def nrs_parm(self):
        return Quantity('0.18u').real / self.W.real

    def pd_parm(self):
        return 2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real)

    def as_parm(self):
        return int(
            (self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real

    def ps_parm(self):
        return 2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real)

    def nrd_parm(self):
        return Quantity('0.18u').real / self.W.real

    def nrs_parm(self):
        return Quantity('0.18u').real / self.W.real


class pmos_6p0(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)
        self.nf = int(self._labelsDict['@nf'].labelValue)

    def ad_parm(self):
        return int(
            (self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real

    def pd_parm(self):
        return 2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real)

    def as_parm(self):
        return int(
            (self.nf.real + 1) / 2) * self.W.real / self.nf.real * Quantity(
            '0.18u').real

    def ps_parm(self):
        return 2 * int((self.nf.real + 1) / 2) * (
                self.W.real / self.nf.real + Quantity('0.18u').real)

    def nrd_parm(self):
        return Quantity('0.18u').real / self.W.real

    def nrs_parm(self):
        return Quantity('0.18u').real / self.W.real


class pmoscap_3p3(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)


class pmoscap_6p0(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)


class pplus_u(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)


class ppolyf_u(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)


class rm1(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict['@W'].labelValue)
        self.L = Quantity(self._labelsDict['@L'].labelValue)
        self.m = int(self._labelsDict['@m'].labelValue)


class vnpn_10x10(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)


class vpnp_10x10(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
