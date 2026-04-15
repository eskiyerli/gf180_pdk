# GF180 MCU Process Design Kit (PDK) for Revolution EDA

An early‑stage Python‑based PDK targeting the **GlobalFoundries 180‑nm MCU process** integrated
with the **Revolution EDA** schematic‑to‑GDS IC design environment.

> ⚠️ This PDK is currently **in development**. Only schematic symbols imported from an Xschem
> source are available and have seen minimal testing. Layout support, parametric cells,
> and complete layer definitions are still works in progress. Developers and contributors
> are welcome to help fill out the missing pieces.

## Overview

The goal of `gf180_pdk` is to provide a fully functional design kit for the GF180 MCU
technology, including:

- Symbol library for schematic capture (many devices already imported)
- Instance callback classes for automatic electrical parameter computation
- Schematic and symbol layer definitions for front‑end drawing
- Layout layer definitions (initially empty) and skeleton for future GDS mapping
- Process technology parameters (grid, units, etc.)
- Placeholder directories for pcells, models and DRC decks

**Technology Details:**
- **Process Node:** GF 180‑nm MCU
- **PDK Status:** Alpha / development
- **License:** Commons Clause / MPL‑2.0 (see headers in source files)

---

## What's Implemented

### 1. Symbol Library & Callbacks

A set of device symbols has been imported from Xschem; each symbol is accompanied by a
callback class in `callbacks.py` that reads label values and calculates parameters used
for netlisting and annotation.

**Supported Device Families (partial list):**
- **MOSFETs:** nmos_3p3, nmos_6p0, nmos_3p3_sab, nmos_6p0_nat, etc.
- **Resistors:** dnwpw (diff‑nwell poly‑resistor) with area/ perimeter parameters
- **Capacitors:** mim_2p0fF, nmoscap_3p3, nmoscap_6p0
- Additional variants with multiple fingers and implant options

Callbacks automatically compute device dimensions, area, perimeter, and source/drain
resistance using `quantiphy.Quantity` objects.  See `callbacks.py` for the full list of
classes and formulae.

### 2. Layer Definitions

#### Schematic & Symbol Layers (`schLayers.py` / `symLayers.py`)

Basic drawing layers for wires, pins, annotations and device outlines.  These modules
follow the Revolution EDA dataclass conventions, defining colours, line styles and
z‑order for schematic rendering.

#### Layout Layers (`layoutLayers.py`)

Currently empty; reserved for future definitions of GDS layer/datatype mappings when
layout support is added.

### 3. Process Parameters (`process.py` & `gf180_mcu_tech.py`)

Defines grid settings and GDS units used by the layout editor:

- **DBU:** 1000 (1 µm = 1000 DBU)
- **Snap grid:** 50 nm
- **Major grid:** 100 nm
- **GDS unit:** 1 µm with 1 nm precision

This information is queried by Revolution EDA at runtime to maintain consistent
geometry and snapping.

### 4. Project Skeleton

Several directories are present but not yet populated:

- `pcells/` – placeholder for future parametric layout cells (currently only `base.py`)
- `models/` – contains a couple of example `.xyce` files for simulation
- `drc/` – intended location for KLayout rule decks
- `stipples/` – fill patterns used by layout rendering

---

## How to Use with Revolution EDA

### Installation

1. **Clone or copy** the `gf180_pdk` folder into your Revolution EDA workspace:
   ```bash
   cd /path/to/revolution-eda
   git clone <gf180_pdk_repo> gf180_pdk
   ```
2. **Configure the PDK path** either by setting the `REVEDA_PDK_PATH` environment
   variable or by adding it to the `.env` file in the root of Revolution EDA
   (relative or absolute path).
3. **Restart Revolution EDA** to load the new PDK.
4. **Add the library directory** (`gf180_mcu`) in the *Library Browser* via the
   *Options* dialog or menu, so that schematic symbols appear in the component list.

### Creating Schematics

1. Launch the Revolution EDA schematic editor.
2. Select **GF180 MCU** from the PDK selector (if applicable).
3. Add instances via **Right‑click → Add Instance** and choose from the `gf180_mcu`
   library.
4. Double‑click an instance to edit parameters; values should use Quantiphy units
   (e.g. `10u`, `180n`, `4e-3`).
5. Connect pins and build your circuit as usual.

> ⚠️ Layout support is not yet implemented. The layout editor currently will accept
> imported GDS or blank cells only; parametric cells and layer mappings will be
> provided in a future update.

### Running Simulations

The project contains a couple of simple Xyce netlists in `models/`. When you
export a netlist from a schematic, callbacks automatically generate appropriate
parameter values, but be aware that the GF180 model library is not yet integrated
with Revolution EDA’s netlisting engine.  You may need to manually include
`models/*.xyce` or translate them to `.lib` format.

---

## Project Structure

```
gf180_pdk/
├── README.md                   # This file
├── __init__.py                 # Package initialization (empty)
├── config.json                 # PDK metadata used by menu system
├── callbacks.py                # Instance parameter callbacks (≃370 lines)
├── process.py                  # Grid and GDS unit definitions
├── gf180_mcu_tech.py           # Technology class exposing techParams
├── gf180_mcu_tech.json         # Node definition JSON
├── schLayers.py                # Schematic layer definitions
├── symLayers.py                # Symbol layer definitions
├── layoutLayers.py             # Layout layer definitions (currently stub)
├── pcells/                     # Parametric cells (base.py only)
│   └── base.py                 # Base cell classes / helpers
├── models/                     # Example simulation files (*.xyce)
├── drc/                        # DRC rule decks (empty placeholder)
└── stipples/                   # Fill pattern files used by layout
```

---

## Development & Contribution

Contributors are encouraged to expand the PDK by implementing the missing pieces:

- **Add parametric cells** in `pcells/` following the patterns in other PDKs (e.g. IH PDK).
- **Define layout layers** with proper GDS mappings in `layoutLayers.py`.
- **Create callback classes** for new devices as symbols are added.
- **Populate `models/`** with SPICE or Xyce model libraries and connect them
  through the netlisting system.
- **Develop DRC rule decks** for GF180 and integrate with `klayoutDRC.py`.

The existing `callbacks.py` file already demonstrates how to compute geometry-related
parameters using `Quantity` objects; new classes should follow the same approach.

---

## License

The core PDK files are provided under the **Commons Clause** condition atop the
Mozilla Public License 2.0.  See the license headers at the top of each Python
file for full details.

---

**Last Updated:** February 2026  
**Status:** Alpha / development


