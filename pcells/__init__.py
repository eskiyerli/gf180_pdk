#    "Commons Clause" License Condition v1.0
#   #
#    The Software is provided to you by the Licensor under the License, as defined
#    below, subject to the following condition.
#
#    Without limiting other conditions in the License, the grant of rights under the
#    License will not include, and the License does not grant to you, the right to
#    Sell the Software.
#
#    For purposes of the foregoing, "Sell" means practicing any or all of the rights
#    granted to you under the License to provide to third parties, for a fee or other
#    consideration (including without limitation fees for hosting) a product or service whose value
#    derives, entirely or substantially, from the functionality of the Software. Any
#    license notice or attribution required by the License must also include this
#    Commons Clause License Condition notice.
#
#   Add-ons and extensions developed for this software may be distributed
#   under their own separate licenses.
#
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)
#
from .base import baseCell
from .diodes import (dnwpw, np_3p3, np_diode, pn_diode, nwp_diode,
                     dnwpw_diode, dnwps_diode, sc_diode)
from .mimcap import mim_2p0fF, mimcap
from .mosfet import (nmos_3p3, nmos_3p3_sab, nmos_6p0, nmos_6p0_nat,
                     pmos_3p3, pmos_3p3_sab, pmos_6p0,
                     nmos, pmos, nmos_10p0_asym, pmos_10p0_asym)
from .resistors import (nplus_u, pplus_u, npolyf_u, ppolyf_u, nwell, rm1,
                        metal_resistor, nplus_s_resistor, pplus_s_resistor,
                        nplus_u_resistor, pplus_u_resistor, nwell_resistor,
                        pwell_resistor, npolyf_s_resistor,
                        ppolyf_s_resistor, npolyf_u_resistor,
                        ppolyf_u_resistor, ppolyf_u_high_Rs_resistor)
from .moscaps import (nmoscap_3p3, nmoscap_6p0, pmoscap_3p3, pmoscap_6p0,
                      nmoscap, pmoscap, nmoscap_b, pmoscap_b)
from .bjt import (vnpn_10x10, vnpn_5x5, vnpn_0p54x16, vnpn_0p54x8,
                  vnpn_0p54x4, vnpn_0p54x2, vpnp_10x10, vpnp_5x5,
                  vpnp_0p42x10, vpnp_0p42x5, efuse, npn_bjt, pnp_bjt)

pcells = {
    "nmos_3p3": nmos_3p3,
    "nmos_3p3_sab": nmos_3p3_sab,
    "nmos_6p0": nmos_6p0,
    "nmos_6p0_nat": nmos_6p0_nat,
    "pmos_3p3": pmos_3p3,
    "pmos_3p3_sab": pmos_3p3_sab,
    "pmos_6p0": pmos_6p0,
    "np_3p3": np_3p3,
    "dnwpw": dnwpw,
    "mim_2p0fF": mim_2p0fF,
    "nplus_u": nplus_u,
    "pplus_u": pplus_u,
    "npolyf_u": npolyf_u,
    "ppolyf_u": ppolyf_u,
    "nwell": nwell,
    "rm1": rm1,
    "nmoscap_3p3": nmoscap_3p3,
    "nmoscap_6p0": nmoscap_6p0,
    "pmoscap_3p3": pmoscap_3p3,
    "pmoscap_6p0": pmoscap_6p0,
    "vnpn_10x10": vnpn_10x10,
    "vnpn_5x5": vnpn_5x5,
    "vnpn_0p54x16": vnpn_0p54x16,
    "vnpn_0p54x8": vnpn_0p54x8,
    "vnpn_0p54x4": vnpn_0p54x4,
    "vnpn_0p54x2": vnpn_0p54x2,
    "vpnp_10x10": vpnp_10x10,
    "vpnp_5x5": vpnp_5x5,
    "vpnp_0p42x10": vpnp_0p42x10,
    "vpnp_0p42x5": vpnp_0p42x5,
    "efuse": efuse,
    # Generic upstream generators (pcell views only, no symbols)
    "nmos": nmos,
    "pmos": pmos,
    "nmos_10p0_asym": nmos_10p0_asym,
    "pmos_10p0_asym": pmos_10p0_asym,
    "npn_bjt": npn_bjt,
    "pnp_bjt": pnp_bjt,
    "np_diode": np_diode,
    "pn_diode": pn_diode,
    "nwp_diode": nwp_diode,
    "dnwpw_diode": dnwpw_diode,
    "dnwps_diode": dnwps_diode,
    "sc_diode": sc_diode,
    "nmoscap": nmoscap,
    "pmoscap": pmoscap,
    "nmoscap_b": nmoscap_b,
    "pmoscap_b": pmoscap_b,
    "mimcap": mimcap,
    "metal_resistor": metal_resistor,
    "nplus_s_resistor": nplus_s_resistor,
    "pplus_s_resistor": pplus_s_resistor,
    "nplus_u_resistor": nplus_u_resistor,
    "pplus_u_resistor": pplus_u_resistor,
    "nwell_resistor": nwell_resistor,
    "pwell_resistor": pwell_resistor,
    "npolyf_s_resistor": npolyf_s_resistor,
    "ppolyf_s_resistor": ppolyf_s_resistor,
    "npolyf_u_resistor": npolyf_u_resistor,
    "ppolyf_u_resistor": ppolyf_u_resistor,
    "ppolyf_u_high_Rs_resistor": ppolyf_u_high_Rs_resistor,
}
