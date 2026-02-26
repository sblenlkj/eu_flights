import os
import math
from typing import Optional


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in kilometers between two points using Haversine formula."""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return round(R * c, 2)


def build_output_path(file_name: str, default_ext: str = '', postfix: Optional[str] = None, out_dir: str = 'data') -> str:
    """Create and return an output path inside `./{out_dir}`.

    - Ensures `./{out_dir}` exists.
    - Uses only the basename of `file_name`.
    - Adds `default_ext` if `file_name` has no extension.
    - Inserts `postfix` before the extension if provided.
    """

    base_name = os.path.basename(file_name)
    base, ext = os.path.splitext(base_name)

    if ext == '' and default_ext:
        ext = default_ext

    post = postfix or ''
    out_name = f"{base}{post}{ext}"

    dir_path = os.path.join('.', out_dir)
    os.makedirs(dir_path, exist_ok=True)

    return os.path.join(dir_path, out_name)
