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
"""Cross-simulator consistency for the staged GF180MCU model sets.

Runs one canonical DC-sweep circuit through every installed simulator
(vacask / ngspice / Xyce) and requires the staged libraries to agree
within tolerance. This is the direct check for porting defects in the
VACASK behavioral rewrites and the Xyce syntax patches: all three decks
derive from the same upstream model cards, so device currents must match.

Stdlib-only; the test is skipped unless at least two simulators are
installed.
"""

import math
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PDK_ROOT = Path(__file__).resolve().parent.parent
MODELS = PDK_ROOT / "models"

# Model/stimulus set shared by all decks: one 3.3V nmos Id-Vd curve,
# one np_3p3 diode IV curve, one nplus_u sheet-resistance point.
VDS_GRID = "0 3.3 0.3"
VD_GRID = "-1 1.1 0.21"


def _vacask_fixture(tmp: Path):
    m = (MODELS / "vacask").as_posix()
    sim = tmp / "xsim_vacask.sim"
    sim.write_text(f"""* cross-sim canonical circuit
include "{m}/mos.lib" section=tt
include "{m}/diode.lib" section=tt
include "{m}/res.lib" section=tt
include "{m}/common.lib"
include "{m}/design.lib"
model vd vsource
model vg vsource
model vn vsource
vd (d 0) vd dc=0
vg (g 0) vg dc=1.0
x1 (d g 0 0) nmos_3p3 w=4u l=0.28u
vn (n 0) vn dc=0
d1 (n 0) np_3p3 area=1e-12 pj=4e-6
x2 (d 0 0) nplus_u r_width=1u r_length=10u
control
  options rawfile="ascii"
  sweep vd instance="vd" parameter="dc" from=0 to=3.3 step=0.3
    analysis mos op
  sweep vn instance="vn" parameter="dc" from=-1 to=1.1 step=0.21
    analysis dio op
endc
""")
    return sim, ["mos", "dio"]


def _ngspice_fixture(tmp: Path):
    m = (MODELS / "ngspice").as_posix()
    cir = tmp / "xsim_ngspice.cir"
    cir.write_text(f"""* cross-sim canonical circuit
Vd d 0 dc 0
Vg g 0 dc 1.0
X1 d g 0 0 nmos_3p3 W=4u L=0.28u
Vn n 0 dc 0
D1 n 0 np_3p3 AREA=1e-12 PJ=4e-6
X2 d 0 0 nplus_u r_width=1u r_length=10u
.control
set filetype=ascii
dc Vd {VDS_GRID}
wrdata xsim_ngspice_mos.csv i(Vd)
dc Vn {VD_GRID}
wrdata xsim_ngspice_dio.csv abs(i(Vn))
quit
.endc
.include "{m}/design.ngspice"
.lib "{m}/sm141064.ngspice" typical
.lib "{m}/sm141064.ngspice" diode_typical
.lib "{m}/sm141064.ngspice" res_typical
.end
""")
    return cir, ["mos", "dio"]


def _xyce_fixture(tmp: Path):
    m = (MODELS / "xyce").as_posix()
    cir = tmp / "xsim_xyce.cir"
    cir.write_text(f"""* cross-sim canonical circuit
Vd d 0 dc 0
Vg g 0 dc 1.0
X1 d g 0 0 nmos_3p3 W=4u L=0.28u
Vn n 0 dc 0
D1 n 0 np_3p3 AREA=1e-12 PJ=4e-6
X2 d 0 0 nplus_u r_width=1u r_length=10u
.dc Vd {VDS_GRID}
.print dc FORMAT=CSV file=xsim_xyce_mos.csv {{I(Vd)}}
.dc Vn {VD_GRID}
.print dc FORMAT=CSV file=xsim_xyce_dio.csv {{I(Vn)}}
.inc "{m}/design.xyce"
.lib "{m}/sm141064.xyce" typical
.lib "{m}/sm141064.xyce" diode_typical
.lib "{m}/sm141064.xyce" res_typical
.end
""")
    return cir, ["mos", "dio"]


