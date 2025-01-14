# Librerias standar
import glob
import hashlib
import os
import sys
import time
import xml.etree.ElementTree as ET
from contextlib import nullcontext
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
from PySide6 import QtWidgets as qtw
# Archivos locales
from logger_config import logger
from Credenciales.credencial import MainCreateCredentials
from DescargaFacturasSAT.BaseDir import BASE_DIR
from Credenciales.credencial import UiForm as CredencialesForm
from utils import base_archivos


# Configuración
SAT_URL = "https://portalcfdi.facturaelectronica.sat.gob.mx/"
DEMO_URL = "https://www.boxfactura.com/sat-captcha-ai-model/"
RFC_FILE = os.path.join(BASE_DIR, "RFC.txt")
PASSWORD_FILE = os.path.join(BASE_DIR, "passwd.txt")
CAPTCHA_FILE = os.path.join(BASE_DIR, "captcha_sat.png")
BuscarRFC = "GCO740121MC5"


def cargar_credenciales():
    try:
        with open(RFC_FILE, 'r') as rfc_file:
            rfc_content = rfc_file.read().strip()
        with open(PASSWORD_FILE, 'r') as password_file:
            password_content = password_file.read().strip()
        return rfc_content, password_content
    except FileNotFoundError:
        MainCreateCredentials()
        logger.error("Uno o ambos archivos de credenciales no se encontraron.")
        raise
    except Exception as e:
        logger.error(f"Error al cargar credenciales: {e}")
        raise

def configurar_navegador(ruta_descarga):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920x1080")
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", ruta_descarga)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/xml")  # Evitar confirmación de descarga
    options.set_preference("pdfjs.disabled", True)  # Evitar visor de PDF integrado

    service = Service(executable_path=os.path.join(BASE_DIR,"geckodriver.exe"))
    driver = webdriver.Firefox(service=service, options=options)
    return driver

def descargar_captcha(driver):
    captcha_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "divCaptcha"))
    )
    captcha_screenshot = captcha_element.screenshot_as_png
    time.sleep(2)
    captcha_image = Image.open(BytesIO(captcha_screenshot))
    captcha_image.save(CAPTCHA_FILE)
    logger.info(f"Captcha guardado en {CAPTCHA_FILE}")
    return CAPTCHA_FILE

def resolver_captcha_en_demo(driver, captcha_image):
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
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
    if len(captcha_result) == 0:
        time.sleep(15)
        try:
            captcha_result = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span.demo-output-result[data-js-result]')) or
                EC.presence_of_element_located((By.CLASS_NAME, "demo-output-result")))
        except Exception as e:
            logger.error(f"Error al resolver captcha: {e}")
        return captcha_result
    logger.info(f"Captcha resuelto: {captcha_result}")
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return captcha_result

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
    except:
        return False

def crear_estructura_carpetas(base_dir, anio, mes, RFC):
    # Meses en texto
    nombres_meses = {
        "1": "enero", "2": "febrero", "3": "marzo", "4": "abril",
        "5": "mayo", "6": "junio", "7": "julio", "8": "agosto",
        "9": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"
    }
    mes_texto = nombres_meses.get(mes, mes)
    ruta_RFC = os.path.join(base_dir, "xml_descargado", RFC)
    ruta_anio = os.path.join(ruta_RFC, anio)
    ruta_mes = os.path.join(ruta_anio, mes_texto)
    os.makedirs(ruta_mes, exist_ok=True)
    logger.info(f"Carpeta creada o ya existente: {ruta_mes}")
    return ruta_mes

