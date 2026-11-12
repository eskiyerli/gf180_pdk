# Upstream Provenance

This PDK ports the primitive-device library of the GlobalFoundries GF180MCU
open PDK. Record the pinned revision here so future ports/diffs can be
re-based.

| Field | Value |
|---|---|
| Source repository | https://github.com/google/globalfoundries-pdk-libs-gf180mcu_fd_pr |
| Pinned commit | `9f992d5a9186d1f7820c58f039c484ad35b2edea` |
| Commit date | 2023-05-31 |
| `git describe` | `v0.0.0-49-g9f992d5` |
| Reference port | `ihp_pdk` (IHP SG13G2 Revolution EDA PDK) |

## Staged-file manifest

| Upstream path | Ported to | Notes |
|---|---|---|
| `cells/xschem/symbols/*.sym` (22 files) | `gf180_mcu/*/symbol.json` | All 22 symbols, enriched with `VacaskNetlistLine`, `lvsNetlistLine`, `paramDefs` |
| `cells/klayout/pymacros/cells/{mos,diode,res,mimcap,moscap,bjt,efuse}.py` + `draw_*.py` | `pcells/*.py` | All 30 enabled generator names → 60 registered entries (generic views + fixed variants) |
| `cells/klayout/pymacros/cells/{vnpn,vpnp}_*.gds`, `efuse.gds` | `pcells/*.gds` | Fixed-layout fixtures for BJT variants and efuse |
| `models/ngspice/{design,sm141064,smbb000149}.ngspice` | `models/ngspice/` | Byte-for-byte |
| `models/ngspice/*` (same decks, Xyce syntax) | `models/xyce/` | +2 parser fixes: named `.ENDL` on every `smbb000149` section; `c_length`/`c_width` in `sm141064` MOSCAP expressions |
| `models/ngspice/*` | `models/vacask/` | `ng2vclib` conversion + manual behavioral adaptation — see `models/vacask/README.md` |
| `rules/klayout/drc/gf180mcu*.drc` (3 decks) | `drc/` | 9 run sets, process options A/B/C |
| `rules/klayout/lvs/gf180mcu.lvs` | `lvs/` | 3 process options |
| `tech/klayout/gf180mcu.lyp` | `layoutLayers.py`, `stipples/I*.txt` | Intrinsic dither patterns regenerated as 16x16 tiles; 119/119 layer patterns verified |

## Not ported (by design)

- `models/ngspice/testing/` — upstream characterization golden data
  (`180MCU_SPICE_DATA`); retained upstream for future regression harness.
- `cells/klayout/testing/` — pcell test GDS goldens; retained upstream for
  Phase-2 layout verification.
- `cells/klayout/pymacros` scaffolding (`gf180mcu.lym`, `settings.json`,
  test cases) — KLayout-specific.
- Standard-cell / IO libraries — outside this repo's scope (`fd_pr` is the
  primitive-device library only).
- The disabled upstream `efuse` generator is ported anyway (it exists in
  the upstream source, commented out of the registry).
