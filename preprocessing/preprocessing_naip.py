



import os
import rasterio
from pathlib import Path
from util import split_and_save_patches
import glob

year = "2022"
tile_name = "m_3707654_sw_18_060_20210913.tif"

base_path = Path.cwd().parent

raw_tile_path = os.path.join(base_path, "dataset/raw/NAIP/{}/{}".format(year, tile_name))

b_path = os.path.join(base_path, "dataset/processed/NAIP_{}".format(year))

# Setting up different directories for the data
(base_path / 'dataset' / 'processed' /'NAIP_{}'.format(year)).mkdir(exist_ok=True, parents=True)

output_dir = os.path.join(b_path, "patches")

# Image patch generation
split_and_save_patches(raw_tile_path, output_dir, patch_size=256, overlap=30, skip_partial=True)


