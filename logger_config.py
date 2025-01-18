import os
import logging

# Ruta para los logs en la carpeta del usuario
LOG_DIR = os.path.join(os.path.expanduser("~"), "FacturaDML", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar logger
LOG_FILE = os.path.join(LOG_DIR, "application.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s - (%(filename)s:%(lineno)d)",
)
logger = logging.getLogger(__name__)
