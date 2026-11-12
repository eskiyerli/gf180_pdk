#
# Revolution EDA
#
# Copyright (c) 2026 Revolution Semiconductor
#
# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
##


import json
import os


class GF180_MCU_Tech():

    def __init__(self):
        techFilePath = os.path.join(os.path.dirname(__file__), "gf180_mcu_tech.json")

        with open(techFilePath, "r") as tech_file:
            jsData = json.load(tech_file)
            self._techParams = jsData["Parameters"]

            # Dictionary comprehension with tuple unpacking
            self._layers = {
                key: tuple(int(x.strip()) for x in value.split(','))
                for key, value in jsData["Layers"].items()
            }

    def name(self):
        return "gf180_mcu"

    @property
    def techParams(self):
        return self._techParams

    @property
    def layers(self):
        return self._layers
