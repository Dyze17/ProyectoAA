import bibtexparser
import os
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

def load_bibtex_file(file_path):
    try:
        with open(file_path, encoding='utf-8') as bibtex_file:
            parser = BibTexParser()
            parser.customization = convert_to_unicode
            bib_database = bibtexparser.load(bibtex_file, parser=parser)
            return bib_database.entries
    except Exception as e:
        print(f"Error al cargar {file_path}: {str(e)}")
        return []


# Función para encontrar todos los archivos .bib recursivamente
def find_bib_files(root_dir):
    bib_files = []
    print(f"Buscando archivos .bib/.bibtex en: {os.path.abspath(root_dir)}")

    # Verifica si el directorio existe
    if not os.path.exists(root_dir):
        print(f"  El directorio {root_dir} no existe")
        return bib_files

    # Comprobar todos los tipos de archivos encontrados para depuración
    all_files = []
    for root, dirs, files in os.walk(root_dir):
        print(f"  • Explorando: {root}")
        print(f"    - Subcarpetas ({len(dirs)}): {', '.join(dirs) if len(dirs) <= 5 else f'{len(dirs)} carpetas'}")
        print(f"    - Archivos ({len(files)}): {', '.join(files) if len(files) <= 5 else f'{len(files)} archivos'}")

        for file in files:
            all_files.append(os.path.join(root, file))
            if file.lower().endswith(('.bib', '.bibtex')):
                full_path = os.path.join(root, file)
                bib_files.append(full_path)
                print(f"    Archivo encontrado: {os.path.basename(full_path)}")

    if not bib_files:
        print(f"  ✗ No se encontraron archivos .bib o .bibtex")
        extensions = {}
        for f in all_files:
            ext = os.path.splitext(f)[1].lower()
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1
        if extensions:
            print(
                f"    - Extensiones encontradas: {', '.join([f'{ext} ({count})' for ext, count in extensions.items()])}")
    else:
        print(f"  Total encontrados: {len(bib_files)} archivos")

    return bib_files


# Directorio raíz donde buscar archivos .bib
# Considerando la estructura del proyecto: ProyectoAA/data y ProyectoAA/src
# Si el script está en src/Parsing o src/cualquier_carpeta, necesitamos subir dos niveles para llegar a "data"

# Obtener la ruta absoluta del script actual
current_script_path = os.path.abspath(__file__)
print(f"Ruta del script actual: {current_script_path}")

# Determinar posibles ubicaciones para la carpeta data
script_dir = os.path.dirname(current_script_path)
print(f"Directorio del script: {script_dir}")

# Si estamos en src/Parsing o similar, determinamos la ruta correcta
possible_data_dirs = [
    "data",  # Si ejecutamos desde la raíz
    "../data",  # Si ejecutamos desde src
    "../../data",  # Si ejecutamos desde src/Parsing o similar
    os.path.join(os.path.dirname(script_dir), "data"),  # Subir un nivel desde src
    os.path.join(os.path.dirname(os.path.dirname(script_dir)), "data")  # Subir dos niveles desde src/Parsing
]

# Intentar encontrar explícitamente la carpeta ProyectoAA/data
current_dir = os.path.abspath('.')
while os.path.basename(current_dir) and os.path.basename(
        current_dir) != "ProyectoAA" and current_dir != os.path.dirname(current_dir):
    current_dir = os.path.dirname(current_dir)

if os.path.basename(current_dir) == "ProyectoAA":
    print(f"¡Encontrada carpeta raíz del proyecto en: {current_dir}!")
    proyecto_data_dir = os.path.join(current_dir, "data")
    possible_data_dirs.insert(0, proyecto_data_dir)  # Priorizar esta ruta

# Encontrar todos los archivos .bib
# Intentar con diferentes rutas relativas en caso de que el script se ejecute desde otra ubicación
print("\nBuscando archivos .bib o .bibtex en posibles ubicaciones:")
for i, possible_dir in enumerate(possible_data_dirs):
    print("Buscando en: {possible_dir}")
    if os.path.exists(possible_dir):
        print(f"  La ruta existe: {os.path.abspath(possible_dir)}")
        found_files = find_bib_files(possible_dir)
        if found_files:
            print(f"  Se encontraron {len(found_files)} archivos en {possible_dir}")
            bibtex_files = found_files
            break
    else:
        print(f"  La ruta no existe: {possible_dir}")

print(f"\nTotal de archivos .bib/.bibtex encontrados: {len(bibtex_files)}")

# Si no se encontraron archivos, buscar ambas extensiones
if not bibtex_files:
    print("\nBuscando específicamente archivos con extensión .bibtex...")
    for possible_dir in possible_data_dirs:
        if os.path.exists(possible_dir):
            print(f"Revisando {possible_dir} para archivos .bibtex...")
            for root, dirs, files in os.walk(possible_dir):
                for file in files:
                    if file.lower().endswith('.bibtex'):
                        full_path = os.path.join(root, file)
                        bibtex_files.append(full_path)
                        print(f"  ✓ Archivo .bibtex encontrado: {full_path}")

print(f"\nArchivos encontrados para procesar: {len(bibtex_files)}")

# Unificar entradas de todos los archivos
all_entries = []
if bibtex_files:
    for file in bibtex_files:
        print(f"Procesando: {file}")
        entries = load_bibtex_file(file)
        all_entries.extend(entries)
        print(f"  - Entradas cargadas: {len(entries)}")
else:
    print("\n¡ATENCIÓN! No se encontró ningún archivo para procesar.")

print(f"Total de registros cargados: {len(all_entries)}")

# Detectar duplicados por título (puedes mejorar esto luego usando similitud)
seen_titles = set()
unique_entries = []
duplicate_entries = []

for entry in all_entries:
    title = entry.get('title', '').strip().lower()
    if title in seen_titles:
        duplicate_entries.append(entry)
    else:
        seen_titles.add(title)
        unique_entries.append(entry)

print(f"Registros únicos: {len(unique_entries)}")
print(f"Registros duplicados: {len(duplicate_entries)}")


# Guardar resultados
def save_bib(entries, filename, output_dir='output'):
    """
    Guarda las entradas BibTeX en un archivo dentro de la carpeta especificada

    Args:
        entries: Lista de entradas BibTeX
        filename: Nombre del archivo a guardar
        output_dir: Directorio donde guardar el archivo (relativo al script)
    """
    if not entries:
        print(f" No hay entradas para guardar en {filename}")
        return

    # Crear el directorio de salida si no existe
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"  Directorio creado: {output_dir}")
        except Exception as e:
            print(f"  Error al crear directorio {output_dir}: {str(e)}")
            return

    # Ruta completa del archivo
    file_path = os.path.join(output_dir, filename)

    # Guardar el archivo
    try:
        db = bibtexparser.bibdatabase.BibDatabase()
        db.entries = entries
        writer = bibtexparser.bwriter.BibTexWriter()
        with open(file_path, 'w', encoding='utf-8') as bibfile:
            bibfile.write(writer.write(db))
        print(f"  Archivo guardado: {file_path}")
    except Exception as e:
        print(f"  Error al guardar {file_path}: {str(e)}")


# Solo guardar archivos si se encontraron entradas
if all_entries:
    save_bib(unique_entries, 'unificados.bib')
    save_bib(duplicate_entries, 'duplicados.bib')
    print("\nProceso completado con éxito.")
else:
    print("\nNo se generaron archivos de salida porque no se encontraron entradas.")