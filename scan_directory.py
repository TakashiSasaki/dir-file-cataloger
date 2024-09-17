import os
import csv
import datetime
import sys
import networkx as nx

# Filename: scan_directory.py

def get_ntfs_timestamp(dt):
    """
    Convert a datetime object to an NTFS timestamp in 100-nanosecond intervals since 1601-01-01.
    """
    # Define the NTFS epoch start date
    ntfs_epoch = datetime.datetime(1601, 1, 1, tzinfo=datetime.UTC)
    # Calculate the difference between the datetime and the NTFS epoch
    delta = dt - ntfs_epoch
    # Convert the difference to 100-nanosecond intervals
    ntfs_timestamp = int(delta.total_seconds() * 10**7)
    return ntfs_timestamp

def get_file_metadata(path):
    """
    Get metadata for a given file or directory.
    """
    stats = os.stat(path)
    # Convert path to absolute path and normalize to use the OS-specific directory separator
    absolute_path = os.path.abspath(path)
    metadata = {
        'Filename': absolute_path,
        'Size': stats.st_size,
        'Date Modified': get_ntfs_timestamp(datetime.datetime.fromtimestamp(stats.st_mtime, datetime.UTC)),
        'Date Created': get_ntfs_timestamp(datetime.datetime.fromtimestamp(stats.st_ctime, datetime.UTC)),
        'Attributes': stats.st_mode  # Simplified attributes; refine as needed
    }
    return metadata

def scan_directory(base_path, max_count=None):
    """
    Traverse the directory tree starting at base_path, collecting file metadata into a graph.
    Returns a NetworkX DiGraph representing the file system structure.
    """
    graph = nx.DiGraph()
    count = 0

    # Print the traversal starting point to stderr
    print(f"Starting traversal at: {os.path.abspath(base_path)}", file=sys.stderr)

    # Walk through all directories and files starting from base_path
    for root, dirs, files in os.walk(base_path):
        root_node = os.path.abspath(root)
        graph.add_node(root_node, **get_file_metadata(root_node))
        
        # Add files in the current directory to the graph
        for name in files:
            file_path = os.path.join(root, name)
            graph.add_node(os.path.abspath(file_path), **get_file_metadata(file_path))
            graph.add_edge(root_node, os.path.abspath(file_path))
            count += 1
            if max_count is not None and count >= max_count:
                return graph

        # Add subdirectories in the current directory to the graph
        for name in dirs:
            dir_path = os.path.join(root, name)
            graph.add_node(os.path.abspath(dir_path), **get_file_metadata(dir_path))
            graph.add_edge(root_node, os.path.abspath(dir_path))
            count += 1
            if max_count is not None and count >= max_count:
                return graph

    return graph

def write_to_csv(graph, output_file='output.csv'):
    """
    Write a graph of metadata dictionaries to a CSV file.
    """
    fieldnames = ['Filename', 'Size', 'Date Modified', 'Date Created', 'Attributes']
    
    # Open CSV file and write header manually
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csvfile.write(','.join(fieldnames) + '\n')
        
        # Use DictWriter to write data rows without quoting numeric fields
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
        for node, data in graph.nodes(data=True):
            writer.writerow(data)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scan directories and collect file metadata.")
    parser.add_argument('path', type=str, nargs='?', help='The base directory to start scanning from.')
    parser.add_argument('--output', type=str, default='output.csv', help='The output CSV file.')
    parser.add_argument('--max-count', type=int, help='Maximum number of entries to collect.')

    args = parser.parse_args()

    # Check if path argument is provided
    if not args.path:
        print("Error: No base path provided for traversal.", file=sys.stderr)
        sys.exit(1)

    # Scan the directory and collect metadata into a graph with an optional max count
    graph = scan_directory(args.path, max_count=args.max_count)

    # Write the collected metadata from the graph to a CSV file
    write_to_csv(graph, args.output)
