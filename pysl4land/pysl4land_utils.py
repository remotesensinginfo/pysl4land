#!/usr/bin/env python
"""
pySL4Land - this file provides a utility classes

See other source files for details
"""
# This file is part of 'pySL4Land'
# A set of tools to process spaceborne lidar (GEDI and ICESAT2) for land (
# pySL4Land) applications
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
# Purpose: utility classes
#
# Author: Pete Bunting
# Email: pfb@aber.ac.uk
# Date: 25/06/2020
# Version: 1.0
#
# History:
# Version 1.0 - Created.

import logging

logger = logging.getLogger(__name__)


def latlon_to_utm_zone_number(latitude, longitude):
    """
    Find the UTM zone number for a give latitude and longitude. UTM zone will be
    returned for all the lat/longs within the input arrays, which must be of the
    same length. Function will also work with a single value, at which point a
    single int will be returned.

    :param latitude: numpy array of floats
    :param longitude: numpy array of floats

    :return: int or array of ints.

    """
    import numpy

    utm_zones = ((longitude + 180) / 6) + 1
    utm_zones = numpy.rint(utm_zones).astype(int)

    utm_zones[
        (56 <= latitude) & (latitude < 64) & (3 <= longitude) & (longitude < 12)
    ] = 32
    utm_zones[
        (72 <= latitude) & (latitude <= 84) & (longitude >= 0) & (longitude < 9)
    ] = 31
    utm_zones[
        (72 <= latitude) & (latitude <= 84) & (longitude >= 0) & (longitude < 21)
    ] = 33
    utm_zones[
        (72 <= latitude) & (latitude <= 84) & (longitude >= 0) & (longitude < 33)
    ] = 35
    utm_zones[
        (72 <= latitude) & (latitude <= 84) & (longitude >= 0) & (longitude < 42)
    ] = 37

    return utm_zones


def latlon_to_mode_utm_zone_number(latitude, longitude):
    """
    Find the mode UTM zone for a list of lat/lon values.

    :param latitude: numpy array of floats
    :param longitude: numpy array of floats
    :return: int (mode UTM zone)

    """
    import scipy.stats

    utm_zones = latlon_to_utm_zone_number(latitude, longitude)
    mode, count = scipy.stats.mode(utm_zones)
    return mode[0]
