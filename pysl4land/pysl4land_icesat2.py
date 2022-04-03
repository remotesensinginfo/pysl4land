#!/usr/bin/env python
"""
pySL4Land - this file provides a class to process ICESAT2 data.

See other source files for details
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
# Purpose: class to process ICESAT2 data.
#
# Author: Pete Bunting
# Email: pfb@aber.ac.uk
# Date: 25/06/2020
# Version: 1.0
#
# History:
# Version 1.0 - Created.

import h5py
import numpy
import pandas
import geopandas
import math
from shapely.geometry import Polygon
import logging
from datetime import datetime, timedelta

import pysl4land.pysl4land_utils

logger = logging.getLogger(__name__)


def get_beam_lst(input_file, strong_only, weak_only):
    """
    A function which returns a list of beam names.

    :param input_file: input file path.
    :return: list of strings

    """
    icesat2_h5_file = h5py.File(input_file, 'r')
    
    orientation = icesat2_h5_file['/orbit_info/sc_orient'][0]
    
    if strong_only == True:
        icesat2_keys = list(icesat2_h5_file.keys())
        strongOrientDict = {0:'l', 1:'r', 21:'error'}
        icesat2_beams = ['gt1' + strongOrientDict[orientation], 'gt2' + strongOrientDict[orientation], 'gt3' + strongOrientDict[orientation]]
        icesat2_beams_lst = []
        for icesat2_beam_name in icesat2_keys:
            if icesat2_beam_name in icesat2_beams:
                icesat2_beams_lst.append(icesat2_beam_name)
        icesat2_h5_file.close()
        
    elif weak_only == True:
        icesat2_keys = list(icesat2_h5_file.keys())
        weakOrientDict = {0:'r', 1:'l', 21:'error'}
        icesat2_beams = ['gt1' + weakOrientDict[orientation], 'gt2' + weakOrientDict[orientation], 'gt3' + weakOrientDict[orientation]]
        icesat2_beams_lst = []
        for icesat2_beam_name in icesat2_keys:
            if icesat2_beam_name in icesat2_beams:
                icesat2_beams_lst.append(icesat2_beam_name)
        icesat2_h5_file.close()
        
    else:
        icesat2_keys = list(icesat2_h5_file.keys())
        icesat2_beams = ['gt1l', 'gt1r', 'gt2l', 'gt2r', 'gt3l', 'gt3r']
        icesat2_beams_lst = []
        for icesat2_beam_name in icesat2_keys:
            if icesat2_beam_name in icesat2_beams:
                icesat2_beams_lst.append(icesat2_beam_name)
        icesat2_h5_file.close()
    
    return icesat2_beams_lst


def get_segment_polygons(latitude, longitude, along_size=100.0, across_size=13.0):
    """
    Get polygon segments.

    """
    n_rows = latitude.shape[0]

    utm_zone = pysl4land.pysl4land_utils.latlon_to_mode_utm_zone_number(latitude, longitude)
    logger.debug("UTM Zone: {}".format(utm_zone))

    epsg_code = 32600 + utm_zone
    logger.debug("UTM Zone EPSG: {}".format(epsg_code))

    logger.debug("Creating pandas dataframe")
    icesat2_pts_df = pandas.DataFrame({'latitude': latitude, 'longitude': longitude})
    logger.debug("Creating geopandas dataframe")
    icesat2_pts_wgs84_gdf = geopandas.GeoDataFrame(icesat2_pts_df, crs='EPSG:4326',
                                                   geometry=geopandas.points_from_xy(icesat2_pts_df.longitude,
                                                                                     icesat2_pts_df.latitude))
    logger.debug("Reprojecting geopandas dataframe to UTM")
    icesat2_pts_utm_gdf = icesat2_pts_wgs84_gdf.to_crs("EPSG:{}".format(epsg_code))

    x = numpy.array(icesat2_pts_utm_gdf.geometry.x)
    y = numpy.array(icesat2_pts_utm_gdf.geometry.y)

    # Step Forward
    x_fwd = numpy.zeros_like(x)
    x_fwd[1:] = x[0:n_rows - 1]
    x_fwd[0] = x[0]

    y_fwd = numpy.zeros_like(y)
    y_fwd[1:] = y[0:n_rows - 1]
    y_fwd[0] = y[0]

    # Step Backwards
    x_bck = numpy.zeros_like(x)
    x_bck[0:n_rows - 1] = x[1:n_rows]
    x_bck[-1] = x[-1]

    y_bck = numpy.zeros_like(y)
    y_bck[0:n_rows - 1] = y[1:n_rows]
    y_bck[-1] = y[-1]

    logger.debug("Calculate the angles.")
    sgl_flight_angle = math.atan((x[-1] - x[0]) / (y[-1] - y[0]))
    flight_angle = numpy.arctan((x_fwd - x_bck) / (y_fwd - y_bck))

    flight_angle_dif = numpy.absolute(flight_angle - sgl_flight_angle)
    flight_angle[flight_angle_dif > 0.1] = sgl_flight_angle

    theta_cos = numpy.cos(flight_angle)
    theta_sin = numpy.sin(flight_angle)

    logger.debug("Calculated the angles.")

    along_size_h = along_size / 2.0
    across_size_h = across_size / 2.0
    logger.debug("along_size_h: {} \t\t across_size_h: {}".format(along_size_h, across_size_h))

    icesat2_pts_utm_gdf['ul_x'] = icesat2_pts_utm_gdf.geometry.x - across_size_h
    icesat2_pts_utm_gdf['ul_y'] = icesat2_pts_utm_gdf.geometry.y + along_size_h
    icesat2_pts_utm_gdf['ul_x_rot'] = icesat2_pts_utm_gdf.geometry.x + theta_cos * (
                icesat2_pts_utm_gdf['ul_x'] - icesat2_pts_utm_gdf.geometry.x) + theta_sin * (
                                                  icesat2_pts_utm_gdf['ul_y'] - icesat2_pts_utm_gdf.geometry.y)
    icesat2_pts_utm_gdf['ul_y_rot'] = icesat2_pts_utm_gdf.geometry.y + -theta_sin * (
                icesat2_pts_utm_gdf['ul_x'] - icesat2_pts_utm_gdf.geometry.x) + theta_cos * (
                                                  icesat2_pts_utm_gdf['ul_y'] - icesat2_pts_utm_gdf.geometry.y)

    icesat2_pts_utm_gdf['ur_x'] = icesat2_pts_utm_gdf.geometry.x + across_size_h
    icesat2_pts_utm_gdf['ur_y'] = icesat2_pts_utm_gdf.geometry.y + along_size_h
    icesat2_pts_utm_gdf['ur_x_rot'] = icesat2_pts_utm_gdf.geometry.x + theta_cos * (
                icesat2_pts_utm_gdf['ur_x'] - icesat2_pts_utm_gdf.geometry.x) + theta_sin * (
                                                  icesat2_pts_utm_gdf['ur_y'] - icesat2_pts_utm_gdf.geometry.y)
    icesat2_pts_utm_gdf['ur_y_rot'] = icesat2_pts_utm_gdf.geometry.y + -theta_sin * (
                icesat2_pts_utm_gdf['ur_x'] - icesat2_pts_utm_gdf.geometry.x) + theta_cos * (
                                                  icesat2_pts_utm_gdf['ur_y'] - icesat2_pts_utm_gdf.geometry.y)

    icesat2_pts_utm_gdf['lr_x'] = icesat2_pts_utm_gdf.geometry.x + across_size_h
    icesat2_pts_utm_gdf['lr_y'] = icesat2_pts_utm_gdf.geometry.y - along_size_h
    icesat2_pts_utm_gdf['lr_x_rot'] = icesat2_pts_utm_gdf.geometry.x + theta_cos * (
                icesat2_pts_utm_gdf['lr_x'] - icesat2_pts_utm_gdf.geometry.x) + theta_sin * (
                                                  icesat2_pts_utm_gdf['lr_y'] - icesat2_pts_utm_gdf.geometry.y)
    icesat2_pts_utm_gdf['lr_y_rot'] = icesat2_pts_utm_gdf.geometry.y + -theta_sin * (
                icesat2_pts_utm_gdf['lr_x'] - icesat2_pts_utm_gdf.geometry.x) + theta_cos * (
                                                  icesat2_pts_utm_gdf['lr_y'] - icesat2_pts_utm_gdf.geometry.y)

    icesat2_pts_utm_gdf['ll_x'] = icesat2_pts_utm_gdf.geometry.x - across_size_h
    icesat2_pts_utm_gdf['ll_y'] = icesat2_pts_utm_gdf.geometry.y - along_size_h
    icesat2_pts_utm_gdf['ll_x_rot'] = icesat2_pts_utm_gdf.geometry.x + theta_cos * (
                icesat2_pts_utm_gdf['ll_x'] - icesat2_pts_utm_gdf.geometry.x) + theta_sin * (
                                                  icesat2_pts_utm_gdf['ll_y'] - icesat2_pts_utm_gdf.geometry.y)
    icesat2_pts_utm_gdf['ll_y_rot'] = icesat2_pts_utm_gdf.geometry.y + -theta_sin * (
                icesat2_pts_utm_gdf['ll_x'] - icesat2_pts_utm_gdf.geometry.x) + theta_cos * (
                                                  icesat2_pts_utm_gdf['ll_y'] - icesat2_pts_utm_gdf.geometry.y)

    def _polygonise_2Dcells(df_row):
        return Polygon([(df_row.ul_x_rot, df_row.ul_y_rot), (df_row.ur_x_rot, df_row.ur_y_rot),
                        (df_row.lr_x_rot, df_row.lr_y_rot), (df_row.ll_x_rot, df_row.ll_y_rot)])

    polys = icesat2_pts_utm_gdf.apply(_polygonise_2Dcells, axis=1)

    logger.debug("Creating geopandas polygons UTM dataframe")
    icesat2_polys_utm_gdf = geopandas.GeoDataFrame(icesat2_pts_df, crs="EPSG:{}".format(epsg_code), geometry=polys)
    logger.debug("Creating geopandas polygons WGS84 dataframe")
    icesat2_polys_wgs84_gdf = icesat2_polys_utm_gdf.to_crs("EPSG:4326".format(epsg_code))

    return numpy.asarray(icesat2_polys_wgs84_gdf.geometry.values)


def get_icesat2_alt08_beam_as_gdf(input_file, icesat2_beam_name, use_seg_polys=False, out_epsg_code=4326, strong_only=False, weak_only=False):
    """

    :param input_file:
    :param icesat2_beam_name:
    :param use_seg_polys:
    :param out_epsg_code:
    :return:
    """
    icesat2_beams = get_beam_lst(input_file, strong_only, weak_only)
    if icesat2_beam_name not in icesat2_beams:
        raise Exception("Beam '{}' is not available within the file: {}".format(icesat2_beam_name, input_file))

    icesat2_h5_file = h5py.File(input_file, 'r')
    if icesat2_h5_file is None:
        raise Exception("Could not open the input ICESAT2 file.")
    
    
    icesat2_beam = icesat2_h5_file[icesat2_beam_name]
    icesat2_beam_keys = list(icesat2_beam.keys())
    if 'land_segments' not in icesat2_beam_keys:
        raise Exception("Could not find land segments information.")

    icesat2_land_beam = icesat2_beam['land_segments']
    icesat2_land_beam_keys = list(icesat2_land_beam.keys())

    # Get canopy data.
    if 'canopy' not in icesat2_land_beam_keys:
        raise Exception("Could not find canopy information.")
    icesat2_beam_canopy = icesat2_land_beam['canopy']

    # Get terrain data.
    if 'terrain' not in icesat2_land_beam_keys:
        raise Exception("Could not find terrain information.")
    icesat2_beam_terrain = icesat2_land_beam['terrain']
    
    icesat2_atlas_sdp_gps_epoch = icesat2_h5_file['ancillary_data']['atlas_sdp_gps_epoch'][0]
    
    gps_epoch_delta_time = icesat2_land_beam['delta_time'] + icesat2_atlas_sdp_gps_epoch
    utc_delta_time = [datetime(1980, 1, 6) + timedelta(seconds=x - (37 - 19)) for x in gps_epoch_delta_time]
    utc_time = [x.strftime("%Y.%m.%d_%H.%M.%S") for x in utc_delta_time]
    
    
    icesat2_beam_df = pandas.DataFrame({
        'asr'                      : icesat2_land_beam['asr'],
        'atlas_pa'                 : icesat2_land_beam['atlas_pa'],
        'beam_azimuth'             : icesat2_land_beam['beam_azimuth'],
        'beam_coelev'              : icesat2_land_beam['beam_coelev'],
        'brightness_flag'          : icesat2_land_beam['brightness_flag'],
        'delta_time'               : icesat2_land_beam['delta_time'],
        'segment_time_utc_ymd_hms' : utc_time,
        'delta_time_beg'           : icesat2_land_beam['delta_time_beg'],
        'delta_time_end'           : icesat2_land_beam['delta_time_end'],
        'dem_flag'                 : icesat2_land_beam['dem_flag'],
        'dem_h'                    : icesat2_land_beam['dem_h'],
        'dem_removal_flag'         : icesat2_land_beam['dem_removal_flag'],
        'h_dif_ref'                : icesat2_land_beam['h_dif_ref'],
        'last_seg_extend'          : icesat2_land_beam['last_seg_extend'],
        'latitude'                 : icesat2_land_beam['latitude'],
        'longitude'                : icesat2_land_beam['longitude'],
        'layer_flag'               : icesat2_land_beam['layer_flag'],
        'msw_flag'                 : icesat2_land_beam['msw_flag'],
        'night_flag'               : icesat2_land_beam['night_flag'],
        'n_seg_ph'                 : icesat2_land_beam['n_seg_ph'],
        'ph_ndx_beg'               : icesat2_land_beam['ph_ndx_beg'],
        'ph_removal_flag'          : icesat2_land_beam['ph_removal_flag'],
        'psf_flag'                 : icesat2_land_beam['psf_flag'],
        'rgt'                      : icesat2_land_beam['rgt'],
        'segment_id_beg'           : icesat2_land_beam['segment_id_beg'],
        'segment_id_end'           : icesat2_land_beam['segment_id_end'],
        'segment_landcover'        : icesat2_land_beam['segment_landcover'],
        'segment_snowcover'        : icesat2_land_beam['segment_snowcover'],
        'segment_watermask'        : icesat2_land_beam['segment_watermask'],
        'sigma_across'             : icesat2_land_beam['sigma_across'],
        'sigma_along'              : icesat2_land_beam['sigma_along'],
        'sigma_atlas_land'         : icesat2_land_beam['sigma_atlas_land'],
        'sigma_h'                  : icesat2_land_beam['sigma_h'],
        'sigma_topo'               : icesat2_land_beam['sigma_topo'],
        'snr'                      : icesat2_land_beam['snr'],
        'solar_azimuth'            : icesat2_land_beam['solar_azimuth'],
        'solar_elevation'          : icesat2_land_beam['solar_elevation'],
        'terrain_flg'              : icesat2_land_beam['terrain_flg'],
        'urban_flag'               : icesat2_land_beam['urban_flag'],
        'segment_cover'              : icesat2_beam_canopy['segment_cover'],
        'canopy_openness'          : icesat2_beam_canopy['canopy_openness'],
        'canopy_rh_conf'           : icesat2_beam_canopy['canopy_rh_conf'],
        'centroid_height'          : icesat2_beam_canopy['centroid_height'],
        'h_canopy'                 : icesat2_beam_canopy['h_canopy'],
        'h_canopy_abs'             : icesat2_beam_canopy['h_canopy_abs'],
        'h_canopy_quad'            : icesat2_beam_canopy['h_canopy_quad'],
        'h_canopy_uncertainty'     : icesat2_beam_canopy['h_canopy_uncertainty'],
        'h_dif_canopy'             : icesat2_beam_canopy['h_dif_canopy'],
        'h_max_canopy'             : icesat2_beam_canopy['h_max_canopy'],
        'h_max_canopy_abs'         : icesat2_beam_canopy['h_max_canopy_abs'],
        'h_mean_canopy'            : icesat2_beam_canopy['h_mean_canopy'],
        'h_mean_canopy_abs'        : icesat2_beam_canopy['h_mean_canopy_abs'],
        'h_median_canopy'          : icesat2_beam_canopy['h_median_canopy'],
        'h_median_canopy_abs'      : icesat2_beam_canopy['h_median_canopy_abs'],
        'h_min_canopy'             : icesat2_beam_canopy['h_min_canopy'],
        'h_min_canopy_abs'         : icesat2_beam_canopy['h_min_canopy_abs'],
        #'landsat_flag'             : icesat2_beam_canopy['landsat_flag'],
        #'landsat_perc'             : icesat2_beam_canopy['landsat_perc'],
        'n_ca_photons'             : icesat2_beam_canopy['n_ca_photons'],
        'n_toc_photons'            : icesat2_beam_canopy['n_toc_photons'],
        'toc_roughness'            : icesat2_beam_canopy['toc_roughness'],
        'canopy_h_metrics_rh25'    : icesat2_beam_canopy['canopy_h_metrics'][:, 0],
        'canopy_h_metrics_rh50'    : icesat2_beam_canopy['canopy_h_metrics'][:, 1],
        'canopy_h_metrics_rh60'    : icesat2_beam_canopy['canopy_h_metrics'][:, 2],
        'canopy_h_metrics_rh70'    : icesat2_beam_canopy['canopy_h_metrics'][:, 3],
        'canopy_h_metrics_rh75'    : icesat2_beam_canopy['canopy_h_metrics'][:, 4],
        'canopy_h_metrics_rh80'    : icesat2_beam_canopy['canopy_h_metrics'][:, 5],
        'canopy_h_metrics_rh85'    : icesat2_beam_canopy['canopy_h_metrics'][:, 6],
        'canopy_h_metrics_rh90'    : icesat2_beam_canopy['canopy_h_metrics'][:, 7],
        'canopy_h_metrics_rh95'    : icesat2_beam_canopy['canopy_h_metrics'][:, 8],
        'canopy_h_metrics_abs_rh25': icesat2_beam_canopy['canopy_h_metrics_abs'][:, 0],
        'canopy_h_metrics_abs_rh50': icesat2_beam_canopy['canopy_h_metrics_abs'][:, 1],
        'canopy_h_metrics_abs_rh60': icesat2_beam_canopy['canopy_h_metrics_abs'][:, 2],
        'canopy_h_metrics_abs_rh70': icesat2_beam_canopy['canopy_h_metrics_abs'][:, 3],
        'canopy_h_metrics_abs_rh75': icesat2_beam_canopy['canopy_h_metrics_abs'][:, 4],
        'canopy_h_metrics_abs_rh80': icesat2_beam_canopy['canopy_h_metrics_abs'][:, 5],
        'canopy_h_metrics_abs_rh85': icesat2_beam_canopy['canopy_h_metrics_abs'][:, 6],
        'canopy_h_metrics_abs_rh90': icesat2_beam_canopy['canopy_h_metrics_abs'][:, 7],
        'canopy_h_metrics_abs_rh95': icesat2_beam_canopy['canopy_h_metrics_abs'][:, 8],
        'h_te_best_fit'            : icesat2_beam_terrain['h_te_best_fit'],
        'h_te_interp'              : icesat2_beam_terrain['h_te_interp'],
        'h_te_max'                 : icesat2_beam_terrain['h_te_max'],
        'h_te_mean'                : icesat2_beam_terrain['h_te_mean'],
        'h_te_median'              : icesat2_beam_terrain['h_te_median'],
        'h_te_min'                 : icesat2_beam_terrain['h_te_min'],
        'h_te_mode'                : icesat2_beam_terrain['h_te_mode'],
        'h_te_skew'                : icesat2_beam_terrain['h_te_skew'],
        'h_te_std'                 : icesat2_beam_terrain['h_te_std'],
        'h_te_uncertainty'         : icesat2_beam_terrain['h_te_uncertainty'],
        'n_te_photons'             : icesat2_beam_terrain['n_te_photons'],
        'terrain_slope'            : icesat2_beam_terrain['terrain_slope']
    })
    
    
    
    if use_seg_polys:
        latitude_arr = numpy.array(icesat2_land_beam['latitude'])
        longitude_arr = numpy.array(icesat2_land_beam['longitude'])
        polys = get_segment_polygons(latitude_arr, longitude_arr, along_size=100.0, across_size=13.0)
        icesat2_beam_gdf = geopandas.GeoDataFrame(icesat2_beam_df, crs='EPSG:4326', geometry=polys)
    else:
        icesat2_beam_gdf = geopandas.GeoDataFrame(icesat2_beam_df, crs='EPSG:4326',
                                                  geometry=geopandas.points_from_xy(icesat2_beam_df.longitude,
                                                                                    icesat2_beam_df.latitude))

    if out_epsg_code != 4326:
        icesat2_beam_gdf = icesat2_beam_gdf.to_crs("EPSG:{}".format(out_epsg_code))
    icesat2_h5_file.close()

    return icesat2_beam_gdf


def icesat2_alt08_beams_gpkg(input_file, out_vec_file, use_seg_polys=False, out_epsg_code=4326, strong_only=False, weak_only=False):
    """
    A function which converts all the beams to a GPKG vector file with each beam as a different
    layer within the vector file.

    :param input_file: input file path.
    :param out_vec_file: output file path
    :param gedi_beam_name: the name of the beam to be processed.
    :param valid_only: If True (default) then returns which are labelled as invalid are removed from the
                       dataframe.
    :param out_epsg_code: If provided the returns will be reprojected to the EPSG code provided.
                          default is EPSG:4326

    """
    icesat2_beams = get_beam_lst(input_file, strong_only, weak_only)
    print(icesat2_beams)
    for icesat2_beam_name in icesat2_beams:
        logger.info("Processing beam '{}'".format(icesat2_beam_name))
        icesat2_beam_gdf = get_icesat2_alt08_beam_as_gdf(input_file, icesat2_beam_name, use_seg_polys, out_epsg_code)
        icesat2_beam_gdf.to_file(out_vec_file, layer=icesat2_beam_name, driver="GPKG")
        logger.info("Finished processing beam '{}'".format(icesat2_beam_name))

