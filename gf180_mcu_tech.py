########################################################################
#
# Copyright 2023 IHP PDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
########################################################################


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
            print(self._layers)

    def name(self):
        return "gf180_mcu"

    @property
    def techParams(self):
        return self._techParams

    @property
    def layers(self):
        return self._layers
