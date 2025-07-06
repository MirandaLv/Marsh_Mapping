# -*- coding: utf-8 -*-

import torch
import random
import numpy as np
import rasterio
from torch.utils.data import Dataset
import os
from pathlib import Path

random.seed(0)
np.random.seed(0)
torch.manual_seed(0)


class GenMARSH(Dataset):

    def __init__(self, folder_path, mode="train", ndvi=True, ndwi=True, datasource="sentinel"):

        self.folder_path = Path(folder_path)
        self.image_files = sorted([
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith(".tif")
        ])

        self.mode = mode

        self.ndvi = ndvi
        self.ndwi = ndwi
        self.datasource = datasource


    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):

        img_path = self.image_files[idx]

        # the dimension is CxHxW
        image = rasterio.open(img_path).read().astype('float32')

        # target = self.df.iloc[idx].loc['label_path']
        # target = rasterio.open(target).read().astype('int8')  # 1xHxW

        if self.datasource.lower() == 'naip':
            image = image / 255.  # image = image/10000*3.5 (sentinel)
        elif self.datasource.lower() == 'sentinel':
            image = image / 10000
        else:
            raise ("The data source should be NAIP or sentinel")

        if self.mode == "train":
            # exclusing Coastal aerosol, Water vapour, and SWIR - Cirrus bands from analysis in Sentinel, since these bands are mainly for the atmospheric correction and cloud screen.
            # 'RGBV' (B2, B3, B4, B8), 'B01'(Coastal aerosol), 'B05', 'B06', 'B07', 'B09'(Water vapour), 'B10' (SWIR - Cirrus), 'B11', 'B12', 'B8A' (in the original research data)
            if self.datasource == 'sentinel':  # 5,9,10 (index: 4,8,9)
                image = np.concatenate([image[:4, :, :], image[5:8, :, :], image[10:, :, :]], axis=0).astype('float32') #B2,3,4,8,5,6,7,11,12,B8A

        elif self.mode == "test": # new processed data
            if self.datasource == "sentinel":
                # New sentinel data acquistion: band_list = ["02", "03", "04", "05", "06", "07", "08" ,"8A", "11", "12"]
                # Change to B2,3,4,8,5,6,7,11,12,B8A
                # make sure the testing data's band corresponds to the training data band
                image = np.concatenate([
                    image[:3],
                    image[6][None, :, :],
                    image[3:6],
                    image[8:],
                    image[7][None, :, :]
                ], axis=0).astype('float32')

        if self.ndvi:
            if self.datasource.lower() == 'naip':  # NAIP bands: R,G,B,NIR
                ndvi = (image[3, :, :] - image[0, :, :]) / (
                            image[3, :, :] + image[0, :, :])  # (NIR - R) / (NIR + R)
                ndvi = ndvi[np.newaxis, :, :]
                image = np.concatenate([image, ndvi], axis=0).astype('float32')

            elif self.datasource.lower() == 'sentinel':
                ndvi = (image[3, :, :] - image[2, :, :]) / (
                            image[3, :, :] + image[2, :, :])  # (NIR - R) / (NIR + R)
                ndvi = ndvi[np.newaxis, :, :]
                image = np.concatenate([image, ndvi], axis=0).astype('float32')

        if self.ndwi:
            ndwi = (image[1, :, :] - image[3, :, :]) / (image[1, :, :] + image[3, :, :])  # NDWI = (G-NIR)/(G+NIR)
            ndwi = ndwi[np.newaxis, :, :]
            image = np.concatenate([image, ndwi], axis=0).astype('float32')

        #         image = image[[0,1,2,3], :, :] # Use only four bands from Sentinel for testing.
        sample = {'image': image, 'filename': os.path.basename(img_path)}

        return sample

