import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Deshabilitar la creación de UI en Matplotlib para entornos headless/GUI de Tkinter
plt.switch_backend('Agg')


class BarGrapher:
    def __init__(self, nodes_csv_path, status_callback):
        self.nodes_csv_path = nodes_csv_path
        self.status_callback = status_callback
        self.df = None

    def load_data(self):
        if not os.path.exists(self.nodes_csv_path):
            self.status_callback(f"BarGrapher: No se encuentra el archivo de nodos: {self.nodes_csv_path}")
            return False
        try:
            self.df = pd.read_csv(self.nodes_csv_path)
            if self.df.empty:
                self.status_callback(f"BarGrapher: El archivo de nodos {self.nodes_csv_path} está vacío.")
                return False
            self.status_callback(
                f"BarGrapher: Datos de nodos cargados desde {self.nodes_csv_path} ({len(self.df)} filas).")
            return True
        except pd.errors.EmptyDataError:
            self.status_callback(
                f"BarGrapher: El archivo de nodos {self.nodes_csv_path} está vacío o no es un CSV válido.")
            return False
        except Exception as e:
            self.status_callback(f"BarGrapher: Error cargando datos de nodos: {e}")
            return False

    def plot_top_terms_by_category(self, output_image_path, top_n=20):
        if self.df is None or self.df.empty:
            self.status_callback("BarGrapher: No hay datos cargados o están vacíos. No se puede generar el gráfico.")
            return

        # Verificar columnas necesarias
        required_cols = ["Frequency", "Label", "Category"]
        if not all(col in self.df.columns for col in required_cols):
            self.status_callback(
                f"BarGrapher: Faltan columnas requeridas en el CSV de nodos ({', '.join(required_cols)}).")
            return

        try:
            top_df = self.df.sort_values(by="Frequency", ascending=False).head(top_n)

            if top_df.empty:
                self.status_callback("BarGrapher: No hay datos suficientes para el top N solicitado.")
                return

            plt.figure(figsize=(14, 9))  # Ajustar tamaño para mejor visualización
            sns.barplot(
                data=top_df,
                y="Label",
                x="Frequency",
                hue="Category",
                dodge=False,  # Si quieres barras apiladas por categoría (si tiene sentido) o separadas
                palette="viridis"  # Cambiar paleta de colores
            )

            plt.xlabel("Frecuencia", fontsize=12)
            plt.ylabel("Término", fontsize=12)
            plt.title(f"Top {top_n} términos más frecuentes por categoría", fontsize=14)
            plt.xticks(fontsize=10)
            plt.yticks(fontsize=10)  # Ajustar tamaño de etiquetas de los ejes
            plt.legend(title="Categoría", bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)
            plt.tight_layout(rect=[0, 0, 0.85, 1])  # Ajustar layout para que la leyenda no se corte

            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
            plt.savefig(output_image_path, dpi=150)  # Ajustar DPI si es necesario
            plt.close()  # Cerrar la figura para liberar memoria
            self.status_callback(f"BarGrapher: Gráfico guardado en: {output_image_path}")

        except Exception as e:
            self.status_callback(f"BarGrapher: Error generando gráfico de barras: {e}")
            import traceback
            self.status_callback(traceback.format_exc())


def run_bargrapher(status_callback, project_root_dir):
    status_callback("Iniciando BarGrapher...")
    nodes_file = os.path.join(project_root_dir, "output", "data_normalizer", "keyword_nodes.csv")
    output_visual_dir = os.path.join(project_root_dir, "output", "visual")
    os.makedirs(output_visual_dir, exist_ok=True)
    output_image = os.path.join(output_visual_dir, "BarGraphCategory.png")

    grapher_instance = BarGrapher(nodes_file, status_callback)
    if grapher_instance.load_data():
        grapher_instance.plot_top_terms_by_category(output_image)
    else:
        status_callback("BarGrapher: ❌ No se pudo generar el gráfico de barras debido a problemas con los datos.")
    status_callback("BarGrapher completado.")