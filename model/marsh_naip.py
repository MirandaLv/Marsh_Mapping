
from pathlib import Path
import torch
from torch.utils.data import DataLoader
import rasterio
from dataloader import GenMARSH
from trainer import SemanticSegmentationTask
import sys

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from processing.stitching import stitch_tiff_patches

import os

def load_model(checkpoint_path: Path, device: torch.device) -> torch.nn.Module:
    """Loads the model from checkpoint and sets it to evaluation mode."""
    print(f"[INFO] Loading model from: {checkpoint_path}")
    model = SemanticSegmentationTask.load_from_checkpoint(str(checkpoint_path))
    model.to(device)
    model.eval()
    return model


def prepare_dataloader(patch_folder: Path, batch_size: int = 32) -> DataLoader:
    """Prepares the dataloader for inference."""
    dataset = GenMARSH(str(patch_folder), ndwi=False, datasource="NAIP")
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=False
    )
    return dataloader


def write_prediction(pred: torch.Tensor, filename: str, reference_path: Path, output_dir: Path) -> None:
    """Writes a single prediction array to a GeoTIFF using the reference image's metadata."""
    with rasterio.open(reference_path) as src:
        profile = src.profile
        profile.update({
            "count": 1,
            "dtype": 'float32',
            "compress": "lzw"
        })
        out_path = output_dir / f"pred_{filename}"
        with rasterio.open(out_path, 'w', **profile) as dst:
            dst.write(pred.astype('float32'), 1)


def run_inference(model: torch.nn.Module, dataloader: DataLoader, output_dir: Path, device: torch.device) -> None:
    """Runs inference on all batches and saves the predictions."""
    output_dir.mkdir(parents=True, exist_ok=True)

    print("[INFO] Starting inference...")
    with torch.no_grad():
        for i, batch in enumerate(dataloader):
            print(f"[INFO] Processing batch {i+1}/{len(dataloader)}")

            X = batch['image'].to(device)
            filenames = batch['filename']
            output = model(X)
            preds = torch.argmax(output, dim=1).cpu().numpy()

            for pred, fname in zip(preds, filenames):
                original_path = dataloader.dataset.folder_path / fname
                write_prediction(pred, fname, original_path, output_dir)

    print("[INFO] Inference complete.")


def main(year: str, tile_name: str) -> None:

    base_path = os.path.join(project_root, 'dataset')

    # Add underscore only if tile_name is provided
    suffix = f"{tile_name}" if tile_name else ""

    patch_folder = Path(base_path) / f"processed/NAIP_{year}/{suffix}_patches"
    checkpoint_path = Path(project_root) / f"weights/NAIP/unet/last.ckpt"
    prediction_output = Path(base_path) / f"predicted/NAIP/inference_{year}_{suffix}"
    mosaic_output = Path(base_path) / f"predicted/NAIP/merge_{year}_{suffix}.tif"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    batch_size = 32

    dataloader = prepare_dataloader(patch_folder, batch_size)
    model = load_model(checkpoint_path, device)
    run_inference(model, dataloader, prediction_output, device)

    print("[INFO] Stitching predicted tiles into a mosaic...")

    try:
        stitch_tiff_patches(prediction_output, mosaic_output)
        print(f"[INFO] Mosaic saved to: {mosaic_output}")
    except Exception as e:
        print(f"[WARN] Failed to stitch TIFF patches due to error: {str(e)}")
        print("[HINT] This is likely due to too many open files or system limits.")
        print("       Consider one of the following alternatives:")

        print("\n[Option 1] Using `gdalbuildvrt` + `gdal_translate` (recommended for large sets):")
        print(f"  gdalbuildvrt output.vrt {prediction_output}/*.tif")
        print(f"  gdal_translate output.vrt {mosaic_output}")

        print("\n[Option 2] Using `gdal_merge.py` (may also hit file limits):")
        print(f"  gdal_merge.py -o {mosaic_output} {prediction_output}/*.tif")

        print("\n[Option 3] Implement chunked stitching using rasterio in batches.")
        print("  (e.g., group files and merge a few hundred at a time into intermediate mosaics)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run marsh segmentation inference and stitching.")
    parser.add_argument("--year", type=str, required=True, help="Year of NAIP imagery to process")
    parser.add_argument("--tile-name", type=str, default="", help="Optional tile name to append to output folder")

    args = parser.parse_args()
    main(args.year, args.tile_name)









