import logging
import os


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directorio raíz del proyecto

# Define la carpeta de logs y el archivo de logs
LOG_DIR = os.path.join(ROOT_DIR, "logs")  # Carpeta de logs
LOG_FILE = os.path.join(LOG_DIR, "app_logs.txt")  # Archivo de logs dentro de la carpeta

# Crear la carpeta de logs si no existe
os.makedirs(LOG_DIR, exist_ok=True)

# Configuración básica del logger
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a",  # Agregar logs al archivo en lugar de sobrescribirlo
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,  # Cambiar a DEBUG para más detalles
)

# Crear un logger reutilizable
logger = logging.getLogger("AppLogger")
