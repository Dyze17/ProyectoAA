import bibtexparser
import os
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode


def _load_bibtex_file_internal(file_path, status_callback):
    try:
        with open(file_path, encoding='utf-8') as bibtex_file:
            parser = BibTexParser()
            parser.customization = convert_to_unicode
            parser.ignore_errors = True  # Ignorar errores menores en archivos BibTeX
            bib_database = bibtexparser.load(bibtex_file, parser=parser)
            return bib_database.entries
    except Exception as e:
        status_callback(f"Parser: Error al cargar {file_path}: {str(e)}")
        return []


def _find_bib_files_internal(data_root_dir, status_callback):
    bib_files = []
    status_callback(f"Parser: Buscando archivos .bib/.bibtex en: {os.path.abspath(data_root_dir)}")

    if not os.path.exists(data_root_dir):
        status_callback(f"Parser: El directorio de datos {data_root_dir} no existe.")
        return bib_files

    for root, _, files in os.walk(data_root_dir):
        for file in files:
            if file.lower().endswith(('.bib', '.bibtex')):
                full_path = os.path.join(root, file)
                bib_files.append(full_path)
                status_callback(f"Parser: Archivo encontrado: {os.path.basename(full_path)}")

    if not bib_files:
        status_callback(f"Parser: No se encontraron archivos .bib o .bibtex en {data_root_dir}")
    return bib_files


def _save_bib_internal(entries, filename, output_dir, status_callback):
    if not entries:
        status_callback(f"Parser: No hay entradas para guardar en {filename}")
        return

    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)

    try:
        db = bibtexparser.bibdatabase.BibDatabase()
        db.entries = entries
        writer = bibtexparser.bwriter.BibTexWriter()
        writer.indent = '  '  # Para mejor legibilidad
        writer.comma_first = False
        with open(file_path, 'w', encoding='utf-8') as bibfile:
            bibfile.write(writer.write(db))
        status_callback(f"Parser: Archivo guardado: {file_path} ({len(entries)} entradas)")
    except Exception as e:
        status_callback(f"Parser: Error al guardar {file_path}: {str(e)}")


def run_parser(status_callback, project_root_dir):
    status_callback("Iniciando Parser...")

    data_dir = os.path.join(project_root_dir, "data")
    output_parsing_dir = os.path.join(project_root_dir, "output", "parsing")
    os.makedirs(output_parsing_dir, exist_ok=True)

    bibtex_files = _find_bib_files_internal(data_dir, status_callback)

    if not bibtex_files:
        status_callback(
            "Parser: No se encontraron archivos BibTeX para procesar. Asegúrate de que los archivos .bib estén en la carpeta 'data'.")
        status_callback("Parser completado (sin archivos).")
        return

    all_entries = []
    for file_path in bibtex_files:
        status_callback(f"Parser: Procesando: {os.path.basename(file_path)}")
        entries = _load_bibtex_file_internal(file_path, status_callback)
        all_entries.extend(entries)
        status_callback(f"Parser: {len(entries)} entradas cargadas desde {os.path.basename(file_path)}.")

    status_callback(f"Parser: Total de registros cargados: {len(all_entries)}")
    if not all_entries:
        status_callback("Parser: No se cargaron entradas. Verifique los archivos BibTeX.")
        status_callback("Parser completado (sin entradas).")
        return

    seen_titles = set()
    unique_entries = []
    duplicate_entries = []

    for entry in all_entries:
        title = entry.get('title', '').strip().lower()
        # Un ID único podría ser mejor si está disponible (ej. DOI)
        # entry_id = entry.get('ID', title) # Usar ID si existe, sino título
        if title and title in seen_titles:  # Solo considerar duplicados si hay título
            duplicate_entries.append(entry)
        else:
            if title:  # Añadir a seen_titles solo si hay título
                seen_titles.add(title)
            unique_entries.append(entry)  # Añadir todas las entradas a unique_entries, incluso las sin título

    status_callback(f"Parser: Registros únicos (o sin título): {len(unique_entries)}")
    status_callback(f"Parser: Registros duplicados (basado en título): {len(duplicate_entries)}")

    _save_bib_internal(unique_entries, 'unificados.bib', output_parsing_dir, status_callback)
    _save_bib_internal(duplicate_entries, 'duplicados.bib', output_parsing_dir, status_callback)

    status_callback("Parser completado.")