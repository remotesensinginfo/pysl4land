#!/usr/bin/env python
"""
Setup script for pySL4Land. Use like this for Unix:

$ python setup.py install

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
# Purpose:  install software.
#
# Author: Pete Bunting
# Email: pfb@aber.ac.uk
# Date: 25/06/2020
# Version: 1.0
#
# History:
# Version 1.0 - Created.

from setuptools import setup
import glob
import pysl4land

setup(name='pysl4land',
    version=pysl4land.PYSL4LAND_VERSION,
    description='Python tools to process spaceborne lidar (GEDI and ICESAT2) for land (pySL4Land) applications.',
    author='Pete Bunting',
    author_email='petebunting@mac.com',
    scripts=glob.glob("bin/*.py"),
    include_package_data=True,
    packages=['pysl4land'],
    license='LICENSE.txt',
    install_requires=['h5py', 'numpy', 'scipy', 'geopandas', 'shapely'],
    url='https://github.com/remotesensinginfo/pysl4land',
    classifiers=['Intended Audience :: Developers',
                 'Operating System :: OS Independent',
                 "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",])
