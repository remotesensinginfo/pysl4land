#!/usr/bin/env python
"""
pySL4Land - Command line tool to process GEDI data.
"""
# This file is part of 'pySL4Land'
# A set of tools to process spaceborne lidar (GEDI and ICESAT2) for land (pySL4Land) applications
#
# Copyright 2020 Pete Bunting
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Purpose: Command line utility for processing GEDI data.
#
# Author: Pete Bunting
# Email: pfb@aber.ac.uk
# Date: 25/06/2020
# Version: 1.0
#
# History:
# Version 1.0 - Created.


import argparse
import logging

import pysl4land.pysl4land_gedi

logger = logging.getLogger("pysl4landgeditools.py")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input", type=str, required=True, help="Specify an input HDF5 file."
    )
    parser.add_argument(
        "-o", "--output", type=str, required=True, help="Specify an output GPKG file."
    )
    parser.add_argument(
        "-e",
        "--epsg",
        type=int,
        default=4326,
        help="Optionally provide an EPSG code for " "the output vector.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Specify that all points should be " "outputted and no filtering applied.",
    )

    args = parser.parse_args()

    valid_only = not args.all
    pysl4land.pysl4land_gedi.gedi02_b_beams_gpkg(
        args.input, args.output, valid_only, args.epsg
    )
