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
"""Static validation of the GF180MCU PDK port assets.

Stdlib-only tests: no KLayout, PySide6, or Revolution EDA imports.
Run from the PDK root: ``python -m unittest discover -s tests -v``.
"""

import ast
import hashlib
import inspect
import json
import os
import re
import unittest
from pathlib import Path
from unittest import mock

PDK_ROOT = Path(__file__).resolve().parent.parent

DRC_DECKS = ("gf180mcu.drc", "gf180mcu_antenna.drc", "gf180mcu_density.drc")
LVS_DECKS = ("gf180mcu.lvs",)

REQUIRED_SYMBOL_ATTRS = (
    "SpiceNetlistLine",
    "lvsNetlistLine",
    "lvsDeviceType",
    "modelName",
    "lvs_model",
    "pinOrder",
    "paramDefs",
)

# modelName / lvs_model per symbol directory; entries where both equal the
# cell name are implied.
MODEL_OVERRIDES = {
    "dnwpw": ("dnwpw", "dnwpw_3p3"),
    "mim_2p0fF": ("mim_2p0fF", "mim_single_2p0fF"),
    "nmos_6p0_nat": ("nmos_6p0_nat", "nmos_6p0_nat"),
    "vpnp_10x10": ("vpnp_10x10", "vpnp_10x10"),
}

LVS_DEVICE_TYPES = {
    "mos": ("nmos_3p3", "nmos_3p3_sab", "nmos_6p0", "nmos_6p0_nat",
            "pmos_3p3", "pmos_3p3_sab", "pmos_6p0"),
    "cap": ("nmoscap_3p3", "nmoscap_6p0", "pmoscap_3p3", "pmoscap_6p0",
            "mim_2p0fF"),
    "res": ("nplus_u", "pplus_u", "npolyf_u", "ppolyf_u", "nwell", "rm1"),
    "dio": ("np_3p3", "dnwpw"),
    "bjt": ("vnpn_10x10", "vpnp_10x10"),
}

# Corrected label defaults: cell -> {param: default}
EXPECTED_DEFAULTS = {
    "nmos_6p0": {"W": "0.30u", "L": "0.70u"},
    "nmos_6p0_nat": {"W": "0.80u", "L": "1.80u"},
    "pmos_6p0": {"W": "0.30u", "L": "0.50u"},
    "np_3p3": {"r_w": "1u", "r_l": "1u"},
    "rm1": {"W": "0.6u", "L": "0.6u"},
    "mim_2p0fF": {"W": "5u", "L": "5u"},
    "nmoscap_3p3": {"W": "1.06u", "L": "1u"},
    "nmoscap_6p0": {"W": "1.06u", "L": "1u"},
    "pmoscap_3p3": {"W": "1.06u", "L": "1u"},
    "pmoscap_6p0": {"W": "1.06u", "L": "1u"},
}

EXPECTED_VIA_NAMES = (
    "contactActive", "contactPoly", "via1", "via2", "via3", "via4", "via5",
)
EXPECTED_PATH_NAMES = (
    "nwell", "active", "poly2", "metal1", "metal2", "metal3", "metal4",
    "metal5", "metalTop9K", "metalTop11K", "metalTop30K",
)

_ABSOLUTE_HOME = re.compile(r"/(?:var/)?home/")


def _iter_symbol_items(data):
    """Yield symbol item dicts regardless of JSON top-level schema."""
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
    elif isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item
            elif isinstance(value, dict):
                yield value


