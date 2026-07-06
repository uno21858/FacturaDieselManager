# Librerias standar
import glob
import hashlib
import os
from pathlib import Path
import time
import xml.etree.ElementTree as ET
from io import BytesIO
from PIL import Image
# Librerías externas
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
# Archivos locales
from logger_config import logger, LOG_DIR
from DescargaFacturasSAT.BaseDir import BASE_DIR
from utils import base_archivos, conceptos_cfdi


# Configuración
SAT_URL = "https://portalcfdi.facturaelectronica.sat.gob.mx/"
DEMO_URL = "https://www.boxfactura.com/sat-captcha-ai-model/"
RFC_FILE = os.path.join(BASE_DIR, "RFC.txt")
PASSWORD_FILE = os.path.join(BASE_DIR, "passwd.txt")
CAPTCHA_FILE = os.path.join(BASE_DIR, "captcha_sat.png")
BuscarRFC = "GCO740121MC5"
NAMESPACES = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}


def cargar_credenciales():
    try:
        with open(RFC_FILE, 'r') as rfc_file:
            rfc_content = rfc_file.read().strip()
        with open(PASSWORD_FILE, 'r') as password_file:
            password_content = password_file.read().strip()
        return rfc_content, password_content
    except FileNotFoundError:
        logger.error("Uno o ambos archivos de credenciales no se encontraron.")
        raise
    except Exception as e:
        logger.error(f"Error al cargar credenciales: {e}")
        raise

def configurar_navegador(ruta_descarga):
    options = Options()
    #options.add_argument("--headless")
    options.add_argument("--window-size=1920x1920")
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", ruta_descarga)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/xml")  # Evitar confirmación de descarga
    options.set_preference("pdfjs.disabled", True)  # Evitar visor de PDF integrado

    # detecta el OS; log de geckodriver junto a los demás logs, no en el cwd
    import platform
    gecko_log = os.path.join(LOG_DIR, "geckodriver.log")
    open(gecko_log, "w").close()  # solo interesa la última sesión
    if platform.system() == "Windows":
        service = Service(executable_path=os.path.join(BASE_DIR, "geckodriver.exe"), log_output=gecko_log)
    else:  # Mac/Linux: usa geckodriver del PATH
        service = Service(log_output=gecko_log)
    return webdriver.Firefox(service=service, options=options)

def descargar_captcha(driver):
    # Esperar no solo presencia, sino visibilidad
    captcha_element = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "divCaptcha"))
    )
    captcha_screenshot = captcha_element.screenshot_as_png
    time.sleep(1)
    captcha_image = Image.open(BytesIO(captcha_screenshot))
    captcha_image.save(CAPTCHA_FILE)
    logger.info(f"Captcha guardado en {CAPTCHA_FILE}")
    return CAPTCHA_FILE

def resolver_captcha_en_demo(driver, captcha_image):
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    try:
        driver.get(DEMO_URL)
        time.sleep(1)
        upload_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
        )
        upload_element.send_keys(captcha_image)
        time.sleep(8)
        captcha_result = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span.demo-output-result[data-js-result]'))
        ).text
        if not captcha_result:
            # El modelo a veces tarda más; un solo reintento
            time.sleep(10)
            captcha_result = driver.find_element(
                By.CSS_SELECTOR, 'span.demo-output-result[data-js-result]').text
        logger.info(f"Captcha resuelto: {captcha_result}")
        return captcha_result
    finally:
        # Siempre regresar a la pestaña del SAT, aun si el demo falló
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

# Iniciar sesion en el SAT
def iniciar_sesion_en_sat(driver, rfc, password, captcha_text):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "rfc"))
    ).send_keys(rfc)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "password"))
    ).send_keys(password)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "userCaptcha"))
    ).send_keys(captcha_text)
    time.sleep(.5)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "submit"))
    ).click()
    logger.info("Intentando iniciar sesión en el SAT")

# Verificar errores de inicio de sesion
def verificar_error(driver):
    try:
        error_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "msgError"))
        ).text
        logger.error(f"Error detectado: {error_message}")
        return True
    except Exception:
        return False

def crear_estructura_carpetas(base_archivos: str, anio: str, mes: str, RFC: str) -> str:
    """
    Crea la estructura {base}/xml_descargado/{RFC}/{anio}/{mes_texto}
    y regresa la ruta del mes.
    """
    nombres_meses = {
        "1": "01-enero", "2": "02-febrero", "3": "03-marzo", "4": "04-abril",
        "5": "05-mayo", "6": "06-junio", "7": "07-julio", "8": "08-agosto",
        "9": "09-septiembre", "10": "10-octubre", "11": "11-noviembre", "12": "12-diciembre"
    }
    mes_texto = nombres_meses.get(mes, mes)

    ruta_mes = Path(base_archivos) / "xml_descargado" / RFC / anio / mes_texto
    ruta_mes.mkdir(parents=True, exist_ok=True)
    logger.info(f"Carpeta creada o ya existente: {ruta_mes}")
    return str(ruta_mes)


