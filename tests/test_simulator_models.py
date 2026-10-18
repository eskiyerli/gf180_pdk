"""Runtime smoke tests for the staged GF180MCU simulator models.

These tests are intentionally stdlib-only: they generate temporary SPICE
fixtures and invoke system-installed Xyce/Ngspice executables when present.
"""

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PDK_ROOT = Path(__file__).resolve().parent.parent
XYCE_MODELS = PDK_ROOT / "models" / "xyce"
NGSPICE_MODELS = PDK_ROOT / "models" / "ngspice"
VACASK_MODELS = PDK_ROOT / "models" / "vacask"


def _family_fixture(model_dir: Path, ext: str, output: Path, *, ngspice: bool) -> str:
    analysis = (
        f".dc Vd33 0 1 0.5\n"
        f".print dc FORMAT=CSV file={output} "
        "{I(Vd33)} {I(Vsp)} {I(Vd60)} {I(Vdnat)} {I(Vc)} "
        "{I(Vdiod)} {I(Vr)} {I(Vcap)} {I(Vmoscap)} {I(Vf)} {I(Vdh)}\n"
    )
    if ngspice:
        analysis = (
            ".control\n"
            "dc Vd33 0 1 0.5\n"
            f"wrdata {output} i(Vd33) i(Vsp) i(Vd60) i(Vdnat) i(Vc) "
            "i(Vdiod) i(Vr) i(Vcap) i(Vmoscap) i(Vf) i(Vdh)\n"
            "quit\n"
            ".endc\n"
        )
    return f"""* GF180MCU staged model-family smoke test
Vd33 d33 0 dc 1.0
Vg33 g33 0 dc 1.0
Xn33 d33 g33 0 0 nmos_3p3 W=4u L=0.28u
Vd33s d33s 0 dc 1.0
Vg33s g33s 0 dc 1.0
Xn33s d33s g33s 0 0 nmos_3p3_sab W=4u L=0.28u
Vsp sp 0 dc 1.0
Vgp gp 0 dc 0.0
Xp33 0 gp sp sp pmos_3p3 W=4u L=0.28u
Vgps gps 0 dc 0.0
Xp33s 0 gps sp sp pmos_3p3_sab W=4u L=0.28u
Vd60 d60 0 dc 3.0
Vg60 g60 0 dc 3.0
Xn60 d60 g60 0 0 nmos_6p0 W=4u L=0.6u
Vdnat dnat 0 dc 1.0
Vgnat gnat 0 dc 1.0
Xnnat dnat gnat 0 0 nmos_6p0_nat W=4u L=1.8u
Vsp6 sp6 0 dc 3.0
Vgp6 gp6 0 dc 0.0
Xp60 0 gp6 sp6 sp6 pmos_6p0 W=4u L=0.5u
Vc c 0 dc 1.0
Vb b 0 dc 0.8
Xbjt c b 0 0 vnpn_10x10
Vcp cp 0 dc -1.0
Vbp bp 0 dc -0.8
Xp cp bp 0 vpnp_10x10
Vdiod diod 0 dc 0.7
Dnp diod 0 np_3p3 AREA=1e-12 PJ=4e-6
Ddn diod 0 dnwpw AREA=9e-12
Vr rtop 0 dc 1.0
Xres rtop 0 0 nplus_u r_width=1u r_length=10u
Xpures rtop 0 0 pplus_u r_width=1u r_length=10u
Xnpoly rtop 0 0 npolyf_u r_width=1u r_length=10u
Xppoly rtop 0 0 ppolyf_u r_width=1u r_length=10u
Xrm rtop 0 rm1 r_width=1u r_length=10u
Xnw rtop 0 0 nwell r_width=3u r_length=10u
Vcap ctop 0 dc 1.0
Xcap ctop 0 mim_2p0fF c_width=5u c_length=5u
Vmoscap mtop 0 dc 1.0
Xmoscap mtop 0 nmoscap_3p3 c_width=1u c_length=1.06u
Xnmoscap6 mtop 0 nmoscap_6p0 c_width=1u c_length=1.06u
Xpmoscap3 mtop 0 pmoscap_3p3 c_width=1u c_length=1.06u
Xpmoscap6 mtop 0 pmoscap_6p0 c_width=1u c_length=1.06u
Vf ftop 0 dc 1.0
Xfuse ftop 0 efuse pblow=1
Vdh dh 0 dc 10.0
Vgh gh 0 dc 10.0
Xh dh gh 0 0 nmos_10p0_asym W=4u L=0.6u
{analysis}.include "{model_dir / f'design.{ext}'}"
.lib "{model_dir / f'sm141064.{ext}'}" typical
.lib "{model_dir / f'sm141064.{ext}'}" bjt_typical
.lib "{model_dir / f'sm141064.{ext}'}" diode_typical
.lib "{model_dir / f'sm141064.{ext}'}" res_typical
.lib "{model_dir / f'sm141064.{ext}'}" mimcap_typical
.lib "{model_dir / f'sm141064.{ext}'}" moscap_typical
.lib "{model_dir / f'smbb000149.{ext}'}" typical
.end
"""


