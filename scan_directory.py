import os
import csv
import sys
import networkx as nx
from get_file_metadata_windows import get_file_metadata_windows  # Import the Windows-specific function
from get_file_metadata import get_file_metadata

# filename: scan_directory.py

def scan_directory(base_path, max_count=None, use_windows=False):
    """
    Traverse the directory tree starting at base_path, collecting file metadata into a graph.
    Returns a NetworkX DiGraph representing the file system structure.
    """
    graph = nx.DiGraph()
    count = 0

    # Select the appropriate metadata function
    get_metadata = get_file_metadata_windows if use_windows else get_file_metadata

    # Print the traversal starting point to stderr
    print(f"Starting traversal at: {os.path.abspath(base_path)}", file=sys.stderr)

    # Walk through all directories and files starting from base_path
    for root, dirs, files in os.walk(base_path):
        root_node = os.path.abspath(root)
        metadata = get_metadata(root_node)
        if metadata:
            graph.add_node(root_node, **metadata)
        
        # Add files in the current directory to the graph
        for name in files:
            file_path = os.path.join(root, name)
            metadata = get_metadata(file_path)
            if metadata:
                graph.add_node(os.path.abspath(file_path), **metadata)
                graph.add_edge(root_node, os.path.abspath(file_path))
            count += 1
            if max_count is not None and count >= max_count:
                return graph

        # Add subdirectories in the current directory to the graph
        for name in dirs:
            dir_path = os.path.join(root, name)
            metadata = get_metadata(dir_path)
            if metadata:
                graph.add_node(os.path.abspath(dir_path), **metadata)
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
    parser.add_argument('-w', '--windows', action='store_true', help='Use Windows API to fetch NTFS file attributes and timestamps.')

    args = parser.parse_args()

    # Check if path argument is provided
    if not args.path:
        print("Error: No base path provided for traversal.", file=sys.stderr)
        sys.exit(1)

    # Scan the directory and collect metadata into a graph with an optional max count
    graph = scan_directory(args.path, max_count=args.max_count, use_windows=args.windows)

    # Write the collected metadata from the graph to a CSV file
    write_to_csv(graph, args.output)
