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
"""Layout verification: staged fixed-layout GDS vs upstream fixtures.

Compares the ``pcells/*.gds`` fixed-layout fixtures (10 BJT variants +
efuse) shape-for-shape against the upstream KLayout pymacros fixtures
they were ported from. Shape-set equality per (layer, datatype) proves
the staged layouts are faithful; any drift would silently corrupt
silicon for these cells.

Requires the ``klayout`` Python module (``pip install klayout``) and the
upstream repo checkout — point ``GF180_UPSTREAM`` at it or keep the
default sibling-checkout layout. DRC/LVS *deck* execution additionally
needs the KLayout executable (the pymod cannot run Ruby .drc/.lvs
decks); that remains a Phase-2 follow-up.
"""

import hashlib
import os
import unittest
from pathlib import Path

PDK_ROOT = Path(__file__).resolve().parent.parent

try:
    import klayout.db as kdb
except ImportError:
    kdb = None

FIXTURES = tuple(
    ("bjt", n) for n in
    ("vnpn_0p54x16", "vnpn_0p54x2", "vnpn_0p54x4", "vnpn_0p54x8",
     "vnpn_10x10", "vnpn_5x5",
     "vpnp_0p42x10", "vpnp_0p42x5", "vpnp_10x10", "vpnp_5x5")
) + (("efuse", "efuse"),)

_DEFAULT_UP = Path(os.environ.get(
    "GF180_UPSTREAM",
    Path(__file__).resolve().parents[5] /
    "GitHub/globalfoundries-pdk-libs-gf180mcu_fd_pr"))


def _shape_signature(path: Path) -> dict:
    """{(layer, datatype): sorted frozenset of polygon point lists}."""
    ly = kdb.Layout()
    ly.read(str(path))
    sig = {}
    for ci in ly.each_cell():
        cell = ly.cell(ci.name)
        for li in ly.each_layer():
            layer = ly.layer(li)
            shapes = sorted(
                tuple(
                    (pt.x, pt.y)
                    for pt in sh.polygon.each_point_hull()
                ) if sh.is_polygon() or sh.is_box() or sh.is_path()
                else ("other",)
                for sh in cell.each_shape(li)
            )
            sig.setdefault((layer[0], layer[1]), []).extend(shapes)
    return {k: sorted(v) for k, v in sig.items()}


@unittest.skipUnless(kdb, "klayout python module not installed")
class TestFixtureGdsVsUpstream(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up_cells = (_DEFAULT_UP / "cells" / "klayout" / "pymacros"
                        / "cells")
        if not (cls.up_cells / "bjt" / "vnpn_10x10.gds").exists():
            raise unittest.SkipTest(
                f"upstream checkout not found: {cls.up_cells}")

    def test_fixtures_match_upstream(self):
        for family, name in FIXTURES:
            with self.subTest(cell=name):
                ours = PDK_ROOT / "pcells" / "data" / family / \
                    f"{name}.gds"
                up = self.up_cells / family / f"{name}.gds"
                self.assertTrue(ours.is_file(), ours)
                self.assertTrue(up.is_file(), up)
                if hashlib.sha256(ours.read_bytes()).digest() == \
                        hashlib.sha256(up.read_bytes()).digest():
                    continue  # byte-identical
                self.assertEqual(
                    _shape_signature(ours), _shape_signature(up),
                    f"{name}: shape mismatch vs upstream fixture")

    def test_upstream_testcase_library_present(self):
        tc = _DEFAULT_UP / "cells" / "klayout" / "testing" / \
            "testcases" / "bjt_pcells.gds"
        if not tc.is_file():
            self.skipTest("upstream testcases golden not present")
        ly = kdb.Layout()
        ly.read(str(tc))
        cells = {c.name for c in ly.each_cell()}
        for name in FIXTURES[:10]:
            with self.subTest(cell=name):
                self.assertIn(name, cells)


if __name__ == "__main__":
    unittest.main()
