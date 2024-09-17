import os
import csv
import datetime
import sys
import networkx as nx

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

def scan_directory(base_path, max_count=None):
    """
    Traverse the directory tree starting at base_path, collecting file metadata into a graph.
    Returns a NetworkX DiGraph representing the file system structure.
    """
    graph = nx.DiGraph()
    count = 0

    # Print the traversal starting point to stderr
    print(f"Starting traversal at: {os.path.normpath(base_path)}", file=sys.stderr)

    # Walk through all directories and files starting from base_path
    for root, dirs, files in os.walk(base_path):
        root_node = os.path.normpath(root)
        graph.add_node(root_node, **get_file_metadata(root_node))
        
        # Add files in the current directory to the graph
        for name in files:
            file_path = os.path.join(root, name)
            graph.add_node(file_path, **get_file_metadata(file_path))
            graph.add_edge(root_node, file_path)
            count += 1
            if max_count is not None and count >= max_count:
                return graph

        # Add subdirectories in the current directory to the graph
        for name in dirs:
            dir_path = os.path.join(root, name)
            graph.add_node(dir_path, **get_file_metadata(dir_path))
            graph.add_edge(root_node, dir_path)
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
        
        # Use DictWriter to write data rows with quotes
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
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
