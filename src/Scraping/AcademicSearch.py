import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

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
        driver.get("https://research-ebsco-com.crai.referencistas.com/c/rfbjy2/search")

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

        time.sleep(10)
        try:
            print("Buscando y clickeando el label del checkbox (por data-auto)...")
            label_checkbox = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'label[data-auto="control-label"]')
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", label_checkbox)
            label_checkbox.click()
            print("Checkbox seleccionado correctamente a través del label.")
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
        except Exception as e:
            print(f"No se pudo hacer clic en el botón de descarga: {e}")

        try:
            print("Buscando y clickeando el botón de descarga de elementos seleccionados...")
            download_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-auto="bulk-menu-download-button"]')
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
            download_button.click()
            print("Botón de descarga clickeado.")
        except Exception as e:
            print(f"No se pudo hacer clic en el botón de descarga: {e}")

        try:
            print("Buscando y clickeando el botón de formato BibTeX...")
            # Primero buscamos el input de radio
            bibtex_radio = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'input[data-auto="bulk-download-formats-group-input"][value="bibtex"]')
            ))

            # A veces hacer clic directo en el input no funciona, mejor hacemos clic en su etiqueta asociada
            # o usamos JavaScript para hacer clic
            driver.execute_script("arguments[0].scrollIntoView(true);", bibtex_radio)
            driver.execute_script("arguments[0].click();", bibtex_radio)
            print("Opción BibTeX seleccionada correctamente.")

            # Esperar un momento para que el formato sea registrado
            time.sleep(2)

            # Ahora buscamos y hacemos clic en el botón para descargar
            download_confirm_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-auto="bulk-download-modal-download-button"]')
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", download_confirm_button)
            download_confirm_button.click()
            print("Botón de descarga final clickeado.")
        except Exception as e:
            print(f"No se pudo seleccionar el formato BibTeX o confirmar la descarga: {e}")
        time.sleep(5)
        driver.quit()
    except Exception as e:
        print(f"Error durante la automatización: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    query = "computational thinking"
    realizar_login_y_busqueda(query)
