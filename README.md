# Marsh_Mapping

This post includes the process of predicting tidal marshes from sentinel multispectral imagery, from data dowmload, preprocssing, to model prediction, and stitching back to original tile dimension.

1. Download a sentinel raw imagery from copernicus (https://dataspace.copernicus.eu/).
   1. A series of matching tiles that intersect the study area will be downloaded. For larger areas, multiple tiles meeting the specified criteria (e.g., cloud coverage, acquisition time) may be retrieved. When multiple tiles cover the same area and meet all criteria, the selection will be based on the lowest cloud coverage.
2. Preprocessing the raw imagery:
      1. Converting the raw .jp2 imagery band to .tif 
      2. Reprojecting individual sentinel band (.tif) to WGS-84, and resampling all bands into standarded 10m resolution.
      3. Imagery mosaic if multiple tiles are downloaded.
      4. Merging the 10-m bands into a multispectral imagery. 
      5. Creating imagery patches and saved into 'data/sentinel/patches' for imagery inferencing.
3. ddddd
4. Model prediction of the generated imagery patches, and mosaic the output imagery prediction to the raw imagery size.



- Sentinel metadata retrieval -> .csv (done)
- Sentinel data downloader (done)
- Imagery tile preprocessing (done) 
- Model architecture
- deep learning dataloader
- imagery inference
- stitch back to original data

- Maybe add a NAIP feature to the code;
- 