def _read_ascii_raw(path: Path):
    names, points, in_vars, in_vals = [], [], False, False
    for line in path.read_text().splitlines():
        s = line.strip()
        if s == "Variables:":
            in_vars = True
        elif s == "Values:":
            in_vars, in_vals = False, True
        elif in_vars and s:
            p = s.split()
            if len(p) >= 2:
                names.append(p[1])
        elif in_vals and s:
            p = s.split()
            if len(p) == 1:
                points[-1].append(float(p[0]))
            else:
                points.append([float(p[1])])
    return names, points


def _read_wrdata_csv(path: Path):
    pts = []
    for line in path.read_text().splitlines():
        parts = line.split()
        nums = []
        for p in parts:
            try:
                nums.append(float(p))
            except ValueError:
                pass
        if len(nums) >= 2:
            pts.append((nums[0], abs(nums[1])))
    return pts


def _run(binary: str, arg: str, tmp: Path):
    result = subprocess.run([binary, arg], cwd=tmp, capture_output=True,
                            text=True, timeout=600)
    if result.returncode != 0:
        raise AssertionError(
            f"{binary} failed:\n{result.stdout[-1500:]}\n"
            f"{result.stderr[-1500:]}")


def _curves(tmp: Path) -> dict:
    """sim -> {series_name: [(v, |i|)]}."""
    out = {}
    if shutil.which("vacask"):
        sim, analyses = _vacask_fixture(tmp)
        _run("vacask", sim.name, tmp)
        curves = {}
        for a in analyses:
            names, points = _read_ascii_raw(tmp / f"{a}.raw")
            src = "vd" if a == "mos" else "vn"
            curves[a] = [(p[names.index(src)],
                          abs(p[names.index(f"{src}:flow(br)")]))
                         for p in points]
        out["vacask"] = curves
    if shutil.which("ngspice"):
        cir, analyses = _ngspice_fixture(tmp)
        _run("ngspice", cir.name, tmp)
        out["ngspice"] = {
            a: _read_wrdata_csv(tmp / f"xsim_ngspice_{a}.csv")
            for a in analyses}
    for exe in ("Xyce", "XyceNF", "xyce"):
        if shutil.which(exe):
            cir, analyses = _xyce_fixture(tmp)
            _run(exe, cir.name, tmp)
            out["xyce"] = {
                a: _read_wrdata_csv(tmp / f"xsim_xyce_{a}.csv")
                for a in analyses}
            break
    return out


class TestCrossSimulator(unittest.TestCase):
    def test_dc_curves_agree(self):
        with tempfile.TemporaryDirectory() as td:
            curves = _curves(Path(td))
        sims = sorted(curves)
        if len(sims) < 2:
            self.skipTest(
                f"need >=2 simulators for cross-check, found {sims}")
        ref = curves[sims[0]]
        for other in sims[1:]:
            for series, ref_pts in ref.items():
                with self.subTest(pair=(sims[0], other), series=series):
                    got = dict(curves[other][series])
                    errs = []
                    for v, i in ref_pts:
                        g = got.get(v)
                        if g is None or i <= 0 or g <= 0:
                            continue
                        errs.append(abs(math.log10(g) - math.log10(i)))
                    self.assertTrue(errs, f"{series}: no common points")
                    mean = sum(errs) / len(errs)
                    self.assertLessEqual(
                        mean, 0.05,
                        f"{other} vs {sims[0]} {series}: mean log10 "
                        f"err {mean:.3f}, max {max(errs):.3f}")
                    self.assertLessEqual(
                        max(errs), 0.15,
                        f"{other} vs {sims[0]} {series}: max log10 "
                        f"err {max(errs):.3f}")


if __name__ == "__main__":
    unittest.main()
