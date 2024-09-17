import os
import csv
import datetime
import sys

#filename: scan_directory.py

def get_file_metadata(path):
    """
    Get metadata for a given file or directory.
    """
    stats = os.stat(path)
    # Normalize path to use the OS-specific directory separator
    normalized_path = os.path.normpath(path)
    metadata = {
        'Filename': normalized_path,
        'Size': stats.st_size,
        'Date Modified': datetime.datetime.fromtimestamp(stats.st_mtime, datetime.UTC).isoformat(),
        'Date Created': datetime.datetime.fromtimestamp(stats.st_ctime, datetime.UTC).isoformat(),
        'Attributes': stats.st_mode  # Simplified attributes; refine as needed
    }
    return metadata

def scan_directory(base_path):
    """
    Traverse the directory tree starting at base_path, collecting file metadata.
    Returns a list of metadata dictionaries.
    """
    all_metadata = []
    count = 0
    max_count = 10  # Limit the output to 10 items for testing

    # Print the traversal starting point to stderr
    print(f"Starting traversal at: {os.path.normpath(base_path)}", file=sys.stderr)

    # Walk through all directories and files starting from base_path
    for root, dirs, files in os.walk(base_path):
        for name in files:
            file_path = os.path.join(root, name)
            metadata = get_file_metadata(file_path)
            all_metadata.append(metadata)
            count += 1
            if count >= max_count:
                break
        if count >= max_count:
            break
        for name in dirs:
            dir_path = os.path.join(root, name)
            metadata = get_file_metadata(dir_path)
            all_metadata.append(metadata)
            count += 1
            if count >= max_count:
                break
        if count >= max_count:
            break

    return all_metadata

def write_to_csv(metadata_list, output_file='output.csv'):
    """
    Write a list of metadata dictionaries to a CSV file.
    """
    fieldnames = ['Filename', 'Size', 'Date Modified', 'Date Created', 'Attributes']
    
    # Open CSV file and write header manually
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csvfile.write(','.join(fieldnames) + '\n')
        
        # Use DictWriter to write data rows with quotes
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        for data in metadata_list:
            writer.writerow(data)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scan directories and collect file metadata.")
    parser.add_argument('path', type=str, nargs='?', help='The base directory to start scanning from.')
    parser.add_argument('--output', type=str, default='output.csv', help='The output CSV file.')

    args = parser.parse_args()

    # Check if path argument is provided
    if not args.path:
        print("Error: No base path provided for traversal.", file=sys.stderr)
        sys.exit(1)

    # Scan the directory and collect metadata
    metadata = scan_directory(args.path)

    # Write the collected metadata to a CSV file
    write_to_csv(metadata, args.output)
