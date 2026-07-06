import os
from DescargaFacturasSAT.BaseDir import BASE_DIR
from logger_config import logger

base_archivos = os.path.dirname(os.path.abspath(__file__))
RFC_FILE = os.path.join(BASE_DIR, "RFC.txt")
PASSWORD_FILE = os.path.join(BASE_DIR, "passwd.txt")

# Los CFDI nuevos usan namespace 4.0 y los viejos 3.x
CFDI_NAMESPACES = ('http://www.sat.gob.mx/cfd/4', 'http://www.sat.gob.mx/cfd/3')

def conceptos_cfdi(root):
    """Regresa los cfdi:Concepto de un XML, sea CFDI 4.0 o 3.x."""
    for ns in CFDI_NAMESPACES:
        conceptos = root.findall(f'.//{{{ns}}}Concepto')
        if conceptos:
            return conceptos
    return []

def crear_archivos_credenciales(rfc=None, password=None):
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
