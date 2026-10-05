"""Great-circle distance between two points on the globe."""
import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in kilometres.

    Coarse on purpose: the geography data's coordinates are region centroids, not
    ports, so this is a reach ESTIMATE, the same spirit as everything else in
    this file being an order-of-magnitude model rather than a survey.
    """
    earth_radius_km = 6371.0
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    angular_term = (math.sin(dphi / 2) ** 2
                    + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlmb / 2) ** 2)
    return 2 * earth_radius_km * math.asin(math.sqrt(angular_term))
