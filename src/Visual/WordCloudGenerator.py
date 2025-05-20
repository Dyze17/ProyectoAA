import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import os
import colorsys

# Deshabilitar la creación de UI en Matplotlib para entornos headless/GUI de Tkinter
plt.switch_backend('Agg')


# La función generate_distinct_colors se puede mantener tal cual o renombrar a _internal
# si solo se usa aquí. Por ahora, la dejamos como está.
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
    def __init__(self, nodes_csv_path, status_callback, category_colors=None):
        """
        Inicializa el generador de la nube de palabras.
        :param nodes_csv_path: Ruta al archivo CSV con los datos de los términos.
        :param status_callback: Función para reportar el estado a la GUI.
        :param category_colors: Diccionario opcional de colores para las categorías.
        """
        self.nodes_csv_path = nodes_csv_path
        self.df = None
        self.category_colors = category_colors
        self.status_callback = status_callback

    def load_data(self):
        """Carga los datos desde el archivo CSV."""
        if not os.path.exists(self.nodes_csv_path):
            self.status_callback(f"WordCloudGenerator: No se encuentra el archivo de nodos: {self.nodes_csv_path}")
            return False
        try:
            self.df = pd.read_csv(self.nodes_csv_path)
            if self.df.empty:
                self.status_callback(f"WordCloudGenerator: El archivo de nodos {self.nodes_csv_path} está vacío.")
                return False
            self.status_callback(
                f"WordCloudGenerator: Datos cargados desde {os.path.basename(self.nodes_csv_path)} ({len(self.df)} filas).")
            return True
        except pd.errors.EmptyDataError:
            self.status_callback(
                f"WordCloudGenerator: El archivo de nodos {self.nodes_csv_path} está vacío o no es un CSV válido.")
            return False
        except Exception as e:
            self.status_callback(f"WordCloudGenerator: Error cargando datos de nodos: {e}")
            return False

    def generate_word_cloud(self, output_image_path):
        """Genera una nube de palabras a partir de los términos más frecuentes, usando colores de categorías."""
        if self.df is None or self.df.empty:
            self.status_callback(
                "WordCloudGenerator: No se han cargado datos o están vacíos. No se puede generar la nube.")
            return

        required_cols = ['Frequency', 'Label', 'Category']  # Asegurar que Category también esté para la lógica de color
        if not all(col in self.df.columns for col in required_cols):
            self.status_callback(
                f"WordCloudGenerator: El archivo CSV no contiene las columnas necesarias ({', '.join(required_cols)}).")
            return

        # Filtrar filas donde 'Label' o 'Frequency' puedan ser NaN, o Frequency <=0
        self.df.dropna(subset=['Label', 'Frequency'], inplace=True)
        self.df = self.df[self.df['Frequency'] > 0]

        if self.df.empty:
            self.status_callback("WordCloudGenerator: No hay términos con frecuencia válida después del filtrado.")
            return

        # Creamos un diccionario con los términos y su frecuencia
        # Asegurarse de que no haya duplicados en 'Label' antes de set_index, o manejarlo
        if self.df['Label'].duplicated().any():
            self.status_callback(
                "WordCloudGenerator: Advertencia - Se encontraron etiquetas (Label) duplicadas. Usando la primera ocurrencia para frecuencia.")
            # Podrías agrupar y sumar frecuencias si las etiquetas duplicadas deben combinarse
            # terms_df = self.df.groupby('Label')['Frequency'].sum()
            # terms = terms_df.to_dict()
            # O, para mantener la lógica original de solo tomar la frecuencia de la primera aparición:
            temp_df = self.df.drop_duplicates(subset=['Label'], keep='first')
            terms = temp_df.set_index('Label')['Frequency'].to_dict()
        else:
            terms = self.df.set_index('Label')['Frequency'].to_dict()

        if not terms:
            self.status_callback(
                "WordCloudGenerator: No hay términos para generar la nube después de crear el diccionario de frecuencias.")
            return

        # Lógica para colores (tu lógica original)
        # Si se proporcionan colores de categoría, se usan; si no, se generan.
        # Esto requiere que la columna 'Category' exista.
        final_term_colors = {}  # Para la función color_func de WordCloud
        color_map_for_wordcloud = "viridis"  # Default colormap si no se usan colores por categoría

        if 'Category' in self.df.columns:
            # Crear un mapa de término a color
            if self.category_colors:  # Si se pasaron colores predefinidos
                # Asegurarse que self.df tenga la categoría para cada término en `terms`
                # Esto podría ser un poco ineficiente si se hace por cada término en un bucle grande.
                # Es mejor construir un mapa de Label -> Category primero.
                label_to_category_map = self.df.drop_duplicates(subset=['Label']).set_index('Label')[
                    'Category'].to_dict()
                for term_label in terms.keys():
                    category = label_to_category_map.get(term_label)
                    if category:
                        final_term_colors[term_label] = self.category_colors.get(str(category),
                                                                                 '#999999')  # Gris por defecto
                    else:
                        final_term_colors[term_label] = '#999999'
            else:  # Generar colores si no se pasaron
                unique_categories = self.df['Category'].dropna().astype(str).unique()
                if len(unique_categories) > 0:
                    generated_cat_colors = generate_distinct_colors(len(unique_categories))
                    category_to_color_map = dict(zip(unique_categories, generated_cat_colors))

                    label_to_category_map = self.df.drop_duplicates(subset=['Label']).set_index('Label')[
                        'Category'].astype(str).to_dict()
                    for term_label in terms.keys():
                        category = label_to_category_map.get(term_label)
                        if category:
                            final_term_colors[term_label] = category_to_color_map.get(category, '#999999')
                        else:
                            final_term_colors[term_label] = '#999999'
                else:  # No hay categorías válidas
                    for term_label in terms.keys():
                        final_term_colors[term_label] = '#999999'  # Todo gris

            # Función para asignar color a cada palabra en la nube
            # La API de WordCloud puede usar color_func o colormap.
            # Si queremos colores específicos por palabra basados en categoría, color_func es más directo.
            # La lógica original usaba colormap, pero la intención parece ser colorear por categoría.
            # Si tu intención era usar un colormap general y no colores por categoría,
            # puedes quitar la lógica de final_term_colors y solo pasar colormap.
            # Vamos a intentar usar color_func si tenemos final_term_colors.

            # Modificación: La librería wordcloud no toma un diccionario de colores directamente.
            # Usa una función `color_func`.
            # O, si queremos mantener `colormap="viridis"` como en tu original, entonces
            # la lógica de `category_colors` y `term_colors` no se usaría para colorear la nube,
            # sino quizás para una leyenda externa si la necesitaras.
            # Tu código original tiene: `colormap="viridis"`.generate_from_frequencies(terms)
            # Y luego intenta usar term_colors, lo cual no es como funciona la API directamente.

            # Opción 1: Mantener colormap="viridis" (tu código original)
            # En este caso, la lógica de category_colors no se usaría para el coloreado de la nube.
            # wordcloud_instance = WordCloud(width=1200, height=600, background_color="white",
            #                               colormap="viridis").generate_from_frequencies(terms)

            # Opción 2: Colorear por categoría usando color_func
            # Esto requiere una función que WordCloud llamará para cada palabra.
            def category_color_func(word, **kwargs):
                return final_term_colors.get(word, "#999999")  # Devuelve el color para la palabra

            if final_term_colors:  # Si logramos mapear colores a términos
                wordcloud_instance = WordCloud(width=1200, height=600, background_color="white",
                                               color_func=category_color_func).generate_from_frequencies(terms)
                self.status_callback("WordCloudGenerator: Usando colores por categoría para la nube de palabras.")
            else:  # Fallback a colormap si no hay colores de categoría
                wordcloud_instance = WordCloud(width=1200, height=600, background_color="white",
                                               colormap="viridis").generate_from_frequencies(terms)
                self.status_callback(
                    "WordCloudGenerator: No se pudieron determinar colores por categoría, usando colormap viridis.")

        else:  # No hay columna 'Category'
            self.status_callback(
                "WordCloudGenerator: No se encontró la columna 'Category'. Usando colormap viridis por defecto.")
            wordcloud_instance = WordCloud(width=1200, height=600, background_color="white",
                                           colormap="viridis").generate_from_frequencies(terms)

        plt.figure(figsize=(12, 6))  # Ajustar tamaño
        plt.imshow(wordcloud_instance, interpolation="bilinear")
        plt.axis("off")
        plt.title("Nube de Palabras de Términos Frecuentes", fontsize=16)  # Título más descriptivo
        plt.tight_layout(pad=0)  # Ajustar padding

        try:
            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
            wordcloud_instance.to_file(output_image_path)
            self.status_callback(f"WordCloudGenerator: Nube de palabras guardada en: {output_image_path}")
        except Exception as e:
            self.status_callback(f"WordCloudGenerator: Error al guardar la imagen de la nube de palabras: {e}")
        finally:
            plt.close()  # Cerrar la figura para liberar memoria


# --- Función principal para llamar desde gui_controller ---
def run_wordcloud_generator(status_callback, project_root_dir):
    status_callback("Iniciando WordCloudGenerator...")

    nodes_file_input = os.path.join(project_root_dir, "output", "data_normalizer", "keyword_nodes.csv")
    output_visual_dir = os.path.join(project_root_dir, "output", "visual")
    os.makedirs(output_visual_dir, exist_ok=True)
    output_image = os.path.join(output_visual_dir, "WordCloud_Terms.png")  # Nombre de archivo de salida

    # En este punto, no estamos pasando `category_colors` predefinidos,
    # así que el generador usará su propia lógica para crearlos si es necesario,
    # o usará el colormap por defecto si la columna Category no está o está vacía.
    generator = WordCloudGenerator(nodes_csv_path=nodes_file_input, status_callback=status_callback)

    if generator.load_data():
        generator.generate_word_cloud(output_image_path=output_image)
    else:
        status_callback(
            "WordCloudGenerator: No se pudo generar la nube de palabras debido a problemas con los datos de entrada.")

    status_callback("WordCloudGenerator completado.")