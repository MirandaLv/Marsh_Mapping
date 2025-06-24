
import geopandas as gpd
import numpy as np
from shapely.geometry import box, Polygon


def get_poly_bound(gdf):
    bounds = gdf['geometry'].bounds
    minx = np.min(bounds.minx)
    miny = np.min(bounds.miny)
    maxx = np.max(bounds.maxx)
    maxy = np.max(bounds.maxy)

    return minx, miny, maxx, maxy

# boundary_file = '../dataset/raw/VA_TMI_2011_2019.shp'

boundary_file = '../dataset/raw/guinea_marsh.geojson'

boundary_df = gpd.read_file(boundary_file)
boundary_df = boundary_df.to_crs(4326)
bounds = boundary_df['geometry'].bounds

minx, miny, maxx, maxy = get_poly_bound(boundary_df)
bbox_polygon = box(minx, miny, maxx, maxy)

# Convert bounding box to GeoDataFrame
bbox_gdf = gpd.GeoDataFrame(index=[0], crs='EPSG:4326', geometry=[bbox_polygon])

# Save to GeoJSON
bbox_gdf.to_file('../bounding_box_guinea.geojson', driver='GeoJSON')

print(f"Bounding box exported to ../bounding_box_guinea.geojson")