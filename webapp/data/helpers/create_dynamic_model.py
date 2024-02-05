from django.contrib.gis.db import models

def create_dynamic_model(column_names):
    class_name = 'DynamicGeoJSONModel'
    attrs = {'__module__': __name__}
    for column_name in column_names:
        attrs[column_name] = models.CharField(max_length=255)  # Adjust field type as needed
    dynamic_model = type(class_name, (models.Model,), attrs)
    return dynamic_model