# --- Pasos internos de la descarga (solo los usa descarga()) ---

def _seleccionar_valor(driver, locator, valor):
    """Selecciona una opción de un <select>; si Selenium se niega
    (opción 'disabled' transitoria del SAT), la fuerza con JavaScript."""
    elemento = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(locator))
    try:
        Select(elemento).select_by_value(valor)
    except Exception:
        driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('change'));", elemento, valor)

def _ir_a_recibidos(driver):
    boton_recibidos = WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/form/main/div[1]/div[2]/div[1]/div/div[1]/div/nav/ul/div[2]/li/a")))
    boton_recibidos.click()
    time.sleep(2)
    logger.info("✓ Navegado a Recibidos")

def _aplicar_filtros(driver, year, mes):
    """Selecciona rango de fechas, mes/año, RFC receptor y estado 'vigente'.
    Regresa False si no pudo aplicar algún filtro."""
    # Rango de fechas
    logger.info("Seleccionando rango de fechas...")
    try:
        radio_fechas = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_MainContent_RdoFechas")))
        radio_fechas.click()
        logger.info("✓ Rango de fechas seleccionado")
    except Exception as e:
        logger.warning(f"Error al hacer click en radio de fechas, intentando con JavaScript: {e}")
        driver.execute_script("document.getElementById('ctl00_MainContent_RdoFechas').click();")
        logger.info("✓ Rango de fechas seleccionado (JavaScript)")
    time.sleep(1)

    # Mes y año
    logger.info(f"Seleccionando mes: {mes} y año: {year}")
    try:
        _seleccionar_valor(driver, (By.ID, "ctl00_MainContent_CldFecha_DdlMes"), str(mes))
        _seleccionar_valor(driver, (By.ID, "DdlAnio"), str(year))
    except Exception as e:
        logger.warning(f"No se pudo seleccionar mes/año: {e}")
        return False

    # RFC receptor
    logger.info(f"Ingresando RFC: {BuscarRFC}")
    rfc_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ctl00_MainContent_TxtRfcReceptor")))
    rfc_input.clear()
    rfc_input.send_keys(BuscarRFC)
    time.sleep(1)

    # Estado de comprobante 'vigente'
    logger.info("Seleccionando estado de comprobante...")
    estado_elemento = esperar_elemento_clickeable(
        driver, (By.ID, "ctl00_MainContent_DdlEstadoComprobante"), timeout=15)
    if not estado_elemento:
        logger.error("No se pudo encontrar el elemento de estado")
        return False
    try:
        Select(estado_elemento).select_by_value("1")
        logger.info("Estado de comprobante seleccionado: vigente")
    except Exception as e:
        logger.error(f"Error al seleccionar estado: {e}")
        driver.execute_script("""
            var select = document.getElementById('ctl00_MainContent_DdlEstadoComprobante');
            select.value = '1';
            select.dispatchEvent(new Event('change'));
        """)
        logger.info("Estado seleccionado usando JavaScript")
    time.sleep(.5)
    return True

def _ejecutar_busqueda(driver):
    """Click en 'Buscar CFDI' y espera resultados CON facturas.
    La tabla existe en el DOM aunque el postback regrese vacío; lo que confirma
    una búsqueda real son los botones de descarga."""
    logger.info("Ejecutando búsqueda de CFDIs...")
    try:
        boton_buscar = driver.find_element(By.ID, "ctl00_MainContent_BtnBusqueda")
    except Exception as e:
        # El id a veces no aparece; buscar el botón por su texto visible
        logger.warning(f"No se encontró el botón por id, buscando por texto: {e}")
        try:
            boton_buscar = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                    "//input[@value='Buscar CFDI'] | //button[normalize-space()='Buscar CFDI']")))
        except Exception as e2:
            logger.error(f"No se encontró el botón de búsqueda: {e2}")
            return False

    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_buscar)
    time.sleep(2)
    # Click real (no solo el JS del onclick): el botón es type=submit con
    # clientSubmit=false, así que el envío del formulario lo hace el click nativo
    driver.execute_script("arguments[0].click();", boton_buscar)
    logger.info("✓ Búsqueda ejecutada")

    logger.info("Esperando a que se carguen los resultados...")
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "ctl00_MainContent_tblResult")))
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[@name='BtnDescarga']")))
        time.sleep(2)
        logger.info("✓ Resultados con facturas encontrados")
        return True
    except Exception:
        logger.warning("Sin facturas en los resultados")
        _guardar_debug(driver)
        return False

