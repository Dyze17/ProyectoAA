import time
import os
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


# La función que será llamada desde gui_controller.py
def run_scraper(query, stop_event, status_callback, chrome_profile_path, scraper_name="ScienceDirect_Original"):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # NO SE USA --headless
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        if not os.path.exists(chrome_profile_path):
            status_callback(
                f"[{scraper_name}] ADVERTENCIA: El directorio del perfil de Chrome no existe: {chrome_profile_path}. Intentando sin perfil.")
        else:
            options.add_argument(f"--user-data-dir={chrome_profile_path}")
    except Exception as e:
        status_callback(f"[{scraper_name}] Error al configurar el perfil de Chrome: {e}. Intentando sin perfil.")

    driver = None
    try:
        status_callback(f"[{scraper_name}] Iniciando WebDriver...")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)

        # Aquí comienza tu lógica original de `realizar_login_y_busqueda` para ScienceDirect
        status_callback(f"[{scraper_name}] Navegando a ScienceDirect...")
        driver.get("https://www-sciencedirect-com.crai.referencistas.com")

        if stop_event.is_set(): status_callback(f"[{scraper_name}] Detenido."); driver.quit(); return

        status_callback(f"[{scraper_name}] Buscando el botón de 'Iniciar sesión con Google'...")
        google_login_button = wait.until(EC.element_to_be_clickable((By.ID, "btn-google")))
        google_login_button.click()
        status_callback(
            f"[{scraper_name}] Clic en 'Iniciar sesión con Google'. Esperando autenticación (puede requerir acción manual)...")

        try:
            WebDriverWait(driver, 120).until(
                EC.any_of(  # Espera a que aparezca CUALQUIERA de estos elementos, indicando login
                    EC.presence_of_element_located((By.ID, "gh-myaccount-btn")),
                    EC.presence_of_element_located((By.ID, "qs"))
                )
            )
            status_callback(f"[{scraper_name}] Login parece exitoso.")
        except TimeoutException:
            status_callback(f"[{scraper_name}] Timeout esperando confirmación de login en ScienceDirect.")
            if driver: driver.quit(); return

        if stop_event.is_set(): status_callback(f"[{scraper_name}] Detenido."); driver.quit(); return

        # Tu lógica original para hacer clic en "My account" si es necesario
        # status_callback(f"[{scraper_name}] Buscando el botón de 'My account'...")
        # my_account_button = wait.until(EC.element_to_be_clickable((By.ID, "gh-myaccount-btn")))
        # my_account_button.click() # Esto podría no ser necesario si el campo de búsqueda ya está visible

        status_callback(f"[{scraper_name}] Buscando el campo de búsqueda...")
        search_box = wait.until(EC.visibility_of_element_located((By.ID, "qs")))
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        status_callback(f"[{scraper_name}] Búsqueda '{query}' enviada.")

        if stop_event.is_set(): status_callback(f"[{scraper_name}] Detenido."); driver.quit(); return

        status_callback(f"[{scraper_name}] Esperando redirección y modificando URL con parámetros...")
        WebDriverWait(driver, 30).until(EC.url_contains("search"))  # Esperar a que la URL contenga 'search'
        time.sleep(2)  # Pausa para estabilizar URL

        current_url = driver.current_url
        # Tu lógica original para modificar la URL
        if "show=100" not in current_url:  # Evitar añadir show=100 si ya está
            base_url_for_params = current_url.split('&show=')[0]  # Quitar show existente si lo hay
            if "?" not in base_url_for_params:  # Si no hay query params
                modified_url = f"{base_url_for_params}?accessTypes=openaccess&show=100"
            else:
                modified_url = f"{base_url_for_params}&accessTypes=openaccess&show=100"
        else:  # si show=100 ya está, solo asegurar accessTypes
            if "accessTypes=openaccess" not in current_url:
                modified_url = f"{current_url}&accessTypes=openaccess"
            else:
                modified_url = current_url

        if modified_url != current_url:
            status_callback(f"[{scraper_name}] Navegando a URL modificada: {modified_url}")
            driver.get(modified_url)
            wait.until(EC.presence_of_element_located((By.ID, "select-all-results")))  # Esperar carga de nueva URL
        else:
            status_callback(f"[{scraper_name}] URL ya contiene los parámetros deseados.")

        status_callback(f"[{scraper_name}] Búsqueda inicial con filtros completada.")

        page_count = 1
        max_pages_scrape_sd = 5  # Límite para pruebas
        while page_count <= max_pages_scrape_sd:  # Tu bucle de paginación original
            if stop_event.is_set():
                status_callback(f"[{scraper_name}] Proceso detenido durante paginación (página {page_count}).")
                break

            status_callback(f"[{scraper_name}] Procesando página {page_count}...")

            try:
                status_callback(f"[{scraper_name}] Buscando y seleccionando el checkbox 'Select all articles'...")
                select_all_checkbox = wait.until(EC.element_to_be_clickable((By.ID, "select-all-results")))
                driver.execute_script("arguments[0].scrollIntoView(true);", select_all_checkbox)
                time.sleep(0.5)
                # select_all_checkbox.click() # Clic normal
                driver.execute_script("arguments[0].click();", select_all_checkbox)  # Clic con JS
                status_callback(f"[{scraper_name}] Checkbox 'Select all' seleccionado.")
                time.sleep(1)
            except Exception as e:
                status_callback(
                    f"[{scraper_name}] No se pudo seleccionar el checkbox 'Select all': {e}. Fin de paginación?")
                break

            if stop_event.is_set(): break
            try:
                status_callback(f"[{scraper_name}] Clic en botón 'Export'...")
                export_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[contains(text(),'Export')]]")
                ))
                # driver.execute_script("arguments[0].scrollIntoView(true);", export_button) # Podría no ser necesario si es clickable
                driver.execute_script("arguments[0].click();", export_button)
                time.sleep(1)
            except Exception as e:
                status_callback(f"[{scraper_name}] No se pudo hacer clic en el botón 'Export': {e}")
                break

            if stop_event.is_set(): break
            try:
                status_callback(f"[{scraper_name}] Clic en 'Export citation to BibTeX'...")
                bibtex_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[contains(text(),'Export citation to BibTeX')]]")
                ))
                driver.execute_script("arguments[0].click();", bibtex_button)
                status_callback(f"[{scraper_name}] Descarga de BibTeX para página {page_count} iniciada.")
                time.sleep(5)  # Espera para la descarga
            except Exception as e:
                status_callback(f"[{scraper_name}] No se pudo hacer clic en 'Export citation to BibTeX': {e}")
                break

            if stop_event.is_set(): break
            # Tu lógica original de deseleccionar (clic de nuevo en "select all")
            try:
                # Re-encontrar el checkbox por si la página se refrescó
                select_all_checkbox_again = wait.until(EC.element_to_be_clickable((By.ID, "select-all-results")))
                if select_all_checkbox_again.is_selected():
                    status_callback(f"[{scraper_name}] Deseleccionando 'Select all' para la siguiente página...")
                    driver.execute_script("arguments[0].click();", select_all_checkbox_again)
                    time.sleep(1)
            except Exception as e_deselect:
                status_callback(f"[{scraper_name}] Advertencia: no se pudo deseleccionar 'Select all': {e_deselect}")

            if stop_event.is_set(): break
            status_callback(f"[{scraper_name}] Buscando botón 'next' para ir a la siguiente página...")
            try:
                # Asegurarse que el botón 'next' no esté deshabilitado
                next_button_xpath = "//li[contains(@class,'next-link') and not(contains(@class,'disabled'))]/a"
                next_button = wait.until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", next_button)  # Clic con JS
                status_callback(f"[{scraper_name}] Navegando a la siguiente página de resultados ({page_count + 1}).")
                wait.until(EC.presence_of_element_located((By.ID, "select-all-results")))  # Espera carga
                page_count += 1
                time.sleep(2)
            except TimeoutException:
                status_callback(f"[{scraper_name}] No se encontró el botón 'next' habilitado o no hay más páginas.")
                break
            except Exception as e_next:
                status_callback(f"[{scraper_name}] Error al intentar ir a la siguiente página: {e_next}")
                break

        status_callback(f"[{scraper_name}] Proceso de scraping finalizado.")
        # El input() original se elimina, el driver se cierra en el finally.

    except WebDriverException as e:
        status_callback(f"[{scraper_name}] Error de WebDriver: {e}.")
    except Exception as e:
        status_callback(f"[{scraper_name}] Error inesperado: {e}")
        import traceback
        status_callback(traceback.format_exc())
    finally:
        if driver:
            try:
                driver.quit()
                status_callback(f"[{scraper_name}] WebDriver cerrado.")
            except Exception as e_quit:
                status_callback(f"[{scraper_name}] Error al cerrar WebDriver: {e_quit}")