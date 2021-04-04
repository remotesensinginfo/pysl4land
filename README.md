# pysl4land
Python tools to process spaceborne lidar (GEDI and ICESAT2) for land (pySL4Land) applications. 

## Supported Data Products

It is pretty straight forward to add suport for new data products but at the moment I've just implemented what I need therefore just the following products are supported.

### GEDI

 - GEDI02_b

### ICESAT-2

 - ALT08

## Install
To install create a new python environment and install the following:
 
    pip install geopandas
    pip install h5py
    pip install scipy
 
Download pysl4land release, extract and then run:

    python setup.py install

## Run

You can then run with the following commands which will create geopackage files you can open within a GIS:
For GEDI data:

    pysl4landgeditools.py -i input_gedi.h5 -o output_gedi.gpkg
 
For ICESAT-2 data:

    pysl4landicesat2tools.py -i input_icesat2.h5 -o output_icesat2.gpkg --polys

For ICESAT-2 WEAK/STRONG BEAMS ONLY:
    
    pysl4landicesat2tools.py -i input_icesat2.h5 -o output_icesat2.gpkg --polys --strong_only
