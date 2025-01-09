import sys
from contextlib import nullcontext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import Select
import xml.etree.ElementTree as ET
import hashlib
import glob
from logger_config import logger
from PIL import Image
from io import BytesIO
import time
import os


def preguntar_mes():
    meses_a_descargar = {
        "enero": "1", "febrero": "2", "marzo": "3", "abril": "4",
        "mayo": "5", "junio": "6","julio": "7", "agosto": "8",
        "septiembre": "9", "octubre": "10", "noviembre": "11", "diciembre": "12"}

    mes = input("Ingresa el mes que deseas descargar (enero, febrero, etc...): ").lower()
    if mes in meses_a_descargar:
        return meses_a_descargar[mes]
    else:
        print("Mes inválido.")
        return preguntar_mes()

def preguntar_anio():
    anio = input("Ingresa los dos últimos dígitos del año que deseas descargar (ej. 21): ")
    if len(anio) == 2 and anio.isnumeric():
        anio_completo = int("20" + anio)
        anio_actual = int(time.strftime("%Y"))
        if anio_completo <= anio_actual:
            return anio
        else:
            print("Año inválido. No intente viajar al futuro.")
    else:
        print("Año inválido.")
    return preguntar_anio()

# Configuración
SAT_URL = "https://portalcfdi.facturaelectronica.sat.gob.mx/"
DEMO_URL = "https://www.boxfactura.com/sat-captcha-ai-model/"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RFC_FILE = os.path.join(BASE_DIR, "RFC.txt")
PASSWORD_FILE = os.path.join(BASE_DIR, "passwd.txt")
CAPTCHA_FILE = os.path.join(BASE_DIR, "captcha_sat.png")
BuscarRFC = "GCO740121MC5"

def crear_archivos_credenciales(rfc=None, password=None):
    """Crea los archivos de credenciales si no existen."""
    if not os.path.exists(RFC_FILE):
        if not rfc:
            raise ValueError("El RFC no se proporcionó y no existe un archivo.")
        with open(RFC_FILE, 'w') as rfc_file:
            rfc_file.write(rfc)
        logger.info(f"Archivo RFC creado correctamente: {RFC_FILE}")
    else:
        logger.info("El archivo RFC ya existe.")

    if not os.path.exists(PASSWORD_FILE):
        if not password:
            raise ValueError("La contraseña no se proporcionó y no existe un archivo.")
        with open(PASSWORD_FILE, 'w') as password_file:
            password_file.write(password)
        logger.info(f"Archivo de contraseña creado correctamente: {PASSWORD_FILE}")
    else:
        logger.info("El archivo de contraseña ya existe.")


def cargar_credenciales():
    try:
        with open(RFC_FILE, 'r') as rfc_file:
            rfc_content = rfc_file.read().strip()
        with open(PASSWORD_FILE, 'r') as password_file:
            password_content = password_file.read().strip()
        return rfc_content, password_content
    except FileNotFoundError:
        logger.error("Uno o ambos archivos de credenciales no se encontraron.")
        crear_archivos_credenciales()
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

    service = Service(executable_path=os.path.join(os.getcwd(),"geckodriver.exe"))
    driver = webdriver.Firefox(service=service, options=options)
    return driver

# Descargar captcha del SAT
def descargar_captcha(driver):
    captcha_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "divCaptcha"))
    )
    captcha_screenshot = captcha_element.screenshot_as_png
    time.sleep(2)
    captcha_image = Image.open(BytesIO(captcha_screenshot))
    captcha_image.save(CAPTCHA_FILE)
    print(f"Captcha guardado en {CAPTCHA_FILE}")
    return CAPTCHA_FILE

# Resolver captcha en pagina
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
            print(f"Error al resolver captcha: {e}")
        return captcha_result
    print(f"Captcha resuelto: {captcha_result}")
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
    print("Intentando iniciar sesión en el SAT...")

# Verificar errores de inicio de sesion
def verificar_error(driver):
    try:
        error_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "msgError"))
        ).text
        print(f"Error detectado: {error_message}")
        intentos_maximos = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "")))
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
    print(f"Carpeta creada o ya existente: {ruta_mes}")
    return ruta_mes

