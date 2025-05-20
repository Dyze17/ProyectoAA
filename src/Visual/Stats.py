import bibtexparser
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os

plt.switch_backend('Agg')


def _bib_to_dataframe_internal(bib_file, status_callback):
    if not os.path.exists(bib_file):
        status_callback(f"Stats: Error - No se encontró el archivo BibTeX unificado: {bib_file}")
        return pd.DataFrame()
    try:
        with open(bib_file, encoding='utf-8') as bibtex_file:
            parser = bibtexparser.bparser.BibTexParser()
            parser.customization = bibtexparser.customization.convert_to_unicode
            parser.ignore_errors = True
            bib_database = bibtexparser.load(bibtex_file, parser=parser)
            df = pd.DataFrame(bib_database.entries)
            status_callback(f"Stats: Archivo {os.path.basename(bib_file)} cargado, {len(df)} registros.")
            return df
    except Exception as e:
        status_callback(f"Stats: Error al cargar {bib_file}: {str(e)}")
        return pd.DataFrame()


def _graficar_top_columna_internal(df, columna, titulo, nombre_archivo_salida, status_callback, top_n=15):
    if columna not in df.columns or df[columna].isnull().all():
        status_callback(f"Stats: La columna '{columna}' no existe o está vacía. No se generará el gráfico '{titulo}'.")
        return

    try:
        # Limpiar valores NaN antes de contar y tomar el top N
        top_valores = df[columna].dropna().value_counts().nlargest(top_n)
        if top_valores.empty:
            status_callback(f"Stats: No hay datos suficientes en la columna '{columna}' para el gráfico '{titulo}'.")
            return

        plt.figure(figsize=(12, 7))  # Ajustado para mejor legibilidad
        ax = sns.barplot(y=top_valores.index.astype(str), x=top_valores.values,
                         palette="crest")  # Astype(str) para y-axis
        plt.title(titulo, fontsize=14)
        plt.xlabel('Número de publicaciones', fontsize=12)
        plt.ylabel(columna.capitalize(), fontsize=12)
        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10)

        # Añadir etiquetas de valor a las barras
        for i, v in enumerate(top_valores.values):
            ax.text(v + 0.2, i, str(v), color='black', va='center', fontsize=9)

        plt.tight_layout()
        os.makedirs(os.path.dirname(nombre_archivo_salida), exist_ok=True)
        plt.savefig(nombre_archivo_salida, dpi=150)
        plt.close()
        status_callback(f"Stats: Gráfico guardado: {nombre_archivo_salida}")
    except Exception as e:
        status_callback(f"Stats: Error generando gráfico para columna '{columna}': {e}")
        import traceback
        status_callback(traceback.format_exc())


def run_stats(status_callback, project_root_dir):
    status_callback("Iniciando Generador de Estadísticas...")

    bib_file_input = os.path.join(project_root_dir, "output", "parsing", "unificados.bib")
    output_visual_dir = os.path.join(project_root_dir, "output", "visual")
    os.makedirs(output_visual_dir, exist_ok=True)

    df = _bib_to_dataframe_internal(bib_file_input, status_callback)

    if df.empty:
        status_callback("Stats: No hay datos para generar estadísticas.")
        status_callback("Stats completado (sin datos).")
        return

    # Top Autores (primer autor)
    if 'author' in df.columns:
        df_autores = df[['author']].dropna().copy()
        # Extraer solo el primer autor de forma más robusta
        df_autores['primer_autor'] = df_autores['author'].apply(
            lambda x: x.split(' and ')[0].strip() if pd.notnull(x) and ' and ' in x else str(x).strip())
        _graficar_top_columna_internal(
            df_autores, 'primer_autor', 'Top 15 Autores (Primer Autor)',
            os.path.join(output_visual_dir, 'stats_top_primeros_autores.png'), status_callback
        )

    # Publicaciones por Año y Tipo
    if 'ENTRYTYPE' in df.columns and 'year' in df.columns:
        df_tipo_año = df[['ENTRYTYPE', 'year']].dropna().copy()
        df_tipo_año = df_tipo_año[df_tipo_año['year'].astype(str).str.match(r'^\d{4}$')]  # Años de 4 dígitos
        if not df_tipo_año.empty:
            df_tipo_año['year'] = df_tipo_año['year'].astype(int)

            # Filtrar años dentro de un rango razonable si es necesario (ej. 1980-año actual)
            current_year = pd.Timestamp.now().year
            df_tipo_año = df_tipo_año[(df_tipo_año['year'] >= 1980) & (df_tipo_año['year'] <= current_year)]

            if not df_tipo_año.empty:
                orden_anios = sorted(df_tipo_año['year'].unique())
                plt.figure(figsize=(14, 7))
                sns.countplot(data=df_tipo_año, x='year', hue='ENTRYTYPE', order=orden_anios, palette="viridis")
                plt.title("Número de publicaciones por año y tipo", fontsize=14)
                plt.xlabel("Año", fontsize=12)
                plt.ylabel("Cantidad", fontsize=12)
                plt.xticks(rotation=45, ha="right", fontsize=10)
                plt.yticks(fontsize=10)
                plt.legend(title="Tipo", fontsize=10)
                plt.tight_layout()
                plt.savefig(os.path.join(output_visual_dir, 'stats_publicaciones_por_año_tipo.png'), dpi=150)
                plt.close()
                status_callback(f"Stats: Gráfico guardado: stats_publicaciones_por_año_tipo.png")
            else:
                status_callback(
                    "Stats: No hay datos de año/tipo válidos después del filtrado para el gráfico de publicaciones.")
        else:
            status_callback("Stats: No hay datos de año/tipo para el gráfico de publicaciones.")

    # Distribución por Tipo
    if 'ENTRYTYPE' in df.columns:
        _graficar_top_columna_internal(df, 'ENTRYTYPE', 'Distribución por Tipo de Producto',
                                       os.path.join(output_visual_dir, 'stats_tipo_producto.png'), status_callback)
    # Top Journals
    if 'journal' in df.columns:
        _graficar_top_columna_internal(df, 'journal', 'Top 15 Journals',
                                       os.path.join(output_visual_dir, 'stats_top_journals.png'), status_callback)
    # Top Publishers
    if 'publisher' in df.columns:
        _graficar_top_columna_internal(df, 'publisher', 'Top 15 Publishers',
                                       os.path.join(output_visual_dir, 'stats_top_publishers.png'), status_callback)

    status_callback("Stats completado.")