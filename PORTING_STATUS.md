# GF180MCU Revolution EDA Port — Status

Milestones 1-7: simulation model assets, KLayout DRC/LVS integration, port
validation scaffold, process vias/paths, symbol/callback validation,
native Revolution PCells for all 22 symbol cells, fixed-layout PCells
for all ten upstream BJT variants plus the bundled efuse cell, and
upstream-faithful generic PCell classes for the remaining upstream
generator names (60 registered PCell entries total).

Source: `globalfoundries-pdk-libs-gf180mcu_fd_pr` (upstream).
Reference port: `ihp_pdk` (IHP SG13G2 Revolution EDA PDK).

## Inventory

| Area | Upstream | Revolution port | Status |
|------|----------|-----------------|--------|
| Primitive symbols (`gf180_mcu/*/symbol.json`) | 22 | 22 present, statically validated | Ported |
| Symbol/netlist cross-validation | — | static checks in `tests/` | Implemented |
| `pcellParameterMap.json` (SDL contract) | — | all 22 cells mapped | Implemented |
| Process vias/paths (`process.py`) | — | 7 vias, 11 paths defined | Implemented — exercised by PCell runtime smoke tests |
| Registered KLayout PCell classes (`cells/klayout/pymacros`) | 30 enabled generator classes (an efuse generator exists upstream but is commented out) | All 30 upstream enabled generator names are represented in the Revolution registry — 60 total entries = 22 symbol cells + 38 upstream-only entries (29 generic generator views + 8 extra fixed BJT variants + efuse). The generic views expose the upstream option surface (volt/deepnwell/pcmpgr/bulk, BJT `Type`, MIM stack gating) | Runtime smoke test passes in the Revolution Poetry env (Qt offscreen); this is not DRC/LVS signoff — no KLayout/DRC runtime validation |
| Symbol MOS PCells (`nmos_3p3`, `nmos_3p3_sab`, `nmos_6p0`, `nmos_6p0_nat`, `pmos_3p3`, `pmos_3p3_sab`, `pmos_6p0`) | `draw_nmos`/`draw_pmos`/`draw_nmos_6p0_nat` | Fixed-voltage bindings of the faithful generic `draw_nmos`/`draw_pmos` port (upstream `bulk` None/Bulk Tie/Guard Ring, `deepnwell`, `pcmpgr`, `grw>=0.36`, `ld`, dogbone landings, voltage minima); `nmos_6p0_nat` is a dedicated `draw_nmos_6p0_nat` port with the upstream `nat_enc_cmp + cmp2cmp` bulk-tie offset | Implemented — runtime-verified for all bulk modes, deep-nwell, PCMP double guard ring, narrow-device and single-finger cases; fixes vs the earlier simplified cells: Guard Ring support, native bulk tie moved outside the NAT marker, `pmos_6p0` min L corrected 0.50→0.55 |
| Xyce model set (`models/xyce/`) | design, sm141064, smbb000149 | staged, with Xyce parser-compatibility fixes for `smbb000149` `.ENDL` library names and MOSCAP `c_length`/`c_width` references | Runtime validated: XyceNF 7.10 all-symbol-family smoke passes |
| Ngspice model set (`models/ngspice/`) | design, sm141064, smbb000149 | staged byte-for-byte | Runtime validated: ngspice-47 all-symbol-family smoke passes |
| VACASK model set (`models/vacask/`) | converted from the Ngspice decks via `ng2vclib` plus manual behavioral adaptation | native VACASK libraries: per-family `section tt/ss/ff/sf/fs` corner blocks (`mos`, `ldmos`, `bjt`, `diode`, `res`, `mimcap`, `moscap`) plus `common`, `design`, `statistical`, `noise_corner`, `ldmos_statistical`, `ldmos_nmos`, `ldmos_pmos`, `ldmos_noise` support files | Runtime validated: vacask 0.3.4 all-family OP smoke passes for all five corners; `m=` multiplier is forwarded through subcircuits to `$mfactor` |
| `modelLibSettings.json` | — | `${PDK_ROOT}`-relative Xyce + Ngspice + VACASK entries, including all `sm141064` sections required by symbol `modelName`s and VACASK `tt` corner sections for all seven device families | Implemented |
| KLayout DRC decks (`drc/`) | gf180mcu, antenna, density | 3 decks integrated, 9 run sets (main/antenna/density × options A/B/C) | Implemented — execution blocked locally: no `klayout` executable or Python module |
| KLayout LVS deck (`lvs/`) | gf180mcu.lvs | 1 deck integrated, process options A/B/C | Implemented — execution blocked locally: no `klayout` executable or Python module |
| Menu actions (`config.json`) | — | KLayoutDRC / KLayoutLVS under `Check` | Implemented — PDK modules import in the Revolution Poetry env; KLayout execution blocked by missing executable |
| Layout layer stipples (`layoutLayers.py`, `stipples/`) | KLayout intrinsic dither patterns `I0`–`I15` per `tech/klayout/gf180mcu.lyp` | True KLayout pattern bitmaps regenerated as `stipples/I<n>.txt` (16x16 tiles); every layer's `btexture` remapped `C<n>` → `I<n>` | Implemented — per-layer verified against the upstream `.lyp` (119/119 exact). Legacy `stipples/C*.txt` files are retained but unreferenced |

