def get_column_names(feature_collection):
    first_feature = feature_collection['features'][0]
    properties = first_feature['properties']
    column_names = list(properties.keys())
    return column_names