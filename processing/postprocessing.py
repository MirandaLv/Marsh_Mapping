
from pathlib import Path
from util import read_multiband_image, create_land_water_mask, compute_ndwi, read_band, mask_marsh_prediction, save_raster


def process_marsh_mask(raw_image_path: Path,
                       marsh_pred_path: Path,
                       output_path: Path,
                       ndwi_threshold: float = 0.0) -> None:
    """
    Clean marsh prediction mask by removing areas classified as water based on NDWI.

    Args:
        raw_image_path (Path): Path to 4-band input image (RGB + NIR).
        marsh_pred_path (Path): Path to binary marsh prediction (1=marsh, 0=non-marsh).
        output_path (Path): Path to save cleaned marsh mask.
        ndwi_threshold (float): Threshold for land/water separation using NDWI.
    """

    print(f"[INFO] Reading raw image from: {raw_image_path}")
    raw = read_multiband_image(raw_image_path)
    green = raw[1]  # Band 2: Green (0-based index 1)
    nir = raw[3]    # Band 4: NIR   (0-based index 3)

    print("[INFO] Computing NDWI...")
    ndwi = compute_ndwi(green, nir)

    print(f"[INFO] Creating land/water mask using threshold: {ndwi_threshold}")
    land_mask = create_land_water_mask(ndwi, threshold=ndwi_threshold)

    print(f"[INFO] Reading marsh prediction from: {marsh_pred_path}")
    marsh_pred = read_band(marsh_pred_path, band_index=1)  # assuming it's single-band

    print("[INFO] Applying land mask to marsh prediction...")
    cleaned_marsh = mask_marsh_prediction(marsh_pred, land_mask)

    print(f"[INFO] Saving cleaned marsh prediction to: {output_path}")
    save_raster(output_path, cleaned_marsh, reference_raster=marsh_pred_path)

    print("[INFO] Done.")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent

    # Example usage
    raw_image = project_root / "dataset/raw/NAIP/2022/m_3707654_sw_18_060_20210913.tif"
    marsh_pred = project_root / "dataset/predicted/NAIP/merge_2022_m_3707654_sw_18_060_20210913.tif"
    output_mask = project_root / "dataset/predicted/NAIP/merge_2022_m_3707654_sw_18_060_20210913_cleaned.tif"


    process_marsh_mask(
        raw_image_path=raw_image,
        marsh_pred_path=marsh_pred,
        output_path=output_mask,
        ndwi_threshold=0.5  # adjust threshold as needed (e.g., 0.1 for conservative masking)
    )
