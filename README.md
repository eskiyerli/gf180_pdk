# GF180 MCU Process Design Kit (PDK) for Revolution EDA

An early‑stage Python‑based PDK targeting the **GlobalFoundries 180‑nm MCU process** integrated
with the **Revolution EDA** schematic‑to‑GDS IC design environment.

> ⚠️ This PDK is currently **in development**. A 22‑device schematic symbol library imported from
> an Xschem source, matching instance callbacks, and a full layout layer map are available and
> have seen limited testing. Parametric cells, via definitions, and DRC decks are still works in
> progress. Developers and contributors are welcome to help fill out the missing pieces.

## Overview

The goal of `gf180_pdk` is to provide a fully functional design kit for the GF180 MCU
technology, including:

- Symbol library for schematic capture (22 devices already imported)
- Instance callback classes for automatic electrical parameter computation
- Schematic and symbol layer definitions for front‑end drawing
- Layout layer definitions with GDS layer/datatype mappings (auto‑generated from a KLayout LYP file)
- Process technology parameters (grid, units, layer and device constants)
- Xyce model‑library settings for simulation
- Placeholder packages for pcells and DRC decks

**Technology Details:**
- **Process Node:** GF 180‑nm MCU
- **PDK Status:** Alpha / development
- **License:** Commons Clause / MPL‑2.0 (see headers in source files)

---

## What's Implemented

### 1. Symbol Library & Callbacks

A set of 22 device symbols has been imported from Xschem into the `gf180_mcu` library; each
symbol is accompanied by a callback class in `callbacks.py` that reads label values and
calculates parameters used for netlisting and annotation.

**Supported Device Families:**
- **MOSFETs:** nmos_3p3, nmos_3p3_sab, nmos_6p0, nmos_6p0_nat, pmos_3p3, pmos_3p3_sab, pmos_6p0
- **MOS capacitors:** nmoscap_3p3, nmoscap_6p0, pmoscap_3p3, pmoscap_6p0
- **Resistors:** dnwpw (diff‑nwell poly resistor) with area/perimeter parameters, rm1 (metal
  resistor), nplus_u, pplus_u, npolyf_u, ppolyf_u, nwell
- **Capacitors:** mim_2p0fF
- **Diodes:** np_3p3
- **Bipolar transistors:** vnpn_10x10, vpnp_10x10

Callbacks automatically compute device dimensions, area, perimeter, and source/drain
resistance using `quantiphy.Quantity` objects. See `callbacks.py` for the full list of
classes and formulae.

### 2. Layer Definitions

#### Schematic & Symbol Layers (`schLayers.py` / `symLayers.py`)

Drawing layers for wires, pins, annotations and device outlines. These modules
follow the Revolution EDA dataclass conventions, defining colours, line styles and
z‑order for schematic rendering.

#### Layout Layers (`layoutLayers.py`)

A full set of 119 layout layers auto‑generated from a KLayout `.lyp` layer‑properties
file. Each `layLayer` carries colour, fill stipple, z‑order, visibility, and the GDS
layer/datatype pair, so the layout editor can draw on GF180 layers and read/write GDS
with the correct mapping. Complementary data lives in `gf180_mcu_tech.json` (174 named
layer entries plus 32 technology parameters such as resistor and metal dimensions).

### 3. Process Parameters (`process.py` & `gf180_mcu_tech.py`)

Defines grid settings and GDS units used by the layout editor:

- **DBU:** 1000 (1 µm = 1000 DBU)
- **Snap grid:** 50 nm
- **Major grid:** 100 nm
- **GDS unit:** 1 µm with 1 nm precision

This information is queried by Revolution EDA at runtime to maintain consistent
geometry and snapping. Via and path definitions (`processVias` / `processPaths`) are
not yet defined for this process.

### 4. Project Skeleton

Several packages are present but not yet populated:

- `pcells/` – contains only the `baseCell` foundation class; no parametric cells are
  registered yet
- `models/` – Xyce model files (`sm141064.xyce`, `smbb000149.xyce`, `design.xyce`)
- `stipples/` – fill patterns used by layout rendering

---

## How to Use with Revolution EDA

### Installation

1. **Clone or copy** the `gf180_pdk` folder into your Revolution EDA workspace:
   ```bash
   cd /path/to/revolution-eda
   git clone <gf180_pdk_repo> gf180_pdk
   ```
2. **Configure the PDK path** either by setting the `REVEDA_PDK_PATH` environment
   variable or by adding it to the `.env` file in the root of Revolution EDA
   (relative or absolute path).
3. **Restart Revolution EDA** to load the new PDK.
4. **Add the library directory** (`gf180_mcu`) in the *Library Browser* via the
   *Options* dialog or menu, so that schematic symbols appear in the component list.

### Creating Schematics

1. Launch the Revolution EDA schematic editor.
2. Select **GF180 MCU** from the PDK selector (if applicable).
3. Add instances via **Right‑click → Add Instance** and choose from the `gf180_mcu`
   library.
4. Double‑click an instance to edit parameters; values should use Quantiphy units
   (e.g. `10u`, `180n`, `4e-3`).
5. Connect pins and build your circuit as usual.

### Creating Layouts

The layout editor loads the full GF180 layer map, so you can draw shapes on the
correct GDS layers and import/export GDS. Parametric cells are not yet available —
layout is manual, and there are no via definitions yet, so interconnect must be drawn
with explicit shapes.

### Running Simulations

`modelLibSettings.json` already wires the `models/` Xyce files into the RevedaSim
simulation configuration (Ngspice and VACASK sections are present but empty). When you
export a netlist, callbacks generate the parameter values; verify the generated model
includes against the Xyce decks in `models/` before trusting simulation results.

---

## Project Structure

```
gf180_pdk/
├── README.md                   # This file
├── __init__.py                 # Package initialization
├── config.json                 # PDK metadata used by menu system
├── callbacks.py                # Instance parameter callbacks
├── process.py                  # Grid and GDS unit definitions
├── gf180_mcu_tech.py           # Technology class exposing techParams
├── gf180_mcu_tech.json         # Node definition JSON (params + layer map)
├── modelLibSettings.json       # Preconfigured Xyce model libraries
├── schLayers.py                # Schematic layer definitions
├── symLayers.py                # Symbol layer definitions
├── layoutLayers.py             # Layout layer/GDS mappings (auto-generated)
├── gf180_mcu/                  # Device symbol library (22 cells + reveda.lib)
├── pcells/                     # Parametric cells (base.py only)
│   └── base.py                 # Base cell classes / helpers
├── models/                     # Xyce model files
└── stipples/                   # Fill pattern files used by layout
```

---

## Development & Contribution

Contributors are encouraged to expand the PDK by implementing the missing pieces:

- **Add parametric cells** in `pcells/` following the patterns in the IHP PDK.
- **Define via and path defaults** in `process.py` for the GF180 stack.
- **Create callback classes** for new devices as symbols are added.
- **Populate `models/`** with additional SPICE/Xyce libraries and extend
  `modelLibSettings.json` to Ngspice and VACASK.
- **Develop DRC rule decks** for GF180 and integrate them with `klayoutDRC`-style
  menu actions.

The existing `callbacks.py` file already demonstrates how to compute geometry-related
parameters using `Quantity` objects; new classes should follow the same approach.

---

## License

The core PDK files are provided under the **Commons Clause** condition atop the
Mozilla Public License 2.0. See the license headers at the top of each Python
file for full details.

---

**Last Updated:** October 2026  
**Status:** Alpha / development
