

import os
import boto3
import geopandas as gpd
from pystac_client import Client
from typing import Tuple, List
import pandas as pd

# -------- Configuration -------- #
STAC_URL = "https://catalogue.dataspace.copernicus.eu/stac" # for data filtering
ENDPOINT_URL = "https://eodata.dataspace.copernicus.eu" # for data download

# -------- Replace your access key an secret key from https://dataspace.copernicus.eu/ --------
# More info: https://documentation.dataspace.copernicus.eu/APIs/OData.html#product-download

ACCESS_KEY = ""
SECRET_KEY = ""

PRODUCT_TYPE = "S2MSI2A" # Level-2A product
DATA_COLLECTION = "SENTINEL-2"
MAX_CLOUD_COVER = 3
START_DATE = "2024-05-01"
END_DATE = "2024-09-30"
AOI_PATH = "../bounding_box.geojson"
# AOI_PATH = "../boundary.geojson"
OUTPUT_DIR = ""



def get_url_parts(url: str) -> Tuple[str, str]:
    """Extract the bucket download path"""
    bucket, path = url.lstrip("/").split("/", 1)
    return bucket, path


def download_s3_product(bucket, product_prefix: str, target_dir: str = "") -> None:
    """Download all files under a prefix from a public S3 bucket."""
    files = bucket.objects.filter(Prefix=product_prefix)
    if not list(files):
        raise FileNotFoundError(f"No files found for product: {product_prefix}")

    for file in files:
        local_path = os.path.join(target_dir, file.key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        if not os.path.isdir(local_path):
            print(f"Downloading: {file.key}")
            bucket.download_file(file.key, local_path)


def get_aoi_bbox(aoi_file: str) -> List[float]:
    """Get the bounding box of AOI"""
    gdf = gpd.read_file(aoi_file)
    return gdf.total_bounds.tolist()


def search_sentinel_items(client: Client, bbox: List[float], start: str, end: str, cloud_cover: int, product_type: str) -> List:
    """Search STAC for Sentinel items with filters."""
    results = client.search(
        collections=[DATA_COLLECTION],
        bbox=bbox,
        datetime=f"{start}/{end}"
    )
    # return [item for item in results.items()]
    return [
        item for item in results.items()
        if item.properties.get("cloudCover", 100) <= cloud_cover and
           item.properties.get("productType", "").upper() == product_type.upper()
    ]

def metadata_generation(items: list):
    # Extract the properties dict from each item in the items list
    properties_list = [item.properties for item in items]

    df = pd.DataFrame(properties_list)
    df['item'] = items
    df = df.drop_duplicates()
    return df


# TODO: get a list of downloading tiles that covers the entire AOI

def set_download_granules(df: pd.DataFrame, error_item=None):
    df["downloaded"] = 0

    if error_item is not None: # set not downloadable tiles
        df.loc[df.item == error_item, "downloaded"] = -1

    for i in set(df["tileId"].to_list()):
        best_item = df.loc[(df.tileId == i) & (df.downloaded != -1)].sort_values("cloudCover").iloc[0].granuleIdentifier
        df.loc[df.granuleIdentifier == best_item, "downloaded"] = 1
    return df



# -------- Main Process -------- #

def main():

    if not ACCESS_KEY or not SECRET_KEY:
        raise("Fill the ACCESS KEY and SECRET KEY")

    client = Client.open(STAC_URL)
    bbox = get_aoi_bbox(AOI_PATH)

    print(f"Searching Sentinel-2 imagery ({START_DATE} to {END_DATE}) with cloud cover <={MAX_CLOUD_COVER}%")
    items = search_sentinel_items(client, bbox, START_DATE, END_DATE, MAX_CLOUD_COVER, PRODUCT_TYPE) # Get all items that matched the filter criteria

    # Pick up non repeatable tiles and download
    df = metadata_generation(items)
    df = set_download_granules(df)
    download_items = df.loc[df.downloaded == 1]['item'].tolist()

    if not download_items:
        print("No matching Sentinel-2 products found.")
        return

    for idx, item in enumerate(download_items):
        print(f"\nProcessing item {idx + 1} of {len(items)}")

        # safe_asset = item.assets.get("PRODUCT").to_dict().get("alternate", {}).get("s3")
        #
        # if not safe_asset:
        #     print("Downloadable asset not found in STAC metadata.")
        #     return
        #
        # print("Found downloadable product. Connecting to S3...")
        # session = boto3.session.Session()
        # s3 = session.resource(
        #     's3',
        #     endpoint_url=ENDPOINT_URL,
        #     aws_access_key_id=ACCESS_KEY,
        #     aws_secret_access_key=SECRET_KEY,
        #     region_name='default'
        # )
        #
        # bucket_name, product_path = get_url_parts(safe_asset["href"])
        # print(f"Downloading path: {product_path}")
        #
        # download_s3_product(s3.Bucket(bucket_name), product_path, target_dir=OUTPUT_DIR)
        # print(f"Download completed! Files saved to: {OUTPUT_DIR}")



if __name__ == "__main__":
    main()
