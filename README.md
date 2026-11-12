# GF180MCU Process Design Kit (PDK) for Revolution EDA

A Python-based Process Design Kit for the **GlobalFoundries GF180MCU 180 nm
open-source technology**, integrated with the **Revolution EDA**
schematic-to-GDS IC design environment.

Ported from Google's
[`globalfoundries-pdk-libs-gf180mcu_fd_pr`](https://github.com/google/globalfoundries-pdk-libs-gf180mcu_fd_pr)
primitive-device library (see `docs/UPSTREAM.md` for the pinned upstream
revision). The IHP SG13G2 Revolution EDA PDK (`ihp_pdk`) served as the
reference port.

**Technology Details:**

- **Process Node:** GF180MCU (180 nm MCU, gf180mcuD variant)
- **PDK Version:** 0.3.0
- **License:** MPL-2.0 (see headers in source files)

---

## What's Implemented

### 1. Symbol Library & Callbacks

All 22 device symbols from the upstream xschem library are ported into the
`gf180_mcu` library. Every symbol carries the netlist attributes required by
each output format (`SpiceNetlistLine`, `VacaskNetlistLine`,
`lvsNetlistLine`, `lvsDeviceType`, `modelName`, `pinOrder`, `paramDefs`), and
a matching callback class in `callbacks.py` computes electrical parameters
(junction areas/perimeters, sheet resistance, multiplier folding) from the
placed label values.

**Device families:**

- **MOSFETs:** `nmos_3p3`, `nmos_3p3_sab`, `nmos_6p0`, `nmos_6p0_nat`,
  `pmos_3p3`, `pmos_3p3_sab`, `pmos_6p0`
- **MOS capacitors:** `nmoscap_3p3`, `nmoscap_6p0`, `pmoscap_3p3`,
  `pmoscap_6p0`
- **Resistors:** `nplus_u`, `pplus_u`, `npolyf_u`, `ppolyf_u`, `nwell`,
  `dnwpw`, `rm1` (metal-1)
- **Capacitors:** `mim_2p0fF` (MIM)
- **Diodes:** `np_3p3`
- **Bipolar:** `vnpn_10x10`, `vpnp_10x10`

### 2. Parametric Cells (PCells)

60 registered PCell entries in `pcells/` (see the `pcells` dict in
`pcells/__init__.py`):

- The 22 symbol-backed cells above.
- All upstream enabled generator names as generic parameterized views —
  `nmos`/`pmos` (with `volt`, `deepnwell`, `pcmpgr`, `bulk` options),
  `nmos_10p0_asym`/`pmos_10p0_asym` LDMOS, `npn_bjt`/`pnp_bjt`, all diode
  generators, `nmoscap`/`pmoscap`/`nmoscap_b`/`pmoscap_b`, `mimcap`,
  `metal_resistor`, and the full resistor generator family.
- Fixed-layout BJT variants (`vnpn_*`/`vpnp_*` sizes) and `efuse`, built from
  the upstream GDS fixtures.

Generic-view cells currently have no schematic symbols (matching upstream's
22-symbol scope); they can be placed directly in layout.

### 3. Simulation Models

`modelLibSettings.json` ships `${PDK_ROOT}`-relative library settings for
three simulators:

- **Ngspice** — upstream decks staged byte-for-byte
  (`models/ngspice/`).
- **Xyce** — upstream decks with two parser-compatibility fixes for XyceNF
  7.10 (`models/xyce/`; see `docs/PORTING_STATUS.md`).
- **VACASK** — native libraries converted from the ngspice decks with
  hand-adapted behavioral sources (`models/vacask/`; per-family `tt/ss/ff/
  sf/fs` corner sections plus statistical/noise variants). See
  `models/vacask/README.md` for the conversion recipe and known caveats in
  `docs/vacask_modelling.md`.

### 4. DRC / LVS Integration

- `drc/` — the three upstream KLayout DRC decks (`gf180mcu`, antenna,
  density), exposed as 9 run sets (process options A/B/C).
- `lvs/` — the upstream `gf180mcu.lvs` deck with process options A/B/C.
- Menu actions under **Check → DRC with KLayout…** / **Check → LVS with
  KLayout…** (`klayoutDRC.py`, `klayoutLVS.py`, registered in
  `config.json`).

> Requires a `klayout` executable or Python module on the system; the decks
> are integrated but are not yet covered by runtime regression tests.

### 5. Technology Data

- `gf180_mcu_tech.json` + `gf180_mcu_tech.py` — process parameters and layer
  map.
- `process.py` — 7 via definitions and 11 path definitions.
- `layoutLayers.py` + `stipples/` — layout layer styles; every layer's fill
  pattern verified 1:1 against the upstream KLayout `.lyp` (119/119).
- `schLayers.py`, `symLayers.py` — schematic/symbol layer definitions.
- `pcellParameterMap.json` — SDL contract mapping pcell parameters to
  symbol label values.

## Running the Tests

From the PDK root:

```
python -m unittest discover -s tests -v
```

- `test_pdk_assets.py` — static validation of symbols, parameter maps,
  DRC/LVS deck wiring, process definitions, and pcell registry.
- `test_simulator_models.py` — generates SPICE fixtures exercising every
  symbol-backed model and runs them on `xyce`, `ngspice`, and `vacask` when
  the executables are installed (skipped otherwise).

The full suite also runs inside the Revolution Poetry environment with
`QT_QPA_PLATFORM=offscreen`, where an additional runtime PCell suite
exercises shape generation for all parameterized cells.

## Layout

```
gf180_mcu/          symbol + pcell views for the 22 device cells
pcells/             PCell implementations (mosfet, diodes, resistors,
                    moscaps, mimcap, bjt) + fixed-layout GDS fixtures
models/             ngspice/, xyce/, vacask/ simulator model sets
drc/, lvs/          KLayout rule decks
stipples/           fill patterns referenced by layoutLayers.py
tests/              unittest suite
docs/               porting status, upstream provenance, VACASK notes
```

## Documentation

- `docs/PORTING_STATUS.md` — milestone-by-milestone port inventory and
  validation log.
- `docs/UPSTREAM.md` — pinned upstream revision and staged-file manifest.
- `docs/vacask_modelling.md` — VACASK model caveats, diagnostics, and known
  upstream model defects.
- `models/vacask/README.md` — VACASK library conversion notes.
