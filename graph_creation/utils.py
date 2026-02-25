import os
from typing import Optional


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
