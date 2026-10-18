# Fixed BJT layouts

The ten `vnpn_*`/`vpnp_*` `.gds` files in this directory are copied
byte-for-byte from the Apache-2.0 licensed GF180MCU open PDK directory
`cells/klayout/pymacros/cells/bjt/` of
`globalfoundries-pdk-libs-gf180mcu_fd_pr`:

- `vnpn_10x10.gds`, `vnpn_5x5.gds`, `vnpn_0p54x16.gds`, `vnpn_0p54x8.gds`,
  `vnpn_0p54x4.gds`, `vnpn_0p54x2.gds`
- `vpnp_10x10.gds`, `vpnp_5x5.gds`, `vpnp_0p42x10.gds`, `vpnp_0p42x5.gds`

These fixed mask layouts are converted to native Revolution EDA PCell
shapes at runtime by `pcells/bjt.py`; the original upstream copyright and
Apache-2.0 notices apply to this data.