def _vacask_settings() -> tuple[list[tuple[str, str]], list[str]]:
    settings = json.loads(
        (PDK_ROOT / "modelLibSettings.json").read_text(encoding="utf-8")
    )["simulators"]["VACASK"]
    libs = [
        (
            str(PDK_ROOT / entry["modelPath"].split("${PDK_ROOT}/", 1)[1]),
            entry["modelSection"],
        )
        for entry in settings["modelLibraries"]
        if entry.get("select")
    ]
    includes = [
        str(PDK_ROOT / entry[1].split("${PDK_ROOT}/", 1)[1])
        for entry in settings["includePaths"]
        if entry[0]
    ]
    return libs, includes


def _vacask_fixture() -> str:
    libs, includes = _vacask_settings()
    lib_lines = "".join(
        f'include "{path}" section={section}\n' if section else f'include "{path}"\n'
        for path, section in libs
    )
    include_lines = "".join(f'include "{path}"\n' for path in includes)
    return f"""* GF180MCU staged VACASK model-family smoke test
{lib_lines}{include_lines}model v vsource
vd33 (d33 0) v dc=1.0
vg33 (g33 0) v dc=1.0
xn33 (d33 g33 0 0) nmos_3p3 w=4u l=0.28u m=2
vd33s (d33s 0) v dc=1.0
vg33s (g33s 0) v dc=1.0
xn33s (d33s g33s 0 0) nmos_3p3_sab w=4u l=0.28u
vsp (sp 0) v dc=1.0
vgp (gp 0) v dc=0.0
xp33 (0 gp sp sp) pmos_3p3 w=4u l=0.28u
xps (0 gp sp sp) pmos_3p3_sab w=4u l=0.28u
vd60 (d60 0) v dc=3.0
vg60 (g60 0) v dc=3.0
xn60 (d60 g60 0 0) nmos_6p0 w=4u l=0.6u
xnnat (d60 g60 0 0) nmos_6p0_nat w=4u l=1.8u
xp60 (0 g60 sp sp) pmos_6p0 w=4u l=0.5u
vc (c 0) v dc=1.0
vb (b 0) v dc=0.8
xbjt (c b 0 0) vnpn_10x10 m=2
xp (c b 0) vpnp_10x10
vdiod (diod 0) v dc=0.7
dnp (diod 0) np_3p3 area=1e-12 pj=4e-6
ddn (diod 0) dnwpw area=9e-12
vr (rtop 0) v dc=1.0
xres (rtop 0 0) nplus_u r_width=1u r_length=10u m=2
xpures (rtop 0 0) pplus_u r_width=1u r_length=10u
xnpoly (rtop 0 0) npolyf_u r_width=1u r_length=10u
xppoly (rtop 0 0) ppolyf_u r_width=1u r_length=10u
xrm (rtop 0) rm1 r_width=1u r_length=10u
xnw (rtop 0 0) nwell r_width=3u r_length=10u
xcap (rtop 0) mim_2p0fF c_width=5u c_length=5u m=2
xmoscap (rtop 0) nmoscap_3p3 c_width=1u c_length=1.06u
xpmoscap6 (rtop 0) pmoscap_6p0 c_width=1u c_length=1.06u
xfuse (rtop 0) efuse pblow=1
vdh (dh 0) v dc=10.0
vgh (gh 0) v dc=10.0
xh (dh gh 0 0) nmos_10p0_asym w=4u l=0.6u m=2
xhp (0 gh dh dh) pmos_10p0_asym w=4u l=0.6u

control
  analysis op op
endc
"""


