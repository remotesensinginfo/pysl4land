#!/usr/bin/env python
"""
pySL4Land - this file provides a class to process GEDI data.

See other source files for details
"""
# This file is part of 'pySL4Land'
# A set of tools to process spaceborne lidar (GEDI and ICESAT2) for land
# (pySL4Land) applications
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
# Purpose: class to process GEDI data.
#
# Author: Pete Bunting
# Email: pfb@aber.ac.uk
# Date: 25/06/2020
# Version: 1.0
#
# History:
# Version 1.0 - Created.

import datetime
import logging

import geopandas
import h5py
import pandas

logger = logging.getLogger(__name__)


def get_beam_lst(input_file):
    """
    A function which returns a list of beam names.

    :param input_file: input file path.
    :return: list of strings

    """
    gedi_h5_file = h5py.File(input_file, "r")
    gedi_keys = list(gedi_h5_file.keys())
    gedi_beams = [
        "BEAM0000",
        "BEAM0001",
        "BEAM0010",
        "BEAM0011",
        "BEAM0101",
        "BEAM0110",
        "BEAM1000",
        "BEAM1011",
    ]
    gedi_beams_lst = []
    for gedi_beam_name in gedi_keys:
        if gedi_beam_name in gedi_beams:
            gedi_beams_lst.append(gedi_beam_name)
    gedi_h5_file.close()
    return gedi_beams_lst


def get_metadata(input_file):
    """
    A function which returns a dict of the file metadata.

    :param input_file: input file path.
    :return: dict with the metadata.

    """
    gedi_h5_file = h5py.File(input_file, "r")

    file_att_keys = list(gedi_h5_file.attrs.keys())
    if "short_name" in file_att_keys:
        gedi_short_name = gedi_h5_file.attrs["short_name"]
    else:
        raise Exception("Could not find the GEDI file short name - valid file?")

    metadata_dict = dict()
    if gedi_short_name == "GEDI_L2B":
        gedi_keys = list(gedi_h5_file.keys())

        if "METADATA" in gedi_keys:
            gedi_metadata_keys = list(gedi_h5_file["METADATA"])
            if "DatasetIdentification" in gedi_metadata_keys:
                metadata_dict["version_id"] = gedi_h5_file["METADATA"][
                    "DatasetIdentification"
                ].attrs["VersionID"]
                metadata_dict["pge_version"] = gedi_h5_file["METADATA"][
                    "DatasetIdentification"
                ].attrs["PGEVersion"]
                creation_date_str = gedi_h5_file["METADATA"][
                    "DatasetIdentification"
                ].attrs["creationDate"]
                metadata_dict["creation_date"] = datetime.datetime.strptime(
                    creation_date_str, "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                metadata_dict["file_uuid"] = gedi_h5_file["METADATA"][
                    "DatasetIdentification"
                ].attrs["uuid"]
            else:
                raise Exception(
                    "No metadata DatasetIdentification directory - is this file valid?"
                )
        else:
            raise Exception("No metadata directory - is this file valid?")
    else:
        raise Exception(
            "The input file must be a GEDI_L2B - not implemented for other products yet."
        )
    gedi_h5_file.close()
    return metadata_dict


