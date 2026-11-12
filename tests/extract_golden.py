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
"""Extract golden reference curves from the upstream characterization data.

Development tool (not part of the unittest suite). Reads the upstream
``models/ngspice/testing/180MCU_SPICE_DATA`` xlsx dumps with a stdlib-only
xlsx reader and writes compact CSV golden files into ``tests/golden/`` that
``test_golden_regression.py`` compares simulator output against.

Usage:

    python tests/extract_golden.py <path-to-globalfoundries-pdk-libs-gf180mcu_fd_pr>

Golden data is *measured silicon* (HSPICE ``.nl_out`` dumps converted to
xlsx), not model output — the regression test therefore applies a sanity
tolerance, not an exact-match bound.
"""

import csv
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

GOLDEN_OUT = Path(__file__).resolve().parent / "golden"
DATA = "models/ngspice/testing/180MCU_SPICE_DATA"

DIODE_DEVICES = ("dnwps", "dnwpw", "np_3p3", "np_6p0", "nwp_3p3",
                 "nwp_6p0", "pn_3p3", "pn_6p0", "sc_diode")

# Upstream resistor regression: device -> (xlsx stem, sign, three-terminal)
RESISTOR_DEVICES = {
    "nplus_u":          ("RES01a-wl-nplus_u.nl_out.xlsx", "+", True),
    "pplus_u":          ("RES02a-wl-pplus_u.nl_out.xlsx", "-", True),
    "nplus_s":          ("RES03a-wl-nplus_s.nl_out.xlsx", "+", True),
    "pplus_s":          ("RES04a-wl-pplus_s.nl_out.xlsx", "-", True),
    "nwell":            ("RES05a-wl-nwell.nl_out.xlsx", "+", True),
    "npolyf_u":         ("RES06a-wl-npolyf_u.nl_out.xlsx", "+", True),
    "ppolyf_u":         ("RES07a-wl-ppolyf_u.nl_out.xlsx", "+", True),
    "npolyf_s":         ("RES08a-wl-npolyf_s.nl_out.xlsx", "+", True),
    "ppolyf_s":         ("RES09a-wl-ppolyf_s.nl_out.xlsx", "-", True),
    "ppolyf_u_1k":      ("RES10a-wl-ppolyf_u_1k.nl_out.xlsx", "-", True),
    "ppolyf_u_2k":      ("RES11a-wl-ppolyf_u_2k.nl_out.xlsx", "-", True),
    "ppolyf_u_1k_6p0":  ("RES12a-wl-ppolyf_u_1k_6p0.nl_o.xlsx", "-", True),
    "ppolyf_u_2k_6p0":  ("RES13a-wl-ppolyf_u_2k_6p0.nl_o.xlsx", "-", True),
    "ppolyf_u_3k":      ("RES14a-wl-ppolyf_u_3k.nl_out.xlsx", "-", True),
    "rm1":              ("RES15a-wl-rm1.nl_out.xlsx", "-", False),
    "rm2":              ("RES16a-wl-rm2.nl_out.xlsx", "+", False),
    "rm3":              ("RES17a-wl-rm3.nl_out.xlsx", "+", False),
    "tm6k":             ("RES18a-wl-tm6k.nl_out.xlsx", "+", False),
    "tm9k":             ("RES19a-wl-tm9k.nl_out.xlsx", "+", False),
    "tm11k":            ("RES20a-wl-tm11k.nl_out.xlsx", "+", False),
    "tm30k":            ("RES21a-wl-tm30k.nl_out.xlsx", "+", False),
}

MOS_DEVICES = ("nmos_3p3", "pmos_3p3", "nmos_6p0", "pmos_6p0")

BJT_DEVICES = ("npn", "pnp")

MOSCAP_SHEETS = ("moscap_cv_3p3", "moscap_cv_6p0")

DIODE_TEMPS = (-40, 25, 125, 175)       # block index % 4
BJT_TEMPS = (25, -40, 125, 175)         # quarters of block list


def _col_index(ref: str) -> int:
    """Spreadsheet column letters -> 0-based index."""
    n = 0
    for ch in ref:
        if ch.isalpha():
            n = n * 26 + ord(ch.upper()) - 64
        else:
            break
    return n - 1


