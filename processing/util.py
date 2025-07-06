

# Extract the Sentinel 2 data by bands and merge into one imagery

import os
import rasterio

from rasterio.warp import calculate_default_transform, reproject, Resampling
import fiona
from rasterio.mask import mask
from rasterio.windows import Window
from tqdm import tqdm
from rasterio.merge import merge
from typing import Union, Tuple, List
from pathlib import Path
from rasterio.enums import Resampling as ResampleEnum
import pandas as pd
import numpy as np


def find_img_data_folder(root_path):
    """
    Searching for the correct directory that has the raw Sentinel data downloaded

    :param root_path: Path to sentinel data folder
    :return:
    """

    paths = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Look for folders that end with '.SAFE'
        for dirname in dirnames:
            if dirname.endswith('.SAFE'):
                safe_path = os.path.join(dirpath, dirname)
                # Now search inside the .SAFE directory for IMG_DATA
                for sub_dirpath, sub_dirnames, _ in os.walk(safe_path):
                    if "IMG_DATA" in sub_dirnames:
                        paths.append(os.path.join(sub_dirpath, "IMG_DATA"))
    return paths  # Not found




def re_projection(intif, outtif, resampling_method=ResampleEnum.bilinear):
    """
    Image reprojection to project the raw imagery bands into WGS-84

    :param intif: input imagery path
    :param outtif: reprojected imagery
    :return:
    """
    dst_crs = 'EPSG:4326'

    src = rasterio.open(intif, driver='JP2OpenJPEG')
    transform, width, height = calculate_default_transform(src.crs, dst_crs, src.width, src.height, *src.bounds)
    kwargs = src.meta.copy()
    kwargs.update({
        'crs': dst_crs,
        'transform': transform,
        'width': width,
        'height': height,
        'driver': 'GTiff'
    })

    with rasterio.open(outtif, 'w', **kwargs) as dst:
        for i in range(1, src.count + 1):
            reproject(
                source=rasterio.band(src, i),
                destination=rasterio.band(dst, i),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=resampling_method)

#
#
# def re_projection(
#     intif: Union[str, Path],
#     outtif: Union[str, Path],
#     resampling_method: ResampleEnum = ResampleEnum.bilinear,
#     dst_crs: str = 'EPSG:4326',
#     dst_resolution: Tuple[float, float] = (0.0001,0.0001)  # (x_res, y_res) # default unit is degree 0.000103632
# ):
#     """
#     Reprojects a raster image into a target CRS, with optional resampling method and output resolution.
#
#     Parameters
#     ----------
#     intif : str or Path
#         Path to the input raster file.
#     outtif : str or Path
#         Path to the output reprojected raster file.
#     resampling_method : rasterio.enums.Resampling, optional
#         Resampling method to use during reprojection. Default is nearest.
#     dst_crs : str, optional
#         Target CRS for reprojection. Default is 'EPSG:4326'.
#     dst_resolution : tuple of float (x_res, y_res), optional
#         Desired output resolution in target CRS units (e.g., degrees or meters).
#     """
#     with rasterio.open(intif, driver='JP2OpenJPEG') as src:
#         if dst_resolution:
#             # Manually compute transform and output shape based on resolution
#             transform, width, height = calculate_default_transform(
#                 src.crs, dst_crs, src.width, src.height, *src.bounds, resolution=dst_resolution
#             )
#         else:
#             # Use default transform/size from source
#             transform, width, height = calculate_default_transform(
#                 src.crs, dst_crs, src.width, src.height, *src.bounds
#             )
#
#         kwargs = src.meta.copy()
#         kwargs.update({
#             'crs': dst_crs,
#             'transform': transform,
#             'width': width,
#             'height': height,
#             'driver': 'GTiff'
#         })
#
#         with rasterio.open(outtif, 'w', **kwargs) as dst:
#             for i in range(1, src.count + 1):
#                 reproject(
#                     source=rasterio.band(src, i),
#                     destination=rasterio.band(dst, i),
#                     src_transform=src.transform,
#                     src_crs=src.crs,
#                     dst_transform=transform,
#                     dst_crs=dst_crs,
#                     resampling=resampling_method
#                 )


