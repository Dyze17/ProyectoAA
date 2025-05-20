import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import os
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


class WordCloudGenerator:
    def __init__(self, nodes_csv_path="output/keyword_nodes.csv", category_colors=None):
        """
        Inicializa el generador de la nube de palabras.
        :param nodes_csv_path: Ruta al archivo CSV con los datos de los términos.
        :param category_colors: Diccionario de colores para las categorías (para usar los mismos colores que en otros gráficos).
        """
        self.nodes_csv_path = nodes_csv_path
        self.df = None
        self.category_colors = category_colors  # Usaremos los colores pasados para la consistencia

    def load_data(self):
        """Carga los datos desde el archivo CSV."""
        if not os.path.exists(self.nodes_csv_path):
            print(f"❌ No se encuentra el archivo: {self.nodes_csv_path}")
            return False
        self.df = pd.read_csv(self.nodes_csv_path)
        return True

    def generate_word_cloud(self, output_image_path="output/wordcloud.png"):
        """Genera una nube de palabras a partir de los términos más frecuentes, usando colores de categorías."""
        if self.df is None:
            print("⚠️ No se han cargado datos. Ejecuta load_data() primero.")
            return

        # Filtramos las filas para asegurarnos de que tengamos términos y frecuencias
        if 'Frequency' not in self.df.columns or 'Label' not in self.df.columns:
            print("❌ El archivo CSV no contiene las columnas necesarias ('Frequency', 'Label').")
            return

        # Creamos un diccionario con los términos y su frecuencia
        terms = self.df.set_index('Label')['Frequency'].to_dict()

        # Si ya tenemos los colores de las categorías (pasados desde otros gráficos), los usamos
        if self.category_colors:
            # Mapear colores a los términos basados en su categoría
            term_colors = {
                term: self.category_colors.get(self.df[self.df['Label'] == term]['Category'].iloc[0], '#999999')
                for term in terms}
        else:
            # Si no se pasan colores, generamos los colores
            categories = self.df['Category'].unique()
            category_colors = generate_distinct_colors(len(categories))  # Generamos colores para las categorías
            category_to_color = dict(zip(categories, category_colors))

            # Mapear colores a los términos basados en su categoría
            term_colors = {term: category_to_color.get(self.df[self.df['Label'] == term]['Category'].iloc[0], '#999999')
                           for term in terms}

        # Creamos la nube de palabras
        wordcloud = WordCloud(width=800, height=400, background_color="white",
                              colormap="viridis").generate_from_frequencies(terms)

        # Mostramos la nube de palabras
        plt.figure(figsize=(10, 7))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")  # Quitamos los ejes
        plt.title("Nube de Palabras", fontsize=20)
        plt.tight_layout()

        # Guardamos la imagen como PNG
        try:
            wordcloud.to_file(output_image_path)
            print(f"📊 Nube de palabras guardada en: {output_image_path}")
        except Exception as e:
            print(f"❌ Error al guardar la imagen: {e}")


# --- Bloque principal para autoejecución ---
if __name__ == "__main__":
    print("🔍 Iniciando WordCloudGenerator...")

    # Asumimos que los colores de las categorías ya se generaron en otro gráfico
    category_colors = {
        'Category1': '#ff6347',  # Tomado de algún gráfico anterior
        'Category2': '#4682b4',
        'Category3': '#32cd32',
        # Agregar aquí todos los colores generados
    }

    generator = WordCloudGenerator(category_colors=category_colors)
    if generator.load_data():
        generator.generate_word_cloud(output_image_path="output/wordcloud.png")
    else:
        print("❌ No se pudo generar la nube de palabras. Verifica el archivo CSV.")