def _defined_names(path: Path) -> set:
    """Top-level class/function names defined in a Python source file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
    return names


def _symbol_attrs(data):
    attrs = {}
    for item in _iter_symbol_items(data):
        if item.get("type") == "attr":
            attrs.setdefault(str(item.get("nam", "")), []).append(item)
    return attrs


def _symbol_label_defaults(data):
    defaults = {}
    for item in _iter_symbol_items(data):
        if item.get("type") != "label":
            continue
        nam = str(item.get("nam", ""))
        m = re.search(r"=([^=:\]]+)\]\s*$", str(item.get("def", "")))
        if nam.startswith("@") and m:
            defaults[nam[1:]] = m.group(1)
    return defaults


class TestConfigJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((PDK_ROOT / "config.json").read_text())

    def test_menu_callbacks(self):
        callbacks = {
            item.get("callback")
            for item in self.config.get("menu_items", [])
            if item.get("menu") == "Check"
        }
        self.assertIn("klayoutDRCClick", callbacks)
        self.assertIn("klayoutLVSClick", callbacks)


class TestModelLibSettings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (PDK_ROOT / "modelLibSettings.json").read_text()
        cls.settings = json.loads(cls.raw)

    def test_no_absolute_home_paths(self):
        self.assertNotRegex(self.raw, _ABSOLUTE_HOME)

    def test_pdk_root_paths_resolve(self):
        paths = []
        for sim in self.settings.get("simulators", {}).values():
            for lib in sim.get("modelLibraries", []):
                paths.append(lib.get("modelPath", ""))
            for entry in sim.get("includePaths", []):
                if isinstance(entry, (list, tuple)):
                    paths.extend(str(p) for p in entry)
                else:
                    paths.append(str(entry))
            for entry in sim.get("modulePaths", []):
                if isinstance(entry, (list, tuple)):
                    paths.extend(str(p) for p in entry)
                else:
                    paths.append(str(entry))
        pdk_paths = [p for p in paths if "${PDK_ROOT}" in p]
        self.assertTrue(pdk_paths, "no ${PDK_ROOT} paths found")
        for path in pdk_paths:
            resolved = PDK_ROOT / path.split("${PDK_ROOT}/", 1)[1]
            self.assertTrue(
                resolved.exists(), f"{path} does not resolve under PDK root"
            )

    def test_sm141064_sections_cover_all_symbol_families(self):
        expected = {
            "typical", "bjt_typical", "diode_typical", "res_typical",
            "mimcap_typical", "moscap_typical",
        }
        for sim_name, ext in (("Xyce", "xyce"), ("Ngspice", "ngspice")):
            with self.subTest(simulator=sim_name):
                entries = self.settings["simulators"][sim_name]["modelLibraries"]
                sections = {
                    entry.get("modelSection")
                    for entry in entries
                    if entry.get("modelPath", "").endswith(
                        f"sm141064.{ext}") and entry.get("select")
                }
                self.assertEqual(sections, expected)

    def test_selected_model_sections_exist(self):
        for sim_name, sim in self.settings["simulators"].items():
            for entry in sim.get("modelLibraries", []):
                if not entry.get("select"):
                    continue
                path = PDK_ROOT / entry["modelPath"].split("${PDK_ROOT}/", 1)[1]
                text = path.read_text(errors="replace")
                sections = set(
                    re.findall(r"^\s*\.LIB\s+([^\s]+)\s*$", text, re.M | re.I)
                )
                sections.update(
                    re.findall(r"^section\s+([^\s]+)\s*$", text, re.M)
                )
                with self.subTest(simulator=sim_name, path=path.name,
                                  section=entry["modelSection"]):
                    self.assertIn(entry["modelSection"], sections)


class TestRuleDecks(unittest.TestCase):
    def test_drc_decks_exist_nonempty(self):
        for deck in DRC_DECKS:
            path = PDK_ROOT / "drc" / deck
            self.assertTrue(path.is_file(), f"missing {path}")
            self.assertGreater(path.stat().st_size, 0, f"empty {path}")

    def test_lvs_deck_exists_nonempty(self):
        for deck in LVS_DECKS:
            path = PDK_ROOT / "lvs" / deck
            self.assertTrue(path.is_file(), f"missing {path}")
            self.assertGreater(path.stat().st_size, 0, f"empty {path}")

    def test_lvs_deck_single_guarded_compare(self):
        """Exactly one executable compare, guarded by $schematic."""
        text = (PDK_ROOT / "lvs" / "gf180mcu.lvs").read_text()
        self.assertEqual(
            len(re.findall(r"^\s*comparison_ok\s*=\s*compare\s*$", text, re.M)),
            1,
        )
        standalone = [
            line for line in text.splitlines()
            if re.match(r"^\s*compare\s*$", line)
        ]
        self.assertEqual(standalone, [])


class TestSymbols(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.symbol_files = sorted(
            (PDK_ROOT / "gf180_mcu").glob("*/symbol.json")
        )
        cls.symbol_data = {
            path.parent.name: json.loads(path.read_text())
            for path in cls.symbol_files
        }

    def test_symbols_parse(self):
        self.assertEqual(len(self.symbol_files), 22)
        for name, data in self.symbol_data.items():
            with self.subTest(symbol=name):
                self.assertIsInstance(data, (list, dict))

    def test_callback_classes_exist(self):
        """Every symbol cell name is a top-level class in callbacks.py."""
        callbacks_path = PDK_ROOT / "callbacks.py"
        self.assertTrue(callbacks_path.is_file())
        defined = _defined_names(callbacks_path)
        for name in self.symbol_data:
            with self.subTest(symbol=name):
                self.assertIn(name, defined)

    def test_required_attrs_unique(self):
        for name, data in self.symbol_data.items():
            attrs = _symbol_attrs(data)
            with self.subTest(symbol=name):
                for req in REQUIRED_SYMBOL_ATTRS:
                    self.assertIn(req, attrs, f"{name} missing attr {req}")
                for nam, records in attrs.items():
                    self.assertEqual(
                        len(records), 1, f"{name} duplicate attr {nam}"
                    )

    def test_model_and_lvs_model(self):
        for name, data in self.symbol_data.items():
            attrs = _symbol_attrs(data)
            expected = MODEL_OVERRIDES.get(name, (name, name))
            with self.subTest(symbol=name):
                self.assertEqual(attrs["modelName"][0]["def"], expected[0])
                self.assertEqual(attrs["lvs_model"][0]["def"], expected[1])

    def test_lvs_device_type(self):
        for dev_type, cells in LVS_DEVICE_TYPES.items():
            for name in cells:
                with self.subTest(symbol=name):
                    attrs = _symbol_attrs(self.symbol_data[name])
                    self.assertEqual(
                        attrs["lvsDeviceType"][0]["def"], dev_type
                    )

    def test_corrected_defaults(self):
        for name, expected in EXPECTED_DEFAULTS.items():
            defaults = _symbol_label_defaults(self.symbol_data[name])
            param_defs = json.loads(
                _symbol_attrs(self.symbol_data[name])["paramDefs"][0]["def"]
            )
            pd_defaults = {p["name"]: p["default"] for p in param_defs}
            with self.subTest(symbol=name):
                for param, value in expected.items():
                    self.assertEqual(
                        defaults.get(param), value,
                        f"{name} label @{param} default"
                    )
                    self.assertEqual(
                        pd_defaults.get(param), value,
                        f"{name} paramDefs {param} default"
                    )

    def test_paramdefs_and_pinorder(self):
        for name, data in self.symbol_data.items():
            attrs = _symbol_attrs(data)
            defaults = _symbol_label_defaults(data)
            pins = [
                item.get("nam")
                for item in _iter_symbol_items(data)
                if item.get("type") == "pin"
            ]
            pin_order = [
                p.strip()
                for p in attrs["pinOrder"][0]["def"].split(",")
                if p.strip()
            ]
            with self.subTest(symbol=name):
                param_defs = json.loads(attrs["paramDefs"][0]["def"])
                self.assertIsInstance(param_defs, list)
                for pd in param_defs:
                    self.assertIn("default", pd)
                    self.assertIn(
                        pd["name"], defaults,
                        f"{name}: paramDef {pd['name']} has no @label",
                    )
                self.assertEqual(len(pins), len(set(pins)))
                self.assertEqual(set(pins), set(pin_order))

    def test_label_names_unique(self):
        for name, data in self.symbol_data.items():
            label_names = [
                item.get("nam")
                for item in _iter_symbol_items(data)
                if item.get("type") == "label"
            ]
            dupes = {n for n in label_names if label_names.count(n) > 1}
            with self.subTest(symbol=name):
                self.assertEqual(dupes, set(), f"{name} duplicate labels {dupes}")


PCELL_CELLS = (
    "nmos_3p3", "nmos_3p3_sab", "nmos_6p0", "nmos_6p0_nat",
    "pmos_3p3", "pmos_3p3_sab", "pmos_6p0",
    "np_3p3", "dnwpw", "mim_2p0fF",
    "nplus_u", "pplus_u", "npolyf_u", "ppolyf_u", "nwell", "rm1",
    "nmoscap_3p3", "nmoscap_6p0", "pmoscap_3p3", "pmoscap_6p0",
    "vnpn_10x10", "vpnp_10x10",
)

# Generic upstream-faithful generators (KLayout pymacros ports) that have
# pcell views but no schematic symbol.
GENERIC_UPSTREAM_PCELLS = (
    "nmos", "pmos", "nmos_10p0_asym", "pmos_10p0_asym",
    "npn_bjt", "pnp_bjt",
    "np_diode", "pn_diode", "nwp_diode", "dnwpw_diode", "dnwps_diode",
    "sc_diode",
    "nmoscap", "pmoscap", "nmoscap_b", "pmoscap_b",
    "mimcap",
    "metal_resistor",
    "nplus_s_resistor", "pplus_s_resistor",
    "nplus_u_resistor", "pplus_u_resistor",
    "nwell_resistor", "pwell_resistor",
    "npolyf_s_resistor", "ppolyf_s_resistor",
    "npolyf_u_resistor", "ppolyf_u_resistor",
    "ppolyf_u_high_Rs_resistor",
)

# Fixed-layout cells ported from upstream GDS plus the generic upstream
# generators; none of them have a schematic symbol.
UPSTREAM_ONLY_PCELLS = (
    "vnpn_5x5", "vnpn_0p54x16", "vnpn_0p54x8", "vnpn_0p54x4",
    "vnpn_0p54x2", "vpnp_5x5", "vpnp_0p42x10", "vpnp_0p42x5",
    "efuse",
) + GENERIC_UPSTREAM_PCELLS

ALL_PCELL_CELLS = PCELL_CELLS + UPSTREAM_ONLY_PCELLS

# All 30 generator names enabled in the upstream KLayout pymacros
# (29 generic ports plus nmos_6p0_nat, which doubles as a symbol cell).
UPSTREAM_GENERATORS = (
    GENERIC_UPSTREAM_PCELLS[:4] + ("nmos_6p0_nat",)
    + GENERIC_UPSTREAM_PCELLS[4:]
)

FIXED_BJT_CELLS = (
    "vnpn_10x10", "vnpn_5x5", "vnpn_0p54x16", "vnpn_0p54x8",
    "vnpn_0p54x4", "vnpn_0p54x2",
    "vpnp_10x10", "vpnp_5x5", "vpnp_0p42x10", "vpnp_0p42x5",
)

FIXED_GDS_FILES = {
    "bjt": FIXED_BJT_CELLS,
    "efuse": ("efuse",),
}

# Upstream GF180 source tree used for fixed-layout checksum verification.
GF180_SOURCE = Path(
    os.environ.get(
        "GF180_SOURCE",
        "/var/home/eskiyerli/onedrive_reveda/GitHub/"
        "globalfoundries-pdk-libs-gf180mcu_fd_pr",
    )
)


def _module_level_calls_importPDKModule(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            continue  # function-local calls are allowed
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "importPDKModule"
            ):
                return True
    return False


class TestPcellParameterMap(unittest.TestCase):
    def test_mapping_covers_all_symbols(self):
        pmap = json.loads((PDK_ROOT / "pcellParameterMap.json").read_text())
        self.assertEqual(pmap["schemaVersion"], "1.0")
        self.assertEqual(pmap["pinMappings"], {})
        symbol_files = (PDK_ROOT / "gf180_mcu").glob("*/symbol.json")
        for path in symbol_files:
            with self.subTest(symbol=path.parent.name):
                self.assertIn(path.parent.name, pmap["mappings"])


class TestPdkModuleBindings(unittest.TestCase):
    def test_no_module_level_eager_pdk_imports(self):
        files = [PDK_ROOT / name for name in
                 ("klayoutDRC.py", "klayoutLVS.py", "process.py")]
        files += sorted((PDK_ROOT / "pcells").glob("*.py"))
        for path in files:
            with self.subTest(file=path.name):
                self.assertFalse(
                    _module_level_calls_importPDKModule(path),
                    f"{path.name} calls importPDKModule at module level",
                )

    def test_process_defs_present(self):
        source = (PDK_ROOT / "process.py").read_text()
        for name in EXPECTED_VIA_NAMES:
            self.assertIn(f'"{name}"', source)
        for name in EXPECTED_PATH_NAMES:
            self.assertIn(f'"{name}"', source)


class TestLayoutLayers(unittest.TestCase):
    def test_referenced_stipples_exist_and_are_wellformed(self):
        source = (PDK_ROOT / "layoutLayers.py").read_text(encoding="utf-8")
        textures = set(
            re.findall(r"""btexture\s*=\s*['"]([^'"]+)['"]""", source)
        )
        self.assertTrue(textures, "no btexture references found")
        for texture in sorted(textures):
            with self.subTest(texture=texture):
                path = PDK_ROOT / texture
                self.assertTrue(path.is_file(), f"missing {path}")
                rows = [
                    [int(v) for v in line.split()]
                    for line in path.read_text().splitlines()
                    if line.split()
                ]
                self.assertTrue(rows, f"{path} has no rows")
                width = len(rows[0])
                self.assertTrue(
                    all(len(r) == width for r in rows),
                    f"{path} is not rectangular",
                )
                self.assertTrue(
                    all(v in (0, 1) for r in rows for v in r),
                    f"{path} contains non-binary values",
                )


class TestPcells(unittest.TestCase):
    def test_registry_keys(self):
        tree = ast.parse(
            (PDK_ROOT / "pcells" / "__init__.py").read_text(encoding="utf-8")
        )
        registry = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "pcells" for t in node.targets
            ):
                registry = [
                    k.value for k in node.value.keys
                    if isinstance(k, ast.Constant)
                ]
        self.assertIsNotNone(registry, "pcells dict not found")
        self.assertEqual(sorted(registry), sorted(ALL_PCELL_CELLS))
        symbol_dirs = {
            path.parent.name
            for path in (PDK_ROOT / "gf180_mcu").glob("*/symbol.json")
        }
        # Every symbol cell is registered; the registry may additionally
        # cover upstream-only cells that have no symbol.
        self.assertTrue(symbol_dirs <= set(registry))
        self.assertEqual(
            set(registry) - symbol_dirs, set(UPSTREAM_ONLY_PCELLS))
        # All 30 upstream enabled generator names are registered,
        # including nmos_6p0_nat which doubles as a symbol cell.
        self.assertTrue(set(UPSTREAM_GENERATORS) <= set(registry))

    def test_pcell_json_files(self):
        for cell in ALL_PCELL_CELLS:
            path = PDK_ROOT / "gf180_mcu" / cell / "pcell.json"
            with self.subTest(cell=cell):
                self.assertTrue(path.is_file(), f"missing {path}")
                data = json.loads(path.read_text())
                self.assertEqual(data[0]["cellView"], "pcell")
                self.assertEqual(data[1]["reference"], cell)

    def test_base_constructor_default(self):
        tree = ast.parse(
            (PDK_ROOT / "pcells" / "base.py").read_text(encoding="utf-8")
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "baseCell":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        args = item.args
                        self.assertIn("shapes", [a.arg for a in args.args])
                        idx = [a.arg for a in args.args].index("shapes")
                        default = args.defaults[
                            idx - (len(args.args) - len(args.defaults))
                        ]
                        self.assertIsInstance(default, ast.Constant)
                        self.assertIsNone(default.value)
                        return
        self.fail("baseCell.__init__ not found")


class TestPcellRuntime(unittest.TestCase):
    """Runtime smoke test; skips cleanly without Revolution deps."""

    @classmethod
    def setUpClass(cls):
        try:
            import sys
            from PySide6.QtWidgets import QApplication
            import revedaEditor  # noqa: F401
            cls._app = QApplication.instance() or QApplication([])
            if str(PDK_ROOT.parent) not in sys.path:
                sys.path.insert(0, str(PDK_ROOT.parent))
            import gf180_pdk.pcells as pcells_pkg
            cls.pcells = pcells_pkg.pcells
            cls.lshp = __import__(
                "revedaEditor.common.layoutShapes", fromlist=["layoutPin"]
            )
        except Exception as exc:  # PySide6/revedaEditor/lazy PDK unavailable
            raise unittest.SkipTest(f"Revolution runtime unavailable: {exc}")

    def _pin_names(self, cell):
        return {
            getattr(shape, "pinName", None)
            for shape in cell.shapes
            if isinstance(shape, self.lshp.layoutPin)
        }

    def _layer_names(self, cell):
        return {
            getattr(getattr(shape, "layer", None), "name", None)
            for shape in cell.shapes
        }

    MOS_CELLS = PCELL_CELLS[:7]

    def test_mos_pcells_generate(self):
        for name in self.MOS_CELLS:
            with self.subTest(cell=name):
                cls = self.pcells[name]
                cell = cls()
                cell(w=cls.default_w, l=cls.default_l, nf="1",
                     bulk="Bulk Tie")
                self.assertTrue(cell.shapes, f"{name}: no shapes")
                self.assertEqual(self._pin_names(cell), {"D", "G", "S", "B"})
                self._assert_integer_dbu(cell)
                layers = self._layer_names(cell)
                if cls.sab:
                    self.assertIn("SAB", layers)
                    self.assertIn("ESD_MK", layers)
                if cls.voltage == "6V":
                    self.assertIn("Dualgate", layers)
                if cls.native:
                    self.assertIn("NAT", layers)
                    self.assertIn("Dualgate", layers)
                # minima coercion
                coerced = cls()
                coerced(w="0.01u", l="0.01u", nf="0")
                self.assertGreaterEqual(coerced.w, cls.min_w_um * 1e-6)
                self.assertGreaterEqual(coerced.l, cls.min_l_um * 1e-6)
                self.assertEqual(coerced.nf, 1)

    def test_mos_pcells_guard_ring(self):
        for name in self.MOS_CELLS:
            with self.subTest(cell=name):
                cls = self.pcells[name]
                cell = cls()
                cell(w=cls.default_w, l=cls.default_l, nf="1",
                     bulk="Guard Ring")
                self.assertTrue(cell.shapes, f"{name}: no shapes")
                self.assertEqual(
                    self._pin_names(cell), {"D", "G", "S", "B"})
                self._assert_integer_dbu(cell)
                ring_implant = "Nplus" if cls.polarity == "p" else "Pplus"
                self.assertIn(ring_implant, self._layer_names(cell))

    def test_diode_pcells_generate(self):
        for name in ("np_3p3", "dnwpw"):
            with self.subTest(cell=name):
                cls = self.pcells[name]
                cell = cls()
                cell(w=cls.default_w, l=cls.default_l)
                self.assertTrue(cell.shapes)
                self.assertEqual(self._pin_names(cell), {"p", "m"})
                self._assert_integer_dbu(cell)
                layers = self._layer_names(cell)
                if name == "np_3p3":
                    self.assertIn("DIODE_MK", layers)
                else:
                    self.assertIn("LVPWELL", layers)
                    self.assertIn("DNWELL", layers)
                    self.assertIn("WELL_DIODE_MK", layers)
                coerced = cls()
                coerced(w="0.01u", l="0.01u")
                self.assertGreaterEqual(coerced.w, cls.min_w_um * 1e-6)
                self.assertGreaterEqual(coerced.l, cls.min_l_um * 1e-6)

    def test_mimcap_pcell_generate(self):
        cls = self.pcells["mim_2p0fF"]
        expected = {
            "A": ("Metal3", "Metal2", "Via2"),
            "B": ("Metal4", "Metal3", "Via3"),
            "C": ("Metal5", "Metal4", "Via4"),
        }
        for option, (top, bot, via) in expected.items():
            with self.subTest(option=option):
                cell = cls()
                cell(w="5u", l="5u", option=option)
                self.assertTrue(cell.shapes)
                self.assertEqual(self._pin_names(cell), {"G", "B"})
                self._assert_integer_dbu(cell)
                layers = self._layer_names(cell)
                for required in (top, bot, via, "FuseTop", "CAP_MK",
                                 "MIM_L_MK"):
                    self.assertIn(required, layers)
        # invalid option
        with self.assertRaises(ValueError):
            cls()(w="5u", l="5u", option="Z")
        # minima coercion (DRC MIM.8a: >= 25 um2 FuseTop)
        coerced = cls()
        coerced(w="0.28u", l="0.28u")
        self.assertGreaterEqual(coerced.w, cls.min_size_um * 1e-6)
        self.assertGreaterEqual(coerced.l, cls.min_size_um * 1e-6)

    def test_resistor_pcells_generate(self):
        expected_layers = {
            "nplus_u": {"RES", "SAB", "LVPWELL"},
            "pplus_u": {"RES", "SAB", "Nwell"},
            "npolyf_u": {"RES", "SAB"},
            "ppolyf_u": {"RES", "SAB"},
            "nwell": {"Nwell", "RES"},
            "rm1": {"Metal1_Res"},
        }
        for name in ("nplus_u", "pplus_u", "npolyf_u", "ppolyf_u", "nwell",
                     "rm1"):
            with self.subTest(cell=name):
                cls = self.pcells[name]
                cell = cls()
                cell(w=cls.default_w, l=cls.default_l)
                self.assertTrue(cell.shapes)
                expected_pins = {"M", "P"} if name == "rm1" else {"M", "P", "B"}
                self.assertEqual(self._pin_names(cell), expected_pins)
                self._assert_integer_dbu(cell)
                layers = self._layer_names(cell)
                for required in expected_layers[name]:
                    self.assertIn(required, layers)
                coerced = cls()
                coerced(w="0.01u", l="0.01u")
                self.assertGreaterEqual(coerced.w, cls.min_w_um * 1e-6)
                self.assertGreaterEqual(coerced.l, cls.min_l_um * 1e-6)
                if name == "nwell":
                    # M/P terminal stripes lie outside the RES_MK body
                    # x interval (M right <= 0, P left >= w in scene DBU)
                    w_dbu = cell._microns(cls.default_w) * 1000
                    pin_rects = {}
                    for shape in cell.shapes:
                        if isinstance(shape, self.lshp.layoutPin):
                            rect = shape.rect
                            pin_rects[shape.pinName] = (
                                rect() if callable(rect) else rect
                            )
                    self.assertLessEqual(pin_rects["M"].right(), 0)
                    self.assertGreaterEqual(pin_rects["P"].left(), w_dbu)

    def test_moscap_pcells_generate(self):
        for name in ("nmoscap_3p3", "nmoscap_6p0", "pmoscap_3p3",
                     "pmoscap_6p0"):
            with self.subTest(cell=name):
                cls = self.pcells[name]
                cell = cls()
                cell(w=cls.default_w, l=cls.default_l)
                self.assertTrue(cell.shapes)
                self.assertEqual(self._pin_names(cell), {"G", "B"})
                self._assert_integer_dbu(cell)
                layers = self._layer_names(cell)
                for required in ("COMP", "Poly2", "MOS_CAP_MK"):
                    self.assertIn(required, layers)
                if cls.polarity == "p":
                    self.assertIn("Nwell", layers)
                if cls.voltage == "6V":
                    self.assertIn("Dualgate", layers)
                coerced = cls()
                coerced(w="0.01u", l="0.01u")
                self.assertGreaterEqual(coerced.w, cls.min_w_um * 1e-6)
                self.assertGreaterEqual(coerced.l, cls.min_l_um * 1e-6)

    # Expected pin sets for the generic upstream generators (default
    # options; LDMOS pins are D/G/S/B, sc_diode pins are N/P).
    GENERIC_PINS = dict(
        {name: {"D", "G", "S", "B"}
         for name in ("nmos", "pmos", "nmos_10p0_asym",
                      "pmos_10p0_asym")},
        npn_bjt={"C", "B", "E", "S"},
        pnp_bjt={"C", "B", "E"},
        **{name: {"p", "m"}
           for name in ("np_diode", "pn_diode", "nwp_diode",
                        "dnwpw_diode", "dnwps_diode")},
        sc_diode={"N", "P"},
        **{name: {"G", "B"}
           for name in ("nmoscap", "pmoscap", "nmoscap_b",
                        "pmoscap_b")},
        mimcap={"G", "B"},
        metal_resistor={"M", "P"},
        **{name: {"M", "P", "B"}
           for name in ("nplus_s_resistor", "pplus_s_resistor",
                        "nplus_u_resistor", "pplus_u_resistor",
                        "nwell_resistor", "pwell_resistor",
                        "npolyf_s_resistor", "ppolyf_s_resistor",
                        "npolyf_u_resistor", "ppolyf_u_resistor",
                        "ppolyf_u_high_Rs_resistor")},
    )

    # Constructor-attr overrides needed so option-degenerate default
    # geometry still emits the expected pins (e.g. the moscap gate opens
    # only for w > ~0.9 um).
    GENERIC_ATTR_OVERRIDES = {
        name: {"w": "1u"}
        for name in ("nmoscap", "pmoscap", "nmoscap_b", "pmoscap_b")
    }

    def _call_with_ctor_attrs(self, cls, name):
        """Instantiate ``cls`` and call it with its own stored attrs.

        The constructor stores every ``__call__`` parameter as an
        attribute, so replaying them exercises the full option surface
        at default values.
        """
        cell = cls()
        attrs = {
            p: getattr(cell, p)
            for p in inspect.signature(cell.__call__).parameters
        }
        attrs.update(self.GENERIC_ATTR_OVERRIDES.get(name, {}))
        if name in ("mimcap", "metal_resistor"):
            # Stack option gating: force the option-A stack.
            with mock.patch.dict(os.environ, {"GF_PDK_OPTION": "A"}):
                cell(**attrs)
        else:
            cell(**attrs)
        return cell

    def test_generic_upstream_pcells_generate(self):
        for name in GENERIC_UPSTREAM_PCELLS:
            with self.subTest(cell=name):
                cls = self.pcells[name]
                cell = self._call_with_ctor_attrs(cls, name)
                self.assertTrue(cell.shapes, f"{name}: no shapes")
                self.assertEqual(
                    self._pin_names(cell), self.GENERIC_PINS[name])
                self._assert_integer_dbu(cell)
        # All 30 upstream generator names resolve to live classes.
        for name in UPSTREAM_GENERATORS:
            with self.subTest(generator=name):
                self.assertIn(name, self.pcells)

    def test_generic_option_smoke(self):
        # 5V MOS option emits V5_XTOR and Dualgate markers
        for name in ("nmos", "pmos"):
            with self.subTest(cell=name, option="5V"):
                cell = self.pcells[name]()
                cell(w="1u", l="0.6u", volt="5V")
                layers = self._layer_names(cell)
                self.assertIn("V5_XTOR", layers)
                self.assertIn("Dualgate", layers)
        # deep-nwell nmos draws LVPWELL inside DNWELL
        cell = self.pcells["nmos"]()
        cell(w="1u", l="0.28u", deepnwell=True)
        layers = self._layer_names(cell)
        self.assertIn("DNWELL", layers)
        self.assertIn("LVPWELL", layers)
        # deep-nwell diode variants draw DNWELL
        for name in ("np_diode", "pn_diode"):
            with self.subTest(cell=name, option="deepnwell"):
                cell = self.pcells[name]()
                cell(w="1u", l="1u", deepnwell=True)
                self.assertIn("DNWELL", self._layer_names(cell))
        # inside-well moscaps draw Dualgate at 5/6V
        for name in ("nmoscap_b", "pmoscap_b"):
            with self.subTest(cell=name, option="5/6V"):
                cell = self.pcells[name]()
                cell(w="1u", l="1u", volt="5/6V")
                self.assertIn("Dualgate", self._layer_names(cell))
        # high-Rs poly resistor draws Dualgate + Resistor block at 5/6V
        cell = self.pcells["ppolyf_u_high_Rs_resistor"]()
        cell(w="1u", l="1u", volt="5/6V")
        layers = self._layer_names(cell)
        self.assertIn("Dualgate", layers)
        self.assertIn("Resistor", layers)
        # mimcap stack gating follows GF_PDK_OPTION
        cls = self.pcells["mimcap"]
        with mock.patch.dict(os.environ, {"GF_PDK_OPTION": "A"}):
            cls()(w="1u", l="1u", mim_option="MIM-A")
            with self.assertRaises(TypeError):
                cls()(w="1u", l="1u", mim_option="MIM-B")

    def test_contact_array_exact_fit(self):
        """baseCell.contactArray emits cuts for exact-fit landings."""
        for name in ("np_3p3", "dnwpw"):
            with self.subTest(cell=name):
                cls = self.pcells[name]
                cell = cls()
                cell(w=cls.default_w, l=cls.default_l)
                contacts = [
                    shape for shape in cell.shapes
                    if getattr(getattr(shape, "layer", None), "name", None)
                    == "Contact"
                ]
                self.assertTrue(
                    contacts, f"{name}: no Contact shapes generated")

    def test_fixed_bjt_pcells_generate(self):
        for name in FIXED_BJT_CELLS:
            if name.startswith("vnpn"):
                pins, wells = {"C", "B", "E", "S"}, ("DNWELL", "LVPWELL")
            else:
                pins, wells = {"C", "B", "E"}, ("Nwell",)
            with self.subTest(cell=name):
                cls = self.pcells[name]
                cell = cls()
                # constructor already generates the fixed layout
                self.assertTrue(cell.shapes)
                cell()
                self.assertTrue(cell.shapes)
                self.assertEqual(self._pin_names(cell), pins)
                self._assert_integer_dbu(cell)
                layers = self._layer_names(cell)
                for required in ("LVS_BJT", "DRC_BJT", *wells):
                    self.assertIn(required, layers)

    def test_efuse_pcell_generate(self):
        cls = self.pcells["efuse"]
        cell = cls()
        # constructor already generates the fixed layout
        self.assertTrue(cell.shapes)
        cell()
        self.assertTrue(cell.shapes)
        self.assertEqual(self._pin_names(cell), {"in", "out"})
        self._assert_integer_dbu(cell)
        layers = self._layer_names(cell)
        for required in ("EFUSE_MK", "LVS_Source", "PLFUSE",
                         "Poly2", "Contact", "Metal1"):
            self.assertIn(required, layers)
        # The upstream efuse geometry is offset far from the origin; the
        # converter normalizes it so the bounding box starts at (0, 0).
        min_x = min(point.x() for shape in cell.shapes
                    for point in self._points(shape))
        min_y = min(point.y() for shape in cell.shapes
                    for point in self._points(shape))
        self.assertEqual(min_x, 0)
        self.assertEqual(min_y, 0)

    def test_bundled_gds_matches_upstream(self):
        # Bundled GDS data present and, when the upstream source tree is
        # available, identical to the authoritative layouts.
        for subdir, names in FIXED_GDS_FILES.items():
            gds_dir = PDK_ROOT / "pcells" / "data" / subdir
            src_dir = (GF180_SOURCE / "cells" / "klayout" / "pymacros" /
                       "cells" / subdir)
            for name in names:
                with self.subTest(gds=f"{subdir}/{name}.gds"):
                    bundled = gds_dir / f"{name}.gds"
                    self.assertTrue(bundled.is_file())
                    self.assertGreater(bundled.stat().st_size, 0)
                    source = src_dir / f"{name}.gds"
                    if source.is_file():
                        self.assertEqual(
                            hashlib.sha256(bundled.read_bytes()).hexdigest(),
                            hashlib.sha256(source.read_bytes()).hexdigest())

    def _points(self, shape):
        pts = getattr(shape, "points", None)
        pts = pts() if callable(pts) else pts
        if pts:
            return list(pts)
        rect = getattr(shape, "rect", None)
        r = rect() if callable(rect) else rect
        if r is not None and hasattr(r, "topLeft") and hasattr(r, "bottomRight"):
            return [r.topLeft(), r.bottomRight()]
        return []

    def _assert_integer_dbu(self, cell):
        for shape in cell.shapes:
            for point in self._points(shape):
                self.assertEqual(point.x(), int(point.x()))
                self.assertEqual(point.y(), int(point.y()))


class TestSymbolNetlisting(unittest.TestCase):
    """Load a real symbol instance through schematicItems and netlist it.

    Exercises the full ``sys.ld`` -> ``labelValue`` -> ``createXyceSymbolLine``
    path so edited instance parameters must appear in the emitted line.
    Skips cleanly when the Revolution runtime is unavailable.
    """

    @classmethod
    def setUpClass(cls):
        try:
            import types
            from PySide6.QtWidgets import QApplication
            import revedaEditor  # noqa: F401
            cls._app = QApplication.instance() or QApplication([])
            import revedaEditor.backend.libraryModelView as lmview
            from revedaEditor.tests import sceneTestUtils
            from revedaEditor.fileio import loadJSON
            from revedaEditor.netlisting.xyceNetlist import xyceNetlist
            cls.types = types
            cls.lmview = lmview
            cls.sceneTestUtils = sceneTestUtils
            cls.loadJSON = loadJSON
            cls.xyceNetlist = xyceNetlist
        except Exception as exc:
            raise unittest.SkipTest(f"Revolution runtime unavailable: {exc}")

    def _makeInstance(self, cellName, ld):
        libraryDict = {"gf180_mcu": PDK_ROOT / "gf180_mcu"}
        scene = self.sceneTestUtils.makeSchematicScene()
        scene.libraryDict = libraryDict
        record = {
            "type": "sys", "lib": "gf180_mcu", "cell": cellName,
            "view": "symbol", "nam": "I0", "ic": 0, "ld": ld,
            "loc": [0, 0], "ang": 0, "ign": 0,
            "br": [0, 0, 100, 100], "fl": [1, 1],
        }
        symbol = self.loadJSON.schematicItems(scene)._createSymbolShape(record)
        self.assertIsNotNone(symbol, f"{cellName} failed to instantiate")
        return symbol, libraryDict, scene

    def _netlister(self, scene, libraryDict):
        editor = self.types.SimpleNamespace(
            centralW=self.types.SimpleNamespace(scene=scene),
            libraryDict=libraryDict,
            libraryView=self.types.SimpleNamespace(
                libraryModel=self.lmview.designLibrariesModel(libraryDict)),
            libName="gf180_mcu", cellName="nmos_3p3", viewName="schematic",
            switchViewList=["schematic", "symbol"],
            stopViewList=["symbol"],
        )
        return self.xyceNetlist(editor, PDK_ROOT / "tests" / "_tmp_netlist.cir")

    def test_edited_instance_params_in_xyce_line(self):
        edited = {
            "@instName": ["I0", True], "@modelName": ["nmos_3p3", True],
            "@W": ["1u", True], "@L": ["0.5u", True],
            "@nf": ["2", True], "@m": ["3", True],
        }
        symbol, libraryDict, scene = self._makeInstance("nmos_3p3", edited)
        self.assertEqual(symbol.labels["@W"].labelValue, "1u")
        self.assertEqual(symbol.labels["@nf"].labelValue, "2")
        symbol.pinNetMap = {"D": "d", "G": "g", "S": "s", "B": "b"}
        lines = self._netlister(scene, libraryDict).createXyceSymbolLine(
            symbol)
        self.assertEqual(len(lines), 1)
        line = lines[0]
        for expected in ("L=0.5u", "W=1u", "nf=2", "m=3"):
            self.assertIn(expected, line)
        # callback-derived geometry params must recompute, not vanish
        for param in ("ad=", "as=", "pd=", "ps=", "nrd=", "nrs="):
            self.assertIn(param, line)
        # no unresolved @tokens may survive into the line
        self.assertNotRegex(line, r"@\w+")

    def test_default_instance_params_in_xyce_line(self):
        # empty ld: paramDefs/label defaults must still yield a full line
        symbol, libraryDict, scene = self._makeInstance("nmos_3p3", {})
        symbol.pinNetMap = {"D": "d", "G": "g", "S": "s", "B": "b"}
        lines = self._netlister(scene, libraryDict).createXyceSymbolLine(
            symbol)
        self.assertEqual(len(lines), 1)
        line = lines[0]
        for expected in ("L=0.28u", "W=0.22u", "nf=1", "m=1", "ad="):
            self.assertIn(expected, line)
        self.assertNotRegex(line, r"@\w+")


class TestPythonSyntax(unittest.TestCase):
    def test_python_files_ast_parse(self):
        files = sorted(PDK_ROOT.glob("*.py"))
        files += sorted((PDK_ROOT / "pcells").glob("*.py"))
        self.assertTrue(files, "no Python files found")
        for path in files:
            with self.subTest(file=str(path)):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


if __name__ == "__main__":
    unittest.main()
