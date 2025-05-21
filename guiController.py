# ProyectoAA/gui_controller.py
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
import os
import sys
import time

# --- Configuración de Rutas ---
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

from src.Scraping import AcademicSearch, AppliedScience, ScienceDirect
from src.Parsing import Parser
from src.Visual import dataNormalizer, BarGrapher, graphicator, Stats, WordCloudGenerator, similitud


class App:
    def __init__(self, root_window):
        self.root_window = root_window
        self.root_window.title("Asistente de Automatización (v2025.05.20_Cont)")
        self.root_window.geometry("800x650")

        self.project_root_dir = project_root
        self.stop_current_task_event = threading.Event()  # Renombrado para claridad

        os.makedirs(os.path.join(self.project_root_dir, "output", "parsing"), exist_ok=True)
        os.makedirs(os.path.join(self.project_root_dir, "output", "data_normalizer"), exist_ok=True)
        os.makedirs(os.path.join(self.project_root_dir, "output", "visual"), exist_ok=True)
        os.makedirs(os.path.join(self.project_root_dir, "output", "similarity_analysis"), exist_ok=True)
        os.makedirs(os.path.join(self.project_root_dir, "data"), exist_ok=True)

        config_frame = ttk.LabelFrame(root_window, text="Configuración")
        config_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(config_frame, text="Término de búsqueda:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.query_var = tk.StringVar(value="computational thinking")
        self.query_entry = ttk.Entry(config_frame, textvariable=self.query_var, width=40)
        self.query_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(config_frame, text="Perfil de Chrome:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.chrome_profile_var = tk.StringVar(value=r"C:\Users\Default\AppData\Local\Google\Chrome\User Data\Default")
        self.chrome_profile_entry = ttk.Entry(config_frame, textvariable=self.chrome_profile_var, width=40)
        self.chrome_profile_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.browse_button = ttk.Button(config_frame, text="Buscar...", command=self.browse_chrome_profile)
        self.browse_button.grid(row=1, column=2, padx=5, pady=5)

        self.skip_scraping_var = tk.BooleanVar(value=False)
        self.skip_scraping_check = ttk.Checkbutton(
            config_frame,
            text="Saltar fase de Scraping (usar datos existentes en 'data/')",
            variable=self.skip_scraping_var,
            command=self.toggle_scraping_options
        )
        self.skip_scraping_check.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        controls_frame = ttk.Frame(root_window)
        controls_frame.pack(padx=10, pady=5, fill="x")

        self.start_button = ttk.Button(controls_frame, text="Iniciar Proceso Completo", command=self.start_full_process)
        self.start_button.pack(side="left", padx=5)

        self.stop_task_button = ttk.Button(controls_frame, text="Detener Tarea Actual",
                                           command=self.stop_current_task_ui, state="disabled")
        self.stop_task_button.pack(side="left", padx=5)

        status_frame = ttk.LabelFrame(root_window, text="Progreso")
        status_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD, height=15, font=("Arial", 9))
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progressbar = ttk.Progressbar(root_window, variable=self.progress_var, maximum=100)
        self.progressbar.pack(padx=10, pady=(0, 10), fill="x")

        self.toggle_scraping_options()

    def toggle_scraping_options(self):
        if self.skip_scraping_var.get():
            self.query_entry.config(state="disabled")
            self.chrome_profile_entry.config(state="disabled")
            self.browse_button.config(state="disabled")
        else:
            self.query_entry.config(state="normal")
            self.chrome_profile_entry.config(state="normal")
            self.browse_button.config(state="normal")

    def browse_chrome_profile(self):
        directory = filedialog.askdirectory(
            title="Selecciona la carpeta del perfil de Chrome (ej. User Data/Default o User Data/Profile X)")
        if directory:
            self.chrome_profile_var.set(directory)

    def update_status(self, message):
        self.root_window.after(0, self._update_status_text, message)

    def _update_status_text(self, message):
        self.status_text.insert(tk.END, time.strftime("[%H:%M:%S] ") + message + "\n")
        self.status_text.see(tk.END)
        self.root_window.update_idletasks()

    def update_progress(self, step, total_steps):
        self.root_window.after(0, self._update_progressbar, step, total_steps)

    def _update_progressbar(self, step, total_steps):
        if total_steps > 0:
            self.progress_var.set((step / total_steps) * 100)
        else:
            self.progress_var.set(0)
        self.root_window.update_idletasks()

    def start_full_process(self):
        self.start_button.config(state="disabled")
        self.stop_task_button.config(state="normal")  # Habilitar botón de detener al iniciar

        self.status_text.delete(1.0, tk.END)
        self.stop_current_task_event.clear()  # Reiniciar el evento de detención
        self.progress_var.set(0)

        query = self.query_var.get()
        chrome_profile = self.chrome_profile_var.get()

        if not self.skip_scraping_var.get():
            if not query:
                self.update_status("Error: El término de búsqueda no puede estar vacío si se realiza scraping.")
                self.finalize_process_ui_state();
                return
            if not chrome_profile or not os.path.isdir(chrome_profile):
                self.update_status(f"Error: La ruta del perfil de Chrome no es válida: {chrome_profile}")
                self.finalize_process_ui_state();
                return

        process_thread = threading.Thread(target=self._execute_pipeline, args=(query, chrome_profile))
        process_thread.daemon = True
        process_thread.start()

    def _execute_pipeline(self, query, chrome_profile):
        num_scraper_tasks = 3
        tasks_base_count = 7

        perform_scraping = not self.skip_scraping_var.get()
        actual_total_tasks = tasks_base_count + (num_scraper_tasks if perform_scraping else 0)
        current_task_num = 0

        # Helper para avanzar el progreso y resetear el evento de stop para la siguiente tarea
        def advance_to_next_stage():
            nonlocal current_task_num
            current_task_num += 1
            self.update_progress(current_task_num, actual_total_tasks)
            # Importante: Si queremos que el botón "Detener" afecte solo a la tarea actual
            # y no a las siguientes automáticamente, podríamos resetear el evento aquí.
            # PERO, si el usuario presiona "Detener", usualmente quiere detener la secuencia
            # a menos que explícitamente inicie otra. Por ahora, no lo resetearemos aquí,
            # el chequeo `if self.stop_current_task_event.is_set():` al inicio de cada sección se encargará.
            # Si una tarea es interrumpible, el botón de stop se habilitará de nuevo para ella.
            self.stop_task_button.config(state="normal")  # Re-habilitar para la siguiente tarea (si es detenible)

        try:
            # --- FASE DE SCRAPING ---
            if perform_scraping:
                self.update_status("--- Iniciando Fase de Scraping (Secuencial) ---")
                self.stop_task_button.config(state="normal")  # Habilitar para la fase de scraping
                scraper_modules_and_names = [
                    (AcademicSearch, "AcademicSearch_Original"),
                    (AppliedScience, "AppliedScience_Original"),
                    (ScienceDirect, "ScienceDirect_Original"),
                ]

                for module, name in scraper_modules_and_names:
                    if self.stop_current_task_event.is_set():
                        self.update_status(
                            f"Fase de Scraping detenida por usuario antes de {name}. Se saltarán los scrapers restantes.")
                        # Actualizar progreso para los scrapers no ejecutados
                        remaining_scrapers = len(scraper_modules_and_names) - scraper_modules_and_names.index(
                            (module, name))
                        for _ in range(remaining_scrapers):
                            advance_to_next_stage()
                        break  # Salir del bucle de scrapers

                    self.update_status(f"Ejecutando scraper: {name} (puede ser detenido)...")
                    module.run_scraper(query, self.stop_current_task_event, self.update_status, chrome_profile, name)
                    advance_to_next_stage()

                    if self.stop_current_task_event.is_set():  # Si este scraper fue el que se detuvo
                        self.update_status(f"Scraper {name} detenido por usuario. Se saltarán los scrapers restantes.")
                        # Actualizar progreso para los scrapers restantes
                        current_idx = scraper_modules_and_names.index((module, name))
                        remaining_scrapers_after_stop = len(scraper_modules_and_names) - (current_idx + 1)
                        for _ in range(remaining_scrapers_after_stop):
                            advance_to_next_stage()
                        break  # Salir del bucle de scrapers

                if self.stop_current_task_event.is_set():
                    self.update_status("Fase de Scraping interrumpida. Continuando con el pipeline...")
                else:
                    self.update_status("--- Fase de Scraping Completada ---")
            else:
                self.update_status("--- Fase de Scraping OMITIDA por el usuario ---")

            # Deshabilitar botón de stop si la fase actual no es explícitamente detenible
            # (o si es muy rápida)
            self.stop_task_button.config(state="disabled")

            # --- FASE DE PARSING ---
            if self.stop_current_task_event.is_set():
                self.update_status("Saltando Parsing debido a detención previa."); advance_to_next_stage();
            else:
                self.update_status("--- Iniciando Fase de Parsing ---")
                Parser.run_parser(self.update_status, self.project_root_dir)
                advance_to_next_stage()
                self.update_status("--- Parsing Completado ---")

            # --- FASE DE NORMALIZACIÓN ---
            if self.stop_current_task_event.is_set():
                self.update_status("Saltando Normalización debido a detención previa."); advance_to_next_stage();
            else:
                self.update_status("--- Iniciando Normalización de Datos ---")
                dataNormalizer.run_data_normalizer(self.update_status, self.project_root_dir)
                advance_to_next_stage()
                self.update_status("--- Normalización de Datos Completada ---")

            # --- FASE DE VISUALIZACIONES ---
            if not self.stop_current_task_event.is_set():
                self.update_status("--- Iniciando Generación de Visualizaciones ---")

            if self.stop_current_task_event.is_set():
                self.update_status("Saltando BarGraph..."); advance_to_next_stage();
            else:
                self.update_status("Generando BarGraph...")
                BarGrapher.run_bargrapher(self.update_status, self.project_root_dir)
                advance_to_next_stage()
                self.update_status("BarGraph generado.")

            if self.stop_current_task_event.is_set():
                self.update_status("Saltando Graphicator..."); advance_to_next_stage();
            else:
                self.update_status("Generando Graph (Network)...")
                graphicator.run_graphicator(self.update_status, self.project_root_dir)
                advance_to_next_stage()
                self.update_status("Graph (Network) generado.")

            if self.stop_current_task_event.is_set():
                self.update_status("Saltando WordCloud..."); advance_to_next_stage();
            else:
                self.update_status("Generando Nube de Palabras...")
                WordCloudGenerator.run_wordcloud_generator(self.update_status, self.project_root_dir)
                advance_to_next_stage()
                self.update_status("Nube de Palabras generada.")

            # --- FASE DE ANÁLISIS DE SIMILITUD (DETENIBLE) ---
            if self.stop_current_task_event.is_set():
                self.update_status("Saltando Análisis de Similitud debido a detención previa.")
                advance_to_next_stage()
            else:
                self.update_status("Iniciando Análisis de Similitud de Abstracts (puede ser detenido)...")
                self.stop_task_button.config(state="normal")  # Habilitar botón para esta tarea
                similitud.run_similarity_analysis(self.update_status, self.project_root_dir,
                                                           self.stop_current_task_event)
                self.stop_task_button.config(state="disabled")  # Deshabilitar después de que termine o se detenga
                advance_to_next_stage()
                if self.stop_current_task_event.is_set():
                    self.update_status("Análisis de Similitud detenido por el usuario. Continuando pipeline...")
                    self.stop_current_task_event.clear()  # IMPORTANTE: Resetear el evento aquí si queremos que las siguientes tareas no se salten automáticamente
                else:
                    self.update_status("Análisis de Similitud de Abstracts completado.")

            # --- FASE DE ESTADÍSTICAS ADICIONALES ---
            if self.stop_current_task_event.is_set():
                self.update_status("Saltando Estadísticas Adicionales..."); advance_to_next_stage();
            else:
                self.update_status("Generando Estadísticas Adicionales...")
                Stats.run_stats(self.update_status, self.project_root_dir)
                advance_to_next_stage()
                self.update_status("Estadísticas Adicionales generadas.")

            if not self.stop_current_task_event.is_set():  # Si no se detuvo en ninguna parte
                self.update_status("--- Visualizaciones Completadas ---")

            if actual_total_tasks > 0: self.progress_var.set(100)  # Asegurar 100%

            if self.stop_current_task_event.is_set():  # Si en algún punto se detuvo
                self.update_status(
                    "====== PROCESO INTERRUMPIDO POR EL USUARIO, TAREAS SUBSIGUIENTES EJECUTADAS/SALTADAS ======")
            else:
                self.update_status("====== PROCESO COMPLETO ======")

        except Exception as e:
            self.update_status(f"Error fatal en el pipeline: {e}")
            import traceback
            self.update_status(traceback.format_exc())
        finally:
            self.finalize_process_ui_state()

    def finalize_process_ui_state(self):
        self.root_window.after(0, self._finalize_ui)

    def _finalize_ui(self):
        self.start_button.config(state="normal")
        self.stop_task_button.config(state="disabled")
        self.toggle_scraping_options()

    def stop_current_task_ui(self):
        self.update_status("Señal de detención enviada a la tarea actual...")
        self.stop_current_task_event.set()
        self.stop_task_button.config(state="disabled")  # Deshabilitar temporalmente para evitar múltiples clics


if __name__ == "__main__":
    main_app_root = tk.Tk()
    app_instance = App(main_app_root)
    main_app_root.mainloop()