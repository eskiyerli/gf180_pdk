# VACASK Model Libraries

Native VACASK device libraries for GF180MCU, produced from the upstream
ngspice decks (`models/ngspice/sm141064.ngspice`, `smbb000149.ngspice`,
`design.ngspice`) with the `ng2vclib` converter, then hand-adapted for
VACASK semantics.

> **Regeneration warning.** The headers say "do not edit by hand;
> regenerate from the PDK model sources", but the manual adaptations
> below are *not* in the converter — a blind re-run of `ng2vclib` will
> lose them. Re-apply each item after regenerating, and diff against
> this list.

## File inventory

Corner libraries — each contains `section tt|ss|ff|sf|fs` blocks:

| File | Family |
|---|---|
| `mos.lib` | `nmos_3p3`, `nmos_3p3_sab`, `nmos_6p0`, `nmos_6p0_nat`, `pmos_*` (all bins) |
| `ldmos.lib` | `nmos_10p0_asym`, `pmos_10p0_asym` (includes `ldmos_nmos.lib`, `ldmos_pmos.lib`, `ldmos_noise.lib`) |
| `bjt.lib` | `vnpn_*`, `vpnp_*` |
| `diode.lib` | `np_*`, `pn_*`, `nwp_*`, `dnwpw*`, `dnwps*`, `sc_diode` |
| `res.lib` | diff/poly/metal/well resistors (+ minimal parasitic junction models) |
| `mimcap.lib` | `mim_*` |
| `moscap.lib` | `nmoscap_*`, `pmoscap_*` |

Support files (plain includes, no sections):

| File | Role |
|---|---|
| `common.lib` | Shared parameters |
| `design.lib` | Global switches (`sw_stat_*`, corner parameter defaults) — enabled |
| `statistical.lib` | Monte-Carlo alternative — **disabled** in `modelLibSettings.json` (conflicts with hard corners by design) |
| `noise_corner.lib` | Noise-corner alternative — **disabled**, same reason |
| `ldmos_statistical.lib` | LDMOS statistical alternative — **disabled**, same reason |
| `ldmos_nmos.lib` / `ldmos_pmos.lib` / `ldmos_noise.lib` | Included by `ldmos.lib` / `ldmos_statistical.lib`; never included directly |

## Manual adaptations (re-apply after any regeneration)

1. **Nonlinear capacitors and voltage-dependent resistors** (MIM, MOSCAP,
   LDMOS parasitics) rewritten as behavioral current sources —
   `i=ddt(C(v)*v)` / `i=v/R(v)` — because VACASK model parameters cannot
   reference terminal voltages.
2. **`temper` / `$temperature`** references translated to `$temp`.
3. **`m=` multiplier**: declared as a subcircuit parameter and forwarded
   as `$mfactor=m` to internal device instances; folded into behavioral
   expressions (which do not support `$mfactor`).
4. **`mim_1p5fF` / `mim_1p0fF` / `mim_2p0fF`** are kept under their
   upstream names as wrapper subcircuits around lowercase implementations
   — works around a VACASK behavioral-source name-mangling issue with
   mixed-case subcircuit names.
5. **Include order**: `res.lib` defines minimal parasitic junction models
   (`np_3p3`, `pn_3p3`, `nwp`) that collide with `diode.lib`. VACASK keeps
   the first definition, so `diode.lib` must be included before
   `res.lib` (the order in `modelLibSettings.json`).
6. **`level=54` / `version=4.6`** LDMOS model cards are mapped to
   `sp_bsim4v8`.

## Corner selection

`modelLibSettings.json` lists every section of each family library and
enables `tt` by default; select another corner by toggling `select` on
the corresponding entry. Available corners: `tt`/`ss`/`ff`/`sf`/`fs`
for `mos.lib` and `ldmos.lib`; `tt`/`ss`/`ff` for `bjt`, `diode`,
`res`, `mimcap`, and `moscap`. All sections pass the all-family
operating-point smoke test (`tests/test_simulator_models.py`).

## Known caveats

See `docs/vacask_modelling.md` for validated AC/transient limitations —
two are *upstream* model-card defects that also reproduce in ngspice:

- `nmos_3p3`/`nmos_3p3_sab` bin `nmos_3p3__8` AC NaN when per-finger
  width `w/nf` < ~0.6 µm (negative effective `noff`); keep `w/nf` >
  ~0.65 µm or use `nf=1`.
- `vnpn_*` AC NaN above ~137 °C with biased collector–substrate junction
  (out-of-spec anyway — spec limit 125 °C).

Debug tip: run with `options matrixcheck=1` to get the offending Jacobian
entry instead of a downstream `NaN found in vector` report.