def _guardar_debug(driver):
    """Guarda screenshot y HTML de lo que ve el navegador, para diagnosticar búsquedas vacías."""
    try:
        with open(os.path.join(LOG_DIR, "busqueda_debug.html"), "w") as f:
            f.write(driver.page_source)
        driver.save_screenshot(os.path.join(LOG_DIR, "busqueda_debug.png"))
        logger.info(f"Debug guardado en {LOG_DIR}/busqueda_debug.html y .png")
    except Exception as e:
        logger.error(f"No se pudo guardar el debug: {e}")

def _siguiente_pagina(driver):
    xpaths = [
        "//ul[contains(@class, 'pagination')]//a[text()='»']",
        "//ul[contains(@class, 'pagination')]//li[last()]/a",
    ]
    for xpath in xpaths:
        try:
            driver.find_element(By.XPATH, xpath).click()
            logger.info("Página cambiada.")
            time.sleep(3)
            return
        except Exception:
            continue
    logger.warning("No se encontró botón de siguiente página, continuando...")

def _descargar_todas(driver, carpeta_destino):
    logger.info("Buscando botones de descarga XML...")
    time.sleep(.3)
    botones_xml = driver.find_elements(By.XPATH, "//span[@name='BtnDescarga']")
    logger.info(f"Total de botones XML encontrados: {len(botones_xml)}")

    if len(botones_xml) == 0:
        logger.warning("No se encontraron facturas para descargar")
        return

    for index in range(len(botones_xml)):
        time.sleep(1)
        try:
            # Re-buscar los botones: el DOM cambia al paginar
            botones_xml = driver.find_elements(By.XPATH, "//span[@name='BtnDescarga']")
            if index < len(botones_xml):
                time.sleep(0.5)
                try:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botones_xml[index])
                        time.sleep(0.3)
                        botones_xml[index].click()
                    except Exception:
                        # Si falla, usar JavaScript click directamente
                        driver.execute_script("arguments[0].click();", botones_xml[index])
                    logger.info(f"Descargando XML {index + 1} de {len(botones_xml)}")
                    esperar_descarga_completa(carpeta_destino)
                except Exception as e:
                    logger.error(f"Error al descargar XML {index + 1}: {e}")

            # Cambiar de página cada 15 facturas
            if (index + 1) % 15 == 0:
                time.sleep(1)
                _siguiente_pagina(driver)

        except Exception as e:
            logger.error(f"Error al procesar factura {index + 1}: {e}")
            continue


# Descargar XML Recibidos
def descarga(driver, carpeta_destino, year, mes=1):
    time.sleep(1)
    _ir_a_recibidos(driver)
    # Re-presionar buscar en una página con el JS roto no sirve: se recarga
    # la página completa entre intentos para empezar con JavaScript fresco
    for intento in (1, 2, 3):
        if intento > 1:
            logger.info(f"Recargando página de búsqueda (intento {intento})...")
            driver.get(driver.current_url)
            time.sleep(3)
        if not _aplicar_filtros(driver, year, mes):
            continue
        if _ejecutar_busqueda(driver):
            break
    else:
        logger.error("Sin resultados tras 3 intentos: mes sin facturas o búsqueda fallida")
        _guardar_debug(driver)
        return
    _descargar_todas(driver, carpeta_destino)
    logger.info("Descarga de XMLs completada.")
    time.sleep(2)

def esperar_elemento_clickeable(driver, locator, timeout=10):
    """
    Espera a que un elemento sea clickeable y maneja elementos que lo puedan obstruir
    """
    try:
        # Primero intenta esperar a que sea clickeable
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        return element
    except Exception:
        # Si no es clickeable, intenta encontrar el elemento y hacer scroll hacia él
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            try:
                element.click()
            except Exception:
                driver.execute_script("arguments[0].click();", element)
            return element
        except Exception:
            return None


def esperar_descarga_completa(carpeta_destino, tiempo_espera=30):
    tiempo_inicio = time.time()
    while time.time() - tiempo_inicio < tiempo_espera:
        archivos_temporales = glob.glob(os.path.join(carpeta_destino, "*.part"))
        if not archivos_temporales:
            break
        time.sleep(1)