def reproject_to_match(
    input_raster: Union[str, Path],
    output_raster: Union[str, Path],
    reference_raster: Union[str, Path],
    resampling_method: Resampling = Resampling.bilinear
):
    """
    Reproject and resample an input raster to match the spatial resolution, transform,
    CRS, and shape of a reference raster.

    Parameters
    ----------
    input_raster : str or Path
        Path to input raster to be reprojected.
    output_raster : str or Path
        Path to save the reprojected raster.
    reference_raster : str or Path
        Path to the reference raster to match.
    resampling_method : rasterio.enums.Resampling
        Resampling method (nearest, bilinear, cubic, etc.).
    """
    with rasterio.open(reference_raster) as ref:
        dst_crs = ref.crs
        dst_transform = ref.transform
        dst_width = ref.width
        dst_height = ref.height

    with rasterio.open(input_raster) as src:
        dst_profile = src.meta.copy()
        dst_profile.update({
            'crs': dst_crs,
            'transform': dst_transform,
            'width': dst_width,
            'height': dst_height,
            'driver': 'GTiff'
        })

        with rasterio.open(output_raster, 'w', **dst_profile) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=resampling_method
                )


def merge_bands_to_multispectral(band_paths, output_path):
    """
    The raw imagery are downloaded as individual band, merge the band into a multisplectral imagery
    :param band_paths: path to all band info
    :param output_path: output path
    :return:
    """
    # Open all the input bands
    band_data = [rasterio.open(path) for path in band_paths]

    # Check if all input bands have the same dimensions and CRS
    ref_profile = band_data[0].profile
    for b in band_data:
        assert b.width == ref_profile['width'] and b.height == ref_profile['height'], "Band dimensions do not match"
        assert b.crs == ref_profile['crs'], "Band CRS do not match"
        assert b.transform == ref_profile['transform'], "Band transforms do not match"

    # Update the profile to write multiple bands
    out_profile = ref_profile.copy()
    out_profile.update(count=len(band_data))

    # Write to output file
    with rasterio.open(output_path, 'w', **out_profile) as dst:
        for i, src in enumerate(band_data, start=1):
            dst.write(src.read(1), i)

    # Close all band files
    for src in band_data:
        src.close()

    print(f"Combined TIFF written to: {output_path}")

def upsample_raster(
    img_lres_path: Union[str, Path],
    img_hres_path: Union[str, Path],
    outf: Union[str, Path],
    method: Resampling = Resampling.bilinear):
    """
    Resamples a low-resolution TIFF image to match the resolution and spatial extent of a high-resolution reference image.

    Parameters:
    ----------
    img_lres_path : str or Path
        File path to the low-resolution input image.
    img_hres_path : str or Path
        File path to the high-resolution reference image.
    outf : str or Path
        Output file path for the resampled image.
    method : rasterio.enums.Resampling
        Resampling method (default is bilinear).
    """

    with rasterio.open(img_lres_path) as src_lres, rasterio.open(img_hres_path) as src_hres:
        # Get target transform and shape from high-res reference
        target_transform = src_hres.transform
        target_crs = src_hres.crs
        target_shape = (src_hres.height, src_hres.width)

        # Perform the resampling
        data = src_lres.read(
            out_shape=(
                src_lres.count,
                target_shape[0],
                target_shape[1]
            ),
            resampling=method
        )

        # Adjust transform to match new shape
        scale_x = src_lres.width / target_shape[1]
        scale_y = src_lres.height / target_shape[0]
        transform = src_lres.transform * src_lres.transform.scale(scale_x, scale_y)

        # Copy metadata from high-res image for spatial consistency
        meta = src_hres.meta.copy()
        meta.update({
            'height': target_shape[0],
            'width': target_shape[1],
            'transform': target_transform,
            'count': src_lres.count
        })

        # Save the resampled image
        with rasterio.open(outf, 'w', **meta) as dst:
            dst.write(data)

def crop_image(tiff_path, aoi_path, output_path):
    """
    Crop the raw imagery by AOI boundary

    :param tiff_path: raw imagery tiff
    :param aoi_path: AOI file path
    :param output_path: output path
    :return:
    """
    with fiona.open(aoi_path, "r") as shapefile:
        aoi_geometries = [feature["geometry"] for feature in shapefile]

    with rasterio.open(tiff_path) as src:
        # Crop the image using the AOI geometry
        cropped_image, cropped_transform = mask(src, aoi_geometries, crop=True)

        # Update the metadata
        out_meta = src.meta.copy()
        out_meta.update({
            "height": cropped_image.shape[1],
            "width": cropped_image.shape[2],
            "transform": cropped_transform
        })

    # Write the cropped image to a new file
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(cropped_image)

    print(f"Cropped image saved to: {output_path}")


