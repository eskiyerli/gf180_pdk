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
"""KLayout deck verification: run the staged DRC/LVS decks headless.

Executes the ``drc/gf180mcu*.drc`` and ``lvs/gf180mcu.lvs`` decks against
the staged fixture layouts using the same ``-rd`` variable contract as
``klayoutDRC.py``/``klayoutLVS.py``.

Requires the KLayout executable. Configure via environment:

- ``KLAYOUT_EXE``   path to ``klayout_app.exe``/``klayout``
  (default: ``%APPDATA%\\KLayout\\klayout_app.exe``)
- ``GF180_DRC_ALL`` ``1`` to run the full 3-deck x 3-option DRC matrix
  (each run is ~10 min); default runs main option-A only.

Note: the decks' Ruby ``pmap`` memory logger is patched for Windows —
upstream wrote ``[10,40].strip`` which crashes when ``pmap`` is absent
(``NilClass#strip``). Staged decks use ``to_s.strip``.
"""

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

PDK_ROOT = Path(__file__).resolve().parent.parent

KLAYOUT_EXE = os.environ.get(
    "KLAYOUT_EXE",
    os.path.expandvars(
        r"%APPDATA%\KLayout\klayout_app.exe"),
)
FIXTURE = PDK_ROOT / "pcells" / "data" / "bjt" / "vnpn_10x10.gds"

_GF180_OPTIONS = {
    "A": {"metal_top": "30K", "mim_option": "A", "metal_level": "3LM"},
    "B": {"metal_top": "11K", "mim_option": "B", "metal_level": "4LM"},
    "C": {"metal_top": "9K", "mim_option": "B", "metal_level": "5LM"},
}
_LVS_OPTIONS = {
    "A": {"metal_top": "30K", "mim_option": "A", "metal_level": "3LM",
          "poly_res": "1K", "mim_cap": "A"},
    "B": {"metal_top": "11K", "mim_option": "B", "metal_level": "4LM",
          "poly_res": "1K", "mim_cap": "B"},
    "C": {"metal_top": "9K", "mim_option": "B", "metal_level": "5LM",
          "poly_res": "1K", "mim_cap": "B"},
}
DECKS = {"main": "gf180mcu.drc", "antenna": "gf180mcu_antenna.drc",
         "density": "gf180mcu_density.drc"}


def _klayout():
    return KLAYOUT_EXE if Path(KLAYOUT_EXE).is_file() else None


def _run_klayout(args, timeout=3600):
    result = subprocess.run([_klayout()] + args, capture_output=True,
                            text=True, timeout=timeout)
    log = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        raise AssertionError(
            f"klayout failed ({args[2]}):\n{log[-2000:]}")
    return log


def _drc_args(deck_file, inp, rep, topcell, option):
    args = ["-b", "-r", str(deck_file),
            "-rd", f"input={inp}", "-rd", f"report={rep}",
            "-rd", f"topcell={topcell}", "-rd", "run_mode=deep",
            "-rd", "thr=4"]
    if deck_file.name == "gf180mcu.drc":
        args += ["-rd", "feol=true", "-rd", "beol=true",
                 "-rd", "offgrid=true", "-rd", "conn_drc=false"]
    for k, v in _GF180_OPTIONS[option].items():
        args += ["-rd", f"{k}={v}"]
    return args


def _count_violations(lyrdb: Path) -> int:
    if not lyrdb.is_file():
        return -1
    return len(re.findall(r"<item>", lyrdb.read_text()))


@unittest.skipUnless(_klayout(), "klayout executable not configured")
@unittest.skipUnless(os.environ.get("GF180_DRC_RUN") == "1",
                     "DRC deck runs are ~10 min each; opt in with "
                     "GF180_DRC_RUN=1")
class TestDrcDeckExecutes(unittest.TestCase):
    """DRC decks must execute and produce a report on the BJT fixture."""

    def test_main_deck_clean_on_fixture(self):
        sets = list(DECKS) if os.environ.get("GF180_DRC_ALL") == "1" \
            else ["main"]
        with tempfile.TemporaryDirectory() as td:
            for deck in sets:
                for opt in _GF180_OPTIONS:
                    rep = Path(td) / f"{deck}_{opt}.lyrdb"
                    log = _run_klayout(_drc_args(
                        PDK_ROOT / "drc" / DECKS[deck],
                        FIXTURE, rep, "vnpn_10x10", opt))
                    self.assertTrue(rep.is_file(),
                                    f"{deck}-{opt}: no lyrdb produced")
                    n = _count_violations(rep)
                    with self.subTest(run_set=f"{deck}-{opt}"):
                        # Upstream golden fixture: expected clean under
                        # geometry rules. Density runs legitimately flag
                        # fill-density violations on a single cell.
                        if deck == "density":
                            print(f"  {deck}-{opt}: {n} violations "
                                  f"(density on bare cell — informational)")
                        else:
                            self.assertEqual(
                                n, 0,
                                f"{deck}-{opt}: {n} violations on "
                                f"upstream fixture")


@unittest.skipUnless(_klayout(), "klayout executable not configured")
class TestLvsExtraction(unittest.TestCase):
    """LVS deck net_only extraction must emit a netlist for the BJT."""

    def test_net_only_extracts_bjt(self):
        with tempfile.TemporaryDirectory() as td:
            rep = Path(td) / "vnpn_10x10.lvsdb"
            cir = Path(td) / "vnpn_10x10_extracted.cir"
            args = ["-b", "-r", str(PDK_ROOT / "lvs" / "gf180mcu.lvs"),
                    "-rd", f"input={FIXTURE}",
                    "-rd", "topcell=vnpn_10x10",
                    "-rd", f"report={rep}",
                    "-rd", f"target_netlist={cir}",
                    "-rd", "run_mode=deep", "-rd", "thr=4",
                    "-rd", "net_only=true",
                    "-rd", "spice_net_names=true"]
            for k, v in _LVS_OPTIONS["A"].items():
                args += ["-rd", f"{k}={v}"]
            _run_klayout(args)
            self.assertTrue(cir.is_file(), "no extracted netlist")
            text = cir.read_text()
            self.assertRegex(text, r"vnpn_10x10",
                             "extracted netlist lacks the BJT device")


if __name__ == "__main__":
    unittest.main()
