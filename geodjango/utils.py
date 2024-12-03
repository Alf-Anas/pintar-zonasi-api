import os
import tempfile
import zipfile
import csv
import io
from django.contrib.gis.geos import Polygon
from datetime import datetime


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
