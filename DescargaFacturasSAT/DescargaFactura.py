# Librerias standar
import glob
import hashlib
import os
from pathlib import Path
import time
import xml.etree.ElementTree as ET
from contextlib import nullcontext
from io import BytesIO
from PIL import Image
# Librerías externas
from selenium import webdriver
from selenium.webdriver import Keys
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
    #options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", ruta_descarga)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/xml")
    options.set_preference("pdfjs.disabled", True)

    service = Service(executable_path=os.path.join(BASE_DIR,"geckodriver.exe"))
    driver = webdriver.Firefox(service=service, options=options)

    # Forzar tamaño de ventana después de crear el driver
    driver.maximize_window()
    driver.set_window_size(1920, 1080)
    driver.set_window_position(0, 0)

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

def crear_estructura_carpetas(base_archivos: str, anio: str, mes: str, RFC: str) -> str:
    """
    Crea una estructura de carpetas en base a los parámetros proporcionados.

    Args:
        base_archivos (str): Ruta base donde se crearán las carpetas.
        anio (str): Año en formato de texto (e.g., "2025").
        mes (str): Mes en formato numérico (e.g., "1" para enero).
        RFC (str): RFC del cliente o empresa.

    Returns:
        str: Ruta completa de la carpeta creada para el mes específico.
    """
    # Diccionario de nombres de meses
    nombres_meses = {
        "1": "enero", "2": "febrero", "3": "marzo", "4": "abril",
        "5": "mayo", "6": "junio", "7": "julio", "8": "agosto",
        "9": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"
    }

    # Obtener el nombre del mes en texto
    mes_texto = nombres_meses.get(mes, mes)
    logger.info(f"Mes en texto: {mes_texto}")

    # Crear las rutas usando pathlib
    ruta_base = Path(base_archivos)
    ruta_RFC = ruta_base / "xml_descargado" / RFC
    ruta_anio = ruta_RFC / anio
    ruta_mes = ruta_anio / mes_texto

    # Crear las carpetas si no existen
    ruta_mes.mkdir(parents=True, exist_ok=True)
    logger.info(f"Carpeta creada o ya existente: {ruta_mes}")

    return str(ruta_mes)

def scroll_and_wait(driver, scroll_method='smooth'):
    """
    Función mejorada para hacer scroll y esperar a que se cargue el contenido
    """
    logger.info(f"Iniciando scroll con método: {scroll_method}")

    try:
        # Primero, obtener la altura inicial
        initial_height = driver.execute_script("return document.body.scrollHeight")
        logger.info(f"Altura inicial de la página: {initial_height}px")

        if scroll_method == 'smooth':
            # Scroll suave en incrementos
            for i in range(0, initial_height, 500):
                driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.3)

        elif scroll_method == 'end':
            # Scroll directo al final
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        elif scroll_method == 'keys':
            # Usar teclas para hacer scroll
            body = driver.find_element(By.TAG_NAME, 'body')
            for _ in range(10):
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.5)

        # Esperar a que se cargue más contenido
        time.sleep(3)

        # Verificar si la altura cambió (indica que se cargó más contenido)
        new_height = driver.execute_script("return document.body.scrollHeight")
        logger.info(f"Nueva altura después del scroll: {new_height}px")

        if new_height > initial_height:
            logger.info("Se detectó contenido adicional cargado")
        else:
            logger.info("No se detectó contenido adicional")

        return True

    except Exception as e:
        logger.error(f"Error durante el scroll: {e}")
        return False

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
    except:
        # Si no es clickeable, intenta encontrar el elemento y hacer scroll hacia él
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            # Hacer scroll hacia el elemento
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)

            # Intentar hacer click con JavaScript si el click normal falla
            try:
                element.click()
                return element
            except:
                driver.execute_script("arguments[0].click();", element)
                return element
        except:
            return None

