import tkinter as tk
from tkinter import ttk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class CoWordApp(tk.Tk):
    def __init__(self, co_matrix):
        super().__init__()
        self.title("Red de Co-Ocurrencia de Palabras Clave")
        self.geometry("1000x800")

        self.graph_frame = ttk.Frame(self)
        self.graph_frame.pack(fill=tk.BOTH, expand=True)

        self._draw_graph(co_matrix)

    def _draw_graph(self, co_matrix):
        G = nx.Graph()

        for term1, neighbors in co_matrix.items():
            for term2, weight in neighbors.items():
                if term1 != term2 and weight > 0:
                    G.add_edge(term1, term2, weight=weight)

        pos = nx.spring_layout(G, seed=42)
        fig, ax = plt.subplots(figsize=(12, 10))
        nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color='gray', node_size=2000, font_size=10, ax=ax)

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
