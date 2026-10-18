# Fixed efuse layout

`efuse.gds` is copied byte-for-byte from the Apache-2.0 licensed GF180MCU
open PDK file `cells/klayout/pymacros/cells/efuse/efuse.gds` of
`globalfoundries-pdk-libs-gf180mcu_fd_pr`.

The fixed mask layout (top cell `efuse_cell`) is converted to native
Revolution EDA PCell shapes at runtime by `pcells/bjt.py`; the original
upstream copyright and Apache-2.0 notices apply to this data. The upstream
efuse PCell generator is commented out in the upstream library and is not
one of the 30 enabled registered generators.