## Runtime validation

- Revolution Poetry environment: **47 tests, all passed** with
  `QT_QPA_PLATFORM=offscreen` and `REVEDA_PDK_PATH` pointed at this PDK,
  including the runtime PCell suite (shape generation, pins, Guard Ring
  layers, coercion minima for all 7 symbol MOS cells and the other
  parameterized cells).
- Stdlib/system-Python environment: **35 tests, 34 passed, 1 skipped**;
  the skipped test is the Revolution-runtime PCell suite when
  `revedaEditor` is unavailable.
- `vacask` resolves to VACASK 0.3.4. The generated all-family `.sim`
  fixture loads the staged `models/vacask` corner libraries, exercises
  every symbol-backed `modelName` plus efuse and 10V asymmetric LDMOS
  (with `m=` multiplier forwarding), and completes the operating-point
  analysis for all five corners (tt/ss/ff/sf/fs). VACASK reports one
  non-fatal `dnwpw` IKR warning, matching the ngspice behavior.
- `Xyce` resolves to XyceNF 7.10.0. The generated all-family fixture loads
  `design.xyce`, `sm141064.xyce`, and `smbb000149.xyce`; exercises every
  symbol-backed `modelName` plus efuse and 10V asymmetric LDMOS; and
  completes 3 DC-sweep steps with 83 instantiated devices and no solver
  failures.
- `ngspice` resolves to ngspice-47. The equivalent staged Ngspice fixture
  completes 3 DC-sweep rows. Ngspice reports non-fatal warnings for three
  unsupported VPNP parameters (`cbcp`, `cbep`, `ccsp`) and a disabled
  `dnwpw` IKR model effect.
- The `revedasim` Ngspice integration was audited and fixed so generated
  rundecks now emit configured `.LIB`/`.INC` model directives; its
  integration script passes, including a model-settings rundeck check.
- KLayout is not installed in either the shell or the Revolution Poetry
  environment (`klayout` executable and `klayout` Python module are absent),
  so the DRC/LVS decks and GUI menu actions could not be executed. The menu
  modules import successfully and expose 9 DRC run sets plus 3 LVS process
  options.

## Xyce compatibility patches

The upstream Xyce files required two minimal syntax fixes before XyceNF
7.10 could parse them:

- every outer `.LIB` block in `smbb000149.xyce` now ends with a named
  `.ENDL <section>`;
- all eight MOSCAP current expressions in `sm141064.xyce` now use the
  declared subcircuit parameters `c_length` and `c_width` instead of the
  undeclared symbols `l` and `w`.

The configured `models/xyce/` copies and the duplicate root-level
`models/*.xyce` copies were patched consistently. Ngspice model files are
unchanged.

## VACASK conversion notes

The `models/vacask/` libraries were produced from the Ngspice decks with
the `ng2vclib` converter, then hand-adapted for VACASK semantics:

- nonlinear capacitors and voltage-dependent resistors (MIM, MOSCAP,
  LDMOS parasitics) were rewritten as behavioral current sources
  (`i=ddt(C(v)*v)` / `i=v/R(v)`), since VACASK model parameters cannot
  reference terminal voltages;
- Ngspice `temper`/`$temperature` references were translated to `$temp`;
- the SPICE call-level multiplier `m` is a declared subcircuit parameter
  forwarded as `$mfactor=m` to internal device instances (and folded
  into behavioral expressions, which do not support `$mfactor`);
- `mim_1p5fF`/`mim_1p0fF`/`mim_2p0fF` keep their upstream names as
  wrapper subcircuits around lowercase implementations, working around
  a VACASK behavioral-source name-mangling issue with mixed-case
  subcircuit names;
- `statistical.lib`/`noise_corner.lib`/`ldmos_statistical.lib` are
  Monte-Carlo/noise alternatives and conflict with the hard-corner
  files by design — they ship disabled in `modelLibSettings.json`;
- `res.lib` defines minimal parasitic junction models (`np_3p3`,
  `pn_3p3`, `nwp`) that collide with `diode.lib`; VACASK keeps the
  first definition, so `diode.lib` must be included before `res.lib`
  (it is, in `modelLibSettings.json` order).

The GF180 `level=54`/`version=4.6` LDMOS models are mapped to
`sp_bsim4v8`, and every symbol now carries a `VacaskNetlistLine`
attribute for the VACASK netlister.

## Next milestones

1. Schematic symbols / parameter maps for the generic upstream generator
   views (currently layout-only pcell views).
2. End-to-end DRC/LVS regression runs against upstream test layouts.
