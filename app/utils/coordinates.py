from pyproj import Transformer


def convert_polygon_to_latlng(coordinates):
    """
    Convert polygon cooordinates like this [[[121125.385, 488125.808],[121114.701, 488135.926]]] to a classic lat and lng.
    Converting EPSG::28992 (Dutch RD New) to EPSG:4326 (WGS84)
    """
    transformer = Transformer.from_crs("EPSG:28992", "EPSG:4326")

    x, y = coordinates[0][0]

    lat, lng = transformer.transform(x, y)

    return lat, lng
