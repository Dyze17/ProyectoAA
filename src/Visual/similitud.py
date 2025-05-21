import csv
import math
import string
import os
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode, homogenize_latex_encoding

def _limpiar_texto_internal(texto, status_callback):
    if not isinstance(texto, str):
        texto = ""
    try:
        texto_limpio = " ".join(texto.split())
        texto_limpio = texto_limpio.lower().translate(str.maketrans("", "", string.punctuation))
        return texto_limpio.split()
    except Exception as e:
        # status_callback(f"SimilarityAnalyzer: Error limpiando texto (primeros 50 chars: '{str(texto)[:50]}...'): {e}")
        return []


def _calcular_tf_internal(texto, status_callback):
    tf = {}
    palabras = _limpiar_texto_internal(texto, status_callback)
    if not palabras:
        return tf
    for palabra in palabras:
        tf[palabra] = tf.get(palabra, 0) + 1
    total_palabras = len(palabras)
    if total_palabras == 0:
        return tf
    for palabra in tf:
        tf[palabra] /= total_palabras
    return tf


def _calcular_idf_internal(documentos_texto, status_callback, stop_event=None):  # Añadido stop_event
    N = len(documentos_texto)
    if N == 0:
        status_callback("SimilarityAnalyzer: No hay documentos para calcular IDF.")
        return {}
    idf = {}
    for idx, texto in enumerate(documentos_texto):
        if stop_event and stop_event.is_set():
            status_callback("SimilarityAnalyzer: Cálculo de IDF detenido.")
            return idf  # Retornar lo calculado hasta ahora
        if idx % 500 == 0 and idx > 0:
            status_callback(f"SimilarityAnalyzer: (IDF) Procesando documento {idx + 1}/{N}...")
        palabras_unicas_doc = set(_limpiar_texto_internal(texto, status_callback))
        for palabra in palabras_unicas_doc:
            idf[palabra] = idf.get(palabra, 0) + 1

    palabras_a_eliminar_idf = []
    for palabra, num_documentos_con_palabra in idf.items():
        if num_documentos_con_palabra <= 0:
            palabras_a_eliminar_idf.append(palabra)
            continue
        try:
            idf[palabra] = math.log(N / float(num_documentos_con_palabra))
        except ValueError:
            idf[palabra] = 0.0

    for palabra_a_eliminar in palabras_a_eliminar_idf:
        if palabra_a_eliminar in idf: del idf[palabra_a_eliminar]
    return idf


def _calcular_tfidf_internal(documentos_texto, status_callback, stop_event=None):  # Añadido stop_event
    if not documentos_texto:
        status_callback("SimilarityAnalyzer: No hay documentos para calcular TF-IDF.")
        return []
    status_callback("SimilarityAnalyzer: Calculando IDF para todos los documentos (puede ser detenido)...")
    idf_map = _calcular_idf_internal(documentos_texto, status_callback, stop_event)  # Pasar stop_event

    if stop_event and stop_event.is_set():
        status_callback("SimilarityAnalyzer: Cálculo de TF-IDF detenido durante IDF.")
        return []

    status_callback("SimilarityAnalyzer: IDF calculado.")

    vectores_tfidf_list = []
    total_docs = len(documentos_texto)
    for idx, texto in enumerate(documentos_texto):
        if stop_event and stop_event.is_set():
            status_callback(f"SimilarityAnalyzer: Cálculo de TF-IDF detenido en vector {idx + 1}/{total_docs}.")
            break
        if idx % 100 == 0 or idx == total_docs - 1:
            status_callback(f"SimilarityAnalyzer: Calculando TF-IDF - Vector {idx + 1}/{total_docs}")
        tf_vector = _calcular_tf_internal(texto, status_callback)
        tfidf_vector_actual = {}
        for palabra, tf_score in tf_vector.items():
            tfidf_vector_actual[palabra] = tf_score * idf_map.get(palabra, 0.0)
        vectores_tfidf_list.append(tfidf_vector_actual)

    if not (stop_event and stop_event.is_set()):
        status_callback("SimilarityAnalyzer: Todos los vectores TF-IDF calculados.")
    return vectores_tfidf_list