def get_gedi02_b_beam_as_gdf(
    input_file, gedi_beam_name, valid_only=True, out_epsg_code=4326
):
    """
    A function which gets a geopandas dataframe for a beam. Note the parameters
    with multiple values in the z axis are not included in the dataframe.

    :param input_file: input file path.
    :param gedi_beam_name: the name of the beam to be processed.
    :param valid_only: If True (default) then returns which are labelled as invalid
                       are removed from the dataframe.
    :param out_epsg_code: If provided the returns will be reprojected to the EPSG
                          code provided. default is EPSG:4326

    """
    gedi_beams = get_beam_lst(input_file)
    if gedi_beam_name not in gedi_beams:
        raise Exception(
            "Bean '{}' is not available within the file: {}".format(
                gedi_beam_name, input_file
            )
        )

    gedi_h5_file = h5py.File(input_file, "r")

    file_att_keys = list(gedi_h5_file.attrs.keys())
    if "short_name" in file_att_keys:
        gedi_short_name = gedi_h5_file.attrs["short_name"]
    else:
        raise Exception("Could not find the GEDI file short name - valid file?")

    if gedi_short_name != "GEDI_L2B":
        raise Exception("The input file must be a GEDI_L2B.")

    logger.debug("Creating geopandas dataframe for beam: {}".format(gedi_beam_name))
    gedi_beam = gedi_h5_file[gedi_beam_name]
    gedi_beam_keys = list(gedi_beam.keys())

    # Get location info.
    gedi_beam_geoloc = gedi_beam["geolocation"]
    # Get land cover data.
    gedi_beam_landcover = gedi_beam["land_cover_data"]

    gedi_beam_df = pandas.DataFrame(
        {
            "elevation_bin0": gedi_beam_geoloc["elevation_bin0"],
            "elevation_lastbin": gedi_beam_geoloc["elevation_lastbin"],
            "height_bin0": gedi_beam_geoloc["height_bin0"],
            "height_lastbin": gedi_beam_geoloc["height_lastbin"],
            "shot_number": gedi_beam_geoloc["shot_number"],
            "solar_azimuth": gedi_beam_geoloc["solar_azimuth"],
            "solar_elevation": gedi_beam_geoloc["solar_elevation"],
            "latitude_bin0": gedi_beam_geoloc["latitude_bin0"],
            "latitude_lastbin": gedi_beam_geoloc["latitude_lastbin"],
            "longitude_bin0": gedi_beam_geoloc["longitude_bin0"],
            "longitude_lastbin": gedi_beam_geoloc["longitude_lastbin"],
            "degrade_flag": gedi_beam_geoloc["degrade_flag"],
            "digital_elevation_model": gedi_beam_geoloc["digital_elevation_model"],
            "landsat_treecover": gedi_beam_landcover["landsat_treecover"],
            "modis_nonvegetated": gedi_beam_landcover["modis_nonvegetated"],
            "modis_nonvegetated_sd": gedi_beam_landcover["modis_nonvegetated_sd"],
            "modis_treecover": gedi_beam_landcover["modis_treecover"],
            "modis_treecover_sd": gedi_beam_landcover["modis_treecover_sd"],
            "beam": gedi_beam["beam"],
            "cover": gedi_beam["cover"],
            "master_frac": gedi_beam["master_frac"],
            "master_int": gedi_beam["master_int"],
            "num_detectedmodes": gedi_beam["num_detectedmodes"],
            "omega": gedi_beam["omega"],
            "pai": gedi_beam["pai"],
            "pgap_theta": gedi_beam["pgap_theta"],
            "pgap_theta_error": gedi_beam["pgap_theta_error"],
            "rg": gedi_beam["rg"],
            "rh100": gedi_beam["rh100"],
            "rhog": gedi_beam["rhog"],
            "rhog_error": gedi_beam["rhog_error"],
            "rhov": gedi_beam["rhov"],
            "rhov_error": gedi_beam["rhov_error"],
            "rossg": gedi_beam["rossg"],
            "rv": gedi_beam["rv"],
            "sensitivity": gedi_beam["sensitivity"],
            "stale_return_flag": gedi_beam["stale_return_flag"],
            "surface_flag": gedi_beam["surface_flag"],
            "l2a_quality_flag": gedi_beam["l2a_quality_flag"],
            "l2b_quality_flag": gedi_beam["l2b_quality_flag"],
        }
    )

    gedi_beam_gdf = geopandas.GeoDataFrame(
        gedi_beam_df,
        crs="EPSG:4326",
        geometry=geopandas.points_from_xy(
            gedi_beam_df.longitude_lastbin, gedi_beam_df.latitude_lastbin
        ),
    )
    if valid_only:
        logger.debug(
            "Masking beam {} so only valid returns remain".format(gedi_beam_name)
        )
        gedi_beam_gdf = gedi_beam_gdf[
            (gedi_beam_gdf.l2a_quality_flag == 1)
            & (gedi_beam_gdf.l2b_quality_flag == 1)
        ]
    if out_epsg_code != 4326:
        logger.debug(
            "Reprojecting beam {} to EPSG:{}.".format(gedi_beam_name, out_epsg_code)
        )
        gedi_beam_gdf = gedi_beam_gdf.to_crs("EPSG:{}".format(out_epsg_code))
    gedi_h5_file.close()
    logger.debug(
        "Finished creating geopandas dataframe for beam: {}".format(gedi_beam_name)
    )
    return gedi_beam_gdf


def gedi02_b_beams_gpkg(input_file, out_vec_file, valid_only=True, out_epsg_code=4326):
    """
    A function which converts all the beams to a GPKG vector file with each beam
    as a different layer within the vector file.

    :param input_file: input file path.
    :param out_vec_file: output file path
    :param gedi_beam_name: the name of the beam to be processed.
    :param valid_only: If True (default) then returns which are labelled as invalid
                       are removed from the dataframe.
    :param out_epsg_code: If provided the returns will be reprojected to the
                          EPSG code provided. default is EPSG:4326

    """
    gedi_beams = get_beam_lst(input_file)
    for gedi_beam_name in gedi_beams:
        logger.info("Processing beam '{}'".format(gedi_beam_name))
        gedi_beam_gdf = get_gedi02_b_beam_as_gdf(
            input_file, gedi_beam_name, valid_only, out_epsg_code
        )
        gedi_beam_gdf.to_file(out_vec_file, layer=gedi_beam_name, driver="GPKG")
        logger.info("Finished processing beam '{}'".format(gedi_beam_name))
