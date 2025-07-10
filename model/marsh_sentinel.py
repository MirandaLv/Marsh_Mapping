#
# from trainer import SemanticSegmentationTask
# import os
# import torch
# from torch.utils.data import DataLoader
# from dataloader import GenMARSH
# import rasterio
# import sys
# from pathlib import Path
#
# project_root = Path(__file__).resolve().parent.parent
# sys.path.append(str(project_root))
#
# from processing.stitching import stitch_tiff_patches
#
# # prepare data for training
#
# year = "2017"
#
# folder_path = project_root / "dataset" / "processed" / f"sentinel_{year}" / "patches" #image_multiband_128_more
#
# model_path = project_root / "weights" / "sentinel" / "unet" / "last.ckpt"
# outpath = project_root / "dataset" / "predicted" / "sentinel" / f"inference_{year}"
#
# os.makedirs(outpath, exist_ok=True)
#
# batch_size = 32
#
# # Load image patches
# dataset = GenMARSH(folder_path, mode="test")
# dataloader = DataLoader(dataset,
#                 batch_size = batch_size,
#                 shuffle = False,
#                 num_workers = 0,
#                 pin_memory = False)
#
#
# mpath = model_path
# model = SemanticSegmentationTask.load_from_checkpoint(mpath)
#
#
# def run_inference(model, dataloader, output_dir, device):
#
#     model.eval()
#     model.to(device)
#
#     os.makedirs(output_dir, exist_ok=True)
#
#     with torch.no_grad():
#         print("Working on Inferencing...")
#         for i, batch in enumerate(dataloader):
#
#             print("Working on batch {}".format(i))
#             X = batch['image'].to(device)
#             filenames = batch['filename']  # list of filenames in the batch
#             output = model(X)
#             preds = torch.argmax(output, dim=1).cpu().numpy()  # shape: (B, H, W)
#
#             for pred, fname in zip(preds, filenames):
#                 original_path = os.path.join(dataloader.dataset.folder_path, fname)
#                 with rasterio.open(original_path) as src:
#                     profile = src.profile
#                     profile.update({
#                         "count": 1,
#                         "dtype": 'float32',
#                         "compress": "lzw"})
#
#                     out_path = os.path.join(output_dir, f"pred_{fname}")
#                     with rasterio.open(out_path, 'w', **profile) as dst:
#                         dst.write(pred.astype('float32'), 1)  # Write to band 1 (uint8)
#
#
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# run_inference(model, dataloader, outpath, device)
#
# output_mosaic_path = "../dataset/merge_{}.tif".format(year)
# stitch_tiff_patches(outpath, output_mosaic_path)
#
#



from pathlib import Path
import sys
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
from processing.stitching import stitch_tiff_patches

import torch
from torch.utils.data import DataLoader
import rasterio

from trainer import SemanticSegmentationTask
from dataloader import GenMARSH



def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_paths(year: str, aoi: str) -> dict:
    root = get_project_root()
    return {
        "patches": root / "dataset" / "processed" / f"sentinel_{aoi}_{year}" / "patches",
        "weights": root / "weights" / "sentinel" / "unet" / "last.ckpt",
        "output": root / "dataset" / "predicted" / "sentinel" / f"inference_{aoi}_{year}",
        "mosaic": root / "dataset" / "predicted" / "sentinel" / f"merge_{aoi}_{year}.tif"
    }


def run_inference(model, dataloader, output_dir: Path, device: torch.device) -> None:
    model.eval()
    model.to(device)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Starting inference...")
    with torch.no_grad():
        for i, batch in enumerate(dataloader):
            print(f"Processing batch {i + 1}")
            X = batch["image"].to(device)
            filenames = batch["filename"]
            preds = torch.argmax(model(X), dim=1).cpu().numpy()

            for pred, fname in zip(preds, filenames):
                input_path = dataloader.dataset.folder_path / fname
                output_path = output_dir / f"pred_{fname}"

                with rasterio.open(input_path) as src:
                    profile = src.profile.copy()
                    profile.update({
                        "count": 1,
                        "dtype": "float32",
                        "compress": "lzw"
                    })

                    with rasterio.open(output_path, 'w', **profile) as dst:
                        dst.write(pred.astype("float32"), 1)


def main(year: str = "2017", aoi: str = 'aoi', batch_size: int = 32) -> None:
    paths = get_paths(year, aoi)
    paths["output"].mkdir(parents=True, exist_ok=True)

    dataset = GenMARSH(paths["patches"], mode="test")
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=False)

    model = SemanticSegmentationTask.load_from_checkpoint(paths["weights"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    run_inference(model, dataloader, paths["output"], device)

    # Stitch the predicted patches
    try:
        stitch_tiff_patches(paths["output"], paths["mosaic"])
        print(f"[INFO] Mosaic saved to: {paths['mosaic']}")
    except Exception as e:
        print(f"[WARN] Failed to stitch TIFF patches due to error: {str(e)}")
        print("[HINT] This is likely due to too many open files or system limits.")
        print("       Consider one of the following alternatives:")

        print("\n[Option 1] Using `gdalbuildvrt` + `gdal_translate` (recommended for large sets):")
        print(f"  gdalbuildvrt output.vrt {paths['output']}/*.tif")
        print(f"  gdal_translate output.vrt {paths['mosaic']}")

        print("\n[Option 2] Using `gdal_merge.py` (may also hit file limits):")
        print(f"  gdal_merge.py -o {paths['mosaic']} {paths['output']}/*.tif")

        print("\n[Option 3] Implement chunked stitching using rasterio in batches.")
        print("  (e.g., group files and merge a few hundred at a time into intermediate mosaics)")

if __name__ == "__main__":
    main('2018', 'aoi')