def create_mosaic(proj_band_paths, mosaic_path):
    """
    Create a mosaic GeoTIFF from a list of raster file paths if it does not already exist.

    Parameters:
        proj_band_paths (list of str or Path): List of raster file paths to mosaic.
        mosaic_path (str or Path): Path to save the mosaic.

    Returns:
        Path: The path to the created mosaic file.
    """

    if not mosaic_path.is_file():
        # Open all source rasters
        src_files_to_mosaic = [rasterio.open(str(path)) for path in proj_band_paths]

        # Perform merge
        mosaic, out_transform = merge(src_files_to_mosaic)

        # Copy metadata and update
        out_meta = src_files_to_mosaic[0].meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_transform,
        })

        # Write mosaic to disk
        mosaic_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        with rasterio.open(mosaic_path, "w", **out_meta) as dest:
            dest.write(mosaic)

        # Close source files
        for src in src_files_to_mosaic:
            src.close()

    print("Finish mosaic, the output path is {} ...".format(mosaic_path))



def split_and_save_patches(input_tif, output_dir, patch_size=256, overlap=0, bands=None, skip_partial=True, csv_filename ="patch_index.csv"):
    """
    Create image patches for model training/inferencing

    Parameters:
        input_tif (str): Path to input image.
        output_dir (str): Output directory for patches.
        patch_size (int): Patch size in pixels (square).
        overlap (int): Overlap between patches in pixels.
        bands (list or None): List of band indices to include (1-based). If None, includes all.
        skip_partial (bool): Skip patches that would go beyond image bounds.
    """
    os.makedirs(output_dir, exist_ok=True)
    csv_path = Path(output_dir) / csv_filename
    patch_names = []
    patch_paths = []

    with rasterio.open(input_tif) as src:
        img_width = src.width
        img_height = src.height
        total_bands = src.count if bands is None else len(bands)

        step = patch_size - overlap
        count = 0

        col_steps = range(0, img_width - (patch_size if skip_partial else 0) + 1, step)
        row_steps = range(0, img_height - (patch_size if skip_partial else 0) + 1, step)

        for top in tqdm(row_steps, desc="Processing rows"):
            for left in col_steps:
                win_width = min(patch_size, img_width - left)
                win_height = min(patch_size, img_height - top)

                if skip_partial and (win_width < patch_size or win_height < patch_size):
                    continue

                window = Window(left, top, win_width, win_height)
                transform = src.window_transform(window)

                # Read only selected bands and window
                patch = src.read(indexes=bands, window=window) if bands else src.read(window=window)

                meta = src.meta.copy()
                meta.update({
                    "driver": "GTiff",
                    "height": win_height,
                    "width": win_width,
                    "transform": transform,
                    "count": total_bands
                })

                patch_filename = f"patch_{count:05d}.tif"
                patch_path = os.path.join(output_dir, patch_filename)
                with rasterio.open(patch_path, 'w', **meta) as dst:
                    dst.write(patch)

                patch_names.append(patch_filename)
                patch_paths.append(str(Path(patch_path).resolve()))

                count += 1

    # Create DataFrame
    df = pd.DataFrame({
        "patch_name": patch_names,
        "patch_path": patch_paths
    })

    df.to_csv(csv_path, index=False)
    print(f"{count} patches saved to {output_dir}")



# Post processing

def compute_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Compute the NDWI index."""
    ndwi = (green.astype(np.float32) - nir) / (green + nir + 1e-6)
    return ndwi


def read_band(image_path: Path, band_index: int) -> np.ndarray:
    """Reads a specific band from a raster file (1-based indexing)."""
    with rasterio.open(image_path) as src:
        return src.read(band_index)


def read_multiband_image(image_path: Path) -> np.ndarray:
    """Reads a multiband raster and returns as NumPy array."""
    with rasterio.open(image_path) as src:
        return src.read()  # shape: (bands, height, width)


def create_land_water_mask(ndwi: np.ndarray, threshold: float) -> np.ndarray:
    """Generates a binary land/water mask from NDWI."""
    land_mask = (ndwi < threshold).astype(np.uint8)  # 1 = land, 0 = water
    return land_mask


def mask_marsh_prediction(marsh_pred: np.ndarray, land_mask: np.ndarray) -> np.ndarray:
    """
    Removes marsh predictions from areas classified as water.
    Automatically crops the land mask to match prediction size if needed.
    """
    if land_mask.shape != marsh_pred.shape:
        # Calculate crop offsets
        h, w = marsh_pred.shape
        land_mask_cropped = land_mask[:h, :w]
        print(f"[WARN] land_mask shape {land_mask.shape} doesn't match marsh_pred shape {marsh_pred.shape}. Cropping land_mask.")
    else:
        land_mask_cropped = land_mask

    return marsh_pred * land_mask_cropped


def save_raster(output_path: Path, data: np.ndarray, reference_raster: Path, dtype='uint8') -> None:
    """Saves a single-band raster using the spatial reference of another file."""
    with rasterio.open(reference_raster) as src:
        meta = src.meta.copy()
        meta.update({
            'count': 1,
            'dtype': dtype,
            'compress': 'lzw'
        })
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(data, 1)

