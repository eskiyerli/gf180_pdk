# GF180 PDK Development for Revolution EDA
This repository aims to create a working setup for GF 180 process in Revolution EDA. Revolution EDA is an schematic-to-GDS custom  circuit design platform for professional engineers.
At the moment, there is only front-end (schematic symbols) imported from Xschem format. There has been minimal testing so far and the symbol is not yet complete. 
In due course, parametric layout cells will also be created. Anybody interested in creating them is always welcome.

To use this PDK with Revolution EDA, please set `REVEDA_PDK_PATH` to its file system location. For example:
if you cloned the repo to "/home/someUser/gf180_pdk', you should set `REVEDA_PDK_PATH=/home/someUser/gf180_pdk' in your `.env` file underneath the main **Revolution EDA** 
installation.

Alternatively, you could use *Revolution EDA Options* dialog by choosing *Options* menu
from *Revolution EDA* main window:

<img width="871" height="665" alt="revedaOptionsDialogue" src="https://github.com/user-attachments/assets/2fa757a0-5a82-420b-910b-6222715425a4" />

You  might need to restart the Revolution EDA if the PDK is changed to propagate the paths throughout the software.

You would also need to add *g180_mcu* directory in *Library Browser*:

<img width="816" height="723" alt="libraryPathSelection" src="https://github.com/user-attachments/assets/f5d0d6f4-bda4-41ba-86d4-09871c02774b" />

<img width="701" height="501" alt="gf180Library" src="https://github.com/user-attachments/assets/5057e9d8-ec72-482e-85af-ad4ad25e5c57" />

You could now use the available symbols in creating schematics.

Note that **Revolution EDA** PDKs should always following files under the PDK installation directory:
1. `__init__.py`: PDK is a module that is loaded by **Revolution EDA**
2. `callbacks.py`: Any instance callbacks to determine the results of *PyLabel*s on the symbols are handled in this module.
3. `schLayers.py`: Specifics of base definitions for schematics drawings such as net widths, colours, pin colours, etc are described in this module.
4. `symLayers.py`: Like `schLayers.py` module, this module define symbol drawing related properties.
5. `layoutLayers.py`: This module is used to define layout layer definitions and is critical. At the moment, it is empty.
6. `pcells.py`: This module would include all Python classes related to layout parametric cells. It also momentarily empty.


