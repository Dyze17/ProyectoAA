import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
import os
import sys
import time

# --- Configuración de Rutas ---
# Asumiendo que gui_controller.py está en la raíz de ProyectoAA
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)  # Agrega src al inicio de sys.path

# --- Importa las funciones modificadas de tus scripts ---
from src.Scraping import AcademicSearch, AppliedScience, ScienceDirect
from src.Parsing import Parser
from src.Visual import dataNormalizer, BarGrapher, graphicator, Stats, WordCloudGenerator  # Asegúrate que WordCloudGenerator esté aquí


class App:
    def __init__(self, root_window):
        self.root_window = root_window
        self.root_window.title("Asistente de Automatización de Proyectos (v2025.05.19)")
        self.root_window.geometry("800x650")  # Un poco más de alto para el nuevo checkbox

        self.project_root_dir = project_root

        self.stop_scraping_event = threading.Event()
        # self.scraping_threads = [] # Ya no se usa una lista de hilos para scrapers

        # --- Crear directorios de output principales ---
        os.makedirs(os.path.join(self.project_root_dir, "output", "parsing"), exist_ok=True)
        os.makedirs(os.path.join(self.project_root_dir, "output", "data_normalizer"), exist_ok=True)
        os.makedirs(os.path.join(self.project_root_dir, "output", "visual"), exist_ok=True)
        os.makedirs(os.path.join(self.project_root_dir, "data"), exist_ok=True)  # Para los .bib

        # --- Configuración ---
        config_frame = ttk.LabelFrame(root_window, text="Configuración")
        config_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(config_frame, text="Término de búsqueda:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.query_var = tk.StringVar(value="computational thinking")
        self.query_entry = ttk.Entry(config_frame, textvariable=self.query_var, width=40)
        self.query_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(config_frame, text="Perfil de Chrome:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.chrome_profile_var = tk.StringVar(
            value=r"C:\Users\Default\AppData\Local\Google\Chrome\User Data\Default")  # Un perfil genérico, AJUSTAR
        self.chrome_profile_entry = ttk.Entry(config_frame, textvariable=self.chrome_profile_var, width=40)
        self.chrome_profile_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.browse_button = ttk.Button(config_frame, text="Buscar...", command=self.browse_chrome_profile)
        self.browse_button.grid(row=1, column=2, padx=5, pady=5)

        # --- Opción: Saltar Scraping ---
        self.skip_scraping_var = tk.BooleanVar(value=False)  # Por defecto, no saltar scraping
        self.skip_scraping_check = ttk.Checkbutton(
            config_frame,
            text="Saltar fase de Scraping (usar datos existentes en 'data/')",
            variable=self.skip_scraping_var,
            command=self.toggle_scraping_options
        )
        self.skip_scraping_check.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        # --- Controles ---
        controls_frame = ttk.Frame(root_window)
        controls_frame.pack(padx=10, pady=5, fill="x")

        self.start_button = ttk.Button(controls_frame, text="Iniciar Proceso Completo", command=self.start_full_process)
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(controls_frame, text="Detener Scraper Actual",
                                      command=self.stop_scraping_scripts_ui, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        # --- Visualización de Estado ---
        status_frame = ttk.LabelFrame(root_window, text="Progreso")
        status_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD, height=15, font=("Arial", 9))
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progressbar = ttk.Progressbar(root_window, variable=self.progress_var, maximum=100)
        self.progressbar.pack(padx=10, pady=(0, 10), fill="x")

        self.toggle_scraping_options()  # Llamar para establecer el estado inicial de los campos de scraping

    def toggle_scraping_options(self):
        """Habilita o deshabilita las opciones de scraping según el checkbox."""
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
        # Asegurar que las actualizaciones de GUI se hagan en el hilo principal
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
            self.progress_var.set(0)  # Caso donde no hay tareas (ej. si se saltan todas)
        self.root_window.update_idletasks()

    def start_full_process(self):
        self.start_button.config(state="disabled")
        if not self.skip_scraping_var.get():
            self.stop_button.config(state="normal")  # Activar botón de detener si se va a hacer scraping
        else:
            self.stop_button.config(state="disabled")

        self.status_text.delete(1.0, tk.END)
        self.stop_scraping_event.clear()  # Reiniciar el evento de detención
        self.progress_var.set(0)

        query = self.query_var.get()
        chrome_profile = self.chrome_profile_var.get()

        if not self.skip_scraping_var.get():  # Validar solo si no se salta el scraping
            if not query:
                self.update_status("Error: El término de búsqueda no puede estar vacío si se realiza scraping.")
                self.finalize_process_ui_state()
                return
            if not chrome_profile or not os.path.isdir(chrome_profile):
                self.update_status(f"Error: La ruta del perfil de Chrome no es válida: {chrome_profile}")
                self.finalize_process_ui_state()
                return

        # Hilo principal para todo el pipeline para no congelar la GUI
        process_thread = threading.Thread(target=self._execute_pipeline, args=(query, chrome_profile))
        process_thread.daemon = True
        process_thread.start()

    def _execute_pipeline(self, query, chrome_profile):
        num_scraper_tasks = 3
        # Definición de tareas base (sin scraping):
        # Parsing (1), Normalizer (1), BarGrapher (1), Graphicator (1), WordCloud (1), Stats (1)
        tasks_base_count = 6

        perform_scraping = not self.skip_scraping_var.get()

        actual_total_tasks = tasks_base_count + (num_scraper_tasks if perform_scraping else 0)
        current_task_num = 0

        def next_task():
            nonlocal current_task_num
            current_task_num += 1
            self.update_progress(current_task_num, actual_total_tasks)

        try:
            if perform_scraping:
                self.update_status("--- Iniciando Fase de Scraping (Secuencial, Navegador Visible) ---")
                # Usar los nombres de scraper de la versión "Original Logic" que creamos
                scraper_modules_and_names = [
                    (AcademicSearch, "AcademicSearch_Original"),
                    (AppliedScience, "AppliedScience_Original"),
                    (ScienceDirect, "ScienceDirect_Original"),
                ]

                scrapers_completed_or_stopped_count = 0
                for module, name in scraper_modules_and_names:
                    if self.stop_scraping_event.is_set():  # Chequear antes de iniciar el siguiente scraper
                        self.update_status(f"Scraping general detenido por el usuario antes de iniciar {name}.")
                        # No se ejecutarán más scrapers. El progreso ya se habrá actualizado por los anteriores.
                        break

                    self.update_status(f"Ejecutando scraper: {name}...")
                    # Llamada directa y secuencial. La función run_scraper debe manejar su propio try/except/finally y el stop_event.
                    module.run_scraper(query, self.stop_scraping_event, self.update_status, chrome_profile, name)

                    scrapers_completed_or_stopped_count += 1
                    next_task()  # Avanzar progreso después de cada scraper (ya sea que complete o se detenga)

                    if self.stop_scraping_event.is_set():  # Chequear si este scraper específico fue detenido
                        self.update_status(f"Scraper {name} detenido por el usuario.")
                        # El bucle for terminará naturalmente o se romperá si el evento se mantiene.
                        # Ya no es necesario el break aquí si queremos que el evento sea "global" para la fase.
                        # Si se presiona stop, el siguiente scraper no iniciará por el chequeo al inicio del bucle.

                # Al final de la fase de scraping (ya sea completada o interrumpida)
                # Asegurar que el progreso de los scrapers esté completo si se detuvo a mitad.
                while scrapers_completed_or_stopped_count < num_scraper_tasks and perform_scraping:
                    # Esto solo se ejecutaría si el bucle de scrapers se rompió prematuramente Y queremos
                    # que la barra de progreso "salte" las tareas de scraping no realizadas.
                    next_task()
                    scrapers_completed_or_stopped_count += 1

                if self.stop_scraping_event.is_set():
                    self.update_status("Fase de Scraping interrumpida. Continuando con las siguientes fases...")
                else:
                    self.update_status("--- Fase de Scraping (Secuencial) Completada ---")

            else:  # Si se salta el scraping
                self.update_status("--- Fase de Scraping OMITIDA por el usuario ---")
                # No se llama a next_task() para los scrapers porque no se ejecutan.
                # actual_total_tasks ya está ajustado.

            # --- Las siguientes fases se ejecutan siempre ---

            self.update_status("--- Iniciando Fase de Parsing ---")
            Parser.run_parser(self.update_status, self.project_root_dir)
            next_task()  # Contar como una tarea completada
            self.update_status("--- Parsing Completado ---")

            self.update_status("--- Iniciando Normalización de Datos ---")
            dataNormalizer.run_data_normalizer(self.update_status, self.project_root_dir)
            next_task()
            self.update_status("--- Normalización de Datos Completada ---")

            self.update_status("--- Iniciando Generación de Visualizaciones ---")

            self.update_status("Generando BarGraph...")
            BarGrapher.run_bargrapher(self.update_status, self.project_root_dir)
            next_task()
            self.update_status("BarGraph generado.")

            self.update_status("Generando Graph (Network) con Lógica Original...")
            graphicator.run_graphicator(self.update_status, self.project_root_dir)  # Usando la versión restaurada
            next_task()
            self.update_status("Graph (Network) con Lógica Original generado.")

            self.update_status("Generando Nube de Palabras...")
            WordCloudGenerator.run_wordcloud_generator(self.update_status, self.project_root_dir)
            next_task()
            self.update_status("Nube de Palabras generada.")

            self.update_status("Generando Estadísticas Adicionales...")
            Stats.run_stats(self.update_status, self.project_root_dir)
            next_task()
            self.update_status("Estadísticas Adicionales generadas.")

            self.update_status("--- Visualizaciones Generadas ---")
            if actual_total_tasks > 0: self.progress_var.set(100)  # Asegurar que la barra llegue al 100% si hubo tareas
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
        self.stop_button.config(state="disabled")  # Siempre deshabilitar al final del pipeline completo
        self.toggle_scraping_options()  # Restaura el estado de los campos de scraping

    def stop_scraping_scripts_ui(self):
        self.update_status("Señal de detención enviada al scraper actual...")
        self.stop_scraping_event.set()
        # El botón se deshabilitará una vez que la fase de scraping termine o se interrumpa por completo,
        # o cuando todo el pipeline termine, en _finalize_ui.
        # Considera deshabilitarlo aquí si solo quieres un intento de "stop" por fase.
        self.stop_button.config(state="disabled")


if __name__ == "__main__":
    main_app_root = tk.Tk()
    app_instance = App(main_app_root)
    main_app_root.mainloop()