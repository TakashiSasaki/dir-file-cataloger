# filename get_file_metadata.py

import os
import datetime
import sys

def get_ntfs_timestamp(dt):
    """
    Convert a datetime object to an NTFS timestamp in 100-nanosecond intervals since 1601-01-01.
    """
    ntfs_epoch = datetime.datetime(1601, 1, 1, tzinfo=datetime.UTC)
    delta = dt - ntfs_epoch
    ntfs_timestamp = int(delta.total_seconds() * 10**7)
    return ntfs_timestamp

def get_file_metadata(path):
    """
    Get metadata for a given file or directory using standard Python methods.
    """
    try:
        stats = os.stat(path)
        absolute_path = os.path.abspath(path)

        # Use st_birthtime for file creation time if available, fallback to st_ctime otherwise
        if hasattr(stats, 'st_birthtime'):
            creation_time = stats.st_birthtime
        else:
            creation_time = stats.st_ctime  # Fallback for systems without st_birthtime

        metadata = {
            'Filename': absolute_path,
            'Size': stats.st_size,
            'Date Modified': get_ntfs_timestamp(datetime.datetime.fromtimestamp(stats.st_mtime, datetime.UTC)),
            'Date Created': get_ntfs_timestamp(datetime.datetime.fromtimestamp(creation_time, datetime.UTC)),
            'Attributes': stats.st_mode
        }
        return metadata
    except OSError as e:
        print(f"Error retrieving metadata for {path}: {e}", file=sys.stderr)
        return None
