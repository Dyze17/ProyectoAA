import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def realizar_login_y_busqueda(query):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    profile_path = r"C:\Users\ASUS\chromeSelenium"
    options.add_argument(f"--user-data-dir={profile_path}")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        print("Navegando a Academic Search...")
        driver.get("https://research-ebsco-com.crai.referencistas.com/c/rfbjy2/search?defaultdb=asn")

        print("Buscando el botón de 'Iniciar sesión con Google'...")
        google_login_button = wait.until(EC.element_to_be_clickable((By.ID, "btn-google")))
        google_login_button.click()

        print("Esperando campo de búsqueda...")
        search_box = wait.until(EC.presence_of_element_located((By.ID, "search-input")))

        print(f"Ingresando búsqueda: {query}")
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        print("Esperando resultados...")
        wait.until(EC.presence_of_element_located((By.ID, "results-per-page-dropdown-toggle-button")))

        print("Clic en botón para desplegar menú...")
        mostrar_button = wait.until(EC.element_to_be_clickable((By.ID, "results-per-page-dropdown-toggle-button")))
        mostrar_button.click()

        print("Esperando opción '50' en el dropdown...")
        opcion_50 = wait.until(EC.element_to_be_clickable((By.ID, "results-per-page-dropdown-item-3")))
        opcion_50.click()

        time.sleep(5)  # Esperar a que se carguen los resultados con la nueva cantidad

        try:
            print("Buscando y clickeando el label del checkbox (por data-auto)...")
            label_checkbox = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'label[data-auto="control-label"]')
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", label_checkbox)
            label_checkbox.click()
            print("Checkbox seleccionado correctamente a través del label.")
            time.sleep(1)  # Pequeña pausa para asegurar que el checkbox esté seleccionado
        except Exception as e:
            print(f"No se pudo hacer clic en el label del checkbox: {e}")

        try:
            print("Buscando y clickeando el botón de descarga de elementos seleccionados...")
            download_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-auto="bulk-menu-download-button"]')
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
            download_button.click()
            print("Botón de descarga clickeado.")
            time.sleep(1)  # Pequeña pausa para asegurar que se abra el modal de descarga
        except Exception as e:
            print(f"No se pudo hacer clic en el botón de descarga: {e}")

        try:
            print("Buscando y clickeando el botón de formato BibTeX...")
            bibtex_radio = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'input[data-auto="bulk-download-formats-group-input"][value="bibtex"]')
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", bibtex_radio)
            driver.execute_script("arguments[0].click();", bibtex_radio)
            print("Opción BibTeX seleccionada correctamente.")
            time.sleep(1)

            download_confirm_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-auto="bulk-download-modal-download-button"]')
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", download_confirm_button)
            download_confirm_button.click()
            print("Botón de descarga final clickeado.")
        except Exception as e:
            print(f"No se pudo seleccionar el formato BibTeX o confirmar la descarga: {e}")

        print("Esperando a que se complete la descarga...")
        time.sleep(3)  # Aumentar el tiempo de espera para la descarga

        # Cerrar el modal de descarga (usando JavaScript para evitar problemas de intercepción)
        try:
            print("Cerrando el modal de descarga...")
            # Primero intentamos cerrar el modal haciendo clic en el overlay
            try:
                overlay = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div.nuc-bulk-download-modal__overlay')
                ))
                driver.execute_script("arguments[0].click();", overlay)
                print("Modal cerrado clickeando en el overlay.")
            except:
                # Si no funciona, intentamos con el botón de cierre
                close_button = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'button[data-auto="close-button"]')
                ))
                driver.execute_script("arguments[0].click();", close_button)
                print("Modal cerrado clickeando en el botón de cierre.")

            # Verificar que el modal se ha cerrado esperando a que desaparezca
            try:
                WebDriverWait(driver, 5).until_not(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div.nuc-bulk-download-modal__overlay.eb-modal__overlay--forward-animate'))
                )
                print("Modal cerrado correctamente.")
            except TimeoutException:
                print("ADVERTENCIA: El modal parece seguir presente. Intentando continuar...")
                # Intentar hacer clic en un área vacía de la página para cerrar cualquier modal
                driver.execute_script("document.body.click();")
                time.sleep(2)
        except Exception as e:
            print(f"No se pudo cerrar el modal de descarga: {e}")
        time.sleep(3)    # Esperar a que la página se estabilice después de cerrar el modal

        page_number = 2
        while True:
            try:
                # Deseleccionar el checkbox de la primera página
                try:
                    print("Buscando el primer checkbox seleccionado en la página...")
                    # Obtener todos los checkboxes seleccionados
                    checkboxes_seleccionados = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]:checked')
                    if checkboxes_seleccionados:
                        print(f"Se encontraron {len(checkboxes_seleccionados)} checkboxes seleccionados.")

                        # Deseleccionar el primer checkbox que controla todos los elementos
                        # Intentamos identificarlo por su posición o atributos
                        for i, checkbox in enumerate(checkboxes_seleccionados):
                            try:
                                # Intentar obtener el texto cercano o el aria-label
                                parent_element = checkbox.find_element(By.XPATH, "./..")
                                if parent_element:
                                    aria_label = checkbox.get_attribute("aria-label")
                                    print(f"Checkbox #{i + 1} - aria-label: {aria_label}")

                                    # Si el aria-label contiene "Seleccionar todos" o similar
                                    if aria_label and ("todos" in aria_label.lower() or "all" in aria_label.lower() or
                                                       "1 -" in aria_label or "resultados 1" in aria_label.lower()):
                                        print(f"Encontrado el checkbox principal con aria-label: {aria_label}")
                                        driver.execute_script("arguments[0].click();", checkbox)
                                        time.sleep(1)
                                        print("Checkbox principal deseleccionado.")
                                        break
                            except:
                                pass

                        # Si no encontramos ninguno específico, intentamos con el primero
                        if checkboxes_seleccionados[0].is_selected():
                            print("Deseleccionando el primer checkbox seleccionado...")
                            driver.execute_script("arguments[0].click();", checkboxes_seleccionados[0])
                            time.sleep(1)
                            print("Primer checkbox deseleccionado.")
                    else:
                        print("No se encontraron checkboxes seleccionados.")
                except Exception as e:
                    print(f"Error al intentar deseleccionar checkboxes: {e}")

                print("\n--- NAVEGACIÓN A LA SIGUIENTE PÁGINA DE RESULTADOS ---")
                try:
                    print("Buscando específicamente el botón de 'Mostrar más resultados' con el icono de archivo...")

                    # Buscar el botón por selector más específico que incluye la clase del botón de paginación
                    mostrar_mas_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR,
                                                        'button.eb-pagination__button[data-auto="show-more-button"]'))
                    )

                    print(f"Botón encontrado: {mostrar_mas_button.get_attribute('outerHTML')[:100]}...")

                    # Asegurar que el botón es visible en la pantalla
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", mostrar_mas_button)

                    time.sleep(2)

                    # Intentar el clic usando JavaScript para evitar problemas de intercepción
                    print("Intentando hacer clic en el botón...")
                    driver.execute_script("arguments[0].click();", mostrar_mas_button)
                    print("Botón 'Mostrar más resultados' clickeado exitosamente.")

                    # Esperar a que se carguen más resultados
                    print("Esperando a que se carguen más resultados...")
                    time.sleep(3)
                except Exception as e:
                    print(f"Error al trabajar con el botón 'Mostrar más resultados': {e}")

                print("\n--- SELECCIONANDO CHECKBOX DE LA SIGUIENTE PAGINA PÁGINA ---")
                page_id = f"result-list-page-{page_number}"
                try:
                    # Primero, desplazarnos hasta el divisor de página para asegurarnos de que es visible
                    page_divider = wait.until(EC.presence_of_element_located(
                        (By.ID, page_id)
                    ))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
                                          page_divider)
                    time.sleep(1)

                    checkbox_id = page_id + "-checkbox"
                    # Ahora buscamos el checkbox específico de la página 2
                    page_checkbox = wait.until(EC.presence_of_element_located(
                        (By.ID, checkbox_id)
                    ))

                    # Verificar si ya está seleccionado
                    if page_checkbox.is_selected():
                        print("El checkbox de la página 2 ya está seleccionado.")
                    else:
                        # Hacer clic en el checkbox usando JavaScript para mayor confiabilidad
                        print("Seleccionando el checkbox de la página 2...")
                        driver.execute_script("arguments[0].click();", page_checkbox)
                        time.sleep(1)

                        # Verificar que se ha seleccionado
                        if page_checkbox.is_selected():
                            print("Checkbox de la página 2 seleccionado correctamente.")
                        else:
                            print(
                                "ADVERTENCIA: No se pudo verificar que el checkbox fue seleccionado. Intentando nuevamente...")
                            driver.execute_script("arguments[0].checked = true;", page_checkbox)
                except Exception as e:
                    print(f"Error al seleccionar el checkbox de la página 2: {e}")

                # Se vuelve al inicio para descargar
                try:
                    print("Buscando el botón 'Volver al inicio'...")
                    back_to_top_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-auto="back-to-top"]'))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", back_to_top_button)
                    driver.execute_script("arguments[0].click();", back_to_top_button)
                    print(" Botón 'Volver al inicio' clickeado correctamente.")
                except Exception as e:
                    print(f" No se pudo hacer clic en el botón 'Volver al inicio': {e}")
                time.sleep(3)

                # Se descarga la pagina seleccionada
                try:
                    print("Buscando y clickeando el botón de descarga de elementos seleccionados...")
                    download_button = wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, 'button[data-auto="bulk-menu-download-button"]')
                    ))
                    driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
                    download_button.click()
                    print("Botón de descarga clickeado.")
                    time.sleep(1)  # Pequeña pausa para asegurar que se abra el modal de descarga
                except Exception as e:
                    print(f"No se pudo hacer clic en el botón de descarga: {e}")

                try:
                    print("Buscando y clickeando el botón de formato BibTeX...")
                    bibtex_radio = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'input[data-auto="bulk-download-formats-group-input"][value="bibtex"]')
                    ))
                    driver.execute_script("arguments[0].scrollIntoView(true);", bibtex_radio)
                    driver.execute_script("arguments[0].click();", bibtex_radio)
                    print("Opción BibTeX seleccionada correctamente.")
                    time.sleep(1)

                    download_confirm_button = wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, 'button[data-auto="bulk-download-modal-download-button"]')
                    ))
                    driver.execute_script("arguments[0].scrollIntoView(true);", download_confirm_button)
                    download_confirm_button.click()
                    print("Botón de descarga final clickeado.")
                except Exception as e:
                    print(f"No se pudo seleccionar el formato BibTeX o confirmar la descarga: {e}")
                time.sleep(3)  # Aumentar el tiempo de espera para la descarga

                # Cerrar el modal de descarga (usando JavaScript para evitar problemas de intercepción)
                try:
                    print("Cerrando el modal de descarga...")
                    # Primero intentamos cerrar el modal haciendo clic en el overlay
                    try:
                        overlay = wait.until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, 'div.nuc-bulk-download-modal__overlay')
                        ))
                        driver.execute_script("arguments[0].click();", overlay)
                        print("Modal cerrado clickeando en el overlay.")
                    except:
                        # Si no funciona, intentamos con el botón de cierre
                        close_button = wait.until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, 'button[data-auto="close-button"]')
                        ))
                        driver.execute_script("arguments[0].click();", close_button)
                        print("Modal cerrado clickeando en el botón de cierre.")

                    # Verificar que el modal se ha cerrado esperando a que desaparezca
                    try:
                        WebDriverWait(driver, 5).until_not(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, 'div.nuc-bulk-download-modal__overlay.eb-modal__overlay--forward-animate'))
                        )
                        print("Modal cerrado correctamente.")
                    except TimeoutException:
                        print("ADVERTENCIA: El modal parece seguir presente. Intentando continuar...")
                        # Intentar hacer clic en un área vacía de la página para cerrar cualquier modal
                        driver.execute_script("document.body.click();")
                        time.sleep(2)
                except Exception as e:
                    print(f"No se pudo cerrar el modal de descarga: {e}")
                time.sleep(3)

                page_number += 1
            except Exception as e:
                print(f"No se encontraron mas paginas {e}")

        time.sleep(5)

    except Exception as e:
        print(f"Error durante la automatización: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    query = "computational thinking"
    realizar_login_y_busqueda(query)