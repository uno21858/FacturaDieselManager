import time
import sys
from PySide6 import QtWidgets as qtw

from Credenciales.UI.credenciales_windows import Ui_Form
from DescargaFacturasSAT.DescargaFactura import crear_archivos_credenciales
from logger_config import logger


class UiForm(qtw.QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.pb_Cancel.clicked.connect(self.close)
        self.pb_Ok.clicked.connect(self.guardar_credenciales)

    def guardar_credenciales(self):
        try:
            rfc = self.le_RFC.text().strip().upper()
            password = self.le_passwd.text().strip()

            if len(rfc) != 12:
                self.lb_message.setText("RFC inválido. Debe tener 12 caracteres.")
                logger.warning("Intento de guardar credenciales con RFC inválido.")
                return

            if not password:
                self.lb_message.setText("La contraseña no puede estar vacía.")
                logger.warning("Intento de guardar credenciales sin contraseña.")
                return

            crear_archivos_credenciales(rfc=rfc, password=password)
            self.lb_message.setText("Credenciales guardadas correctamente.")
            logger.info("Credenciales guardadas correctamente.")
            time.sleep(1)
            self.close()
        except Exception as e:
            logger.error(f"Error al guardar credenciales: {e}")
            self.lb_message.setText("Ocurrió un error al guardar las credenciales.")
        finally:
            pass

def log_uncaught_exceptions(exctype, value, tb):
    """Captura todas las excepciones no manejadas."""
    logger.critical("Excepción no manejada", exc_info=(exctype, value, tb))
    sys.__excepthook__(exctype, value, tb)

def MainCreateCredentials():
    # Configuración global para capturar excepciones no manejadas
    sys.excepthook = log_uncaught_exceptions

    app = qtw.QApplication(sys.argv)

    # Mostrar la ventana de las credenciales
    window = UiForm()
    window.show()

    sys.exit(app.exec())

