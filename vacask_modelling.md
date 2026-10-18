# VACASK Modelling Notes — GF180MCU

Known modelling limitations and diagnostics for the `models/vacask/` device
libraries, found during AC/transient validation beyond the original
operating-point smoke tests.

The libraries are converted from the upstream ngspice decks
(`models/ngspice/sm141064.ngspice`, `smbb000149.ngspice`) and verified to
be parameter-faithful. Both issues below are **upstream model limitations**
— they reproduce identically in ngspice — not VACASK conversion defects.
VACASK surfaces them as hard errors (with `matrixcheck=1`) where ngspice
silently produces NaN results.

## Diagnostics

Add to the control block:

```
options matrixcheck=1
```

Without it, VACASK only validates the solved AC vector and reports the
first non-finite unknown, e.g. `NaN found in vector, row node
'I11:flow(br)'` — `flow(br)` is the current unknown of any
potential-contributing element (vsource, inductor, `v=` behavioral
source) and is usually *not* the offending device. With `matrixcheck=1`
the pre-solve Jacobian validation reports the exact entry, e.g.

```
NaN found in matrix, row node 'I2:I6:m0:d_int', column node 'I2:I6:m0:d_int'.
```

`print instance("I2:I6:m0")` then dumps the device opvars; a NaN in the
charge/capacitance outputs (`qg`/`qb`/`qd`/`qs`, `cgg`…`cbb`) while the
DC opvars (`id`, `gm`, `gds`, `vth`, `vgsteff`) are finite identifies a
charge-model domain error.

Note: the first line of a `.sim` file is a title — it is ignored, so do
not put an `include`/`load` on line 1.

## 1. `nmos_3p3` AC NaN at small per-finger width (short-channel bin)

**Affected:** `nmos_3p3` / `nmos_3p3_sab` devices that resolve to model
bin `nmos_3p3__8` — `l` in [0.28, 0.5) µm and total `w` in [1.2, 10) µm —
when the **per-finger width `w/nf` ≲ ~0.6 µm**, in all corners
(tt/ss/ff/sf/fs). Example: `w=2u l=0.28u nf=4` (0.5 µm/finger) fails at
the first AC frequency point; `nf=2` or `w=2.5u` is clean. The boundary
is bias-dependent (observed 0.5–0.55 µm/finger in subthreshold);
treat w/nf ≤ 0.65 µm as unsafe in this bin.

**Mechanism.** The bin card carries `noff=-0.59809917` with
`lnoff=1.299e-6`, `wnoff=3.066e-6`, `pnoff=-1.533e-12`. BSIM4 applies
binning (the `l*/w*/p*` terms) on the per-finger effective width
`weff = w/nf - 2*wint`, so for `w/nf < ~0.6 µm` the effective `noff`
goes negative (e.g. −0.977 at weff=0.48 µm). In the `capmod=2` charge
path (`cvchargemod=0`) a negative `noff` inverts the softplus
`Vgsteff = noff·Vt·ln(1+exp((Vgst−voffcv)/(noff·Vt)))`, producing a
*negative* CV Vgsteff (−0.15 at the diff-pair OP). The next expression,

```
DeltaPhi = Vtm*ln(1.0 + T1*Vgsteff/Denomi)   # bsim4v8.va capmod==2 block
```

then evaluates `ln` of a negative argument → NaN → `VgDP` → all intrinsic
charges and capacitances → NaN AC Jacobian. DC convergence and all
current opvars are unaffected, so OP looks normal.

**Upstream status:** identical `noff` values in the upstream
`sm141064.ngspice` card `nmos_3p3.8`. ngspice emits only
`Warning: Noff = -0.976989 is too small`, computes the same NaN
charge opvars, and returns NaN AC data without aborting. No other bin
in `mos.lib` has a negative `noff` crossing inside its legal range
(verified across all 34 `tt` bins). This is a GlobalFoundries model-card
defect: the bin's legal total-width range admits multi-finger
geometries whose per-finger `noff` is invalid.

**Workaround:** keep `w/nf > ~0.65 µm` for short-channel `nmos_3p3` —
e.g. `w=2u nf=2` instead of `nf=4` (verified: full `tb_diffPair` rundeck
completes the 1 kHz–1 GHz AC sweep). Total width is preserved; only the
S/D junction-capacitance partitioning changes slightly. `nf=1` is also
safe. Do not patch `mos.lib` — it is generated and parameter-faithful to
upstream; a fix belongs upstream or in the conversion source deck.

## 2. `vnpn_*` BJT AC NaN above ~137 °C

**Affected:** all vertical NPN cells (`vnpn_10x10`, `vnpn_5x5`,
`vnpn_0p54x16`, `vnpn_0p54x8`, `vnpn_0p54x4`, `vnpn_0p54x2`) when
`option="temp"` ≳ 137 °C and the collector–substrate junction is biased
(`vsub` ≠ 0). Failure signature:

```
NaN found in matrix, row node 'x1:q0:c_int', column node 'x1:q0:c_int'.
```

**Mechanism.** The npn model cards use `vjs=0.35175`; `sp_bjt`
temperature-adjusts it with the SPICE `pbfact` formula, and the adjusted
substrate-junction potential `BJTtSubpot` crosses zero near 137–138 °C.
The C–sub charge code then divides by ~0
(`capsub = czsub*(1 + xms*vsub/load_ps)` in `spice/bjt.va`) or takes
`ln` of a negative argument for `vsub<0`. At the same temperature with
`vsub=0` the device is clean, confirming the C–sub charge path as the
source.

**Upstream status:** the equations and `vjs=0.35175` are taken verbatim
from the upstream deck; the npn cells are specified for −40…125 °C, so
this is out-of-spec operation anyway. The lateral PNP cells (`vpnp_*`,
`tlevc=1`) use a linear potential update and are clean to at least
175 °C.

**Workaround:** keep `temp ≤ 125 °C` (spec max) in circuits containing
`vnpn_*`; above that the model is unqualified.

## What was verified clean

- All device families (`nmos/pmos_3p3`, `nmos/pmos_6p0`, `nmos_6p0_nat`,
  `nmos_10p0_asym/pmos_10p0_asym`, `vnpn_*`, `vpnp_*`, `nplus/pplus/nwp/
  dnwpw` diodes, `rm*/tm*` resistors, `mim_*`, `nmoscap_*`, `efuse`)
  pass AC sweeps over wide bias ranges at `tt` and ambient temps up to
  each family's specified limit, plus a `noise` sweep.
- `agauss`/`gauss`/`unif` in `statistical.lib`-style parameters return
  their nominal value outside Monte-Carlo analyses — the `mis_*`/`mc_*`
  mismatch parameters are harmless in plain OP/AC/noise.
- Out-of-bin geometry errors (e.g. `l`/`w` below the model's range)
  produce clean `Domain error`/`bin_not_found` diagnostics, not NaN.
