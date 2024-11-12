import os
import tempfile
import zipfile


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