def borrar_basura(ruta_mes):
    """
    Elimina archivos duplicados y facturas que tengan un importe en 0 o no contengan el campo 'Importe'.
    """
    archivos_xml = [a for a in os.listdir(ruta_mes) if a.endswith(".xml")]
    hash_dict = {}
    duplicados = []
    facturas_eliminadas = 0
    # Borra duplicados (y archivos vacíos, que el parser XML no puede procesar)
    for archivo in archivos_xml:
        ruta_archivo = os.path.join(ruta_mes, archivo)
        if os.path.getsize(ruta_archivo) == 0:
            os.remove(ruta_archivo)
            logger.info(f"Archivo vacío eliminado: {archivo}")
            continue
        with open(ruta_archivo, "rb") as f:
            archivo_hash = hashlib.md5(f.read()).hexdigest()
        if archivo_hash in hash_dict:
            duplicados.append(ruta_archivo)
        else:
            hash_dict[archivo_hash] = ruta_archivo
    for duplicado in duplicados:
        os.remove(duplicado)
    logger.info(f"Total duplicados eliminados: {len(duplicados)}")

    # Eliminar facturas con importe en 0 o sin el campo Importe
    for archivo in archivos_xml:
        ruta_archivo = os.path.join(ruta_mes, archivo)
        if not os.path.exists(ruta_archivo):  # ya se borró como duplicado
            continue
        try:
            root = ET.parse(ruta_archivo).getroot()
            conceptos = conceptos_cfdi(root)
            eliminar = True
            for concepto in conceptos:
                importe = concepto.attrib.get('Importe')
                if importe and float(importe) > 0:
                    eliminar = False
                    break
            if eliminar:
                os.remove(ruta_archivo)
                logger.info(f"Factura eliminada (sin importes válidos): {ruta_archivo}")
                facturas_eliminadas += 1
        except Exception as e:
            logger.error(f"Error al procesar {ruta_archivo}: {e}")

    logger.info(f"Total facturas eliminadas: {facturas_eliminadas}")

def cambiar_nombre(ruta_mes):
    for archivo in os.listdir(ruta_mes):
        if not archivo.endswith(".xml"):
            continue
        ruta_archivo = os.path.join(ruta_mes, archivo)
        try:
            root = ET.parse(ruta_archivo).getroot()
            comprobante = root if root.tag.endswith('Comprobante') else root.find('.//cfdi:Comprobante', NAMESPACES)
            folio = comprobante.attrib.get('Folio', 'sin_folio') if comprobante is not None else 'sin_folio'

            destino = os.path.join(ruta_mes, f"D{folio}.xml")
            # Evitar sobreescribir si dos facturas traen el mismo folio
            n = 1
            while os.path.exists(destino) and destino != ruta_archivo:
                destino = os.path.join(ruta_mes, f"D{folio}_{n}.xml")
                n += 1
            if destino != ruta_archivo:
                os.rename(ruta_archivo, destino)
                logger.info(f"Archivo renombrado: {os.path.basename(destino)}")
        except Exception as e:
            logger.error(f"Error al procesar {ruta_archivo}: {e}")


def MainDescarga(mes, anio, worker_thread=None):
    mes = str(mes)
    year = str(anio)

    try:
        rfc, password = cargar_credenciales()
    except FileNotFoundError:
        logger.error("Uno o ambos archivos de credenciales no se encontraron.")
        if worker_thread:
            worker_thread.credentials_needed.emit()
        return
    except Exception as e:
        logger.error(f"Error al cargar las credenciales: {e}")
        if worker_thread:
            worker_thread.error.emit("Error", "Ocurrió un error al cargar las credenciales.")
        return

    driver = None
    try:
        carpeta_destino = crear_estructura_carpetas(base_archivos, year, mes, BuscarRFC)
        driver = configurar_navegador(carpeta_destino)
        intentos = 0
        max_intentos = 4
        driver.get(SAT_URL)

        # Esperar carga completa de JavaScript
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        time.sleep(3)

        while intentos < max_intentos:
            try:
                time.sleep(2)
                captcha_path = descargar_captcha(driver)
                captcha_text = resolver_captcha_en_demo(driver, captcha_path)
                iniciar_sesion_en_sat(driver, rfc, password, captcha_text)
                time.sleep(1)
                if verificar_error(driver):
                    intentos += 1
                    logger.info(f"Reintentando... ({intentos}/{max_intentos})")
                    driver.get(SAT_URL)
                    # Re-esperar carga completa
                    WebDriverWait(driver, 20).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete'
                    )
                    time.sleep(3)
                else:
                    descarga(driver, carpeta_destino, year, int(mes))
                    borrar_basura(carpeta_destino)
                    cambiar_nombre(carpeta_destino)
                    if worker_thread:
                        worker_thread.info.emit("Éxito", "Facturas descargadas correctamente")
                    break
            except Exception as e:
                logger.error(f"Error durante el intento: {e}")
                intentos += 1

        if intentos == max_intentos:
            logger.error("Se alcanzó el límite máximo de intentos.")
            if worker_thread:
                worker_thread.error.emit(
                    "Error",
                    "No fue posible completar la descarga después de varios intentos.\nPor favor, inténtelo de nuevo más tarde. Ya que el SAT es una Basura."
                )
    except Exception as e:
        logger.error(f"Error inesperado en el flujo de descarga: {e}")
        if worker_thread:
            worker_thread.error.emit("Error", f"Ocurrió un error inesperado durante la descarga.\nError: {e}")
    finally:
        if driver:
            driver.quit()
        logger.info("Descarga finalizada.")
