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


    # detecta el OS
    import platform
    if platform.system() == "Windows":
        service = Service(executable_path=os.path.join(BASE_DIR,"geckodriver.exe"))
        driver = webdriver.Firefox(service=service, options=options)
    else:  # Mac/Linux
        driver = webdriver.Firefox(options=options)  # Usa geckodriver del PATH
    return driver

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
        time.sleep(10)
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

# Descargar XML Recibidos
def descarga(driver, carpeta_destino, year, mes=1):
    time.sleep(1)
    # Navegar a la sección de Recibidos
    boton_recibidos = WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/form/main/div[1]/div[2]/div[1]/div/div[1]/div/nav/ul/div[2]/li/a")))
    boton_recibidos.click()
    time.sleep(2)
    logger.info("✓ Navegado a Recibidos")

    # Seleccionar rango de fechas
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

    # Seleccionar mes y año
    logger.info(f"Seleccionando mes: {mes} y año: {year}")
    select_mes = Select(driver.find_element(By.ID, "ctl00_MainContent_CldFecha_DdlMes"))
    select_mes.select_by_value(str(mes))
    select_anio = (Select(driver.find_element(By.XPATH, "//*[@id='DdlAnio']")) or
                   driver.find_elements(By.NAME, "ctl00$MainContent$CldFecha$DdlAnio"))
    select_anio.select_by_value(str(year))

    # Ingresar RFC
    logger.info(f"Ingresando RFC: {BuscarRFC}")
    rfc_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ctl00_MainContent_TxtRfcReceptor")))
    rfc_input.clear()
    rfc_input.send_keys(BuscarRFC)
    time.sleep(1)

    # Seleccionar estado de comprobante 'vigente'
    logger.info("Seleccionando estado de comprobante...")
    estado_elemento = esperar_elemento_clickeable(
        driver,
        (By.ID, "ctl00_MainContent_DdlEstadoComprobante"),
        timeout=15
    )

    if estado_elemento:
        try:
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

    time.sleep(.3)

    # Hacer clic en el botón "Buscar CFDI" con JavaScript
    logger.info("Ejecutando búsqueda de CFDIs...")
    try:
        boton_buscar = driver.find_element(By.ID, "ctl00_MainContent_BtnBusqueda")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_buscar)
        time.sleep(1)
        # Ejecutar directamente el código JavaScript del onclick del botón
        driver.execute_script("""
            ocultaResultados();
            WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions("ctl00$MainContent$BtnBusqueda", "", true, "Fechas", "", false, false));
        """)
        logger.info("✓ Búsqueda ejecutada")
    except Exception as e:
        logger.error(f"Error al ejecutar búsqueda con JavaScript: {e}")
        # Último intento: click directo
        try:
            boton_buscar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "ctl00_MainContent_BtnBusqueda")))
            boton_buscar.click()
            logger.info("✓ Búsqueda ejecutada (click directo)")
        except Exception as e2:
            logger.error(f"No se pudo hacer clic en el botón: {e2}")
            return

    # Esperar a que se carguen los resultados
    logger.info("Esperando a que se carguen los resultados...")
    try:
        tabla_resultados = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "ctl00_MainContent_tblResult")))
        logger.info("✓ Tabla de resultados encontrada")
        time.sleep(3)
    except Exception as e:
        logger.error(f"No se encontró la tabla de resultados: {e}")
        return

    # Buscar todos los botones de descarga usando el selector mejorado
    logger.info("Buscando botones de descarga...")
    botones_descarga = driver.find_elements(By.XPATH, "//span[@name='BtnDescarga']")
    try:
        # Encontrar el botón primero
        boton_buscar = driver.find_element(By.ID, "ctl00_MainContent_BtnBusqueda")

        # Hacer scroll solo hasta el botón (no hasta el final)
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_buscar)
        time.sleep(3)

        # Ejecutar directamente el código JavaScript del onclick del botón
        logger.info("Ejecutando click en botón 'Buscar CFDI'...")
        driver.execute_script("""
                ocultaResultados();
                WebForm_DoPostBackWithOptions(new WebForm_PostBackOptions("ctl00$MainContent$BtnBusqueda", "", true, "Fechas", "", false, false));
            """)*2
        logger.info("Botón 'Buscar CFDI' ejecutado con JavaScript")

    except Exception as e:
        logger.error(f"Error al ejecutar búsqueda: {e}")
        # Último intento: click directo
        try:
            boton_buscar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "ctl00_MainContent_BtnBusqueda")))
            boton_buscar.click()
            logger.info("Botón 'Buscar CFDI' clickeado directamente")
        except Exception as e2:
            logger.error(f"No se pudo hacer clic en el botón: {e2}")
            return

    # Esperar a que se carguen los resultados
    logger.info("Esperando a que se carguen los resultados...")

    # Esperar a que aparezca la tabla de resultados
    try:
        tabla_resultados = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "ctl00_MainContent_tblResult")))
        logger.info("Tabla de resultados encontrada")
        time.sleep(3)
    except Exception as e:
        logger.error(f"No se encontró la tabla de resultados: {e}")
        return

    # Buscar todos los botones de descarga XML
    logger.info("Buscando botones de descarga XML...")
    botones_xml = driver.find_elements(By.XPATH, "//span[@name='BtnDescarga']")

    logger.info(f"Total de botones XML encontrados: {len(botones_xml)}")

    if len(botones_xml) == 0:
        logger.warning("No se encontraron facturas para descargar")
        return

    for index in range(len(botones_xml)):
        time.sleep(1)
        try:
            botones_xml = driver.find_elements(By.XPATH, "//span[@name='BtnDescarga']")

            # Descargar XML
            if index < len(botones_xml):
                time.sleep(0.5)
                try:
                    # Intentar scroll y click normal
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botones_xml[index])
                        time.sleep(0.3)
                        botones_xml[index].click()
                    except:
                        # Si falla, usar JavaScript click directamente
                        driver.execute_script("arguments[0].click();", botones_xml[index])

                    logger.info(f"Descargando XML {index + 1} de {len(botones_xml)}")
                    esperar_descarga_completa(carpeta_destino)
                except Exception as e:
                    logger.error(f"Error al descargar XML {index + 1}: {e}")

            # Cambiar de página cada 15 facturas
            if (index + 1) % 15 == 0:
                time.sleep(1)
                try:
                    boton_siguiente = None

                    # Método 1: Por texto "»"
                    try:
                        boton_siguiente = driver.find_element(By.XPATH, "//ul[contains(@class, 'pagination')]//a[text()='»']")
                    except:
                        pass

                    # Método 2: Por posición relativa
                    if not boton_siguiente:
                        try:
                            boton_siguiente = driver.find_element(By.XPATH, "//ul[contains(@class, 'pagination')]//li[last()]/a")
                        except:
                            pass

                    # Método 3: XPath original
                    if not boton_siguiente:
                        try:
                            boton_siguiente = driver.find_element(By.XPATH, "/html/body/form/main/div/div[2]/div[1]/div[2]/div[1]/div[3]/ul/li[6]/a")
                        except:
                            pass

                    if boton_siguiente:
                        boton_siguiente.click()
                        logger.info("Página cambiada.")
                        time.sleep(3)
                    else:
                        logger.warning("No se encontró botón de siguiente página, continuando...")

                except Exception as e:
                    logger.error(f"Error al cambiar de página: {e}")

        except Exception as e:
            logger.error(f"Error al procesar factura {index + 1}: {e}")
            continue



    logger.info("Configuración completada. Los resultados deberían estar cargados.")
    time.sleep(2)
    borrar_basura(carpeta_destino)

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

            try:
                element.click()
                return element
            except:
                driver.execute_script("arguments[0].click();", element)
                return element
        except:
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
        if 'driver' in locals():
            driver.quit()
        logger.info("Descarga finalizada.")