def _vacask_masters() -> set[str]:
    masters = set()
    libs, includes = _vacask_settings()
    for path, section in libs:
        text = Path(path).read_text(encoding="utf-8")
        if section:
            match = re.search(
                rf"(?ms)^section {re.escape(section)}\s*\n(.*?)^endsection\s*$",
                text,
            )
            assert match is not None, f"missing section {section} in {path}"
            text = match.group(1)
        for found in re.finditer(r"(?m)^(?:subckt|model)\s+([^\s(]+)", text):
            masters.add(found.group(1))
    for path in includes:
        text = Path(path).read_text(encoding="utf-8")
        for found in re.finditer(r"(?m)^(?:subckt|model)\s+([^\s(]+)", text):
            masters.add(found.group(1))
    return masters


def _symbol_model_names() -> set[str]:
    names = set()
    for path in sorted((PDK_ROOT / "gf180_mcu").glob("*/symbol.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.values() if isinstance(data, dict) else (data,)
        for value in items:
            for item in value if isinstance(value, list) else (value,):
                if (
                    isinstance(item, dict)
                    and item.get("nam") == "modelName"
                    and item.get("def")
                ):
                    names.add(str(item["def"]))
    return names


class TestStagedModelSyntax(unittest.TestCase):
    def test_fixture_matches_model_lib_settings(self):
        settings = json.loads(
            (PDK_ROOT / "modelLibSettings.json").read_text(encoding="utf-8")
        )
        for ngspice, sim_name, ext, model_dir in (
            (False, "Xyce", "xyce", XYCE_MODELS),
            (True, "Ngspice", "ngspice", NGSPICE_MODELS),
        ):
            sim = settings["simulators"][sim_name]
            expected_libs = [
                (str(PDK_ROOT / entry["modelPath"].split("${PDK_ROOT}/", 1)[1]),
                 entry["modelSection"])
                for entry in sim["modelLibraries"] if entry.get("select")
            ]
            expected_includes = [
                str(PDK_ROOT / entry[1].split("${PDK_ROOT}/", 1)[1])
                for entry in sim["includePaths"] if entry[0]
            ]
            fixture = _family_fixture(model_dir, ext, Path("out.csv"), ngspice=ngspice)
            actual_includes = re.findall(r'^\.include "([^"]+)"', fixture, re.M)
            actual_libs = re.findall(
                r'^\.lib "([^"]+)" ([^\s]+)', fixture, re.M
            )
            with self.subTest(simulator=sim_name):
                self.assertEqual(actual_includes, expected_includes)
                self.assertEqual(actual_libs, expected_libs)

    def test_fixture_uses_all_symbol_models(self):
        fixture = _family_fixture(
            XYCE_MODELS, "xyce", Path("out.csv"), ngspice=False
        ).casefold()
        self.assertEqual(len(_symbol_model_names()), 22)
        for name in sorted(_symbol_model_names()):
            with self.subTest(model=name):
                self.assertIn(name.casefold(), fixture)

    def test_xyce_smbb_libraries_are_named(self):
        paths = (
            XYCE_MODELS / "smbb000149.xyce",
            PDK_ROOT / "models" / "smbb000149.xyce",
        )
        for path in paths:
            with self.subTest(path=path):
                text = path.read_text()
                self.assertEqual(
                    re.findall(r"^\s*\.ENDL\s*$", text, re.M), [])

    def test_vacask_settings_paths_and_sections(self):
        settings = json.loads(
            (PDK_ROOT / "modelLibSettings.json").read_text(encoding="utf-8")
        )["simulators"]["VACASK"]
        self.assertGreaterEqual(len(settings["modelLibraries"]), 7)
        for entry in settings["modelLibraries"]:
            with self.subTest(path=entry["modelPath"]):
                path = PDK_ROOT / entry["modelPath"].split("${PDK_ROOT}/", 1)[1]
                self.assertTrue(path.is_file(), path)
                section = entry.get("modelSection")
                if section:
                    text = path.read_text(encoding="utf-8")
                    self.assertIsNotNone(
                        re.search(
                            rf"(?m)^section {re.escape(section)}\s*$", text
                        ),
                        f"missing section {section} in {path}",
                    )
        for entry in settings["includePaths"]:
            if entry[0]:
                with self.subTest(path=entry[1]):
                    path = PDK_ROOT / entry[1].split("${PDK_ROOT}/", 1)[1]
                    self.assertTrue(path.is_file(), path)

    def test_vacask_libraries_cover_symbol_models(self):
        masters = _vacask_masters()
        missing = [
            name for name in _symbol_model_names() if name not in masters
        ]
        self.assertEqual(missing, [])

    def test_symbols_have_vacask_netlist_line(self):
        missing = []
        for path in sorted((PDK_ROOT / "gf180_mcu").glob("*/symbol.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            found = any(
                isinstance(item, dict) and item.get("nam") == "VacaskNetlistLine"
                for item in data
            )
            if not found:
                missing.append(path.parent.name)
        self.assertEqual(missing, [])

    def test_vacask_fixture_matches_model_lib_settings(self):
        libs, includes = _vacask_settings()
        fixture = _vacask_fixture()
        actual_libs = re.findall(
            r'^include "([^"]+)" section=([^\s]+)', fixture, re.M
        )
        actual_includes = [
            line for line in re.findall(r'^include "([^"]+)"', fixture, re.M)
            if line not in {path for path, _ in actual_libs}
        ]
        self.assertEqual(actual_libs, libs)
        self.assertEqual(actual_includes, includes)

    def test_xyce_moscaps_use_declared_dimensions(self):
        paths = (
            XYCE_MODELS / "sm141064.xyce",
            PDK_ROOT / "models" / "sm141064.xyce",
        )
        for path in paths:
            with self.subTest(path=path):
                text = path.read_text()
                self.assertNotIn("*l*w", text)
                self.assertGreaterEqual(text.count("*c_length*c_width"), 8)


class TestSimulatorSmoke(unittest.TestCase):
    def test_xyce_model_families(self):
        executable = shutil.which("Xyce")
        if executable is None:
            self.skipTest("Xyce executable not installed")
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            netlist = tmpdir / "gf180_xyce_all.cir"
            output = tmpdir / "gf180_xyce_all.csv"
            log = tmpdir / "gf180_xyce_all.log"
            netlist.write_text(
                _family_fixture(XYCE_MODELS, "xyce", output, ngspice=False)
            )
            result = subprocess.run(
                [executable, "-hspice-ext", "all", str(netlist), "-l", str(log)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            log_text = log.read_text() if log.exists() else result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, log_text)
            self.assertNotIn("Netlist error", log_text)
            self.assertNotIn("*** Xyce Abort ***", log_text)
            self.assertIn("Number Successful Steps Taken", log_text)
            self.assertGreaterEqual(
                len([line for line in output.read_text().splitlines() if line.strip()]),
                4,
            )

    def test_ngspice_model_families(self):
        executable = shutil.which("ngspice")
        if executable is None:
            self.skipTest("ngspice executable not installed")
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            netlist = tmpdir / "gf180_ng_all.cir"
            output = tmpdir / "gf180_ng_all.csv"
            netlist.write_text(
                _family_fixture(NGSPICE_MODELS, "ngspice", output, ngspice=True)
            )
            result = subprocess.run(
                [executable, "-b", str(netlist)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            log_text = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, log_text)
            self.assertIn("No. of Data Rows : 3", log_text)
            self.assertGreaterEqual(
                len([line for line in output.read_text().splitlines() if line.strip()]),
                3,
            )

    def test_vacask_model_families(self):
        executable = shutil.which("vacask")
        if executable is None:
            self.skipTest("vacask executable not installed")
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            netlist = tmpdir / "gf180_vacask_all.sim"
            netlist.write_text(_vacask_fixture())
            result = subprocess.run(
                [executable, str(netlist)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=tmpdir,
            )
            log_text = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, log_text)
            self.assertIn("Elapsed time", log_text)
            self.assertNotIn("not found", log_text)
            self.assertNotIn("not defined", log_text)
            self.assertNotIn("Parser syntax error", log_text)


if __name__ == "__main__":
    unittest.main()
