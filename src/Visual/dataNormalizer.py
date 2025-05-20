import csv
import os
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import homogenize_latex_encoding, convert_to_unicode
from collections import Counter
from itertools import combinations
import re

# STOP_WORDS se mantiene igual que en tu script original

STOP_WORDS = {"a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if", "in", "into", "is", "it", "no",
              "not", "of", "on", "or", "such", "that", "the", "their", "then", "there", "these", "they", "this", "to",
              "was", "will", "with", "its", "we", "our", "ours", "you", "your", "he", "she", "him", "her", "has", "had",
              "have", "do", "does", "did", "can", "could", "may", "might", "must", "should", "would", "about", "above",
              "after", "again", "against", "all", "am", "any", "because", "been", "before", "being", "below", "between",
              "both", "during", "each", "few", "from", "further", "here", "how", "i", "just", "me", "more", "most",
              "my", "myself", "nor", "once", "only", "other", "ought", "ourselves", "out", "over", "own", "same", "so",
              "some", "still", "than", "that's", "themselves", "thence", "therefore", "through", "thus", "too", "under",
              "until", "up", "very", "what", "when", "where", "which", "while", "who", "whom", "why", "also", "however",
              "thereby", "therein", "thereof", "thereon", "thereto", "therewith", "hence", "thereafter", "whereas",
              "herein", "hereto", "hereafter", "hereby", "hereof", "hereon", "herewith", "therefor", "www", "com",
              "org", "edu", "gov", "net", "http", "https", "figure", "table", "chapter", "section", "appendix",
              "references", "introduction", "conclusion", "results", "discussion", "methods", "materials", "abstract",
              "keywords", "doi", "issn", "isbn"}


def _normalize_text_internal(text, for_search=True):
    if text is None:
        return ""
    processed_text = str(text).lower().strip()
    return processed_text


