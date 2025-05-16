import networkx as nx
import matplotlib.pyplot as plt
import random

class CoWordGraphView:
    def __init__(self, matrix, terms):
        self.matrix = matrix
        self.terms = terms
        self.node_positions = self._generate_positions()
        self.graph = self._create_graph()

    def _generate_positions(self):
        # Usa posiciones aleatorias (similar a Java) o puedes usar spring_layout como alternativa
        return {term: (random.uniform(0, 1), random.uniform(0, 1)) for term in self.terms}

    def _create_graph(self):
        G = nx.Graph()
        for term1, neighbors in self.matrix.items():
            for term2, weight in neighbors.items():
                if term1 != term2 and weight > 0:
                    G.add_edge(term1, term2, weight=weight)
        return G

    def draw_graph(self):
        pos = self.node_positions
        plt.figure(figsize=(12, 10))
        nx.draw(self.graph, pos, with_labels=True, node_color='skyblue',
                edge_color='gray', node_size=2000, font_size=10)
        plt.title("Red de Co-Ocurrencia de Palabras Clave")
        plt.show()
