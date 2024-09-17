# filename: get_file_metadata_windows.py

import os
import sys
import ctypes
from ctypes import wintypes
import datetime

# Windows API functions and constants
GetFileAttributes = ctypes.windll.kernel32.GetFileAttributesW
GetFileAttributes.argtypes = [wintypes.LPCWSTR]
GetFileAttributes.restype = wintypes.DWORD

CreateFile = ctypes.windll.kernel32.CreateFileW
CreateFile.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
CreateFile.restype = wintypes.HANDLE

GetFileTime = ctypes.windll.kernel32.GetFileTime
GetFileTime.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME)]
GetFileTime.restype = wintypes.BOOL

CloseHandle = ctypes.windll.kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
OPEN_EXISTING = 3

def filetime_to_int(filetime):
    """
    Convert FILETIME structure to a 100-nanosecond interval integer since 1601-01-01.
    """
    return (filetime.dwHighDateTime << 32) + filetime.dwLowDateTime

def get_ntfs_timestamp_from_filetime(filetime):
    """
    Convert FILETIME to NTFS timestamp (100-nanosecond intervals since 1601-01-01).
    """
    return filetime_to_int(filetime)

def get_ntfs_timestamp(dt):
    """
    Convert a datetime object to an NTFS timestamp in 100-nanosecond intervals since 1601-01-01.
    """
    ntfs_epoch = datetime.datetime(1601, 1, 1, tzinfo=datetime.UTC)
    delta = dt - ntfs_epoch
    ntfs_timestamp = int(delta.total_seconds() * 10**7)
    return ntfs_timestamp

def get_file_metadata_windows(path):
    """
    Get metadata for a given file or directory using Windows API to fetch NTFS file attributes and timestamps.
    Falls back to standard Python methods if Windows API fails.
    """
    try:
        absolute_path = os.path.abspath(path)

        # Get NTFS attributes using Windows API
        attrs = GetFileAttributes(absolute_path)
        if attrs == -1:
            raise OSError(f"Failed to get attributes for {absolute_path}")

        # Open the file to retrieve file times
        handle = CreateFile(absolute_path, GENERIC_READ, FILE_SHARE_READ, None, OPEN_EXISTING, attrs, None)
        if handle == wintypes.HANDLE(-1).value:
            raise OSError(f"Failed to open file for getting timestamps: {absolute_path}")

        # Prepare FILETIME structures for creation, access, and write times
        creation_time = wintypes.FILETIME()
        access_time = wintypes.FILETIME()
        write_time = wintypes.FILETIME()

        # Get file times
        if not GetFileTime(handle, ctypes.byref(creation_time), ctypes.byref(access_time), ctypes.byref(write_time)):
            CloseHandle(handle)
            raise OSError(f"Failed to get file times for {absolute_path}")

        # Close the file handle
        CloseHandle(handle)

        metadata = {
            'Filename': absolute_path,
            'Size': os.path.getsize(absolute_path),
            'Date Modified': get_ntfs_timestamp_from_filetime(write_time),
            'Date Created': get_ntfs_timestamp_from_filetime(creation_time),
            'Attributes': attrs
        }
        return metadata
    except OSError as e:
        print(f"Error retrieving metadata for {path} using Windows API: {e}", file=sys.stderr)
        # Fallback to standard Python method
        try:
            stats = os.stat(path)
            
            # Use st_birthtime if available, otherwise fallback to st_ctime
            if hasattr(stats, 'st_birthtime'):
                creation_time = stats.st_birthtime
            else:
                creation_time = stats.st_ctime

            metadata = {
                'Filename': absolute_path,
                'Size': stats.st_size,
                'Date Modified': get_ntfs_timestamp(datetime.datetime.fromtimestamp(stats.st_mtime, datetime.UTC)),
                'Date Created': get_ntfs_timestamp(datetime.datetime.fromtimestamp(creation_time, datetime.UTC)),
                'Attributes': stats.st_mode
            }
            return metadata
        except OSError as e:
            print(f"Error retrieving metadata for {path} using standard methods: {e}", file=sys.stderr)
            return None