def read_xlsx(path: Path) -> list[list]:
    """Positional stdlib xlsx reader: rows -> list of column values."""
    z = zipfile.ZipFile(path)
    shared = []
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall(f"{NS}si"):
            shared.append("".join(t.text or "" for t in si.iter(f"{NS}t")))
    except KeyError:
        pass
    root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in root.iter(f"{NS}row"):
        vals = {}
        maxc = -1
        for c in row.findall(f"{NS}c"):
            idx = _col_index(c.get("r", "A1"))
            maxc = max(maxc, idx)
            v = c.find(f"{NS}v")
            t = c.get("t")
            if v is None:
                vals[idx] = None
            elif t == "s":
                vals[idx] = shared[int(v.text)]
            else:
                try:
                    vals[idx] = float(v.text)
                except (TypeError, ValueError):
                    vals[idx] = v.text
        rows.append([vals.get(i) for i in range(maxc + 1)])
    return rows


def _float(x):
    return x if isinstance(x, float) else None


def _write_csv(name: str, header: list, rows: list):
    GOLDEN_OUT.mkdir(exist_ok=True)
    with open(GOLDEN_OUT / name, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {name}: {len(rows)} rows")


def extract_diode_iv(up: Path):
    """Per-block IV curves anchored on 'Vn1 (V)' header columns.

    Each block i has Vn1 at col c_i, measured |In1| for corners
    typical/ff/ss at c_i+1..c_i+3. Geometry (w,l) comes from meta rows
    1..N in cols 0/1; temperature cycles -40/25/125/175 by block index.
    """
    for dev in DIODE_DEVICES:
        rows = read_xlsx(up / DATA / "Diode" / f"{dev}_iv.nl_out.xlsx")
        header = rows[0]
        dims = [(r[0], r[1]) for r in rows[1:]
                if isinstance(r[0], float) and isinstance(r[1], float)]
        vcols = [i for i, h in enumerate(header) if h == "Vn1 (V)"]
        if not dims or not vcols:
            # sc_diode sheets carry m= variants instead of numeric W/L;
            # skipped — upstream exercises it via m=, not AREA/PJ.
            print(f"  !! no geometry/voltage columns in {dev}, skipped")
            continue
        out = []
        for i, c in enumerate(vcols[:len(dims)]):
            w, l = dims[i]
            temp = DIODE_TEMPS[i % 4]
            for r in rows[1:]:
                if len(r) <= c + 3:
                    continue
                v, it, iff, iss = (_float(r[c]), _float(r[c + 1]),
                                   _float(r[c + 2]), _float(r[c + 3]))
                if v is not None and it is not None:
                    out.append([w, l, temp, v, it, iff or "", iss or ""])
        _write_csv(f"diode_iv_{dev}.csv",
                   ["w_um", "l_um", "temp_c", "v", "i_typ", "i_ff", "i_ss"],
                   out)


def extract_resistor(up: Path):
    """Per-(w,l) sheet resistance rows; RS2 @V=Vdd group."""
    for dev, (xlsx, sign, three_term) in RESISTOR_DEVICES.items():
        rows = read_xlsx(up / DATA / "Resistor" / xlsx)
        header = rows[0]
        try:
            rs2 = [i for i, h in enumerate(header)
                   if isinstance(h, str) and h.startswith("RS2")][0]
        except IndexError:
            print(f"  !! no RS2 column in {xlsx}")
            continue
        out = []
        for r in rows[1:]:
            if len(r) > rs2 + 3 and isinstance(r[0], float):
                w, l = r[0], r[1]
                typ, ff, ss = (_float(r[rs2 + 1]), _float(r[rs2 + 2]),
                               _float(r[rs2 + 3]))
                if typ is not None:
                    out.append([w, l, sign, 1 if three_term else 0,
                                typ, ff or "", ss or ""])
        _write_csv(f"resistor_{dev}.csv",
                   ["w_um", "l_um", "sign", "three_term",
                    "rs_typ", "rs_ff", "rs_ss"], out)


def extract_mos_iv(up: Path):
    """Per-block Id-Vds at stepped Vgs, anchored on 'vds (V)' columns.

    Each geometry block holds a 'vds (V)' column followed by six
    'vgs =<x>' measured-Id columns. Geometry (w,l) comes from meta rows
    in cols 0/1; temperature: first third of blocks 25 C, middle -40 C,
    last 125 C.
    """
    for dev in MOS_DEVICES:
        rows = read_xlsx(up / DATA / "MOS" / f"{dev}_iv.nl_out.xlsx")
        header = rows[0]
        dims = [(r[0], r[1]) for r in rows[1:]
                if isinstance(r[0], float) and isinstance(r[1], float)]
        vds_cols = [i for i, h in enumerate(header)
                    if h in ("vds (V)", "-vds (V)")]
        # first vds column per block belongs to the 'Id' unit; the second
        # is the '|Rds|' unit — keep only columns whose next 6 headers are
        # 'vgs =' (i.e. the Id unit).
        vds_cols = [c for c in vds_cols
                    if c + 6 < len(header)
                    and all(str(header[c + 1 + j]).startswith("vgs =")
                            for j in range(6))]
        nblocks = len(vds_cols)
        tspan = max(1, nblocks // 3)
        out = []
        for i, c in enumerate(vds_cols[:len(dims)]):
            w, l = dims[i]
            temp = 25 if i < tspan else (-40 if i < 2 * tspan else 125)
            vgs_cols = [c + 1 + j for j in range(6)]
            for r in rows[1:]:
                if len(r) <= c + 6:
                    continue
                vds = _float(r[c])
                if vds is None:
                    continue
                ids = [_float(r[gc]) or "" for gc in vgs_cols]
                out.append([w, l, temp, vds] + ids)
        vgs_vals = [str(header[vds_cols[0] + 1 + j]).replace("vgs =", "")
                    for j in range(6)] if vds_cols else []
        _write_csv(f"mos_iv_{dev}.csv",
                   ["w_um", "l_um", "temp_c", "vds"] +
                   [f"id_vgs{v}" for v in vgs_vals], out)


def extract_bjt_icvc(up: Path):
    """IcVc curves anchored on 'vcp'-named columns; next 5 = Ib columns."""
    for dev in BJT_DEVICES:
        rows = read_xlsx(
            up / DATA / "BJT" / f"bjt_{dev}_icvc_f.nl_out.xlsx")
        header = rows[0]
        vcols = [i for i, h in enumerate(header)
                 if isinstance(h, str) and re.match(r"-?vc", h.strip())]
        nblocks = len(vcols)
        span = max(1, nblocks // 4)
        out = []
        for i, c in enumerate(vcols):
            temp = BJT_TEMPS[min(i // span, 3)]
            # device name sits in row 1 at the block's leading 'Ic' column
            dname = rows[1][c - 2] if c >= 2 else None
            dname = str(dname).strip() if isinstance(dname, str) else f"block{i}"
            for r in rows[1:]:
                if len(r) <= c + 5:
                    continue
                vc = _float(r[c])
                if vc is None:
                    continue
                ics = [_float(r[c + 1 + j]) or "" for j in range(5)]
                out.append([dname, temp, vc] + ics)
        _write_csv(f"bjt_icvc_{dev}.csv",
                   ["device", "temp_c", "vc"] +
                   [f"ic_ib_{i}e-6" for i in (1, 3, 5, 7, 9)], out)


def extract_moscap_cv(up: Path):
    """CV curves anchored on 'Vj' header columns; next 3 = corner caps."""
    for sheet in MOSCAP_SHEETS:
        rows = read_xlsx(up / DATA / "Cap" / f"{sheet}.nl_out.xlsx")
        header = rows[0]
        labels = [r[2] for r in rows[1:]
                  if len(r) > 2 and isinstance(r[2], str) and "cap" in r[2]]
        vcols = [i for i, h in enumerate(header) if h == "Vj"]
        out = []
        for i, c in enumerate(vcols[:len(labels)]):
            label = labels[i].split("\n")[0].strip()
            geom = re.search(r"\(([^)]*)\)", labels[i])
            geom = geom.group(1).replace(" ", "") if geom else "?"
            for r in rows[1:]:
                if len(r) <= c + 3:
                    continue
                v, ct, cf, cs = (_float(r[c]), _float(r[c + 1]),
                                 _float(r[c + 2]), _float(r[c + 3]))
                if v is not None and ct is not None:
                    out.append([label, geom, v, ct, cf or "", cs or ""])
        _write_csv(f"{sheet}.csv",
                   ["device", "geometry", "v", "c_ff_typ", "c_ff_ff",
                    "c_ff_ss"], out)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    up = Path(sys.argv[1])
    assert (up / DATA).is_dir(), f"upstream data dir not found: {up/DATA}"
    print("extracting diode IV ...")
    extract_diode_iv(up)
    print("extracting resistor sheet-R ...")
    extract_resistor(up)
    print("extracting MOS IV ...")
    extract_mos_iv(up)
    print("extracting BJT IcVc ...")
    extract_bjt_icvc(up)
    print("extracting MOSCAP CV ...")
    extract_moscap_cv(up)
    print(f"done -> {GOLDEN_OUT}")


if __name__ == "__main__":
    main()
