import os

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import colorsys


def generate_distinct_colors(n):
    """Generates n visually distinct HSV colors, then converts to hex."""
    hsv_colors = []
    for i in range(n):
        hue = i / n
        saturation = 0.85
        value = 0.85
        hsv_colors.append((hue, saturation, value))

    hex_colors = []
    for hsv in hsv_colors:
        rgb_float = colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2])
        hex_colors.append('#%02x%02x%02x' % (int(rgb_float[0] * 255), int(rgb_float[1] * 255), int(rgb_float[2] * 255)))
    return hex_colors


def create_static_graph(nodes_csv_path="keywords_nodes.csv",
                        edges_csv_path="keyword_edges.csv",
                        output_image_path="output/graph.png"):
    """
    Reads node and edge CSV files and creates a static image graph visualization,
    excluding nodes categorized as "Uncategorized".
    """
    print(f"Reading nodes from: {nodes_csv_path}")
    try:
        nodes_df_original = pd.read_csv(nodes_csv_path)
    except FileNotFoundError:
        print(f"Error: Nodes file not found at {nodes_csv_path}")
        return
    except Exception as e:
        print(f"Error reading nodes CSV: {e}")
        return

    print(f"Reading edges from: {edges_csv_path}")
    try:
        edges_df_original = pd.read_csv(edges_csv_path)
    except FileNotFoundError:
        print(f"Error: Edges file not found at {edges_csv_path}")
        return
    except Exception as e:
        print(f"Error reading edges CSV: {e}")
        return

    if nodes_df_original.empty:
        print("Original nodes dataframe is empty. Cannot create graph.")
        return

    # --- Filter out "Uncategorized" nodes ---
    if 'Category' in nodes_df_original.columns:
        nodes_df = nodes_df_original[nodes_df_original['Category'] != 'Uncategorized'].copy()
        num_filtered_out = len(nodes_df_original) - len(nodes_df)
        if num_filtered_out > 0:
            print(f"Filtered out {num_filtered_out} nodes that were 'Uncategorized'.")
        if nodes_df.empty:
            print(
                "All nodes were 'Uncategorized' or the nodes file was empty after filtering. No graph will be generated.")
            # Create an empty plot with a message
            plt.figure(figsize=(10, 10))
            plt.text(0.5, 0.5, 'No categorized nodes to display', ha='center', va='center', fontsize=16)
            plt.axis('off')
            try:
                plt.savefig(output_image_path, format="png", dpi=100)
                plt.close()
                print(f"Empty graph image saved to {output_image_path}")
            except Exception as e:
                print(f"Error saving empty graph image: {e}")
            return
    else:
        print(
            "Warning: 'Category' column not found in nodes CSV. Cannot filter by 'Uncategorized'. Proceeding with all nodes.")
        nodes_df = nodes_df_original.copy()

    # Create a set of valid node IDs from the filtered nodes_df for quick lookup
    valid_node_ids = set(nodes_df['Id'].astype(str))

    # --- Filter edges: only keep edges where both source and target nodes are in the filtered node list ---
    if not edges_df_original.empty:
        edges_df = edges_df_original[
            edges_df_original['Source'].astype(str).isin(valid_node_ids) & \
            edges_df_original['Target'].astype(str).isin(valid_node_ids)
            ].copy()
        num_edges_filtered_out = len(edges_df_original) - len(edges_df)
        if num_edges_filtered_out > 0:
            print(f"Filtered out {num_edges_filtered_out} edges connected to 'Uncategorized' or missing nodes.")
    else:
        edges_df = pd.DataFrame(columns=['Source', 'Target', 'Weight'])  # Empty dataframe if original was empty
        print("Original edges dataframe is empty.")

    # Create a NetworkX graph
    g = nx.Graph()

    # --- Process Categories and Assign Colors (using filtered nodes_df) ---
    node_colors_for_drawing = []
    category_legend_map = {}

    if 'Category' in nodes_df.columns and not nodes_df.empty:
        # Get categories only from the filtered nodes that will be drawn
        unique_categories = sorted(nodes_df['Category'].unique())
        if unique_categories:  # Check if there are any categories left
            generated_hex_colors = generate_distinct_colors(len(unique_categories))
            category_to_hex_color = {category: color for category, color in
                                     zip(unique_categories, generated_hex_colors)}

            for category, color_hex in category_to_hex_color.items():
                category_legend_map[category] = color_hex

            node_colors_for_drawing = [category_to_hex_color.get(cat, '#999999') for cat in nodes_df['Category']]
        else:  # All remaining nodes might somehow have no category if logic is flawed, or only one type
            node_colors_for_drawing = ['#999999'] * len(nodes_df)
    else:  # No 'Category' column or nodes_df is empty
        node_colors_for_drawing = ['#999999'] * len(nodes_df)

    # --- Node Sizes based on Frequency (using filtered nodes_df) ---
    min_node_size_mpl = 50
    max_node_size_mpl = 2000
    node_sizes_for_drawing = [min_node_size_mpl] * len(nodes_df)

    if 'Frequency' in nodes_df.columns and not nodes_df.empty:
        frequencies = nodes_df['Frequency'].fillna(nodes_df['Frequency'].min())
        min_freq = frequencies.min()
        max_freq = frequencies.max()
        if max_freq == min_freq or max_freq <= 0:
            node_sizes_for_drawing = [(min_node_size_mpl + max_node_size_mpl) / 2] * len(nodes_df)
        else:
            scaled_sizes = min_node_size_mpl + ((frequencies - min_freq) / (max_freq - min_freq)) * (
                        max_node_size_mpl - min_node_size_mpl)
            node_sizes_for_drawing = scaled_sizes.tolist()

    # Add filtered nodes to the NetworkX graph
    for i, row in nodes_df.iterrows():  # Iterate over the filtered nodes_df
        node_id = str(row['Id'])
        g.add_node(node_id,
                   label=str(row.get('Label', node_id)),
                   category=row.get('Category', 'Uncategorized'),  # Should not be 'Uncategorized' here
                   frequency=row.get('Frequency', 0))

    # --- Edge Widths based on Weight (using filtered edges_df) ---
    min_edge_width_mpl = 0.5
    max_edge_width_mpl = 5.0
    edge_widths_for_drawing = [min_edge_width_mpl] * len(edges_df)

    if 'Weight' in edges_df.columns and not edges_df.empty:
        weights = edges_df['Weight'].fillna(edges_df['Weight'].min())
        min_weight = weights.min()
        max_weight = weights.max()
        if max_weight == min_weight or max_weight <= 0:
            edge_widths_for_drawing = [(min_edge_width_mpl + max_edge_width_mpl) / 2] * len(edges_df)
        else:
            scaled_widths = min_edge_width_mpl + ((weights - min_weight) / (max_weight - min_weight)) * (
                        max_edge_width_mpl - min_edge_width_mpl)
            edge_widths_for_drawing = scaled_widths.tolist()

    # Add filtered edges to the NetworkX graph
    for i, row in edges_df.iterrows():  # Iterate over the filtered edges_df
        source = str(row['Source'])
        target = str(row['Target'])
        # Nodes should definitely exist due to prior filtering of edges_df
        g.add_edge(source, target, weight=row.get('Weight', 1))

    if not list(g.nodes()):
        print("Graph has no nodes after filtering. Cannot draw.")
        # The earlier check for nodes_df.empty after filtering should handle this, but as a safeguard:
        return

    print("Calculating layout for filtered graph... This might take a moment.")
    try:
        pos = nx.kamada_kawai_layout(g)
        # Or try spring layout:
        # pos = nx.spring_layout(g, k=0.3, iterations=75, seed=42) # Adjust k as needed
    except Exception as e:
        print(f"Layout calculation failed ({e}), falling back to random layout.")
        pos = nx.random_layout(g, seed=42)

    print("Drawing filtered graph...")
    plt.figure(figsize=(25, 25))  # Increased figure size

    nx.draw_networkx_nodes(g, pos,
                           node_size=node_sizes_for_drawing,
                           node_color=node_colors_for_drawing,
                           alpha=0.9)

    if list(g.edges()):  # Only draw edges if some exist after filtering
        nx.draw_networkx_edges(g, pos,
                               width=edge_widths_for_drawing,
                               alpha=0.3,
                               edge_color='grey')
    else:
        print("No edges to draw in the filtered graph.")

    # Consider reducing font size or selective labeling for clarity
    nx.draw_networkx_labels(g, pos, font_size=6, font_family="sans-serif")

    plt.title("Grafico de co-word", size=20)
    plt.axis('off')

    if category_legend_map:  # Only create legend if there are categories to show
        legend_handles = [plt.Line2D([0], [0], marker='o', color='w', label=category,
                                     markersize=10, markerfacecolor=color_hex)
                          for category, color_hex in category_legend_map.items()]
        plt.legend(handles=legend_handles, title="Categorias", loc="best", frameon=True, fontsize=10)

    print(f"Saving static graph to: {output_image_path}")
    try:
        plt.savefig(output_image_path, format="png", dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Graph saved successfully as {output_image_path}")
    except Exception as e:
        print(f"Error saving graph: {e}")


def encontrarArchivoCSV(ruta):
    """
    Attempts to find an input CSV file in common project directory structures.
    Searches in 'output/' subdirectories and directly within:
    1. Current script's directory.
    2. Parent of current script's directory.
    3. Grandparent of current script's directory (potential project root).
    4. Current Working Directory.
    Then searches recursively from the Current Working Directory.
    Returns the absolute path if found, otherwise None.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define potential base directories for search, relative to the script's location and CWD
    potential_base_dirs = [
        script_dir,  # Script's own directory
        os.path.abspath(os.path.join(script_dir, "..")),  # Parent directory (e.g., src/)
        os.path.abspath(os.path.join(script_dir, "..", "..")),  # Grandparent directory (e.g., project root)
        os.getcwd()  # Current working directory
    ]
    # Remove duplicates while preserving order (Python 3.7+)
    # For older Python, use a more verbose method if order is critical for precedence.
    unique_base_dirs = list(dict.fromkeys(potential_base_dirs))

    print(f"\nSearching for '{ruta}':")

    # Check predefined relative locations
    # First, check inside an 'output' subdirectory of these base dirs
    # Then, check directly inside these base dirs
    subdirs_to_check_first = ["output", "."]  # "." means the base_dir itself

    for base_dir in unique_base_dirs:
        for subdir_name in subdirs_to_check_first:
            path_to_try = os.path.join(base_dir, subdir_name, ruta)
            # print(f"  Checking: {os.path.abspath(path_to_try)}") # Uncomment for verbose searching
            if os.path.exists(path_to_try) and os.path.isfile(path_to_try):
                found_path = os.path.abspath(path_to_try)
                print(f"  SUCCESS: Found '{ruta}' at {found_path}")
                return found_path

    print(f"  INFO: '{ruta}' not found in common relative locations based on script path and CWD.")
    print(f"  Now searching recursively from current working directory: {os.getcwd()}")
    for root, dirs, files in os.walk('.'):  # os.walk('.') searches from CWD
        if ruta in files:
            found_path = os.path.abspath(os.path.join(root, ruta))
            # Optional: prioritize if found path contains 'output'
            # if "output" in found_path.lower():
            # print(f"  SUCCESS: Found '{ruta}' recursively (in 'output' like dir) at {found_path}")
            #    return found_path
            print(f"  SUCCESS: Found '{ruta}' recursively at {found_path}")
            return found_path  # Returns the first match from recursive search

    print(f"  ERROR: '{ruta}' could not be located automatically anywhere.")
    return None


# --- Main Execution ---
if __name__ == "__main__":
    nodes_file = encontrarArchivoCSV("src/Visual/output/keyword_nodes.csv")
    edges_file = encontrarArchivoCSV("src/Visual/output/keyword_edges.csv")
    output_file = "output/graph.png"

    create_static_graph(nodes_csv_path=nodes_file,
                        edges_csv_path=edges_file,
                        output_image_path=output_file)