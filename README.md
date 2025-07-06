# Marsh_Mapping

This post outlines the workflow for mapping tidal marshes using Sentinel-2 multispectral imagery and National Agriculture Imagery Program (NAIP) data. It covers the full process - from data download and preprocessing to model prediction and post-processing of the imagery.

### Setting up the working environment

- For mac and linux user:

Run this command on terminal:

`conda env create --file=environment.yml`

      For windows user: Please refer conda user guidance to install conda, and create a virtual environment with the .yaml file (https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html)

- Run this command on terminal to activate the virtual environment:

`conda activate xxxxx`


### Imagery acquisition
- **Sentinel-2 data:** The Copernicus Open Access Hub (SciHub) was deprecated in 2023, thus a more convenient way to access the sentinel data is through the Copernicus Data Space Ecosystem. Follow this link (https://documentation.dataspace.copernicus.eu/APIs/S3.html) to create a CDSE account, and getting the ACCESS KEY and SECRET KEY to access data saved on S3.  

- **NAIP:** Follow this page to download NAIP data: https://github.com/MirandaLv/Marsh_Mapping/tree/main/dataset/raw/NAIP. 



### Imagery preprocessing


### Model inference


### Image post-processing







###
3. Download a sentinel raw imagery from copernicus (https://dataspace.copernicus.eu/).
   1. A series of matching tiles that intersect the study area will be downloaded. For larger areas, multiple tiles meeting the specified criteria (e.g., cloud coverage, acquisition time) may be retrieved. When multiple tiles cover the same area and meet all criteria, the selection will be based on the lowest cloud coverage.
4. Preprocessing the raw imagery:
      1. Converting the raw .jp2 imagery band to .tif 
      2. Reprojecting individual sentinel band (.tif) to WGS-84, and resampling all bands into standarded 10m resolution.
      3. Imagery mosaic if multiple tiles are downloaded.
      4. Merging the 10-m bands into a multispectral imagery. 
      5. Creating imagery patches and saved into 'data/sentinel/patches' for imagery inferencing.
5. ddddd
6. Model prediction of the generated imagery patches, and mosaic the output imagery prediction to the raw imagery size.




### To do
- Sentinel metadata retrieval -> .csv (done)
- Sentinel data downloader (done)
- Imagery tile preprocessing (done) 
- Model architecture
- deep learning dataloader
- imagery inference
- stitch back to original data

- Maybe add a NAIP feature to the code;
