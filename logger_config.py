import os
import logging
from logging.handlers import RotatingFileHandler

# Ruta para los logs en la carpeta del usuario
LOG_DIR = os.path.join(os.path.expanduser("~"), "FacturaDML", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar logger con rotación: máximo 2 MB por archivo, 2 respaldos
LOG_FILE = os.path.join(LOG_DIR, "application.log")
logging.basicConfig(
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=2, encoding="utf-8")],
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s - (%(filename)s:%(lineno)d)",
)
logger = logging.getLogger(__name__)

# Silenciar el DEBUG de librerías externas: al archivo solo llegan sus WARNING+
for _noisy in ("selenium", "urllib3", "PIL", "trio", "trio_websocket"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)
