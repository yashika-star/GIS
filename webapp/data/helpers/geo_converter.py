import io
import json
from django.contrib.gis.gdal import DataSource
from fastkml import kml, Data
import zipfile
import tempfile
import os


class GeoConverter:
    def __new__(cls):
        raise TypeError('Static classes cannot be instantiated')

    @staticmethod
    def kml_to_geojson(kml_doc):
        try:
            k = kml.KML()

            print(kml_doc)

            # Read the KML file
            k.from_string(kml_doc)

            feature_list = []

            for doc in k.features():
                for feature in doc.features():
                    # Extract properties from KML feature (ExtendedData or SimpleData)
                    properties = {
                        'name': feature.name,
                        'description': feature.description
                    }

                    for elem in feature.extended_data.elements:
                        if isinstance(elem, Data):
                            properties[elem.name] = elem.value

                    feature_data = {
                        "type": "Feature",
                        "properties": properties,
                        "geometry": feature.geometry.__geo_interface__
                    }
                    feature_list.append(feature_data)

            geojson_data = {
                "type": "FeatureCollection",
                "features": feature_list,
            }

            print(geojson_data)

            return json.dumps(geojson_data)
        except Exception as e:
            print(f"Error: {e}")

        return None

    @staticmethod
    def shapefile_zip_to_geojson(shapefile_bytes):
        try:
            # Create a ZipFile object from the bytes
            zip_file = zipfile.ZipFile(io.BytesIO(shapefile_bytes))

            # Locate the .shp file within the ZIP archive
            shapefile_name = None
            for file_name in zip_file.namelist():
                if file_name.endswith('.shp'):
                    shapefile_name = file_name
                    break

            if shapefile_name:
                # Create a temporary directory to extract the ZIP contents
                temp_dir = tempfile.mkdtemp()
                # Extract the Shapefile to the temporary directory
                zip_file.extractall(temp_dir)
                # Create path for file
                shapefile_path = os.path.join(temp_dir, shapefile_name)
                # Create a DataSource from the Shapefile bytes
                ds = DataSource(shapefile_path)

                # Assuming there's only one layer in the Shapefile, you can access it like this
                layer = ds[0]

                geojson_data = {
                    "type": "FeatureCollection",
                    # Convert the layer to GeoJSON
                    "features": GeoConverter.layer_to_geojson(layer),
                }

                return json.dumps(geojson_data)
            else:
                print("Shapefile not found in the ZIP archive.")
        except Exception as e:
            print(f"Error: {e}")

        return None

    @staticmethod
    def layer_to_geojson(layer):
        geojson_features = []
        for feature in layer:
            # Convert the feature to a GeoJSON feature
            geojson_feature = {
                "type": "Feature",
                "properties": {field_name: feature.get(field_name) for field_name in layer.fields},
                "geometry": json.loads(feature.geom.geojson),
            }
            geojson_features.append(geojson_feature)

        return geojson_features
