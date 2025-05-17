import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

class BarGrapher:
    def __init__(self, nodes_csv_path="output/keyword_nodes.csv"):
        self.nodes_csv_path = nodes_csv_path
        self.df = None

    def load_data(self):
        if not os.path.exists(self.nodes_csv_path):
            print(f"❌ No se encuentra el archivo: {self.nodes_csv_path}")
            return False
        self.df = pd.read_csv(self.nodes_csv_path)
        return True

    def plot_top_terms_by_category(self, top_n=20, output_path="output/BarGraphCategory.png"):
        if self.df is None:
            print("⚠️ No se han cargado datos. Ejecuta load_data() primero.")
            return

        top_df = self.df.sort_values(by="Frequency", ascending=False).head(top_n)

        plt.figure(figsize=(12, 7))
        sns.barplot(
            data=top_df,
            y="Label",
            x="Frequency",
            hue="Category",
            dodge=False,
            palette="Set3"
        )

        plt.xlabel("Frecuencia")
        plt.ylabel("Término")
        plt.title(f"Top {top_n} términos más frecuentes por categoría")
        plt.legend(title="Categoría", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(output_path)
        print(f"📊 Gráfico guardado en: {output_path}")

# --- Bloque principal para autoejecución ---
if __name__ == "__main__":
    print("🔍 Iniciando BarGrapher...")
    grapher = BarGrapher()
    if grapher.load_data():
        grapher.plot_top_terms_by_category(top_n=20)
    else:
        print("❌ No se pudo generar el gráfico. Verifica el archivo CSV.")
