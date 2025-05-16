import csv
import os

from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import homogenize_latex_encoding, convert_to_unicode
import bibtexparser  # For bibtexparser.loads()
from collections import Counter
from itertools import combinations
import re

# Basic stop words for abstract pre-cleaning if needed, though direct phrase matching reduces reliance on this.
# However, cleaning the abstract slightly before regex matching can sometimes improve accuracy or speed.
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


def normalize_text(text, for_search=True):
    if text is None:
        return ""
    processed_text = str(text).lower().strip()
    if for_search:  # More aggressive cleaning for search terms if needed
        # Optional: remove special characters if they might interfere with \b in regex
        # processed_text = re.sub(r'[^a-z0-9\s-]', '', processed_text) # Keep alphanumeric, spaces, hyphens
        pass  # For now, just lower and strip for search terms as well
    return processed_text


def load_variables_and_categories(variables_csv_path):
    """
    Parses variables.csv.
    Creates a map from searchable terms (lowercase phrases/acronyms) to a canonical name.
    Creates a map from canonical names to categories.
    """
    search_map = {}  # {"searchable_lc_term": "Canonical_Display_Name"}
    category_map = {}  # {"Canonical_Display_Name": "Category"}

    try:
        with open(variables_csv_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                variable_original_case = row.get('Variable', '').strip()
                category_original_case = row.get('Categoria', '').strip()

                if not variable_original_case or not category_original_case:
                    continue  # Skip if variable or category is empty

                # The original variable string will be our canonical name for display and node ID
                canonical_name = variable_original_case
                category_map[canonical_name] = category_original_case

                parts = variable_original_case.split(" - ")
                main_phrase = normalize_text(parts[0])  # normalize_text applies lower() and strip()

                if main_phrase:
                    search_map[main_phrase] = canonical_name

                if len(parts) > 1:
                    acronym = normalize_text(parts[1])
                    if acronym:  # Ensure acronym is not empty
                        search_map[acronym] = canonical_name

    except FileNotFoundError:
        print(f"Error: File not found {variables_csv_path}.")
        return None, None
    except Exception as e:
        print(f"Error reading {variables_csv_path}: {e}")
        return None, None

    # Sort search terms by length (descending) to match longer phrases first
    # This helps if "computational thinking skills" and "computational thinking" are both variables
    sorted_search_terms = sorted(search_map.keys(), key=len, reverse=True)

    # Rebuild search_map with sorted keys if order matters for your matching strategy,
    # though for the current iteration strategy it's not strictly necessary to rebuild the map itself.
    # The list `sorted_search_terms` will be used for iterating.

    return search_map, category_map, sorted_search_terms


def process_bibtex_data(bibtex_file_path, search_map, category_map, sorted_search_terms):
    if not search_map or not category_map:
        print("Warning: Search map or category map is missing/empty. No terms will be matched or categorized.")
        return Counter(), {}, Counter()

    term_counts = Counter()  # {"Canonical_Display_Name": count}
    term_categories = {}  # {"Canonical_Display_Name": "Category"}
    cooccurrence_counts = Counter()

    try:
        with open(bibtex_file_path, 'r', encoding='utf-8') as bibfile:
            bibtex_string = bibfile.read()
            parser = BibTexParser()
            parser.customization = lambda record: convert_to_unicode(homogenize_latex_encoding(record))
            parser.ignore_errors = True
            bib_database = bibtexparser.loads(bibtex_string, parser)
    except FileNotFoundError:
        print(f"Error: File not found {bibtex_file_path}.")
        return Counter(), {}, Counter()
    except Exception as e:
        print(f"Error processing BibTeX {bibtex_file_path}: {e}")
        return Counter(), {}, Counter()

    if not hasattr(bib_database, 'entries') or not bib_database.entries:
        print(f"Warning: No entries found in {bibtex_file_path}.")
        return Counter(), {}, Counter()

    for entry in bib_database.entries:
        abstract_text_raw = entry.get('abstract', '')
        if not abstract_text_raw:
            continue

        abstract_lower = normalize_text(abstract_text_raw)  # Just lowercase and strip the whole abstract once

        # Optional: further clean abstract by removing stop words before phrase matching if desired
        # This might slightly improve matching by reducing noise, but can also remove parts of phrases.
        # For now, we match directly on the lowercased abstract.
        # words_in_abstract = abstract_lower.split()
        # cleaned_abstract_words = [word for word in words_in_abstract if word not in STOP_WORDS]
        # abstract_to_search_in = " ".join(cleaned_abstract_words)
        abstract_to_search_in = abstract_lower

        current_entry_found_canonical_terms = set()

        # Iterate through the pre-sorted search terms (longest first)
        for search_key in sorted_search_terms:
            # Use regex to find whole word/phrase matches. re.escape handles special chars in search_key.
            pattern = r'\b' + re.escape(search_key) + r'\b'

            # Check if this search_key (e.g., "classical test theory" or "ctt") is in the abstract
            if re.search(pattern, abstract_to_search_in):
                canonical_name = search_map[search_key]  # Get the canonical name (e.g., "Classical Test Theory - CTT")
                current_entry_found_canonical_terms.add(canonical_name)

                # Frequency counts how many abstracts the canonical term appears in
                # We add to term_counts only after processing all search_keys for an abstract
                # to ensure a canonical term is counted once per abstract even if multiple aliases match.

        # After checking all search_keys for the current abstract, update counts for found canonical terms
        for canonical_name in current_entry_found_canonical_terms:
            term_counts[canonical_name] += 1
            if canonical_name not in term_categories:  # Assign category if not already done
                term_categories[canonical_name] = category_map[canonical_name]

        if len(current_entry_found_canonical_terms) >= 2:
            for pair in combinations(sorted(list(current_entry_found_canonical_terms)), 2):
                cooccurrence_counts[pair] += 1

    return term_counts, term_categories, cooccurrence_counts


# write_nodes_csv and write_edges_csv remain largely the same as before,
# they will use the canonical names as 'Id' and 'Label'.

def write_nodes_csv(term_counts, term_categories, output_csv_path="phrases_nodes.csv"):
    if term_counts is None or not term_counts:
        print("No categorized terms/phrases found to write to nodes CSV.")
        with open(output_csv_path, mode='w', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['Id', 'Label', 'Frequency', 'Category']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        print(f"Empty nodes data file created at {output_csv_path}")
        return
    try:
        with open(output_csv_path, mode='w', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['Id', 'Label', 'Frequency', 'Category']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for canonical_name, freq in term_counts.items():
                category = term_categories.get(canonical_name, "Error - No Category Found")
                writer.writerow({
                    'Id': canonical_name,  # Use canonical name (original "Variable" string) as ID
                    'Label': canonical_name,  # And as Label
                    'Frequency': freq,  # Number of abstracts it appeared in
                    'Category': category
                })
        print(f"Nodes data (matched phrases/acronyms from abstracts) written to {output_csv_path}")
    except Exception as e:
        print(f"Error writing nodes CSV: {e}")


def write_edges_csv(cooccurrence_counts, output_csv_path="phrases_edges.csv"):
    if cooccurrence_counts is None or not cooccurrence_counts:
        print("No co-occurrences between categorized terms/phrases found to write to edges CSV.")
        with open(output_csv_path, mode='w', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['Source', 'Target', 'Weight', 'Type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        print(f"Empty edges data file created at {output_csv_path}")
        return
    try:
        with open(output_csv_path, mode='w', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['Source', 'Target', 'Weight', 'Type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for pair, weight in cooccurrence_counts.items():
                writer.writerow({
                    'Source': pair[0],  # These are canonical names
                    'Target': pair[1],  # These are canonical names
                    'Weight': weight,
                    'Type': 'Undirected'
                })
        print(f"Edges data (between matched phrases/acronyms) written to {output_csv_path}")
    except Exception as e:
        print(f"Error writing edges CSV: {e}")

def encontrar_archivo(ruta_base):
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


# --- Main Execution ---
variables_file = "variables.csv"
bibtex_file = encontrar_archivo('src/Parsing/output/unificados.bib')
# Changed output filenames to reflect new content
nodes_output_file = "output/keyword_nodes.csv"
edges_output_file = "output/keyword_edges.csv"

print("Starting script (processing abstracts for phrases/acronyms from variables.csv)...")
search_map, category_map, sorted_search_keys = load_variables_and_categories(variables_file)

if search_map is None:
    print("Critical error: Variable data could not be loaded. Script will produce empty output files.")
    counts, categories, cooccurrences = Counter(), {}, Counter()
else:
    print(f"Loaded {len(category_map)} canonical variables with {len(search_map)} search terms (phrases/acronyms).")
    # 'counts' will be term_counts of canonical names
    # 'categories' will be term_categories for canonical names
    counts, categories, cooccurrences = process_bibtex_data(bibtex_file, search_map, category_map, sorted_search_keys)

if counts is None: counts = Counter()
if categories is None: categories = {}
if cooccurrences is None: cooccurrences = Counter()

print(f"Processed {len(counts)} unique canonical phrases/acronyms found in abstracts.")
print(f"Found {len(cooccurrences)} unique co-occurrences between them.")

write_nodes_csv(counts, categories, nodes_output_file)
write_edges_csv(cooccurrences, edges_output_file)

print("\nScript finished.")
print(f"Output files: '{nodes_output_file}' and '{edges_output_file}'")