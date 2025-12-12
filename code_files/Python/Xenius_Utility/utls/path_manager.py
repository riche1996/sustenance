
import os
from pathlib import Path


def safe_join(base_dir, *paths):
    """
    Join two or more pathname components, safely.

    This function joins the base_dir with one or more paths and returns the normalized and absolute
    path of the resulting pathname. If the resulting path is not a subdirectory of the base_dir, a
    ValueError is raised.

    Parameters:
    base_dir (str): The base directory path.
    *paths (str): One or more path components to join with the base directory.

    Returns:
    str: The normalized and absolute path of the resulting pathname.

    Raises:
    ValueError: If the resulting path is not a subdirectory of the base_dir.
    """
    full_path = os.path.normpath(Path(base_dir, *paths))
    resolved_path = os.path.abspath(full_path)

    if not resolved_path.startswith(os.path.abspath(base_dir)):
        raise ValueError("Access to this path is not allowed")

    return full_path


def safe_relpath(file_path, base_dir):
    """
    Return the relative path of a file from a base directory, ensuring that the resulting path is
    safe and does not allow access to files outside the base directory.

    Parameters:
    file_path (str): The path of the file to get the relative path for.
    base_dir (str): The base directory to get the relative path from.

    Returns:
    str: The relative path of the file from the base directory.

    Raises:
    ValueError: If the resulting path is outside the base directory.
    """
    full_path = os.path.normpath(Path(base_dir, file_path))
    resolved_path = os.path.abspath(full_path)
    base_dir = os.path.abspath(base_dir)

    if not resolved_path.startswith(base_dir + os.sep):
        raise ValueError("Access to this path is not allowed")

    relative_path = Path(file_path).relative_to(base_dir)
    return str(relative_path)
