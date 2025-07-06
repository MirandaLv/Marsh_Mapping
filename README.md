# Marsh_Mapping

This post outlines the workflow for mapping tidal marshes using Sentinel-2 multispectral imagery and National Agriculture Imagery Program (NAIP) data. It covers the full process - from data download and preprocessing to model prediction and post-processing of the imagery.

### Setting up the working environment

- For mac and linux user, run this command on terminal:

    `conda env create --file=environment.yml`

For windows user: Please refer conda user guidance to install conda, and create a virtual environment with the .yaml file (https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html)

- Run this command on terminal to activate the virtual environment:

    `conda activate xxxxx`


### Imagery acquisition
- **Sentinel-2 data:** Follow this page to download NAIP data: https://github.com/MirandaLv/Marsh_Mapping/tree/main/dataset/raw/Sentinel-2.  

- **NAIP:** Follow this page to download NAIP data: https://github.com/MirandaLv/Marsh_Mapping/tree/main/dataset/raw/NAIP. 


### Imagery preprocessing

**Sentinel MSI imagery preprocessing from raw**
1. Converting the raw .jp2 imagery band to .tif
2. Reprojecting individual sentinel band (.tif) to WGS-84, and resampling all bands into standarded 10m resolution.
3. Imagery mosaic if multiple tiles are downloaded.
4. Merging the 10-m bands into a multispectral imagery. 
5. Creating imagery patches and saved into 'dataset/sentinel/patches' for imagery inferencing.


### Model inference


### Image post-processing








### To do
- Sentinel metadata retrieval -> .csv (done)
- Sentinel data downloader (done)
- Imagery tile preprocessing (done) 
- Model architecture
- deep learning dataloader
- imagery inference
- stitch back to original data

- Maybe add a NAIP feature to the code;
