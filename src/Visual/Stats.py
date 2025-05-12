import bibtexparser
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os


# Determinar la ruta correcta del archivo
def encontrar_archivo(ruta_base='src/Parsing/output/unificados.bib'):
    posibles_rutas = [
        ruta_base,  # La ruta especificada
        'output/unificados.bib',  # En la carpeta output local
        '../output/unificados.bib',  # Un nivel arriba
        'src/output/unificados.bib',  # En src/output
        '../src/Parsing/output/unificados.bib',  # Un nivel arriba, luego src/Parsing/output
        '../../src/Parsing/output/unificados.bib',  # Dos niveles arriba
    ]

    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            print(f" Archivo encontrado en: {os.path.abspath(ruta)}")
            return ruta

    # Si no se encuentra, mostrar mensaje de error
    print(" No se encontró el archivo en ninguna de estas ubicaciones:")
    for ruta in posibles_rutas:
        print(f"  - {os.path.abspath(ruta)}")

    # Buscar recursivamente
    print("\nBuscando archivo recursivamente en el proyecto...")
    for root, dirs, files in os.walk('.'):
        if 'unificados.bib' in files:
            ruta_encontrada = os.path.join(root, 'unificados.bib')
            print(f" Archivo encontrado en: {os.path.abspath(ruta_encontrada)}")
            return ruta_encontrada

    # Si aún no se encuentra, usar la ruta original
    print(f" No se encontró el archivo unificados.bib en ninguna parte. Se usará la ruta original: {ruta_base}")
    return ruta_base

# Cargar archivo unificado
def bib_to_dataframe(bib_file):
    try:
        with open(bib_file, encoding='utf-8') as bibtex_file:
            parser = bibtexparser.bparser.BibTexParser()
            parser.customization = bibtexparser.customization.convert_to_unicode
            bib_database = bibtexparser.load(bibtex_file, parser=parser)
            return pd.DataFrame(bib_database.entries)
    except FileNotFoundError:
        print(f" Error: No se encontró el archivo {bib_file}")
        print(f"   Directorio actual: {os.path.abspath('.')}")
        raise
    except Exception as e:
        print(f" Error al cargar {bib_file}: {str(e)}")
        raise


def graficar_top_columna(df, columna, titulo, nombre_archivo, top_n=15):
    top_valores = df[columna].value_counts().head(top_n)
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(y=top_valores.index, x=top_valores.values)
    plt.title(titulo, fontsize=14)
    plt.xlabel('Número de publicaciones')
    plt.ylabel(columna.capitalize())

    for i, v in enumerate(top_valores.values):
        ax.text(v + 0.1, i, str(v), va='center')

    plt.tight_layout()
    output_path = os.path.join('output', nombre_archivo)
    plt.savefig(output_path, dpi=300)
    print(f"✓ Gráfico guardado: {os.path.abspath(output_path)}")
    plt.show()


def main():
    print("=" * 80)
    print("ANÁLISIS DE DATOS BIBLIOGRÁFICOS")
    print("=" * 80)

    bib_file = encontrar_archivo()
    df = bib_to_dataframe(bib_file)
    print(f"\nArchivo cargado correctamente. Registros: {len(df)}")

    # Separar todos los autores en filas individuales
    if 'author' in df.columns:
        df_autores = df[['author']].dropna().copy()
        df_autores['primer_autor'] = df_autores['author'].str.split(' and ').str[0].str.strip()

        graficar_top_columna(
            df_autores,
            'primer_autor',
            'Top 15 autores con más apariciones (primer autor)',
            'top_primeros_autores.png'
        )

    # Estadísticas por tipo y año
    if 'ENTRYTYPE' in df.columns and 'year' in df.columns:
        df_tipo_año = df[['ENTRYTYPE', 'year']].dropna().copy()

        # Convertir año a entero y filtrar los que realmente son numéricos
        df_tipo_año = df_tipo_año[df_tipo_año['year'].astype(str).str.isdigit()]
        df_tipo_año['year'] = df_tipo_año['year'].astype(int)

        # Ordenar años
        orden_anios = sorted(df_tipo_año['year'].unique())

        plt.figure(figsize=(14, 6))
        sns.countplot(data=df_tipo_año, x='year', hue='ENTRYTYPE', order=orden_anios)
        plt.title("Número de publicaciones por año y tipo de producto")
        plt.xlabel("Año")
        plt.ylabel("Cantidad")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('output/publicaciones_por_año_tipo.png', dpi=300)
        print("✓ Gráfico guardado: output/publicaciones_por_año_tipo.png")
        plt.show()

    # Distribución por tipo
    if 'ENTRYTYPE' in df.columns:
        graficar_top_columna(df, 'ENTRYTYPE', 'Distribución por tipo de producto', 'tipo_producto.png')

    # Top 15 journals
    if 'journal' in df.columns:
        graficar_top_columna(df, 'journal', 'Top 15 journals con más apariciones', 'top_journals.png')

    # Top 15 publishers
    if 'publisher' in df.columns:
        graficar_top_columna(df, 'publisher', 'Top 15 publishers con más apariciones', 'top_publishers.png')

if __name__ == "__main__":
    main()