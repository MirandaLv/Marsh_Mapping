
from trainer import SemanticSegmentationTask
import os
import torch
from torch.utils.data import DataLoader
from dataloader import GenMARSH
import rasterio
from processing.stitching import stitch_tiff_patches

# prepare data for training

year = "2023"

folder_path = "../dataset/processed/sentinel_{}/patches".format(year) #image_multiband_128_more
model_path = "../weights/sentinel/unet/last.ckpt"
outpath = "../dataset/predicted/NAIP/inference_{}".format(year)

os.makedirs(outpath, exist_ok=True)

batch_size = 32

# Load image patches
dataset = GenMARSH(folder_path, mode="test")
dataloader = DataLoader(dataset,
                batch_size = batch_size,
                shuffle = False,
                num_workers = 0,
                pin_memory = False)


mpath = model_path
model = SemanticSegmentationTask.load_from_checkpoint(mpath)


def run_inference(model, dataloader, output_dir, device):

    model.eval()
    model.to(device)

    os.makedirs(output_dir, exist_ok=True)

    with torch.no_grad():
        print("Working on Inferencing...")
        for i, batch in enumerate(dataloader):

            print("Working on batch {}".format(i))
            X = batch['image'].to(device)
            filenames = batch['filename']  # list of filenames in the batch
            output = model(X)
            preds = torch.argmax(output, dim=1).cpu().numpy()  # shape: (B, H, W)

            for pred, fname in zip(preds, filenames):
                original_path = os.path.join(dataloader.dataset.folder_path, fname)
                with rasterio.open(original_path) as src:
                    profile = src.profile
                    profile.update({
                        "count": 1,
                        "dtype": 'float32',
                        "compress": "lzw"})

                    out_path = os.path.join(output_dir, f"pred_{fname}")
                    with rasterio.open(out_path, 'w', **profile) as dst:
                        dst.write(pred.astype('float32'), 1)  # Write to band 1 (uint8)


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
run_inference(model, dataloader, outpath, device)

output_mosaic_path = "../dataset/merge_{}.tif".format(year)
stitch_tiff_patches(outpath, output_mosaic_path)