def descarga(driver, carpeta_destino, mes, year):
    time.sleep(2)

    # Navegar a la sección de Recibidos
    boton_recibidos = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/form/main/div[1]/div[2]/div[1]/div/div[1]/div/nav/ul/div[2]/li/a")))
    boton_recibidos.click()

    # Seleccionar rango de fechas
    driver.find_element(By.ID, "ctl00_MainContent_RdoFechas").click()
    time.sleep(3)
    # Seleccionar mes
    select_mes = Select(driver.find_element(By.ID, "ctl00_MainContent_CldFecha_DdlMes"))
    select_mes.select_by_value(mes)
    time.sleep(2)

    # Seleccionar año (corregido)
    logger.info(f"Seleccionando año: {year}")
    full_year = "20" + year

    time.sleep(2)
    # Intentar encontrar el elemento del año con diferentes ID y XPATH
    try:
        select_anio = Select(driver.find_element(By.ID, "ctl00_MainContent_CldFecha_DdlAnio"))
    except:
        try:
            select_anio = Select(driver.find_element(By.ID, "DdlAnio"))
        except:
            select_anio = Select(driver.find_element(By.XPATH, "//select[contains(@id, 'DdlAnio')]"))

    select_anio.select_by_value(full_year)
    logger.info(f"Año seleccionado: {full_year}")
    time.sleep(2)

    # Ingresar RFC
    driver.find_element(By.XPATH, "//*[@id='ctl00_MainContent_TxtRfcReceptor']").send_keys(BuscarRFC)
    Select(driver.find_element(By.ID, "ctl00_MainContent_DdlEstadoComprobante")).select_by_value("1")
    driver.find_element(By.ID, "ctl00_MainContent_BtnBusqueda").click()
    time.sleep(2)


    # Seleccionar estado de comprobante 'vigente' (mejorado)
    logger.info("Seleccionando estado de comprobante...")
    estado_elemento = esperar_elemento_clickeable(
        driver,
        (By.ID, "ctl00_MainContent_DdlEstadoComprobante"),
        timeout=15
    )

    if estado_elemento:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'bottom'});", estado_elemento)
            time.sleep(1)
            estado_select = Select(estado_elemento)
            estado_select.select_by_value("1")
            logger.info("Estado de comprobante seleccionado: vigente")
        except Exception as e:
            logger.error(f"Error al seleccionar estado: {e}")
            # Intentar con JavaScript
            driver.execute_script("""
                var select = document.getElementById('ctl00_MainContent_DdlEstadoComprobante');
                select.value = '1';
                select.dispatchEvent(new Event('change'));
            """)
            logger.info("Estado seleccionado usando JavaScript")
    else:
        logger.error("No se pudo encontrar el elemento de estado")
        return

    time.sleep(2)

    # *** HACER CLIC EN EL BOTÓN "BUSCAR CFDI" ***
    logger.info("Buscando botón 'Buscar CFDI'...")

    # Múltiples métodos para encontrar y hacer clic en el botón
    boton_buscar_encontrado = False

    # Método 1: Por ID
    try:
        boton_buscar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ctl00_MainContent_BtnBusqueda")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_buscar)
        time.sleep(0.5)
        boton_buscar.click()
        logger.info("Botón 'Buscar CFDI' encontrado y clickeado por ID")
        boton_buscar_encontrado = True
    except Exception as e:
        logger.warning(f"No se pudo hacer clic por ID: {e}")

    # Método 2: Por XPath si el anterior falló
    if not boton_buscar_encontrado:
        try:
            boton_buscar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='ctl00_MainContent_BtnBusqueda']")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_buscar)
            time.sleep(0.5)
            boton_buscar.click()
            logger.info("Botón 'Buscar CFDI' encontrado y clickeado por XPath")
            boton_buscar_encontrado = True
        except Exception as e:
            logger.warning(f"No se pudo hacer clic por XPath: {e}")

    # Método 3: Por valor del botón si los anteriores fallaron
    if not boton_buscar_encontrado:
        try:
            boton_buscar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Buscar CFDI']")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_buscar)
            time.sleep(0.5)
            boton_buscar.click()
            logger.info("Botón 'Buscar CFDI' encontrado y clickeado por valor")
            boton_buscar_encontrado = True
        except Exception as e:
            logger.warning(f"No se pudo hacer clic por valor: {e}")

    # Método 4: JavaScript como último recurso
    if not boton_buscar_encontrado:
        try:
            boton_buscar = driver.find_element(By.ID, "ctl00_MainContent_BtnBusqueda")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_buscar)
            time.sleep(0.5)
            driver.execute_script("document.getElementById('ctl00_MainContent_BtnBusqueda').click();")
            logger.info("Botón 'Buscar CFDI' clickeado usando JavaScript")
            boton_buscar_encontrado = True
        except Exception as e:
            logger.error(f"Error al hacer clic con JavaScript: {e}")

    if not boton_buscar_encontrado:
        logger.error("No se pudo encontrar o hacer clic en el botón 'Buscar CFDI'")
        return

    # Esperar a que se carguen los resultados
    logger.info("Esperando a que se carguen los resultados...")
    time.sleep(3)

    # Hacer scroll para cargar todas las facturas (mejorado)
    logger.info("Haciendo scroll para cargar todas las facturas...")

    botones_descarga = driver.find_elements(By.ID, "BtnDescarga") or driver.find_elements(By.XPATH, "//*[@id='BtnDescarga']")
    for index, boton in enumerate(botones_descarga, start=1):
        time.sleep(1)
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton)
            time.sleep(0.5)
            boton.click()
            logger.info(f"Descargando XML {index} de {len(botones_descarga)}")
            esperar_descarga_completa(carpeta_destino)
            if index % 15 == 0:
                time.sleep(1)  # Espera antes de cambiar de página
                try:
                    next_page = driver.find_element(By.XPATH, "/html/body/form/main/div[1]/div[2]"
                                                      "/div[1]/div[2]/div[1]/div[3]/ul/li[36]/a")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page)
                    time.sleep(0.5)
                    next_page.click()
                    logger.info("Página cambiada a .")
                    time.sleep(3)
                except Exception as e:
                    logger.error(f"Error al cambiar de página: {e}")
        except Exception as e:
            logger.error(f"Error al descargar XML {index}: {e}")
        finally:
            continue

    logger.info("Configuración completada. Los resultados deberían estar cargados.")
    time.sleep(2)
    borrar_basura(carpeta_destino)


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

