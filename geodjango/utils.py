import os
import tempfile
import zipfile
import csv
import io
from django.contrib.gis.geos import Polygon
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import environ
import json
import alphashape
from shapely.geometry import shape, mapping, Point
import geopandas as gpd

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()


def is_valid_geospatial_file(file):
    """Return the geospatial file format based on its extension (zip, kml, geojson)."""

    # Ensure the object has a 'name' attribute
    if not hasattr(file, "name"):
        return None

    # Mapping of valid extensions to their corresponding format names
    extension_mapping = {".zip": "zip", ".kml": "kml", ".geojson": "geojson"}

    # Get the file extension
    ext = os.path.splitext(file.name)[1].lower()

    # Return the corresponding format or None if it's not valid
    return extension_mapping.get(ext, None)


def extract_zip_to_temp(file):
    """
    Extract a zip file to a temporary directory.

    Args:
        file: A file-like object representing the zip file.

    Returns:
        A string representing the path of the temporary directory where the zip content is extracted.
    """
    # Ensure the file is a valid zip file
    if not zipfile.is_zipfile(file):
        raise ValueError("The provided file is not a valid zip file.")

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Extract the zip file content to the temporary directory
    with zipfile.ZipFile(file, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    return temp_dir  # Return the path of the temporary directory


def find_shapefile_path(temp_dir):
    """Find the path of the shapefile (.shp) in the given directory."""
    # Loop through all files in the temporary directory
    for file_name in os.listdir(temp_dir):
        # Check if the file has a .shp extension
        if file_name.endswith(".shp"):
            # Return the full path to the shapefile
            return os.path.join(temp_dir, file_name)

    # If no shapefile is found, raise an error
    raise FileNotFoundError("No shapefile (.shp) found in the directory.")


def csv_to_dict(file):
    """
    This function reads a CSV file (file object), removes empty rows, and returns its contents as a list of dictionaries.
    Each dictionary represents a row in the CSV file, where the keys are the column headers.

    :param file: A file-like object (such as an uploaded file)
    :return: List of dictionaries (with empty rows removed)
    """
    file_content = file.read().decode("utf-8")  # Decode the byte content to a string
    file_io = io.StringIO(file_content)
    # Create a CSV DictReader object to read rows as dictionaries
    reader = csv.DictReader(file_io)

    # Filter out rows that are empty (i.e., where all values are empty or None)
    data = [row for row in reader if any(value.strip() for value in row.values())]
    return data


def calculate_bbox_from_csv_points(csv_data):
    # Initialize variables to track min and max lat, lon
    min_lat = float("inf")
    max_lat = float("-inf")
    min_lon = float("inf")
    max_lon = float("-inf")

    # Loop through the CSV data
    for row in csv_data:
        lat = round(
            float(row["lat"]), 6
        )  # Assuming 'lat' is a string and needs to be converted to float
        lon = round(float(row["lon"]), 6)  # Same for 'lon'

        # Update the min/max lat, lon
        min_lat = min(min_lat, lat)
        max_lat = max(max_lat, lat)
        min_lon = min(min_lon, lon)
        max_lon = max(max_lon, lon)

    # Calculate the bounding box using the min/max lat, lon values
    bbox = Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))
    return bbox