# Descargar XML Recibidos
def descarga(driver, carpeta_destino, mes, year):
    time.sleep(2)
    # Navegar a la sección de Recibidos
    boton_recibidos = WebDriverWait(driver, 10).until(
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
    select_anio.select_by_value("20" + year)
    # Ingresar RFC
    driver.find_element(By.XPATH, "//*[@id='ctl00_MainContent_TxtRfcReceptor']").send_keys(BuscarRFC)
    Select(driver.find_element(By.ID, "ctl00_MainContent_DdlEstadoComprobante")).select_by_value("1")
    driver.find_element(By.ID, "ctl00_MainContent_BtnBusqueda").click()
    time.sleep(1)
    # Se va hasta abajo de la página para cargar todas las facturas
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    botones_descarga = driver.find_elements(By.ID, "BtnDescarga") or driver.find_elements(By.XPATH, "//*[@id='BtnDescarga']")
    for index, boton in enumerate(botones_descarga, start=1):
        try:
            # Descarga el archivo
            time.sleep(1)  # Espera breve para evitar sobrecargar la página
            boton.click()
            print(f"Descargando XML {index} de {len(botones_descarga)}")
            esperar_descarga_completa(carpeta_destino)
            if index % 15 == 0:
                time.sleep(1)  # Espera antes de cambiar de página
                try:
                    driver.find_element(By.XPATH, "/html/body/form/main/div[1]/div[2]"
                                                  "/div[1]/div[2]/div[1]/div[3]/ul/li[36]/a").click()

                    print("Página cambiada a .")
                    time.sleep(3)
                except Exception as e:
                    print(f"Error al cambiar de página: {e}")
        except Exception as e:
            print(f"Error al descargar XML {index}: {e}")
        finally:
            continue

    print("Descarga finalizada.")
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
        print(f"Archivo duplicado eliminado: {duplicado}")
    print(f"Total duplicados eliminados: {len(duplicados)}")

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
                print(f"Factura eliminada (sin importes válidos): {ruta_archivo}")
                facturas_eliminadas += 1

        except Exception as e:
            print(f"Error al procesar {ruta_archivo}: {e}")

    print(f"Total facturas eliminadas: {facturas_eliminadas}")
    time.sleep(1)
    cambiar_nombre(ruta_mes)
    time.sleep(1)
    sys.exit()

def cambiar_nombre(ruta_mes): # Cambia el nombre segun el Folio
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
            print(f"Archivo renombrado: D{folio}.xml")
        except Exception as e:
            print(f"Error al procesar {ruta_archivo}: {e}")
        finally:
            continue


if __name__ == "__main__":

    base_dir = os.getcwd()
    crear_archivos_credenciales()
    try:
        rfc, password = cargar_credenciales()
    except Exception as e:
        print(f"Error al cargar las credenciales: {e}")
        sys.exit(1)
    year = preguntar_anio()
    mes = preguntar_mes()
    carpeta_destino = crear_estructura_carpetas(base_dir, "20" + year, mes, BuscarRFC)
    driver = configurar_navegador(carpeta_destino)
    intentos = 0
    max_intentos = 3
    try:
        driver.get(SAT_URL)
        while intentos < max_intentos:
            try:
                time.sleep(1)
                captcha_path = descargar_captcha(driver)
                captcha_text = resolver_captcha_en_demo(driver, captcha_path)
                iniciar_sesion_en_sat(driver, rfc, password, captcha_text)
                if verificar_error(driver):
                    intentos += 1
                    print(f"Reintentando... ({intentos}/{max_intentos})")
                    driver.get(SAT_URL)  # Recargar página
                else:
                    descarga(driver, carpeta_destino, mes, year)
                    break
            except Exception as e:
                print(f"Error durante el intento: {e}")
                intentos += 1
        if intentos == max_intentos:
            print("Se alcanzó el límite máximo de intentos.")
    finally:
        driver.quit()
        print("Navegador cerrado.")
        sys.exit()