def _load_variables_and_categories_internal(variables_csv_path, status_callback):
    search_map = {}
    category_map = {}

    if not os.path.exists(variables_csv_path):
        status_callback(
            f"DataNormalizer: Error - Archivo de variables no encontrado: {variables_csv_path}. Debes crear 'variables.csv' en la raíz del proyecto.")
        return None, None, []

    try:
        with open(variables_csv_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            if 'Variable' not in reader.fieldnames or 'Categoria' not in reader.fieldnames:
                status_callback(
                    f"DataNormalizer: Error - El archivo '{variables_csv_path}' debe tener las columnas 'Variable' y 'Categoria'.")
                return None, None, []

            for row in reader:
                variable_original_case = row.get('Variable', '').strip()
                category_original_case = row.get('Categoria', '').strip()

                if not variable_original_case or not category_original_case:
                    continue

                canonical_name = variable_original_case
                category_map[canonical_name] = category_original_case
                parts = variable_original_case.split(" - ")
                main_phrase = _normalize_text_internal(parts[0])

                if main_phrase:
                    search_map[main_phrase] = canonical_name
                if len(parts) > 1:
                    acronym = _normalize_text_internal(parts[1])
                    if acronym:
                        search_map[acronym] = canonical_name
        status_callback(
            f"DataNormalizer: Cargadas {len(category_map)} variables desde '{os.path.basename(variables_csv_path)}'.")
    except Exception as e:
        status_callback(f"DataNormalizer: Error leyendo {variables_csv_path}: {e}")
        return None, None, []

    sorted_search_terms = sorted(search_map.keys(), key=len, reverse=True)
    return search_map, category_map, sorted_search_terms


def _process_bibtex_data_internal(bibtex_file_path, search_map, category_map, sorted_search_terms, status_callback):
    if not search_map or not category_map:
        status_callback(
            "DataNormalizer: Warning - El mapa de búsqueda o categorías está vacío. No se encontrarán términos.")
        return Counter(), {}, Counter()

    term_counts = Counter()
    term_categories = {}
    cooccurrence_counts = Counter()

    if not os.path.exists(bibtex_file_path):
        status_callback(f"DataNormalizer: Error - Archivo BibTeX unificado no encontrado: {bibtex_file_path}")
        return term_counts, term_categories, cooccurrence_counts

    try:
        with open(bibtex_file_path, 'r', encoding='utf-8') as bibfile:
            bibtex_string = bibfile.read()
            parser = BibTexParser()
            parser.customization = lambda record: convert_to_unicode(homogenize_latex_encoding(record))
            parser.ignore_errors = True
            bib_database = bibtexparser.loads(bibtex_string, parser)
    except Exception as e:
        status_callback(f"DataNormalizer: Error procesando BibTeX {bibtex_file_path}: {e}")
        return Counter(), {}, Counter()

    if not hasattr(bib_database, 'entries') or not bib_database.entries:
        status_callback(f"DataNormalizer: Warning - No se encontraron entradas en {bibtex_file_path}.")
        return Counter(), {}, Counter()

    total_entries_to_process = len(bib_database.entries)  # Guardar el total para usarlo en los mensajes
    status_callback(f"DataNormalizer: Procesando {total_entries_to_process} entradas BibTeX...")
    processed_entries = 0
    for entry in bib_database.entries:
        abstract_text_raw = entry.get('abstract', '')
        if not abstract_text_raw:
            # Si quieres contar las entradas sin abstract como "procesadas" para el conteo, hazlo aquí.
            # Si no, el 'continue' se las salta y processed_entries no se incrementa para ellas.
            # Para que el conteo sea consistente con el total anunciado, deberíamos incrementar processed_entries
            # o filtrar estas entradas antes y anunciar un total diferente.
            # Por ahora, asumamos que "procesar" significa iterar sobre ellas, tengan o no abstract.
            pass  # No hacer nada especial si no hay abstract, se contará en processed_entries

        abstract_lower = _normalize_text_internal(
            abstract_text_raw if abstract_text_raw else "")  # Asegurar que no sea None
        abstract_to_search_in = abstract_lower
        current_entry_found_canonical_terms = set()

        if abstract_text_raw:  # Solo buscar si hay abstract
            for search_key in sorted_search_terms:
                pattern = r'\b' + re.escape(search_key) + r'\b'
                if re.search(pattern, abstract_to_search_in):
                    canonical_name = search_map[search_key]
                    current_entry_found_canonical_terms.add(canonical_name)

        for canonical_name in current_entry_found_canonical_terms:
            term_counts[canonical_name] += 1
            if canonical_name not in term_categories:
                term_categories[canonical_name] = category_map.get(canonical_name, "Sin Categoría")

        if len(current_entry_found_canonical_terms) >= 2:
            for pair in combinations(sorted(list(current_entry_found_canonical_terms)), 2):
                cooccurrence_counts[pair] += 1

        processed_entries += 1  # Incrementar después de procesar la entrada

        # No imprimir el mensaje si es la última entrada Y es un múltiplo de 100,
        # para evitar duplicar con el mensaje final que añadiremos.
        if processed_entries % 100 == 0 and processed_entries != total_entries_to_process:
            status_callback(
                f"DataNormalizer: {processed_entries}/{total_entries_to_process} entradas BibTeX procesadas...")

    # --- LÍNEA AÑADIDA ---
    # Mensaje final después del bucle para confirmar el total de entradas iteradas.
    status_callback(
        f"DataNormalizer: {processed_entries}/{total_entries_to_process} entradas BibTeX iteradas (Fin del procesamiento de entradas).")
    # --------------------

    return term_counts, term_categories, cooccurrence_counts


def _write_nodes_csv_internal(term_counts, term_categories, output_csv_path, status_callback):
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    if not term_counts:  # term_counts es un Counter, puede estar vacío pero no ser None
        status_callback("DataNormalizer: No se encontraron términos categorizados para escribir en CSV de nodos.")
        # Crear archivo vacío con cabeceras
        with open(output_csv_path, mode='w', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['Id', 'Label', 'Frequency', 'Category']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        status_callback(f"DataNormalizer: Archivo de nodos vacío creado en {output_csv_path}")
        return
    try:
        with open(output_csv_path, mode='w', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['Id', 'Label', 'Frequency', 'Category']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for canonical_name, freq in term_counts.items():
                category = term_categories.get(canonical_name, "Error - No Category Found")
                writer.writerow({
                    'Id': canonical_name,
                    'Label': canonical_name,
                    'Frequency': freq,
                    'Category': category
                })
        status_callback(f"DataNormalizer: Datos de nodos (frases/acrónimos) escritos en {output_csv_path}")
    except Exception as e:
        status_callback(f"DataNormalizer: Error escribiendo CSV de nodos: {e}")


def _write_edges_csv_internal(cooccurrence_counts, output_csv_path, status_callback):
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    if not cooccurrence_counts:
        status_callback("DataNormalizer: No se encontraron co-ocurrencias para escribir en CSV de ejes.")
        with open(output_csv_path, mode='w', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['Source', 'Target', 'Weight', 'Type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        status_callback(f"DataNormalizer: Archivo de ejes vacío creado en {output_csv_path}")
        return

    try:
        with open(output_csv_path, mode='w', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['Source', 'Target', 'Weight', 'Type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for pair, weight in cooccurrence_counts.items():
                writer.writerow({
                    'Source': pair[0],
                    'Target': pair[1],
                    'Weight': weight,
                    'Type': 'Undirected'
                })
        status_callback(f"DataNormalizer: Datos de ejes (co-ocurrencias) escritos en {output_csv_path}")
    except Exception as e:
        status_callback(f"DataNormalizer: Error escribiendo CSV de ejes: {e}")


def run_data_normalizer(status_callback, project_root_dir):
    status_callback("Iniciando DataNormalizer...")

    variables_file = os.path.join(project_root_dir, "variables.csv")  # EN LA RAÍZ DEL PROYECTO
    bibtex_file_input = os.path.join(project_root_dir, "output", "parsing", "unificados.bib")

    output_dn_dir = os.path.join(project_root_dir, "output", "data_normalizer")
    os.makedirs(output_dn_dir, exist_ok=True)
    nodes_output_file = os.path.join(output_dn_dir, "keyword_nodes.csv")
    edges_output_file = os.path.join(output_dn_dir, "keyword_edges.csv")

    search_map, category_map, sorted_search_keys = _load_variables_and_categories_internal(variables_file,
                                                                                           status_callback)

    if search_map is None:  # Error ya reportado en _load_variables_and_categories_internal
        status_callback("DataNormalizer: Error crítico al cargar variables. Se generarán archivos vacíos.")
        counts, categories, cooccurrences = Counter(), {}, Counter()  # Asegurar que son Counters vacíos
    else:
        counts, categories, cooccurrences = _process_bibtex_data_internal(
            bibtex_file_input, search_map, category_map, sorted_search_keys, status_callback
        )

    status_callback(f"DataNormalizer: Procesadas {len(counts)} frases/acrónimos únicos encontrados.")
    status_callback(f"DataNormalizer: Encontradas {len(cooccurrences)} co-ocurrencias únicas.")

    _write_nodes_csv_internal(counts, categories, nodes_output_file, status_callback)
    _write_edges_csv_internal(cooccurrences, edges_output_file, status_callback)

    status_callback("DataNormalizer completado.")