def parse_date(date_str):
    """Try parsing a date string with multiple formats."""
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def create_geoserver_layer(layer_name, table_name):
    """Create Geoserver layer dynamically"""

    geoserver_username = env("GEOSERVER_USERNAME", default="")
    geoserver_password = env("GEOSERVER_PASSWORD", default="")
    geoserver_url = env("GEOSERVER_URL", default="")
    geoserver_workspace = env("GEOSERVER_WORKSPACE", default="")
    geoserver_store = env("GEOSERVER_STORE", default="")

    layer_data = {
        "featureType": {
            "name": layer_name,
            "nativeName": table_name,  # The table name in your PostGIS database
            "srs": "EPSG:4326",  # Coordinate reference system (can be modified)
            "store": {
                "@class": "dataStore",
                "name": f"{geoserver_workspace}:{geoserver_store}",
            },
            "enabled": True,
        }
    }

    # Add the layer
    response = requests.post(
        f"{geoserver_url}/workspaces/{geoserver_workspace}/datastores/{geoserver_store}/featuretypes",
        auth=HTTPBasicAuth(geoserver_username, geoserver_password),
        json=layer_data,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 201:
        return {
            "success": True,
            "message": f"Layer '{layer_name}' created successfully!",
        }
    else:
        return {
            "success": False,
            "message": f"Error creating layer: {response.text}",
        }


def delete_geoserver_layer(layer_name):
    """Delete Geoserver layer dynamically"""

    geoserver_username = env("GEOSERVER_USERNAME", default="")
    geoserver_password = env("GEOSERVER_PASSWORD", default="")
    geoserver_url = env("GEOSERVER_URL", default="")

    # Delete the layer
    response = requests.delete(
        f"{geoserver_url}/layers/{layer_name}?recurse=true",
        auth=HTTPBasicAuth(geoserver_username, geoserver_password),
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200:
        return {
            "success": True,
            "message": f"Layer '{layer_name}' deleted!",
        }
    else:
        return {
            "success": False,
            "message": f"Error deleting layer: {response.text}",
        }


def create_concave_hull(input_polygon, alpha=0.003, buffer=0):
    """
    Process concave hull from geojson polygon
    """
    geojson_polygon = input_polygon

    # Convert GeoJSON to a Shapely geometry
    polygon = shape(geojson_polygon)
    gdf = gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326")  # EPSG:4326 is lat/lon

    # Step 2: Reproject to UTM 3857
    gdf_utm = gdf.to_crs(epsg=3857)

    polygon_utm = gdf_utm.geometry[0]
    points = list(polygon_utm.exterior.coords)  # Extract points in UTM coordinates
    for interior in polygon_utm.interiors:
        points.extend(list(interior.coords))

    # Generate the alpha shape (concave hull)
    concave_hull = alphashape.alphashape(points, alpha)
    buffered = concave_hull
    if buffer > 0:
        buffered = concave_hull.buffer(buffer)

    # Step 5: Convert concave hull back to GeoDataFrame
    concave_hull_gdf = gpd.GeoDataFrame(geometry=[buffered], crs=gdf_utm.crs)

    concave_hull_gdf_4326 = concave_hull_gdf.to_crs(epsg=4326)  # Convert back to WGS84
    # Step 7: Convert the concave hull back to GeoJSON
    concave_hull_geojson = mapping(concave_hull_gdf_4326.geometry[0])

    return json.dumps(concave_hull_geojson)


def geojson_line_length(geometry):

    # Convert GeoJSON to a GeoSeries
    gdf = gpd.GeoSeries(
        [shape(geometry)], crs="EPSG:4326"
    )  # GeoJSON is usually EPSG:4326

    # Reproject to a suitable projected CRS for length calculation (e.g., UTM)
    gdf_projected = gdf.to_crs("EPSG:3857")  # Adjust the UTM zone as needed

    # Calculate length in meters
    length_meters = gdf_projected.length[0]
    length_km = round(length_meters / 1000, 3)
    return length_km


def add_unique_items(target_list: list, new_items: list):
    """
    Add items to the target list if they do not already exist based on 'id'.

    Args:
    - target_list: List of dictionaries representing the existing data.
    - new_items: List of dictionaries representing the new data to add.
    """
    existing_ids = {item["id"] for item in target_list}
    for item in new_items:
        if item["id"] not in existing_ids:
            target_list.append(item)


def calculate_distance(start_lat, start_lon, end_lat, end_lon):
    """
    Calculate the distance between two points using GeoPandas.

    Parameters:
        start_lat, start_lon: Latitude and longitude of the first point in decimal degrees.
        end_lat, end_lon: Latitude and longitude of the second point in decimal degrees.

    Returns:
        Distance in meters.
    """
    # Create points for the two locations
    point1 = Point(start_lon, start_lat)
    point2 = Point(end_lon, end_lat)

    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=[point1, point2], crs="EPSG:4326")

    # Convert the GeoDataFrame to a projected CRS (e.g., UTM for accurate distance in meters)
    gdf = gdf.to_crs(epsg=3857)  # Web Mercator (meters)

    # Calculate distance in meters
    distance = gdf.geometry[0].distance(gdf.geometry[1])
    return distance
