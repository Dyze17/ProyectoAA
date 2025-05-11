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
        print("Navegando a ScienceDirect...")
        driver.get("https://www-sciencedirect-com.crai.referencistas.com")

        print("Buscando el botón de 'Iniciar sesión con Google'...")
        google_login_button = wait.until(EC.element_to_be_clickable((By.ID, "btn-google")))
        google_login_button.click()

        print("Buscando el botón de 'My account'...")
        my_account_button = wait.until(EC.element_to_be_clickable((By.ID, "gh-myaccount-btn")))
        my_account_button.click()

        print("Buscando el campo de búsqueda...")
        search_box = wait.until(EC.visibility_of_element_located((By.ID, "qs")))
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        print("Esperando redirección y modificando URL con parámetros...")
        wait.until(EC.url_contains("search"))
        current_url = driver.current_url
        modified_url = f"{current_url}&accessTypes=openaccess&show=100"
        driver.get(modified_url)

        print("Búsqueda inicial completada.")

        while True:
            # 1. Click en checkbox "Select all"
            try:
                print("Buscando y seleccionando el checkbox 'Select all articles' con scroll y JS...")
                select_all_checkbox = wait.until(EC.presence_of_element_located((By.ID, "select-all-results")))
                driver.execute_script("arguments[0].scrollIntoView(true);", select_all_checkbox)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", select_all_checkbox)
                print("Checkbox seleccionado correctamente.")
            except Exception as e:
                print(f"No se pudo seleccionar el checkbox: {e}")
                break  # si no hay checkbox, es probable que no haya más resultados

            # 2. Click en botón Export
            try:
                print("Clic en botón 'Export'...")
                export_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[contains(text(),'Export')]]")
                ))
                driver.execute_script("arguments[0].click();", export_button)
            except Exception as e:
                print(f"No se pudo hacer clic en el botón 'Export': {e}")
                break

            # 3. Click en opción BibTeX
            try:
                print("Clic en 'Export citation to BibTeX'...")
                bibtex_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[contains(text(),'Export citation to BibTeX')]]")
                ))
                driver.execute_script("arguments[0].click();", bibtex_button)
            except Exception as e:
                print(f"No se pudo hacer clic en el botón 'Export citation to BibTeX': {e}")
                break

            # 4. Click en botón "next"
            try:
                print("Buscando botón 'next' para ir a la siguiente página...")
                next_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//li[contains(@class,'next-link')]/a[span[text()='next']]")
                ))
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                driver.execute_script("arguments[0].click();", next_button)
                wait.until(EC.presence_of_element_located((By.ID, "select-all-results")))  # espera que cargue siguiente página
            except Exception as e:
                print("No se encontró el botón 'next' o no se pudo hacer clic. Fin del ciclo.")
                break
            # 5. Se clickea de nuevo para deseleccionar los anteriores
            try:
                print("Buscando y seleccionando el checkbox 'Select all articles' con scroll y JS...")
                select_all_checkbox = wait.until(EC.presence_of_element_located((By.ID, "select-all-results")))
                driver.execute_script("arguments[0].scrollIntoView(true);", select_all_checkbox)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", select_all_checkbox)
                print("Checkbox seleccionado correctamente.")
            except Exception as e:
                print(f"No se pudo seleccionar el checkbox: {e}")
                break  # si no hay checkbox, es probable que no haya más resultados

        print("El navegador permanecerá abierto. Presiona ENTER aquí para cerrarlo manualmente...")
        input()
        driver.quit()

    except Exception as e:
        print(f"Error durante la automatización: {e}")
    finally:
        driver.quit()

# Ejecutar
if __name__ == "__main__":
    query = "computational thinking"
    realizar_login_y_busqueda(query)