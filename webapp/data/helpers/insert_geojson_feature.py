from django.contrib.gis.geos import GEOSGeometry
import json

from django.db import connections


def insert_geojson_features(feature_collection, dynamic_model):
    features = feature_collection['features']
    records = []

    for feature in features:
        properties = feature['properties']
        record = dynamic_model()
        for column_name, value in properties.items():
            setattr(record, column_name, value)
        geometry = feature['geometry']
        record.geom = GEOSGeometry(json.dumps(geometry))
        records.append(record)

    dynamic_model.objects.bulk_create(records)
