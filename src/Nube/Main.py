import os

from Utils import load_variable_categories, load_abstracts
from AbstractProcessor import AbstractProcessor
from CoOccurrenceMatrix import CoOccurrenceMatrix
from CoWordApp import CoWordApp
from WordCloudApp import WordCloudApp
import threading

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

def main():
    try:
        categories = load_variable_categories("variables.csv")
        abstracts = load_abstracts(encontrar_archivo('src/Parsing/output/unificados.bib'))

        processor = AbstractProcessor(categories)
        processor.process_abstracts(abstracts)
        frequency = processor.get_frequency()

        co_matrix = CoOccurrenceMatrix()
        co_matrix.process_abstracts(abstracts, categories)

        # Ejecutar ambas interfaces (una por vez o simultáneas)
        threading.Thread(target=lambda: CoWordApp(co_matrix.get_matrix()).mainloop()).start()
        threading.Thread(target=lambda: WordCloudApp(frequency.get_frequencies()).mainloop()).start()

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()