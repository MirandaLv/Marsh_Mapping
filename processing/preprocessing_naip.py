
import os
from pathlib import Path
from util import split_and_save_patches

project_root = Path(__file__).resolve().parent.parent

year = "2022"
tile_name = "m_3707654_sw_18_060_20210913.tif"

input_stem = tile_name.split('.')[0]

raw_tile_path = os.path.join(project_root, "dataset/raw/NAIP/{}/{}".format(year, tile_name))

b_path = os.path.join(project_root, "dataset/processed/NAIP_{}".format(year))

# Setting up different directories for the data
(project_root / 'dataset' / 'processed' /'NAIP_{}'.format(year)).mkdir(exist_ok=True, parents=True)

output_dir = os.path.join(b_path, "{}_patches".format(input_stem))

# Image patch generation
split_and_save_patches(raw_tile_path, output_dir, patch_size=256, overlap=30, skip_partial=True)


