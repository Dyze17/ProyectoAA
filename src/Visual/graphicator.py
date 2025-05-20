import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import colorsys

plt.switch_backend('Agg')

def _generate_distinct_colors_internal(n, status_callback):
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

def _create_static_graph_internal(nodes_csv_path, edges_csv_path, output_image_path, status_callback):
    status_callback(f"Leyendo nodos desde: {nodes_csv_path}")
    try:
        nodes_df_original = pd.read_csv(nodes_csv_path)
    except Exception as e:
        status_callback(f"Error leyendo nodos: {e}")
        return False

    status_callback(f"Leyendo aristas desde: {edges_csv_path}")
    try:
        edges_df_original = pd.read_csv(edges_csv_path)
    except:
        edges_df_original = pd.DataFrame(columns=['Source', 'Target', 'Weight'])
        status_callback("Advertencia: No se pudo leer el archivo de aristas. Se continuará sin aristas.")

    if nodes_df_original.empty:
        status_callback("El archivo de nodos está vacío.")
        return False

    if 'Category' in nodes_df_original.columns:
        nodes_df = nodes_df_original[nodes_df_original['Category'] != 'Uncategorized'].copy()
        if nodes_df.empty:
            status_callback("Todos los nodos fueron filtrados por 'Uncategorized'. Grafo vacío.")
            plt.figure(figsize=(10, 10))
            plt.text(0.5, 0.5, 'No categorized nodes to display', ha='center', va='center', fontsize=16)
            plt.axis('off')
            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
            plt.savefig(output_image_path, format="png", dpi=100)
            plt.close()
            return True
    else:
        nodes_df = nodes_df_original.copy()

    valid_node_ids = set(nodes_df['Id'].astype(str))
    edges_df = edges_df_original[edges_df_original['Source'].astype(str).isin(valid_node_ids) &
                                 edges_df_original['Target'].astype(str).isin(valid_node_ids)].copy()

    g = nx.Graph()
    node_colors = []
    category_legend_map = {}

    if 'Category' in nodes_df.columns and not nodes_df.empty:
        unique_categories = sorted(nodes_df['Category'].unique())
        color_map = _generate_distinct_colors_internal(len(unique_categories), status_callback)
        category_to_color = dict(zip(unique_categories, color_map))
        node_colors = [category_to_color.get(cat, '#999999') for cat in nodes_df['Category']]
        category_legend_map = category_to_color
    else:
        node_colors = ['#999999'] * len(nodes_df)

    min_size = 50
    max_size = 2000
    if 'Frequency' in nodes_df.columns:
        frequencies = nodes_df['Frequency'].fillna(nodes_df['Frequency'].min())
        min_freq = frequencies.min()
        max_freq = frequencies.max()
        if max_freq != min_freq:
            node_sizes = min_size + ((frequencies - min_freq) / (max_freq - min_freq)) * (max_size - min_size)
        else:
            node_sizes = [(min_size + max_size) / 2] * len(frequencies)
    else:
        node_sizes = [min_size] * len(nodes_df)

    for _, row in nodes_df.iterrows():
        node_id = str(row['Id'])
        g.add_node(node_id,
                   label=str(row.get('Label', node_id)),
                   category=row.get('Category', 'Uncategorized'),
                   frequency=row.get('Frequency', 0))

    min_width = 0.5
    max_width = 5.0
    if 'Weight' in edges_df.columns:
        weights = edges_df['Weight'].fillna(edges_df['Weight'].min())
        min_w = weights.min()
        max_w = weights.max()
        if max_w != min_w:
            edge_widths = min_width + ((weights - min_w) / (max_w - min_w)) * (max_width - min_width)
        else:
            edge_widths = [(min_width + max_width) / 2] * len(weights)
    else:
        edge_widths = [min_width] * len(edges_df)

    for _, row in edges_df.iterrows():
        g.add_edge(str(row['Source']), str(row['Target']), weight=row.get('Weight', 1))

    if not list(g.nodes()):
        status_callback("No hay nodos para graficar.")
        return True

    status_callback("Calculando layout del grafo (Kamada-Kawai)...")
    try:
        pos = nx.kamada_kawai_layout(g)
    except Exception as e:
        status_callback(f"Error en layout: {e}")
        pos = nx.random_layout(g)

    status_callback("Dibujando grafo...")
    plt.figure(figsize=(25, 25))

    nx.draw_networkx_nodes(g, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9)
    if list(g.edges()):
        nx.draw_networkx_edges(g, pos, width=edge_widths, alpha=0.3, edge_color='grey')

    nx.draw_networkx_labels(g, pos, font_size=6, font_family="sans-serif")
    plt.title("Grafico de co-word", size=20)
    plt.axis('off')

    if category_legend_map:
        legend_handles = [plt.Line2D([0], [0], marker='o', color='w', label=cat,
                                     markersize=10, markerfacecolor=color) for cat, color in category_legend_map.items()]
        plt.legend(handles=legend_handles, title="Categorias", loc="best", frameon=True, fontsize=10)

    os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
    plt.savefig(output_image_path, format="png", dpi=300, bbox_inches="tight")
    plt.close()
    status_callback(f"Grafo guardado en: {output_image_path}")
    return True

def run_graphicator(status_callback, project_root_dir):
    status_callback("Ejecutando Graphicator...")

    nodes_path = os.path.join(project_root_dir, "output", "data_normalizer", "keyword_nodes.csv")
    edges_path = os.path.join(project_root_dir, "output", "data_normalizer", "keyword_edges.csv")
    output_path = os.path.join(project_root_dir, "output", "visual", "CoWordGraph.png")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    success = _create_static_graph_internal(nodes_path, edges_path, output_path, status_callback)
    if success:
        status_callback("Graphicator finalizado correctamente.")
    else:
        status_callback("Graphicator terminado con errores.")