import os
import csv
import sys
import networkx as nx
import matplotlib.pyplot as plt
from get_file_metadata_windows import get_file_metadata_windows  # Windows-specific function
from get_file_metadata import get_file_metadata  # Standard Python function

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

def visualize_graph(graph):
    """
    Visualize the directory structure graph using matplotlib and networkx with reduced edge crossings.
    Only directories are visualized. Node labels are the last segment of the path.
    """
    plt.figure(figsize=(12, 8))
    
    try:
        # Use planar layout if the graph is planar, else fallback
        if nx.check_planarity(graph)[0]:
            pos = nx.planar_layout(graph)
        else:
            # Fallback to a layout with reduced crossings (requires pygraphviz)
            pos = nx.nx_agraph.graphviz_layout(graph, prog='dot')
    except Exception as e:
        print(f"Failed to use preferred layout: {e}. Falling back to spring layout.", file=sys.stderr)
        pos = nx.spring_layout(graph)  # Fallback to spring layout
    
    # Extract the last segment of the path for labels
    labels = {node: os.path.basename(node) for node in graph.nodes()}
    nx.draw(graph, pos, labels=labels, with_labels=True, node_size=50, font_size=8, arrows=True)
    plt.title("Directory Structure Visualization with Reduced Edge Crossings")
    plt.show()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scan directories and collect file metadata.")
    parser.add_argument('path', type=str, nargs='?', help='The base directory to start scanning from.')
    parser.add_argument('--output', type=str, default='output.csv', help='The output CSV file.')
    parser.add_argument('--max-count', type=int, help='Maximum number of entries to collect.')
    parser.add_argument('-w', '--windows', action='store_true', help='Use Windows API to fetch NTFS file attributes and timestamps.')
    parser.add_argument('--visualize', action='store_true', help='Visualize the directory structure as a graph.')

    args = parser.parse_args()

    # Check if path argument is provided
    if not args.path:
        print("Error: No base path provided for traversal.", file=sys.stderr)
        sys.exit(1)

    # Scan the directory and collect metadata into a graph with an optional max count
    graph = scan_directory(args.path, max_count=args.max_count, use_windows=args.windows)

    # Write the collected metadata from the graph to a CSV file
    write_to_csv(graph, args.output)

    # Visualize the graph if the --visualize option is specified
    if args.visualize:
        visualize_graph(graph)