# Descargar XML Recibidos
def descarga(driver, carpeta_destino, mes, year):
    time.sleep(2)
    # Navegar a la sección de Recibidos
    boton_recibidos = WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/form/main/div[1]/div[2]/div[1]/div/div[1]/div/nav/ul/div[2]/li/a")))
    boton_recibidos.click()
    # Seleccionar rango de fechas
    driver.find_element(By.ID, "ctl00_MainContent_RdoFechas").click()
    # Seleccionar mes
    select_mes = Select(driver.find_element(By.ID, "ctl00_MainContent_CldFecha_DdlMes"))
    select_mes.select_by_value(mes)
    # Seleccionar año
    select_anio = (Select(driver.find_element(By.XPATH, "//*[@id='DdlAnio']")) or
                   driver.find_elements(By.NAME, "ctl00$MainContent$CldFecha$DdlAnio"))
    select_anio.select_by_value(str(year))
    # Ingresar RFC
    driver.find_element(By.XPATH, "//*[@id='ctl00_MainContent_TxtRfcReceptor']").send_keys(BuscarRFC)
    Select(driver.find_element(By.ID, "ctl00_MainContent_DdlEstadoComprobante")).select_by_value("1")
    driver.find_element(By.ID, "ctl00_MainContent_BtnBusqueda").click()
    time.sleep(1)
    # Se va hasta abajo de la página para cargar todas las facturas
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(.5)
    botones_descarga = driver.find_elements(By.ID, "BtnDescarga") or driver.find_elements(By.XPATH, "//*[@id='BtnDescarga']")
    for index, boton in enumerate(botones_descarga, start=1):
        time.sleep(1)
        try:
            time.sleep(1)
            boton.click()
            logger.info(f"Descargando XML {index} de {len(botones_descarga)}")
            esperar_descarga_completa(carpeta_destino)
            if index % 15 == 0:
                time.sleep(1)  # Espera antes de cambiar de página
                try:
                    driver.find_element(By.XPATH, "/html/body/form/main/div[1]/div[2]"
                                                  "/div[1]/div[2]/div[1]/div[3]/ul/li[36]/a").click()

                    logger.info("Página cambiada a .")
                    time.sleep(3)
                except Exception as e:
                    logger.error(f"Error al cambiar de página: {e}")
        except Exception as e:
            logger.error(f"Error al descargar XML {index}: {e}")
        finally:
            continue

    time.sleep(.5)
    borrar_basura(carpeta_destino)
    driver.quit()

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
    archivos = os.listdir(ruta_mes)
    archivos_xml = [archivo for archivo in archivos if archivo.endswith(".xml")]
    hash_dict = {}
    duplicados = []
    facturas_eliminadas = 0
    # Borra duplicados
    for archivo in archivos_xml:
        ruta_archivo = os.path.join(ruta_mes, archivo)
        with open(ruta_archivo, "rb") as f:
            archivo_hash = hashlib.md5(f.read()).hexdigest()
        if archivo_hash in hash_dict:
            duplicados.append(ruta_archivo)
        else:
            hash_dict[archivo_hash] = ruta_archivo
    for duplicado in duplicados:
        os.remove(duplicado)
        #print(f"Archivo duplicado eliminado: {duplicado}")
    logger.info(f"Total duplicados eliminados: {len(duplicados)}")

    # Eliminar facturas con importe en 0 o sin el campo Importe
    for archivo in archivos_xml:
        ruta_archivo = os.path.join(ruta_mes, archivo)
        try:
            tree = ET.parse(ruta_archivo)
            root = tree.getroot()
            namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}
            conceptos = root.findall('.//cfdi:Concepto', namespaces)
            eliminar = True
            for concepto in conceptos:
                importe = concepto.attrib.get('Importe')
                if importe and float(importe) > 0 or importe == nullcontext:
                    eliminar = False
            if eliminar:
                os.remove(ruta_archivo)
                logger.info(f"Factura eliminada (sin importes válidos): {ruta_archivo}")
                facturas_eliminadas += 1

        except Exception as e:
            logger.error(f"Error al procesar {ruta_archivo}: {e}")

    logger.info(f"Total facturas eliminadas: {facturas_eliminadas}")
    time.sleep(1)
    cambiar_nombre(ruta_mes)

def cambiar_nombre(ruta_mes):
    for archivo in os.listdir(ruta_mes):
        ruta_archivo = os.path.join(ruta_mes, archivo)
        try:
            tree = ET.parse(ruta_archivo)
            root = tree.getroot()
            namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}
            comprobante = root if root.tag.endswith('Comprobante') else root.find('.//cfdi:Comprobante', namespaces)

            if comprobante is not None:
                folio = comprobante.attrib.get('Folio', 'Folio no encontrado')
            else:
                folio = "Folio no encontrado"

            os.rename(ruta_archivo, os.path.join(ruta_mes, f"D{folio}.xml"))
            logger.info(f"Archivo renombrado: D{folio}.xml")
        except Exception as e:
            logger.error(f"Error al procesar {ruta_archivo}: {e}")
        finally:
            continue

def MainDescarga(MainWindow):
    mes = str(MainWindow.mes_numerico_seleccionado)
    year = str(MainWindow.anio_seleccionado)
    try:
        rfc, password = cargar_credenciales()
    except FileNotFoundError:
        logger.error("Uno o ambos archivos de credenciales no se encontraron.")
        qtw.QMessageBox.warning(
            MainWindow,
            "Credenciales faltantes",
            "No se encontraron las credenciales. Por favor, introdúzcalas para continuar."
        )

        # Abre la ventana de creación de credenciales y espera que el usuario las cree
        ventana_credenciales = CredencialesForm(callback=lambda: None)
        ventana_credenciales.exec()
        return
    except Exception as e:
        logger.error(f"Error al cargar las credenciales: {e}")
        qtw.QMessageBox.critical(MainWindow, "Error", "Ocurrió un error al cargar las credenciales.")
        return
    try:
        carpeta_destino = crear_estructura_carpetas(base_archivos, year, mes, BuscarRFC)
        driver = configurar_navegador(carpeta_destino)
        intentos = 0
        max_intentos = 4
        driver.get(SAT_URL)

        while intentos < max_intentos:

            try:
                time.sleep(1)
                captcha_path = descargar_captcha(driver)
                captcha_text = resolver_captcha_en_demo(driver, captcha_path)
                iniciar_sesion_en_sat(driver, rfc, password, captcha_text)

                if verificar_error(driver):
                    intentos += 1
                    logger.info(f"Reintentando... ({intentos}/{max_intentos})")
                    driver.get(SAT_URL)
                else:
                    descarga(driver, carpeta_destino, mes, year)
                    break
            except Exception as e:
                logger.error(f"Error durante el intento: {e}")
                intentos += 1

        if intentos == max_intentos:
            logger.error("Se alcanzó el límite máximo de intentos.")
            qtw.QMessageBox.critical(MainWindow, "Error", "No fue posible completar la descarga después de varios intentos."
                                                          "\nPor favor, inténtelo de nuevo más tarde. Ya que el SAT es una Basura.")
    except Exception as e:
        logger.error(f"Error inesperado en el flujo de descarga: {e}")
        qtw.QMessageBox.critical(MainWindow, "Error", "Ocurrió un error inesperado durante la descarga."
                                                      f"\nError: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()
        logger.info("Descarga finalizada.")

