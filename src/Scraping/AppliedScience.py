import time
import os
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# La función que será llamada desde gui_controller.py
def run_scraper(query, stop_event, status_callback, chrome_profile_path, scraper_name="AcademicSearch_Original"):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # NO SE USA --headless PARA MANTENER LA VISUALIZACIÓN NORMAL
    # options.add_argument("--window-size=1920,1080") # Opcional si quieres un tamaño específico
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        if not os.path.exists(chrome_profile_path):
            status_callback(
                f"[{scraper_name}] ADVERTENCIA: El directorio del perfil de Chrome no existe: {chrome_profile_path}. Intentando sin perfil específico.")
        else:
            options.add_argument(f"--user-data-dir={chrome_profile_path}")
    except Exception as e:
        status_callback(f"[{scraper_name}] Error al configurar el perfil de Chrome: {e}. Intentando sin perfil.")

    driver = None
    try:
        status_callback(f"[{scraper_name}] Iniciando WebDriver...")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)  # Espera un poco más larga por defecto

        # Aquí comienza tu lógica original de `realizar_login_y_busqueda`
        # con 'print' reemplazado por 'status_callback' y chequeos de 'stop_event'

        status_callback(f"[{scraper_name}] Navegando a Academic Search...")
        driver.get("https://research-ebsco-com.crai.referencistas.com/c/rfbjy2/search?defaultdb=aps")

        if stop_event.is_set():
            status_callback(f"[{scraper_name}] Proceso detenido por el usuario.")
            if driver: driver.quit()
            return

        status_callback(f"[{scraper_name}] Buscando el botón de 'Iniciar sesión con Google'...")
        google_login_button = wait.until(EC.element_to_be_clickable((By.ID, "btn-google")))
        google_login_button.click()
        status_callback(
            f"[{scraper_name}] Clic en 'Iniciar sesión con Google'. Esperando autenticación (puede requerir acción manual)...")

        try:
            search_box = WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.ID, "search-input")))
            status_callback(f"[{scraper_name}] Login exitoso (campo de búsqueda encontrado).")
        except TimeoutException:
            status_callback(
                f"[{scraper_name}] Timeout esperando el campo de búsqueda después del login. ¿Problemas con autenticación/carga?")
            if driver: driver.quit()
            return

        if stop_event.is_set(): status_callback(f"[{scraper_name}] Detenido."); driver.quit(); return

        status_callback(f"[{scraper_name}] Ingresando búsqueda: {query}")
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        status_callback(f"[{scraper_name}] Esperando resultados...")
        wait.until(EC.presence_of_element_located((By.ID, "results-per-page-dropdown-toggle-button")))

        status_callback(f"[{scraper_name}] Clic en botón para desplegar menú...")
        mostrar_button = wait.until(EC.element_to_be_clickable((By.ID, "results-per-page-dropdown-toggle-button")))
        mostrar_button.click()

        status_callback(f"[{scraper_name}] Esperando opción '50' en el dropdown...")
        opcion_50 = wait.until(EC.element_to_be_clickable((By.ID, "results-per-page-dropdown-item-3")))
        opcion_50.click()
        status_callback(f"[{scraper_name}] Mostrando 50 resultados por página.")
        time.sleep(5)  # Esperar a que se carguen los resultados con la nueva cantidad

        if stop_event.is_set(): status_callback(f"[{scraper_name}] Detenido."); driver.quit(); return

        # Descarga de la primera página (Lógica Original)
        try:
            status_callback(f"[{scraper_name}] Buscando y clickeando el label del checkbox (por data-auto)...")
            label_checkbox = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'label[data-auto="control-label"]')
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", label_checkbox)
            driver.execute_script("arguments[0].click();", label_checkbox)  # Usar JS para clic más robusto
            status_callback(f"[{scraper_name}] Checkbox seleccionado correctamente a través del label.")
            time.sleep(1)
        except Exception as e:
            status_callback(f"[{scraper_name}] No se pudo hacer clic en el label del checkbox: {e}")

        if stop_event.is_set(): status_callback(f"[{scraper_name}] Detenido."); driver.quit(); return

        try:
            status_callback(
                f"[{scraper_name}] Buscando y clickeando el botón de descarga de elementos seleccionados...")
            download_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-auto="bulk-menu-download-button"]')
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
            download_button.click()
            status_callback(f"[{scraper_name}] Botón de descarga clickeado.")
            time.sleep(1)
        except Exception as e:
            status_callback(f"[{scraper_name}] No se pudo hacer clic en el botón de descarga: {e}")

        if stop_event.is_set(): status_callback(f"[{scraper_name}] Detenido."); driver.quit(); return

        try:
            status_callback(f"[{scraper_name}] Buscando y clickeando el botón de formato BibTeX...")
            bibtex_radio = wait.until(EC.element_to_be_clickable(  # Cambiado a clickable
                (By.CSS_SELECTOR, 'input[data-auto="bulk-download-formats-group-input"][value="bibtex"]')
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", bibtex_radio)
            driver.execute_script("arguments[0].click();", bibtex_radio)
            status_callback(f"[{scraper_name}] Opción BibTeX seleccionada correctamente.")
            time.sleep(1)

            download_confirm_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-auto="bulk-download-modal-download-button"]')
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", download_confirm_button)
            download_confirm_button.click()
            status_callback(f"[{scraper_name}] Botón de descarga final clickeado. (Página 1)")
        except Exception as e:
            status_callback(f"[{scraper_name}] No se pudo seleccionar el formato BibTeX o confirmar la descarga: {e}")

        status_callback(f"[{scraper_name}] Esperando a que se complete la descarga (Página 1)...")
        time.sleep(5)  # Aumentar el tiempo de espera para la descarga

        if stop_event.is_set(): status_callback(f"[{scraper_name}] Detenido."); driver.quit(); return

        # Cerrar el modal de descarga
        try:
            status_callback(f"[{scraper_name}] Intentando cerrar el modal de descarga...")
            # Intento con botón de cierre específico del modal
            close_button_selector = 'div[role="dialog"] button[data-auto="close-button"], div.s धरती-modal-container button.close-button'
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, close_button_selector)))
            driver.execute_script("arguments[0].click();", close_button)
            status_callback(f"[{scraper_name}] Modal de descarga cerrado con botón.")
            WebDriverWait(driver, 5).until_not(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                               'div[role="dialog"].is-open, div.s धरती-modal-container.open')))  # Espera a que desaparezca
        except TimeoutException:
            status_callback(f"[{scraper_name}] Modal no se cerró con botón o ya estaba cerrado. Intentando con ESC.")
            webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except Exception as e_modal_close:
            status_callback(
                f"[{scraper_name}] No se pudo cerrar el modal de descarga de forma usual: {e_modal_close}. Continuando...")
        time.sleep(3)

        page_number = 2
        max_pages_scrape = 5  # Límite para pruebas
        while page_number <= max_pages_scrape:  # Bucle de paginación original
            if stop_event.is_set():
                status_callback(f"[{scraper_name}] Proceso detenido durante paginación (página {page_number}).")
                break

            status_callback(f"[{scraper_name}] --- Iniciando procesamiento para página {page_number} ---")

            # Deseleccionar el checkbox de la página anterior (lógica original)
            try:
                status_callback(f"[{scraper_name}] Buscando checkbox principal seleccionado para deseleccionar...")
                # Tu lógica original para deseleccionar el checkbox que controla todos los elementos.
                # Esta parte es compleja y puede fallar si la UI cambia.
                # Un enfoque más simple sería no depender de deseleccionar, sino seleccionar solo la página actual.
                # Por ahora, manteniendo tu enfoque original:
                checkboxes_seleccionados = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]:checked')
                if checkboxes_seleccionados:
                    # Asumir que el primer checkbox "maestro" o el de la página anterior necesita ser deseleccionado.
                    # Este es un punto frágil. Lo ideal sería un selector más específico para el checkbox de "todos los resultados" de la página anterior
                    # o el checkbox general si es persistente.
                    # Por ejemplo, si el checkbox de la página 1 sigue siendo `label[data-auto="control-label"]`
                    try:
                        main_cb_label = driver.find_element(By.CSS_SELECTOR, 'label[data-auto="control-label"]')
                        main_cb_input_id = main_cb_label.get_attribute('for')
                        if main_cb_input_id:
                            main_cb_input = driver.find_element(By.ID, main_cb_input_id)
                            if main_cb_input.is_selected():
                                status_callback(
                                    f"[{scraper_name}] Deseleccionando checkbox principal (Pág {page_number - 1})...")
                                driver.execute_script("arguments[0].click();", main_cb_label)  # Clic en el label
                                time.sleep(1)
                    except NoSuchElementException:
                        status_callback(
                            f"[{scraper_name}] No se encontró checkbox principal por label para deseleccionar.")
                    except Exception as e_deselect:
                        status_callback(
                            f"[{scraper_name}] Error menor al intentar deseleccionar checkbox principal: {e_deselect}")


                else:
                    status_callback(
                        f"[{scraper_name}] No se encontraron checkboxes seleccionados para deseleccionar (esperado si es la primera iteración del bucle o el sitio los limpia).")
            except Exception as e:
                status_callback(f"[{scraper_name}] Advertencia: Error al intentar deseleccionar checkboxes: {e}")

            if stop_event.is_set(): break
            status_callback(f"[{scraper_name}] Navegando a la siguiente página de resultados (Mostrar más)...")
            try:
                mostrar_mas_button = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button.eb-pagination__button[data-auto="show-more-button"]')))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", mostrar_mas_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", mostrar_mas_button)
                status_callback(f"[{scraper_name}] Botón 'Mostrar más resultados' clickeado exitosamente.")
                time.sleep(5)  # Esperar carga
            except TimeoutException:
                status_callback(
                    f"[{scraper_name}] No se encontró 'Mostrar más resultados'. Asumiendo fin de resultados.")
                break
            except Exception as e:
                status_callback(f"[{scraper_name}] Error al clickear 'Mostrar más resultados': {e}")
                break

            if stop_event.is_set(): break
            status_callback(f"[{scraper_name}] Seleccionando checkbox de la página {page_number}...")
            page_id = f"result-list-page-{page_number}"
            checkbox_id_for_page = page_id + "-checkbox"
            try:
                page_divider = wait.until(EC.presence_of_element_located((By.ID, page_id)))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
                                      page_divider)
                time.sleep(1)

                page_checkbox_element = wait.until(EC.element_to_be_clickable((By.ID, checkbox_id_for_page)))
                if not page_checkbox_element.is_selected():
                    driver.execute_script("arguments[0].click();", page_checkbox_element)
                    status_callback(f"[{scraper_name}] Checkbox de la página {page_number} seleccionado.")
                else:
                    status_callback(f"[{scraper_name}] Checkbox de la página {page_number} ya estaba seleccionado.")
                time.sleep(1)
            except Exception as e:
                status_callback(
                    f"[{scraper_name}] Error al seleccionar el checkbox de la página {page_number}: {e}. Fin de ciclo de paginación.")
                break

            if stop_event.is_set(): break
            status_callback(f"[{scraper_name}] Volviendo al inicio para descargar página {page_number}...")
            try:
                back_to_top_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-auto="back-to-top"]'))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", back_to_top_button)
                driver.execute_script("arguments[0].click();", back_to_top_button)
                status_callback(f"[{scraper_name}] Botón 'Volver al inicio' clickeado.")
                time.sleep(3)
            except Exception as e:
                status_callback(f"[{scraper_name}] No se pudo hacer clic en 'Volver al inicio': {e}")
                # Continuar de todas formas, el botón de descarga debería estar visible si hay elementos seleccionados

            if stop_event.is_set(): break
            # Descarga de la página actual (Lógica Original)
            try:
                status_callback(f"[{scraper_name}] Buscando botón de descarga (Pág {page_number})...")
                download_button_page_n = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button[data-auto="bulk-menu-download-button"]')
                ))
                driver.execute_script("arguments[0].scrollIntoView(true);", download_button_page_n)
                download_button_page_n.click()
                time.sleep(1)

                bibtex_radio_page_n = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'input[data-auto="bulk-download-formats-group-input"][value="bibtex"]')
                ))
                driver.execute_script("arguments[0].click();", bibtex_radio_page_n)
                time.sleep(1)

                download_confirm_page_n = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button[data-auto="bulk-download-modal-download-button"]')
                ))
                download_confirm_page_n.click()
                status_callback(f"[{scraper_name}] Descarga final para página {page_number} clickeada.")
                time.sleep(5)  # Espera descarga
            except Exception as e:
                status_callback(f"[{scraper_name}] Error en descarga para página {page_number}: {e}")
                # Podría ser útil romper el bucle aquí si la descarga es crítica

            if stop_event.is_set(): break
            # Cerrar modal (Lógica Original)
            try:
                status_callback(f"[{scraper_name}] Cerrando modal de descarga (Pág {page_number})...")
                close_button_selector_page_n = 'div[role="dialog"] button[data-auto="close-button"], div.s धरती-modal-container button.close-button'
                close_button_page_n = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, close_button_selector_page_n)))
                driver.execute_script("arguments[0].click();", close_button_page_n)
                WebDriverWait(driver, 5).until_not(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[role="dialog"].is-open, div.s धरती-modal-container.open')))
                status_callback(f"[{scraper_name}] Modal cerrado (Pág {page_number}).")
            except TimeoutException:
                status_callback(f"[{scraper_name}] Modal (Pág {page_number}) no se cerró con botón. Intentando ESC.")
                webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except Exception as e_modal_close_page_n:
                status_callback(
                    f"[{scraper_name}] No se pudo cerrar modal (Pág {page_number}): {e_modal_close_page_n}.")
            time.sleep(3)

            page_number += 1

        status_callback(f"[{scraper_name}] Fin del bucle de paginación o límite alcanzado.")
        time.sleep(5)  # Pausa final antes de cerrar

    except WebDriverException as e:
        status_callback(f"[{scraper_name}] Error de WebDriver: {e}. ¿Está ChromeDriver en el PATH y es compatible?")
        import traceback
        status_callback(traceback.format_exc())
    except Exception as e:
        status_callback(f"[{scraper_name}] Error inesperado durante la automatización: {e}")
        import traceback
        status_callback(traceback.format_exc())
    finally:
        if driver:
            try:
                driver.quit()
                status_callback(f"[{scraper_name}] WebDriver cerrado.")
            except Exception as e_quit:
                status_callback(f"[{scraper_name}] Error al cerrar WebDriver: {e_quit}")