def _coseno_internal(v1, v2):
    if not isinstance(v1, dict) or not isinstance(v2, dict):
        return 0.0
    if len(v1) > len(v2):
        v1, v2 = v2, v1
    dot_product = 0.0
    for k, v1_val in v1.items():
        dot_product += v1_val * v2.get(k, 0.0)
    mag1_sq = sum(v ** 2 for v in v1.values())
    mag2_sq = sum(v ** 2 for v in v2.values())
    if mag1_sq == 0 or mag2_sq == 0:
        return 0.0
    magnitude = math.sqrt(mag1_sq) * math.sqrt(mag2_sq)
    if magnitude == 0:
        return 0.0
    return dot_product / magnitude


def _jaccard_internal(s1, s2, status_callback):
    set1 = set(_limpiar_texto_internal(s1, status_callback))
    set2 = set(_limpiar_texto_internal(s2, status_callback))
    if not set1 and not set2:
        return 1.0
    interseccion = set1.intersection(set2)
    union = set1.union(set2)
    if not union:
        return 0.0
    return len(interseccion) / float(len(union))


# --- Función principal para llamar desde gui_controller ---
# MODIFICADO para aceptar stop_event
def run_similarity_analysis(status_callback, project_root_dir, stop_event=None):  # AÑADIDO stop_event
    status_callback("Iniciando Análisis de Similitud de Abstracts...")

    bibtex_file_input = os.path.join(project_root_dir, "output", "parsing", "unificados.bib")  #

    output_similarity_dir = os.path.join(project_root_dir, "output", "similarity_analysis")
    os.makedirs(output_similarity_dir, exist_ok=True)

    report_txt_path = os.path.join(output_similarity_dir, "similarity_full_report.txt")
    tfidf_csv_path = os.path.join(output_similarity_dir, "similarity_tfidf_pairs.csv")
    jaccard_csv_path = os.path.join(output_similarity_dir, "similarity_jaccard_pairs.csv")

    if not os.path.exists(bibtex_file_input):
        status_callback(f"SimilarityAnalyzer: Error - Archivo BibTeX unificado no encontrado en {bibtex_file_input}")
        status_callback("SimilarityAnalyzer completado (con error).")
        return

    # Chequeo inicial de stop_event
    if stop_event and stop_event.is_set():
        status_callback("SimilarityAnalyzer: Detenido por el usuario antes de cargar datos.")
        return

    abstracts_list = []
    titulos_list = []
    entry_ids_list = []

    status_callback(f"SimilarityAnalyzer: Leyendo datos desde {os.path.basename(bibtex_file_input)}...")
    try:
        with open(bibtex_file_input, 'r', encoding='utf-8') as bibfile:
            parser = BibTexParser(common_strings=True)
            parser.customization = lambda record: convert_to_unicode(homogenize_latex_encoding(record))
            parser.ignore_errors = True
            bib_database = bibtexparser.load(bibfile, parser=parser)  #

        if not bib_database.entries:
            status_callback("SimilarityAnalyzer: No se encontraron entradas en el archivo BibTeX.")
            status_callback("SimilarityAnalyzer completado (sin datos).")
            return

        total_bib_entries = len(bib_database.entries)
        for idx, entry in enumerate(bib_database.entries):
            # Chequeo de stop_event dentro del bucle de carga (menos frecuente)
            if stop_event and stop_event.is_set() and idx > 0 and idx % 200 == 0:
                status_callback(
                    f"SimilarityAnalyzer: Carga de datos detenida en la entrada {idx + 1}/{total_bib_entries}.")
                break  # Salir del bucle de carga
            abstract_text = entry.get('abstract')
            title_text = entry.get('title', '').strip()
            entry_id = entry.get('ID', f"NO_ID_{len(entry_ids_list)}")
            if not title_text: title_text = f"Artículo sin título (ID: {entry_id})"
            if abstract_text and isinstance(abstract_text, str) and abstract_text.strip():
                abstracts_list.append(abstract_text)
                titulos_list.append(title_text)
                entry_ids_list.append(entry_id)
        status_callback(f"SimilarityAnalyzer: {len(abstracts_list)} abstracts válidos cargados para análisis.")

    except Exception as e:
        status_callback(f"SimilarityAnalyzer: Error leyendo o parseando el archivo BibTeX: {e}")
        import traceback
        status_callback(traceback.format_exc())
        status_callback("SimilarityAnalyzer completado (con error).")
        return

    # Chequeo después de cargar datos y antes de cálculos pesados
    if stop_event and stop_event.is_set():
        status_callback("SimilarityAnalyzer: Detenido por el usuario después de cargar datos.")
        # Considerar guardar un reporte vacío o con lo que se tenga si es útil
        return

    if not abstracts_list or len(abstracts_list) < 2:
        status_callback(
            "SimilarityAnalyzer: No hay suficientes abstracts (se necesitan al menos 2) para realizar el análisis de similitud.")
        status_callback("SimilarityAnalyzer completado (datos insuficientes).")
        return

    tfidf_pairs_data = []
    jaccard_pairs_data = []

    # Escribir encabezado del reporte incluso si se detiene
    with open(report_txt_path, 'w', encoding='utf-8') as report_file:
        report_file.write("--- [Reporte de Similitud de Abstracts] ---\n")
        status_callback(f"SimilarityAnalyzer: Reporte detallado se guardará en: {report_txt_path}")
        status_callback(f"SimilarityAnalyzer: Pares TF-IDF CSV: {os.path.basename(tfidf_csv_path)}")
        status_callback(f"SimilarityAnalyzer: Pares Jaccard CSV: {os.path.basename(jaccard_csv_path)}")

        # Calcular similitud TF-IDF + Coseno
        report_file.write("\n--- [Similitud TF-IDF + Coseno] ---\n")
        status_callback("\n--- [Similitud TF-IDF + Coseno] ---")
        # Pasar stop_event a _calcular_tfidf_internal
        vectores_tfidf = _calcular_tfidf_internal(abstracts_list, status_callback, stop_event)

        if stop_event and stop_event.is_set():
            status_callback("SimilarityAnalyzer: Detenido durante el cálculo de TF-IDF.")
            # El reporte TXT y los CSV se guardarán con lo que se haya procesado.

        pares_similares_tfidf_count = 0
        umbral_tfidf = 0.3

        if vectores_tfidf and len(vectores_tfidf) == len(titulos_list):  # Asegurar consistencia
            report_file.write(f"Umbral de similitud TF-IDF aplicado: {umbral_tfidf}\n\n")
            status_callback(
                f"SimilarityAnalyzer: Comparando {len(vectores_tfidf)} vectores TF-IDF (umbral: {umbral_tfidf})...")
            num_vectores = len(vectores_tfidf)
            for i in range(num_vectores):
                if stop_event and stop_event.is_set():
                    status_callback(f"SimilarityAnalyzer: Comparación TF-IDF detenida en vector {i + 1}.")
                    break  # Salir del bucle de comparación TF-IDF
                if i > 0 and i % 50 == 0:
                    status_callback(
                        f"SimilarityAnalyzer: (TF-IDF) Comparando vector {i + 1}/{num_vectores} con el resto...")
                for j in range(i + 1, num_vectores):
                    # No es estrictamente necesario chequear stop_event en el bucle interno si el externo lo hace,
                    # pero no hace daño y puede hacer la detención un poco más responsiva.
                    if stop_event and stop_event.is_set() and j % 100 == 0:  # Chequeo menos frecuente en bucle interno
                        break
                    sim = _coseno_internal(vectores_tfidf[i], vectores_tfidf[j])
                    if sim >= umbral_tfidf:
                        report_file.write(
                            f"  - TF-IDF Sim: '{titulos_list[i]}' ≈ '{titulos_list[j]}' (sim: {sim:.3f})\n")
                        tfidf_pairs_data.append({
                            "ID_1": entry_ids_list[i], "Titulo_1": titulos_list[i],
                            "ID_2": entry_ids_list[j], "Titulo_2": titulos_list[j],
                            "Sim_TFIDF": round(sim, 4)
                        })
                        pares_similares_tfidf_count += 1
                if stop_event and stop_event.is_set(): break  # Salir del bucle externo si el interno se rompió por stop
            report_file.write(
                f"\nTotal pares encontrados con similitud TF-IDF >= {umbral_tfidf} (hasta detención si aplica): {pares_similares_tfidf_count}\n")
            status_callback(
                f"SimilarityAnalyzer: {pares_similares_tfidf_count} pares TF-IDF >= {umbral_tfidf} (guardados en reporte).")
        else:
            if not (stop_event and stop_event.is_set()):
                msg_err = "SimilarityAnalyzer: No se generaron vectores TF-IDF o hay inconsistencia en datos."
                status_callback(msg_err)
                report_file.write(msg_err + "\n")

        # Chequeo antes de Jaccard
        if stop_event and stop_event.is_set():
            status_callback("SimilarityAnalyzer: Detenido por el usuario antes de la comparación Jaccard.")
        else:
            # Calcular similitud Jaccard
            report_file.write("\n--- [Similitud Jaccard] ---\n")
            status_callback("\n--- [Similitud Jaccard] ---")
            umbral_jaccard = 0.25
            report_file.write(f"Umbral de similitud Jaccard aplicado: {umbral_jaccard}\n\n")
            status_callback(f"SimilarityAnalyzer: Comparando con Índice de Jaccard (umbral: {umbral_jaccard})...")
            pares_similares_jaccard_count = 0
            num_abstracts_jaccard = len(abstracts_list)

            for i in range(num_abstracts_jaccard):
                if stop_event and stop_event.is_set():
                    status_callback(f"SimilarityAnalyzer: Comparación Jaccard detenida en abstract {i + 1}.")
                    break  # Salir del bucle de comparación Jaccard
                if i > 0 and i % 50 == 0:
                    status_callback(
                        f"SimilarityAnalyzer: (Jaccard) Comparando abstract {i + 1}/{num_abstracts_jaccard} con el resto...")
                for j in range(i + 1, num_abstracts_jaccard):
                    if stop_event and stop_event.is_set() and j % 100 == 0:
                        break
                    sim = _jaccard_internal(abstracts_list[i], abstracts_list[j], status_callback)
                    if sim >= umbral_jaccard:
                        report_file.write(
                            f"  - Jaccard Sim: '{titulos_list[i]}' ≈ '{titulos_list[j]}' (sim: {sim:.3f})\n")
                        jaccard_pairs_data.append({
                            "ID_1": entry_ids_list[i], "Titulo_1": titulos_list[i],
                            "ID_2": entry_ids_list[j], "Titulo_2": titulos_list[j],
                            "Sim_Jaccard": round(sim, 4)
                        })
                        pares_similares_jaccard_count += 1
                if stop_event and stop_event.is_set(): break  # Salir del bucle externo
            report_file.write(
                f"\nTotal pares encontrados con similitud Jaccard >= {umbral_jaccard} (hasta detención si aplica): {pares_similares_jaccard_count}\n")
            status_callback(
                f"SimilarityAnalyzer: {pares_similares_jaccard_count} pares Jaccard >= {umbral_jaccard} (guardados en reporte).")

    # --- Guardar datos de pares en archivos CSV (fuera del 'with open(report_txt_path...)') ---
    try:
        if tfidf_pairs_data:  # Guardar incluso si está vacío por detención (tendrá solo cabeceras)
            with open(tfidf_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["ID_1", "Titulo_1", "ID_2", "Titulo_2", "Sim_TFIDF"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                if tfidf_pairs_data: writer.writerows(tfidf_pairs_data)  # Solo escribir filas si hay datos
            status_callback(f"SimilarityAnalyzer: Pares TF-IDF guardados en: {os.path.basename(tfidf_csv_path)}")
        elif not (stop_event and stop_event.is_set()):
            status_callback(f"SimilarityAnalyzer: No se encontraron pares TF-IDF para CSV (umbral: {umbral_tfidf}).")
            # Crear CSV vacío con cabeceras si no hay datos y no se detuvo
            with open(tfidf_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["ID_1", "Titulo_1", "ID_2", "Titulo_2", "Sim_TFIDF"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

        if jaccard_pairs_data:  # Guardar incluso si está vacío por detención
            with open(jaccard_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["ID_1", "Titulo_1", "ID_2", "Titulo_2", "Sim_Jaccard"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                if jaccard_pairs_data: writer.writerows(jaccard_pairs_data)
            status_callback(f"SimilarityAnalyzer: Pares Jaccard guardados en: {os.path.basename(jaccard_csv_path)}")
        elif not (stop_event and stop_event.is_set()):
            status_callback(f"SimilarityAnalyzer: No se encontraron pares Jaccard para CSV (umbral: {umbral_jaccard}).")
            with open(jaccard_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["ID_1", "Titulo_1", "ID_2", "Titulo_2", "Sim_Jaccard"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

    except Exception as e_csv:
        status_callback(f"SimilarityAnalyzer: Error guardando reportes CSV: {e_csv}")

    if stop_event and stop_event.is_set():
        status_callback("\nSimilarityAnalyzer INTERRUMPIDO por el usuario. Resultados parciales guardados.")
    else:
        status_callback("\nSimilarityAnalyzer completado.")