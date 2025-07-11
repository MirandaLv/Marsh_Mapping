

import os
import rasterio
from pathlib import Path
from util import re_projection, create_mosaic, merge_bands_to_multispectral, split_and_save_patches, reproject_to_match
import glob

year = "2018"
AOI = "aoi"

project_root = Path(__file__).resolve().parent.parent

# The data are saved to different subfolder name depending on the year
if int(year) >= 2022:
    raw_data_path = Path(os.path.join(project_root, "dataset/raw/Sentinel-2/MSI/L2A/{}".format(year)))
else:
    raw_data_path = Path(os.path.join(project_root, "dataset/raw/Sentinel-2/MSI/L2A_N0500/{}".format(year)))

# aoi_path = os.path.join(base_path, "bounding_box.geojson")

b_path = os.path.join(project_root, "dataset/processed/sentinel_{}_{}".format(AOI, year))

# Setting up different directories for the data
(project_root / 'dataset' / 'processed' /'sentinel_{}_{}'.format(AOI, year)).mkdir(exist_ok=True, parents=True)
(project_root / 'dataset' /'processed' / 'sentinel_{}_{}'.format(AOI, year) / 'reprojection').mkdir(exist_ok=True, parents=True)
reproject_path = os.path.join(b_path, 'reprojection')

merge_output_path = os.path.join(b_path, "combined_{}_{}.tif".format(AOI, year))

output_dir = os.path.join(b_path, "patches")

band_list = ["02", "03", "04", "05", "06", "07", "08" ,"8A", "11", "12"] # getting the band list
res_list = ["10", "10", "10", "20", "20", "20", "10", "20", "20", "20"] # getting the corresponding resolution
all_bands_path = []

mosaic_path_list = []
for b, res in zip(band_list, res_list):

    print("Working on band {}".format(b))
    band_granules_path = list(raw_data_path.rglob("*B{}_{}m.jp2".format(b, res)))

    band_granules_src = [rasterio.open(i, driver='JP2OpenJPEG') for i in band_granules_path]

    proj_band_path = [os.path.join(reproject_path, Path(i).stem + '_wgs84.tif') for i in band_granules_path]

    all_bands_path.append(proj_band_path[0])

    # Reproject all bands to wgs-84
    for file, outfile in zip(band_granules_path, proj_band_path):

        infilename = os.path.basename(file).split('.')[0]
        outfilename_pre = os.path.basename(outfile).split('.')[0][0:-6]

        if infilename == outfilename_pre and not os.path.isfile(outfile):
            print("Reproject file {}".format(file))

            # standardize all band resolution to 10m resolution, default is 0.000103632
            if b == "02":
                re_projection(file, outfile)
                reference_path = outfile
            else:
                reproject_to_match(file, outfile, reference_path)

    mosaic_path = Path(b_path) / 'merge_B{}_{}.tif'.format(b, year)
    create_mosaic(proj_band_path, mosaic_path)

    mosaic_path_list.append(mosaic_path) # get all individual band path for band stacking

# Merge all band information into a multispectral imagery
merge_bands_to_multispectral(mosaic_path_list, merge_output_path)

# Image patch generation
split_and_save_patches(merge_output_path, output_dir, patch_size=128, overlap=10, skip_partial=True)



