import logging
import os


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join(ROOT_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app_logs.txt")

# Crear la carpeta de logs si no existe
os.makedirs(LOG_DIR, exist_ok=True)

# Configuración básica del logger
logging.basicConfig(
    filename=LOG_FILE,
    filemode="a", # Append
    format="%(asctime)s - %(levelname)s - %(message)s %(funcName)s:%(lineno)d",
    level=logging.DEBUG,
)

logger = logging.getLogger("AppLogger")
